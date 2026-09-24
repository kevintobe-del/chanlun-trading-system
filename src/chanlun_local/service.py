from __future__ import annotations

import traceback
from datetime import date, datetime, time, timedelta
from typing import Any

from .database import Database
from .engine import analyze_multilevel
from .models import Bar, normalize_symbol
from .providers import DataSourceError, build_provider
from .reporting import build_report
from .webhooks import configured_platforms, send_report


class AnalysisService:
    def __init__(self, database: Database):
        self.db = database

    def _settings(self) -> dict[str, str]:
        return self.db.get_settings(reveal_secrets=True)

    def _provider(self, source: str | None = None):
        settings = self._settings()
        return build_provider(source or settings.get("provider", "akshare"), settings)

    @staticmethod
    def _cache_sources(provider_name: str) -> set[str]:
        if provider_name == "akshare":
            return {"akshare", "akshare_sina"}
        if provider_name == "hybrid":
            return {"akshare", "akshare_sina", "tushare"}
        return {provider_name}

    def is_trade_date(self, day: date | None = None) -> bool:
        target = day or date.today()
        try:
            return self._provider().is_trade_date(target)
        except Exception:
            return target.weekday() < 5

    def _range(self, timeframe: str, now: datetime) -> datetime:
        settings = self._settings()
        if timeframe == "1d":
            return now - timedelta(days=int(settings.get("daily_years", "5")) * 366)
        if timeframe == "30m":
            return now - timedelta(days=int(settings.get("minute30_years", "2")) * 366)
        return now - timedelta(days=int(settings.get("minute5_days", "180")))

    def refresh_symbol(self, symbol: str, source: str | None = None) -> dict[str, Any]:
        symbol = normalize_symbol(symbol)
        provider = self._provider(source)
        now = datetime.now()
        details: dict[str, Any] = {"provider": provider.name, "timeframes": {}}
        for timeframe in ("1d", "30m", "5m"):
            desired_start = self._range(timeframe, now)
            latest = self.db.last_bar_time(symbol, timeframe)
            overlap = timedelta(days=10 if timeframe == "1d" else 3)
            start = max(desired_start, latest - overlap) if latest else desired_start
            try:
                bars = provider.fetch(symbol, timeframe, start, now)
                count = self.db.upsert_bars(bars)
                details["timeframes"][timeframe] = {
                    "fetched": count,
                    "start": bars[0].ts.isoformat(sep=" ") if bars else None,
                    "end": bars[-1].ts.isoformat(sep=" ") if bars else None,
                }
            except Exception as exc:
                details["timeframes"][timeframe] = {"error": str(exc)}
        return details

    def analyze_symbol(
        self, symbol: str, name: str, session: str, source: str | None = None
    ) -> dict[str, Any]:
        refresh = self.refresh_symbol(symbol, source)
        settings = self._settings()
        now = datetime.now()
        ranges = {
            "1d": now - timedelta(days=int(settings.get("daily_years", "5")) * 366),
            "30m": now - timedelta(days=int(settings.get("minute30_years", "2")) * 366),
            "5m": now - timedelta(days=int(settings.get("minute5_days", "180"))),
        }
        bars_by_level: dict[str, list[Bar]] = {
            timeframe: self.db.load_bars(
                symbol,
                timeframe,
                since,
                self._cache_sources(refresh["provider"]),
            )
            for timeframe, since in ranges.items()
        }
        result = analyze_multilevel(symbol, bars_by_level)
        result["data_refresh"] = refresh
        report = build_report(name, result, session)
        status = result["verdict"]["action"]
        report_id = self.db.save_report(
            symbol=symbol,
            name=name,
            session=session,
            asof=result["meta"].get("asof") or "",
            status=status,
            report_text=report,
            result=result,
        )
        return {"id": report_id, "symbol": symbol, "status": status, "report": report, "result": result}

    def run_all(
        self,
        session: str,
        symbols: list[str] | None = None,
        notify: bool = False,
        skip_non_trade_day: bool = False,
    ) -> dict[str, Any]:
        run_id = self.db.start_run(session)
        if skip_non_trade_day and not self.is_trade_date():
            detail = {"skipped": True, "reason": "非交易日"}
            self.db.finish_run(run_id, "skipped", detail)
            return {"run_id": run_id, **detail}
        watchlist = self.db.list_watchlist(enabled_only=True)
        if symbols:
            wanted = {normalize_symbol(item) for item in symbols}
            watchlist = [item for item in watchlist if item["symbol"] in wanted]
        outputs = []
        errors = []
        for item in watchlist:
            try:
                output = self.analyze_symbol(
                    item["symbol"], item["name"], session, item.get("source")
                )
                outputs.append(output)
                if notify:
                    self._notify(output)
            except Exception as exc:
                errors.append(
                    {
                        "symbol": item["symbol"],
                        "error": str(exc),
                        "trace": traceback.format_exc(limit=4),
                    }
                )
        status = "completed" if not errors else "partial_failure" if outputs else "failed"
        detail = {
            "reports": [{"id": item["id"], "symbol": item["symbol"]} for item in outputs],
            "errors": errors,
        }
        self.db.finish_run(run_id, status, detail)
        return {"run_id": run_id, "status": status, **detail}

    def _notify(self, output: dict[str, Any]) -> None:
        settings = self._settings()
        title = f"{output['symbol']} 缠论分析"
        for platform, url, secret in configured_platforms(settings):
            send_report(platform, url, output["report"], title, secret)

    def test_webhooks(self) -> dict[str, Any]:
        settings = self._settings()
        results = []
        text = "缠论本地工作台 Webhook 测试成功。此消息不包含行情或交易建议。"
        for platform, url, secret in configured_platforms(settings):
            try:
                response = send_report(platform, url, text, "连接测试", secret)
                results.append({"platform": platform, "ok": True, "response": response})
            except Exception as exc:
                results.append({"platform": platform, "ok": False, "error": str(exc)})
        return {"results": results}
