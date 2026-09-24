from __future__ import annotations

import math
import os
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta
from typing import Any

import httpx
import pandas as pd

from .models import Bar, normalize_symbol


class DataSourceError(RuntimeError):
    pass


def _code6(symbol: str) -> str:
    return normalize_symbol(symbol).split(".")[0]


def _prefix_symbol(symbol: str) -> str:
    full = normalize_symbol(symbol)
    code, market = full.split(".")
    return f"{market.lower()}{code}"


def _is_a_share_index(symbol: str) -> bool:
    full = normalize_symbol(symbol)
    code, market = full.split(".")
    return (market == "SZ" and code.startswith("399")) or (
        market == "SH" and code.startswith("000")
    )


def _bypass_proxy_for_hosts(*hosts: str) -> None:
    for variable in ("NO_PROXY", "no_proxy"):
        existing = [item.strip() for item in os.environ.get(variable, "").split(",") if item.strip()]
        known = {item.lower() for item in existing}
        existing.extend(host for host in hosts if host.lower() not in known)
        os.environ[variable] = ",".join(existing)


def _yahoo_symbol(symbol: str) -> str:
    full = normalize_symbol(symbol)
    code, market = full.split(".")
    if market == "SH":
        return f"{code}.SS"
    if market == "SZ":
        return f"{code}.SZ"
    raise DataSourceError("Yahoo Finance 暂不支持北交所代码，请改用 AKShare、Tushare 或新浪财经")


def _float(value: Any) -> float | None:
    if value in (None, "", "--"):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _bar_available_at(ts: datetime, timeframe: str) -> datetime:
    if timeframe == "1d":
        return datetime.combine(ts.date(), time(15, 5))
    return ts


def _validate_bars(bars: list[Bar]) -> list[Bar]:
    unique: dict[datetime, Bar] = {}
    for bar in bars:
        if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
            continue
        if bar.low > min(bar.open, bar.high, bar.close) or bar.high < max(bar.open, bar.low, bar.close):
            continue
        unique[bar.ts] = bar
    return [unique[key] for key in sorted(unique)]


class MarketDataProvider(ABC):
    name = "base"

    @abstractmethod
    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        raise NotImplementedError

    def is_trade_date(self, day: date) -> bool:
        return day.weekday() < 5


