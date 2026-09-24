from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .database import Database
from .models import (
    AutomationSettingsInput,
    DataSettingsInput,
    RunInput,
    WatchlistInput,
    WebhookSettingsInput,
    normalize_symbol,
)
from .service import AnalysisService
from .webhooks import WebhookError, validate_url


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_HOME = Path(os.environ.get("CHANLUN_LOCAL_HOME", PROJECT_ROOT / "data")).expanduser()
STATIC_DIR = PROJECT_ROOT / "static"

database = Database(DATA_HOME / "chanlun-local.sqlite3")
service = AnalysisService(database)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def _scheduled(session: str) -> None:
    settings = database.get_settings(reveal_secrets=False)
    await asyncio.to_thread(
        service.run_all,
        session=session,
        notify=settings.get("default_send_report") == "1",
        skip_non_trade_day=True,
    )


def _configure_scheduler() -> None:
    for job_id in ("premarket", "after_close"):
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
    settings = database.get_settings(reveal_secrets=False)
    if settings.get("automatic_enabled", "1") != "1":
        return
    schedules = (
        ("premarket", settings.get("premarket_time", "08:30")),
        ("after_close", settings.get("after_close_time", "18:00")),
    )
    for job_id, clock in schedules:
        hour, minute = (int(part) for part in clock.split(":"))
        scheduler.add_job(
            _scheduled,
            CronTrigger(
                day_of_week="mon-fri",
                hour=hour,
                minute=minute,
                timezone="Asia/Shanghai",
            ),
            args=[job_id],
            id=job_id,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=21600,
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _configure_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
    database.close()


app = FastAPI(title="缠论本地工作台", version="0.1.0", lifespan=lifespan)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "ai_tokens": 0,
        "scheduler": [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ],
    }


@app.get("/api/state")
def state():
    settings = database.get_settings(reveal_secrets=False)
    return {
        "settings": settings,
        "watchlist": database.list_watchlist(),
        "reports": database.list_reports(50),
        "schedule": {
            "enabled": settings.get("automatic_enabled", "1") == "1",
            "premarket": settings.get("premarket_time", "08:30"),
            "after_close": settings.get("after_close_time", "18:00"),
            "default_send_report": settings.get("default_send_report", "0") == "1",
        },
    }


@app.post("/api/watchlist")
def save_watch(item: WatchlistInput):
    database.upsert_watch(item.symbol, item.name, item.enabled, item.source)
    return {"ok": True, "watchlist": database.list_watchlist()}


@app.delete("/api/watchlist/{symbol}")
def remove_watch(symbol: str):
    try:
        full = normalize_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    database.delete_watch(full)
    return {"ok": True}


@app.post("/api/settings/data")
def save_data_settings(item: DataSettingsInput):
    database.set_settings(item.model_dump())
    return {"ok": True, "settings": database.get_settings(reveal_secrets=False)}


@app.post("/api/settings/webhooks")
def save_webhooks(item: WebhookSettingsInput):
    try:
        if item.feishu_url:
            validate_url("feishu", item.feishu_url)
        if item.wecom_url:
            validate_url("wecom", item.wecom_url)
    except WebhookError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    database.set_settings(item.model_dump())
    return {"ok": True, "settings": database.get_settings(reveal_secrets=False)}


@app.post("/api/settings/automation")
def save_automation(item: AutomationSettingsInput):
    database.set_settings(item.model_dump())
    _configure_scheduler()
    return {
        "ok": True,
        "settings": database.get_settings(reveal_secrets=False),
        "jobs": [job.id for job in scheduler.get_jobs()],
    }


@app.post("/api/run")
async def run_analysis(item: RunInput):
    return await asyncio.to_thread(
        service.run_all,
        session=item.session,
        symbols=item.symbols,
        notify=item.notify,
        skip_non_trade_day=False,
    )


@app.post("/api/webhooks/test")
async def test_webhooks():
    return await asyncio.to_thread(service.test_webhooks)


@app.get("/api/reports")
def reports(limit: int = 50):
    return {"reports": database.list_reports(max(1, min(limit, 200)))}


@app.get("/api/reports/{report_id}")
def report(report_id: str):
    result = database.get_report(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="报告不存在")
    return result


def main() -> None:
    import uvicorn

    port = int(os.environ.get("CHANLUN_LOCAL_PORT", "8792"))
    uvicorn.run("chanlun_local.app:app", host="127.0.0.1", port=port, workers=1)


if __name__ == "__main__":
    main()
