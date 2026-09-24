"""Local-only FastAPI application for the visual workbench."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .engine import DataQualityError, analyze, demo_bundle
from .export import snapshot_html
from .providers import (
    active_source,
    activate_source,
    add_source,
    canonical_symbol,
    configured_bars,
    delete_source,
    instrument_display_name,
    MarketAccessError,
    MarketRateLimitError,
    public_source_config,
)
from .multilevel_reports import (
    generate_report,
    get_report,
    list_reports,
    public_report_settings,
    save_analysis_settings,
    save_automation_settings,
    save_webhook_settings,
    start_report_scheduler,
    stop_report_scheduler,
    test_webhooks,
)
from .watchlists import (
    add_pool_item,
    create_pool,
    delete_pool,
    load_watchlists,
    record_search,
    remove_pool_item,
)


class AnalyzeRequest(BaseModel):
    symbol: str = Field(default="LOCAL", max_length=32)
    timeframe: str = Field(default="1d", max_length=8)
    source: str = Field(default="user_csv", max_length=64)
    bars: List[Dict[str, Any]] = Field(min_length=1, max_length=20000)


class ExportRequest(BaseModel):
    analysis: Dict[str, Any]


class DataSourceCreateRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    api_key: str = Field(default="", max_length=512)


class WatchlistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class WatchlistItemRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    name: str = Field(default="", max_length=64)


class ReportRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    name: str = Field(default="", max_length=64)
    session: str = Field(default="manual", pattern="^(manual|premarket|after_close)$")
    notify: bool = False


class ReportAnalysisSettingsRequest(BaseModel):
    daily_years: int = Field(default=5, ge=2, le=20)
    minute30_years: int = Field(default=2, ge=1, le=10)
    minute5_days: int = Field(default=180, ge=30, le=3650)


class ReportWebhookSettingsRequest(BaseModel):
    feishu_enabled: bool = False
    feishu_url: str | None = Field(default=None, max_length=2048)
    feishu_secret: str | None = Field(default=None, max_length=512)
    wecom_enabled: bool = False
    wecom_url: str | None = Field(default=None, max_length=2048)


class ReportAutomationSettingsRequest(BaseModel):
    automatic_enabled: bool = True
    premarket_time: str = Field(default="08:30", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    after_close_time: str = Field(default="18:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    default_send_report: bool = False


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_report_scheduler()
    yield
    stop_report_scheduler()


app = FastAPI(
    title="Chanlun Visual Research Workbench",
    version=__version__,
    description="Local research proxy only; no trading execution.",
    lifespan=lifespan,
)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": __version__, "execution_allowed": False}


@app.get("/api/demo")
def demo(symbol: str = Query(default="DEMO", max_length=24)) -> Dict[str, Any]:
    bundle = demo_bundle(symbol)
    bundle["name"] = "演示标的"
    return bundle


@app.post("/api/analyze")
def analyze_bars(request: AnalyzeRequest) -> Dict[str, Any]:
    try:
        return analyze(request.bars, request.symbol, request.timeframe, request.source)
    except DataQualityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/quote")
def quote(symbol: str = Query(min_length=1, max_length=24)) -> Dict[str, Any]:
    try:
        provider_symbol = canonical_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    frames = {}
    failures = {}
    try:
        source = active_source()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    source_name = source["name"]
    source_provider = source["provider"]
    timeframes = ("1d", "60m", "30m", "5m")
    provider_error = None
    for index, timeframe in enumerate(timeframes):
        try:
            bars, _ = configured_bars(provider_symbol, timeframe, source)
            frames[timeframe] = analyze(bars, provider_symbol, timeframe, f"{source_provider}:{source_name}")
        except (MarketRateLimitError, MarketAccessError) as exc:
            provider_error = exc
            failures[timeframe] = str(exc)
            for skipped in timeframes[index + 1:]:
                failures[skipped] = "已停止后续请求，避免继续触发上游限制"
            break
        except Exception as exc:  # provider failures must remain visible per timeframe
            failures[timeframe] = str(exc)
    if not frames:
        message = str(provider_error) if provider_error else next(
            iter(failures.values()), "当前数据源行情暂不可用"
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": message,
                "provider": source_name,
                "retryable": isinstance(provider_error, MarketRateLimitError),
                "failures": failures,
            },
        )
    display_name = instrument_display_name(provider_symbol)
    try:
        record_search(provider_symbol, display_name)
    except RuntimeError:
        pass
    return {
        "symbol": provider_symbol,
        "name": display_name,
        "requested_symbol": symbol,
        "source": f"{source_provider}:{source_name}",
        "is_synthetic": False,
        "frames": frames,
        "failures": failures,
    }


@app.get("/api/watchlists")
def get_watchlists() -> Dict[str, Any]:
    try:
        return load_watchlists()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/watchlists", status_code=201)
def add_watchlist(request: WatchlistCreateRequest) -> Dict[str, Any]:
    try:
        return create_pool(request.name)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/watchlists/{pool_id}")
def remove_watchlist(pool_id: str) -> Dict[str, Any]:
    try:
        return delete_pool(pool_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/watchlists/{pool_id}/items")
def add_watchlist_item(pool_id: str, request: WatchlistItemRequest) -> Dict[str, Any]:
    try:
        symbol = canonical_symbol(request.symbol)
        return add_pool_item(pool_id, symbol, request.name.strip() or symbol)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/watchlists/{pool_id}/items/{symbol:path}")
def delete_watchlist_item(pool_id: str, symbol: str) -> Dict[str, Any]:
    try:
        return remove_pool_item(pool_id, canonical_symbol(symbol))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/data-sources")
def list_data_sources() -> Dict[str, Any]:
    try:
        return public_source_config()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/data-sources", status_code=201)
def create_data_source(request: DataSourceCreateRequest) -> Dict[str, Any]:
    try:
        return add_source(request.provider, request.name, request.api_key)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/data-sources/{source_id}/activate")
def set_active_data_source(source_id: str) -> Dict[str, Any]:
    try:
        return activate_source(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/data-sources/{source_id}")
def remove_data_source(source_id: str) -> Dict[str, Any]:
    try:
        return delete_source(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/report-settings")
def report_settings() -> Dict[str, Any]:
    try:
        return public_report_settings()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.put("/api/report-settings/analysis")
def update_report_analysis_settings(request: ReportAnalysisSettingsRequest) -> Dict[str, Any]:
    try:
        return save_analysis_settings(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.put("/api/report-settings/webhooks")
def update_report_webhook_settings(request: ReportWebhookSettingsRequest) -> Dict[str, Any]:
    try:
        return save_webhook_settings(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.put("/api/report-settings/automation")
def update_report_automation_settings(request: ReportAutomationSettingsRequest) -> Dict[str, Any]:
    try:
        return save_automation_settings(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/report-settings/webhooks/test")
async def test_report_webhooks() -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(test_webhooks)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/reports/analyze")
async def analyze_report(request: ReportRequest) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(
            generate_report,
            request.symbol,
            request.name,
            request.session,
            request.notify,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/reports")
def report_history(limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    try:
        return list_reports(limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/reports/{report_id}")
def report_detail(report_id: str) -> Dict[str, Any]:
    try:
        result = get_report(report_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return result


@app.post("/api/export/html", response_class=HTMLResponse)
def export_html(request: ExportRequest) -> HTMLResponse:
    try:
        return HTMLResponse(snapshot_html(request.analysis))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="分析结果不符合导出契约") from exc


STATIC = Path(__file__).resolve().parent / "static"
if (STATIC / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC / "assets")), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str = "") -> Any:
    index = STATIC / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>前端尚未构建</h1><p>请运行 <code>npm --prefix ui run build</code>。</p>",
            status_code=503,
        )
    candidate = (STATIC / path).resolve()
    if path and candidate.is_file() and STATIC in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(index)