class AkshareProvider(MarketDataProvider):
    name = "akshare"

    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        import akshare as ak

        full = normalize_symbol(symbol)
        if timeframe == "1d":
            return self._daily(ak, full, start, end)
        if timeframe not in {"5m", "30m"}:
            raise DataSourceError(f"AKShare 暂不支持周期 {timeframe}")
        return self._minute(ak, full, timeframe[:-1], start, end)

    def _daily(self, ak: Any, symbol: str, start: datetime, end: datetime) -> list[Bar]:
        code = _code6(symbol)
        is_index = _is_a_share_index(symbol)
        last_error: Exception | None = None
        try:
            args = {
                "symbol": code,
                "period": "daily",
                "start_date": start.strftime("%Y%m%d"),
                "end_date": end.strftime("%Y%m%d"),
            }
            frame = (
                ak.index_zh_a_hist(**args)
                if is_index
                else ak.stock_zh_a_hist(**args, adjust="qfq")
            )
            if frame is not None and not frame.empty:
                bars = []
                for _, row in frame.iterrows():
                    ts = pd.to_datetime(row["日期"]).to_pydatetime()
                    bars.append(
                        Bar(
                            symbol=symbol,
                            timeframe="1d",
                            ts=ts,
                            open=float(row["开盘"]),
                            high=float(row["最高"]),
                            low=float(row["最低"]),
                            close=float(row["收盘"]),
                            volume=_float(row.get("成交量")),
                            amount=_float(row.get("成交额")),
                            source=self.name,
                            available_at=_bar_available_at(ts, "1d"),
                        )
                    )
                return _validate_bars(bars)
        except Exception as exc:  # 上游免费接口经常临时不可达，继续走新浪备用
            last_error = exc
        _bypass_proxy_for_hosts(
            "80.push2.eastmoney.com",
            "push2his.eastmoney.com",
            "proxy.finance.qq.com",
            "quotes.sina.cn",
            "finance.sina.com.cn",
        )
        try:
            source = "akshare_sina"
            if is_index:
                try:
                    frame = ak.stock_zh_index_daily_tx(
                        symbol=_prefix_symbol(symbol),
                        start_date=start.strftime("%Y%m%d"),
                        end_date=end.strftime("%Y%m%d"),
                    )
                    source = "akshare_tencent"
                except Exception:
                    frame = ak.stock_zh_index_daily(symbol=_prefix_symbol(symbol))
            else:
                frame = ak.stock_zh_a_daily(
                    symbol=_prefix_symbol(symbol),
                    start_date=start.strftime("%Y%m%d"),
                    end_date=end.strftime("%Y%m%d"),
                    adjust="qfq",
                )
            bars = []
            for _, row in frame.iterrows():
                ts = pd.to_datetime(row["date"]).to_pydatetime()
                if not (start <= ts <= end):
                    continue
                bars.append(
                    Bar(
                        symbol=symbol,
                        timeframe="1d",
                        ts=ts,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=_float(row.get("volume")),
                        amount=_float(row.get("amount")),
                        source=source,
                        available_at=_bar_available_at(ts, "1d"),
                    )
                )
            return _validate_bars(bars)
        except Exception as exc:
            raise DataSourceError(f"AKShare 日线主备接口均失败: {last_error or exc}; {exc}") from exc

    def _minute(
        self, ak: Any, symbol: str, period: str, start: datetime, end: datetime
    ) -> list[Bar]:
        timeframe = f"{period}m"
        is_index = _is_a_share_index(symbol)
        last_error: Exception | None = None
        try:
            args = {
                "symbol": _code6(symbol),
                "start_date": start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": end.strftime("%Y-%m-%d %H:%M:%S"),
                "period": period,
            }
            frame = (
                ak.index_zh_a_hist_min_em(**args)
                if is_index
                else ak.stock_zh_a_hist_min_em(**args, adjust="qfq")
            )
            if frame is not None and not frame.empty:
                return self._minute_frame(symbol, timeframe, frame, "时间", self.name, start, end)
        except Exception as exc:
            last_error = exc
        _bypass_proxy_for_hosts("proxy.finance.qq.com", "quotes.sina.cn", "finance.sina.com.cn")
        try:
            frame = ak.stock_zh_a_minute(
                symbol=_prefix_symbol(symbol), period=period, adjust="" if is_index else "qfq"
            )
            if frame is None or frame.empty:
                raise DataSourceError("新浪分钟接口返回空数据")
            return self._minute_frame(
                symbol, timeframe, frame, "day", "akshare_sina", start, end
            )
        except Exception as exc:
            raise DataSourceError(
                f"AKShare {timeframe} 主备接口均失败: {last_error or exc}; {exc}"
            ) from exc

    @staticmethod
    def _minute_frame(
        symbol: str,
        timeframe: str,
        frame: pd.DataFrame,
        time_col: str,
        source: str,
        start: datetime,
        end: datetime,
    ) -> list[Bar]:
        aliases = {
            "open": ("开盘", "open"),
            "high": ("最高", "high"),
            "low": ("最低", "low"),
            "close": ("收盘", "close"),
            "volume": ("成交量", "volume"),
            "amount": ("成交额", "amount"),
        }

        def value(row: pd.Series, field: str) -> Any:
            for name in aliases[field]:
                if name in row:
                    return row[name]
            return None

        bars = []
        for _, row in frame.iterrows():
            ts = pd.to_datetime(row[time_col]).to_pydatetime()
            if not (start <= ts <= end):
                continue
            numbers = {key: _float(value(row, key)) for key in aliases}
            if any(numbers[key] is None for key in ("open", "high", "low", "close")):
                continue
            bars.append(
                Bar(
                    symbol=symbol,
                    timeframe=timeframe,
                    ts=ts,
                    open=float(numbers["open"]),
                    high=float(numbers["high"]),
                    low=float(numbers["low"]),
                    close=float(numbers["close"]),
                    volume=numbers["volume"],
                    amount=numbers["amount"],
                    source=source,
                    available_at=ts,
                )
            )
        return _validate_bars(bars)

    def is_trade_date(self, day: date) -> bool:
        try:
            import akshare as ak

            frame = ak.tool_trade_date_hist_sina()
            dates = {pd.to_datetime(item).date() for item in frame["trade_date"].tolist()}
            return day in dates
        except Exception:
            return super().is_trade_date(day)


class SinaProvider(MarketDataProvider):
    """通过 AKShare 的新浪财经适配器获取行情，不经过东方财富主接口。"""

    name = "sina"

    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        import akshare as ak

        full = normalize_symbol(symbol)
        if timeframe == "1d":
            try:
                frame = ak.stock_zh_a_daily(
                    symbol=_prefix_symbol(full),
                    start_date=start.strftime("%Y%m%d"),
                    end_date=end.strftime("%Y%m%d"),
                    adjust="qfq",
                )
            except Exception as exc:
                raise DataSourceError(f"新浪财经日线获取失败: {exc}") from exc
            bars = []
            for _, row in frame.iterrows():
                ts = pd.to_datetime(row["date"]).to_pydatetime()
                bars.append(
                    Bar(
                        symbol=full,
                        timeframe="1d",
                        ts=ts,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=_float(row.get("volume")),
                        amount=_float(row.get("amount")),
                        source=self.name,
                        available_at=_bar_available_at(ts, "1d"),
                    )
                )
            return _validate_bars(bars)
        if timeframe not in {"5m", "30m"}:
            raise DataSourceError(f"新浪财经暂不支持周期 {timeframe}")
        try:
            frame = ak.stock_zh_a_minute(
                symbol=_prefix_symbol(full), period=timeframe[:-1], adjust="qfq"
            )
        except Exception as exc:
            raise DataSourceError(f"新浪财经 {timeframe} 获取失败: {exc}") from exc
        if frame is None or frame.empty:
            return []
        return AkshareProvider._minute_frame(
            full, timeframe, frame, "day", self.name, start, end
        )


