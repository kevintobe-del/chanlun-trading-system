"""Integrated multi-timeframe reports backed by the bundled local Chanlun project.

The visual workbench owns market-source selection.  The local-report engine
reuses that one active source and only owns report lookbacks, scheduling,
notification secrets, cached bars and report history.
"""

from __future__ import annotations

import asyncio
import os
import re
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .providers import active_source, canonical_symbol
from .watchlists import load_watchlists


_DB: Any = None
_DB_LOCK = threading.Lock()
_ENGINE_LOCK = threading.Lock()
_SCHEDULER = AsyncIOScheduler(timezone="Asia/Shanghai")


def _data_home() -> Path:
    override = os.environ.get("CHANLUN_REPORT_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / "chanlun-visual" / "reports"


def _database():
    global _DB
    with _DB_LOCK:
        if _DB is None:
            from chanlun_local.database import Database

            _DB = Database(_data_home() / "chanlun-reports.sqlite3")
    return _DB


def close_report_database() -> None:
    global _DB
    with _DB_LOCK:
        if _DB is not None:
            _DB.close()
            _DB = None


def _bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value is True or str(value).lower() in {"1", "true", "yes", "on"}


def public_report_settings() -> dict[str, Any]:
    settings = _database().get_settings(reveal_secrets=False)
    source = active_source()
    return {
        "analysis": {
            "daily_years": int(settings.get("daily_years", "5")),
            "minute30_years": int(settings.get("minute30_years", "2")),
            "minute5_days": int(settings.get("minute5_days", "180")),
        },
        "webhooks": {
            "feishu_enabled": _bool(settings.get("feishu_enabled")),
            "feishu_configured": settings.get("feishu_url") == "configured",
            "feishu_secret_configured": settings.get("feishu_secret") == "configured",
            "wecom_enabled": _bool(settings.get("wecom_enabled")),
            "wecom_configured": settings.get("wecom_url") == "configured",
        },
        "automation": {
            "automatic_enabled": _bool(settings.get("automatic_enabled"), True),
            "premarket_time": settings.get("premarket_time", "08:30"),
            "after_close_time": settings.get("after_close_time", "18:00"),
            "default_send_report": _bool(settings.get("default_send_report")),
        },
        "shared_source": {
            "id": source["id"],
            "provider": source["provider"],
            "name": source["name"],
        },
    }


def save_analysis_settings(values: dict[str, Any]) -> dict[str, Any]:
    _database().set_settings(values)
    return public_report_settings()


def save_webhook_settings(values: dict[str, Any]) -> dict[str, Any]:
    from chanlun_local.webhooks import validate_url

    if values.get("feishu_url"):
        validate_url("feishu", values["feishu_url"])
    if values.get("wecom_url"):
        validate_url("wecom", values["wecom_url"])
    _database().set_settings(values)
    return public_report_settings()


def save_automation_settings(values: dict[str, Any]) -> dict[str, Any]:
    _database().set_settings(values)
    configure_report_scheduler()
    return public_report_settings()


def _engine_symbol(symbol: str) -> str:
    canonical = canonical_symbol(symbol)
    if not re.fullmatch(r"\d{6}\.(SS|SZ|BJ)", canonical):
        raise ValueError("多周期缠论报告当前仅支持 A 股六位证券代码")
    return canonical.replace(".SS", ".SH")


def _provider_settings(source: dict[str, Any], settings: dict[str, str]) -> tuple[str, dict[str, str]]:
    mapping = {"yfinance": "yahoo", "akshare": "akshare", "tushare": "tushare"}
    provider = mapping.get(str(source.get("provider")))
    if not provider:
        raise RuntimeError("当前行情数据源不支持生成多周期报告")
    shared = dict(settings)
    if provider == "tushare":
        shared["tushare_token"] = str(source.get("api_key") or "")
    return provider, shared


def _range_start(timeframe: str, now: datetime, settings: dict[str, str]) -> datetime:
    if timeframe == "1d":
        return now - timedelta(days=int(settings.get("daily_years", "5")) * 366)
    if timeframe == "30m":
        return now - timedelta(days=int(settings.get("minute30_years", "2")) * 366)
    return now - timedelta(days=int(settings.get("minute5_days", "180")))


def _cache_sources(provider_name: str) -> set[str]:
    if provider_name == "akshare":
        return {"akshare", "akshare_sina", "akshare_tencent"}
    return {provider_name}


def generate_report(
    symbol: str,
    name: str = "",
    session: str = "manual",
    notify: bool = False,
) -> dict[str, Any]:
    """Fetch three levels from the shared source and run the deterministic engine."""
    from chanlun_local.engine import analyze_multilevel
    from chanlun_local.providers import build_provider
    from chanlun_local.reporting import build_report
    from chanlun_local.webhooks import configured_platforms, send_report

    db = _database()
    settings = db.get_settings(reveal_secrets=True)
    source = active_source()
    provider_name, provider_settings = _provider_settings(source, settings)
    provider = build_provider(provider_name, provider_settings)
    engine_symbol = _engine_symbol(symbol)
    now = datetime.now()
    refresh: dict[str, Any] = {
        "provider": source["provider"],
        "source_name": source["name"],
        "timeframes": {},
    }

    for timeframe in ("1d", "30m", "5m"):
        desired_start = _range_start(timeframe, now, settings)
        latest = db.last_bar_time(engine_symbol, timeframe)
        overlap = timedelta(days=10 if timeframe == "1d" else 3)
        start = max(desired_start, latest - overlap) if latest else desired_start
        try:
            bars = provider.fetch(engine_symbol, timeframe, start, now)
            count = db.upsert_bars(bars)
            refresh["timeframes"][timeframe] = {
                "fetched": count,
                "start": bars[0].ts.isoformat(sep=" ") if bars else None,
                "end": bars[-1].ts.isoformat(sep=" ") if bars else None,
            }
        except Exception as exc:
            refresh["timeframes"][timeframe] = {"error": str(exc)}

    bars_by_level = {
        timeframe: db.load_bars(
            engine_symbol,
            timeframe,
            _range_start(timeframe, now, settings),
            _cache_sources(provider.name),
        )
        for timeframe in ("1d", "30m", "5m")
    }
    if not any(bars_by_level.values()):
        errors = [
            detail.get("error")
            for detail in refresh["timeframes"].values()
            if detail.get("error")
        ]
        raise RuntimeError(errors[0] if errors else "当前数据源没有返回可用于报告的行情")

    # chan.py's in-memory adapter uses a process-global row buffer. Serialize
    # calculations so an automatic run and a user's search cannot cross-feed bars.
    with _ENGINE_LOCK:
        result = analyze_multilevel(engine_symbol, bars_by_level)
    result["data_refresh"] = refresh
    report_text = build_report(name or engine_symbol, result, session)
    status = result["verdict"]["action"]
    report_id = db.save_report(
        symbol=engine_symbol,
        name=name or engine_symbol,
        session=session,
        asof=result["meta"].get("asof") or "",
        status=status,
        report_text=report_text,
        result=result,
    )
    if notify:
        title = f"{name or engine_symbol}（{engine_symbol}）缠论分析"
        for platform, url, secret in configured_platforms(settings):
            send_report(platform, url, report_text, title, secret)
    return {
        "id": report_id,
        "symbol": engine_symbol,
        "name": name or engine_symbol,
        "status": status,
        "report_text": report_text,
        "result": result,
        "source": {"provider": source["provider"], "name": source["name"]},
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def list_reports(limit: int = 50) -> dict[str, Any]:
    return {"reports": _database().list_reports(max(1, min(limit, 200)))}


def get_report(report_id: str) -> dict[str, Any] | None:
    return _database().get_report(report_id)


def test_webhooks() -> dict[str, Any]:
    from chanlun_local.webhooks import configured_platforms, send_report

    settings = _database().get_settings(reveal_secrets=True)
    output = []
    for platform, url, secret in configured_platforms(settings):
        try:
            response = send_report(
                platform,
                url,
                "缠论可视研究工作台 Webhook 测试成功。此消息不包含行情或交易建议。",
                "连接测试",
                secret,
            )
            output.append({"platform": platform, "ok": True, "response": response})
        except Exception as exc:
            output.append({"platform": platform, "ok": False, "error": str(exc)})
    return {"results": output}


def _scheduled_symbols() -> list[dict[str, str]]:
    watchlists = load_watchlists()
    unique: dict[str, dict[str, str]] = {}
    for pool in watchlists.get("pools", []):
        for item in pool.get("items", []):
            unique[item["symbol"]] = {
                "symbol": item["symbol"],
                "name": item.get("name") or item["symbol"],
            }
    return list(unique.values())


def _is_trade_date() -> bool:
    """Use the shared provider's calendar before running automatic reports."""
    from chanlun_local.providers import build_provider

    settings = _database().get_settings(reveal_secrets=True)
    source = active_source()
    provider_name, provider_settings = _provider_settings(source, settings)
    return build_provider(provider_name, provider_settings).is_trade_date(datetime.now().date())


async def _scheduled_run(session: str) -> None:
    try:
        if not await asyncio.to_thread(_is_trade_date):
            return
    except Exception:
        # A calendar lookup failure should not trigger a potentially stale batch.
        return
    settings = _database().get_settings(reveal_secrets=False)
    notify = _bool(settings.get("default_send_report"))
    for item in _scheduled_symbols():
        try:
            await asyncio.to_thread(
                generate_report,
                item["symbol"],
                item["name"],
                session,
                notify,
            )
        except Exception:
            # One symbol must not prevent the rest of the pool from running.
            continue


def configure_report_scheduler() -> None:
    for job_id in ("chanlun-premarket", "chanlun-after-close"):
        if _SCHEDULER.get_job(job_id):
            _SCHEDULER.remove_job(job_id)
    settings = _database().get_settings(reveal_secrets=False)
    if not _bool(settings.get("automatic_enabled"), True):
        return
    schedules = (
        ("chanlun-premarket", "premarket", settings.get("premarket_time", "08:30")),
        ("chanlun-after-close", "after_close", settings.get("after_close_time", "18:00")),
    )
    for job_id, session, clock in schedules:
        hour, minute = (int(part) for part in clock.split(":"))
        _SCHEDULER.add_job(
            _scheduled_run,
            CronTrigger(day_of_week="mon-fri", hour=hour, minute=minute, timezone="Asia/Shanghai"),
            args=[session],
            id=job_id,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=21600,
        )


def start_report_scheduler() -> None:
    configure_report_scheduler()
    if not _SCHEDULER.running:
        _SCHEDULER.start()


def stop_report_scheduler() -> None:
    if _SCHEDULER.running:
        _SCHEDULER.shutdown(wait=False)
    close_report_database()