class YahooFinanceProvider(MarketDataProvider):
    name = "yahoo"

    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        import yfinance as yf

        full = normalize_symbol(symbol)
        interval = {"1d": "1d", "30m": "30m", "5m": "5m"}.get(timeframe)
        if not interval:
            raise DataSourceError(f"Yahoo Finance 暂不支持周期 {timeframe}")
        effective_start = start
        if timeframe != "1d":
            # Yahoo 官方接口限制分钟数据只能回看最近 60 天。
            effective_start = max(start, end - timedelta(days=59))
        try:
            frame = yf.Ticker(_yahoo_symbol(full)).history(
                start=effective_start,
                end=end + timedelta(days=1),
                interval=interval,
                auto_adjust=True,
                actions=False,
                repair=timeframe == "1d",
                timeout=30,
                raise_errors=True,
            )
        except Exception as exc:
            raise DataSourceError(f"Yahoo Finance {timeframe} 获取失败: {exc}") from exc
        if frame is None or frame.empty:
            return []
        bars = []
        for index, row in frame.iterrows():
            ts = pd.to_datetime(index)
            if ts.tzinfo is not None:
                ts = ts.tz_convert("Asia/Shanghai").tz_localize(None)
            dt = ts.to_pydatetime()
            if timeframe == "1d":
                dt = datetime.combine(dt.date(), time())
            values = {
                key: _float(row.get(next((c for c in frame.columns if str(c).lower() == key), key)))
                for key in ("open", "high", "low", "close", "volume")
            }
            if any(values[key] is None for key in ("open", "high", "low", "close")):
                continue
            bars.append(
                Bar(
                    symbol=full,
                    timeframe=timeframe,
                    ts=dt,
                    open=float(values["open"]),
                    high=float(values["high"]),
                    low=float(values["low"]),
                    close=float(values["close"]),
                    volume=values["volume"],
                    source=self.name,
                    available_at=_bar_available_at(dt, timeframe),
                )
            )
        return _validate_bars(bars)


class TushareProvider(MarketDataProvider):
    name = "tushare"

    def __init__(self, token: str):
        if not token:
            raise DataSourceError("Tushare token 尚未配置")
        import tushare as ts

        self.pro = ts.pro_api(token)

    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        symbol = normalize_symbol(symbol)
        if timeframe == "1d":
            frame = self.pro.daily(
                ts_code=symbol,
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
            )
            return self._normalize_daily(symbol, frame, start, end)
        freq = {"5m": "5min", "30m": "30min"}.get(timeframe)
        if not freq:
            raise DataSourceError(f"Tushare 暂不支持周期 {timeframe}")
        chunks: list[pd.DataFrame] = []
        cursor = start
        step = timedelta(days=120 if timeframe == "5m" else 540)
        while cursor < end:
            chunk_end = min(cursor + step, end)
            frame = self.pro.stk_mins(
                ts_code=symbol,
                freq=freq,
                start_date=cursor.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=chunk_end.strftime("%Y-%m-%d %H:%M:%S"),
            )
            if frame is not None and not frame.empty:
                chunks.append(frame)
            cursor = chunk_end + timedelta(seconds=1)
        if not chunks:
            return []
        return self._normalize_minutes(symbol, timeframe, pd.concat(chunks), start, end)

    def _adjust_factors(self, symbol: str, start: datetime, end: datetime) -> dict[str, float]:
        frame = self.pro.adj_factor(
            ts_code=symbol,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )
        if frame is None or frame.empty:
            return {}
        ordered = frame.sort_values("trade_date")
        latest = float(ordered.iloc[-1]["adj_factor"])
        return {
            str(row["trade_date"]): float(row["adj_factor"]) / latest
            for _, row in frame.iterrows()
        }

    def _normalize_daily(
        self, symbol: str, frame: pd.DataFrame, start: datetime, end: datetime
    ) -> list[Bar]:
        if frame is None or frame.empty:
            return []
        factors = self._adjust_factors(symbol, start, end)
        bars = []
        for _, row in frame.iterrows():
            day = str(row["trade_date"])
            factor = factors.get(day, 1.0)
            ts = datetime.strptime(day, "%Y%m%d")
            bars.append(
                Bar(
                    symbol=symbol,
                    timeframe="1d",
                    ts=ts,
                    open=float(row["open"]) * factor,
                    high=float(row["high"]) * factor,
                    low=float(row["low"]) * factor,
                    close=float(row["close"]) * factor,
                    volume=_float(row.get("vol")),
                    amount=_float(row.get("amount")),
                    source=self.name,
                    available_at=_bar_available_at(ts, "1d"),
                )
            )
        return _validate_bars(bars)

    def _normalize_minutes(
        self,
        symbol: str,
        timeframe: str,
        frame: pd.DataFrame,
        start: datetime,
        end: datetime,
    ) -> list[Bar]:
        time_col = next(
            (name for name in ("trade_time", "datetime", "trade_date") if name in frame.columns),
            None,
        )
        if not time_col:
            raise DataSourceError("Tushare 分钟数据缺少时间字段")
        factors = self._adjust_factors(symbol, start, end)
        bars = []
        for _, row in frame.iterrows():
            ts = pd.to_datetime(row[time_col]).to_pydatetime()
            if not (start <= ts <= end):
                continue
            factor = factors.get(ts.strftime("%Y%m%d"), 1.0)
            bars.append(
                Bar(
                    symbol=symbol,
                    timeframe=timeframe,
                    ts=ts,
                    open=float(row["open"]) * factor,
                    high=float(row["high"]) * factor,
                    low=float(row["low"]) * factor,
                    close=float(row["close"]) * factor,
                    volume=_float(row.get("vol", row.get("volume"))),
                    amount=_float(row.get("amount")),
                    source=self.name,
                    available_at=datetime.combine(ts.date(), time(18, 0)),
                )
            )
        return _validate_bars(bars)

    def is_trade_date(self, day: date) -> bool:
        try:
            day_text = day.strftime("%Y%m%d")
            frame = self.pro.trade_cal(
                exchange="SSE", start_date=day_text, end_date=day_text, is_open="1"
            )
            return frame is not None and not frame.empty
        except Exception:
            return super().is_trade_date(day)


class CustomHttpProvider(MarketDataProvider):
    name = "custom_http"

    def __init__(self, base_url: str, api_key: str = ""):
        if not base_url or not base_url.startswith(("http://", "https://")):
            raise DataSourceError("自定义数据源 URL 无效")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        params = {
            "symbol": normalize_symbol(symbol),
            "timeframe": timeframe,
            "start": start.isoformat(sep=" "),
            "end": end.isoformat(sep=" "),
            "adjust": "qfq",
        }
        try:
            response = httpx.get(self.base_url, params=params, headers=headers, timeout=60)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise DataSourceError(f"自定义数据源请求失败: {exc}") from exc
        rows = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise DataSourceError("自定义数据源必须返回 JSON 数组或 {data:[...]}")
        bars = []
        for row in rows:
            ts = pd.to_datetime(row.get("ts", row.get("datetime", row.get("date")))).to_pydatetime()
            bars.append(
                Bar(
                    symbol=normalize_symbol(symbol),
                    timeframe=timeframe,
                    ts=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=_float(row.get("volume")),
                    amount=_float(row.get("amount")),
                    source=self.name,
                    available_at=pd.to_datetime(row.get("available_at", ts)).to_pydatetime(),
                )
            )
        return _validate_bars(bars)


class HybridProvider(MarketDataProvider):
    name = "hybrid"

    def __init__(self, primary: MarketDataProvider, fallback: MarketDataProvider):
        self.primary = primary
        self.fallback = fallback

    def fetch(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Bar]:
        try:
            bars = self.primary.fetch(symbol, timeframe, start, end)
            if bars:
                return bars
        except Exception:
            pass
        return self.fallback.fetch(symbol, timeframe, start, end)

    def is_trade_date(self, day: date) -> bool:
        try:
            return self.primary.is_trade_date(day)
        except Exception:
            return self.fallback.is_trade_date(day)


def build_provider(name: str, settings: dict[str, str]) -> MarketDataProvider:
    if name == "akshare":
        return AkshareProvider()
    if name == "tushare":
        return TushareProvider(settings.get("tushare_token", ""))
    if name == "yahoo":
        return YahooFinanceProvider()
    if name == "sina":
        return SinaProvider()
    if name == "custom_http":
        return CustomHttpProvider(
            settings.get("custom_base_url", ""), settings.get("custom_api_key", "")
        )
    if name == "hybrid":
        token = settings.get("tushare_token", "")
        primary: MarketDataProvider = TushareProvider(token) if token else AkshareProvider()
        fallback: MarketDataProvider = AkshareProvider()
        return HybridProvider(primary, fallback)
    raise DataSourceError(f"未知数据源: {name}")
