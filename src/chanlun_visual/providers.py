"""Market-data providers and local provider configuration."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


SYMBOL = re.compile(r"^[A-Za-z0-9.=_^-]{1,24}$")
INDEX_SYMBOL_ALIASES = {
    "1A0001": "000001.SS",
    "上证指数": "000001.SS",
    "上证综指": "000001.SS",
    "SHCOMP": "000001.SS",
    "1B0688": "000688.SS",
    "科创50": "000688.SS",
    "STAR50": "000688.SS",
    "深证成指": "399001.SZ",
}
SUPPORTED_PROVIDERS = {
    "yfinance": {"label": "Yahoo Finance", "requires_key": False},
    "tushare": {"label": "Tushare", "requires_key": True},
    "akshare": {"label": "AKShare", "requires_key": False},
}
_MARKET_CACHE: Dict[tuple, tuple] = {}
_MARKET_CACHE_LOCK = threading.Lock()
_MARKET_CACHE_TTL_SECONDS = 300
_NAME_CACHE: Dict[str, tuple] = {}
_NAME_CACHE_TTL_SECONDS = 86400


class MarketRateLimitError(RuntimeError):
    """The selected upstream provider is temporarily throttling requests."""


class MarketAccessError(RuntimeError):
    """The selected upstream provider is inaccessible from this network."""


def canonical_symbol(symbol: str) -> str:
    """Map common bare Greater-China codes to public-provider notation."""
    clean = symbol.strip().upper()
    if clean in INDEX_SYMBOL_ALIASES:
        return INDEX_SYMBOL_ALIASES[clean]
    legacy_index = re.fullmatch(r"1[AB](\d{4})", clean)
    if legacy_index:
        return f"00{legacy_index.group(1)}.SS"
    if not SYMBOL.fullmatch(clean):
        raise ValueError("证券代码格式无效")
    if re.fullmatch(r"\d{6}", clean):
        if clean.startswith(("4", "8", "92")):
            return clean + ".BJ"
        if clean.startswith(("5", "6", "9")):
            return clean + ".SS"
        return clean + ".SZ"
    if re.fullmatch(r"\d{4,5}", clean):
        return clean.zfill(4) + ".HK"
    return clean


def _config_path() -> Path:
    override = os.environ.get("CHANLUN_DATA_SOURCE_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / "chanlun-visual" / "data-sources.json"


def _default_config() -> Dict[str, Any]:
    return {
        "active_id": "builtin-yfinance",
        "sources": [{"id": "builtin-yfinance", "provider": "yfinance", "name": "Yahoo Finance", "api_key": "", "builtin": True}],
    }


def load_source_config() -> Dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return _default_config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("数据源配置文件无法读取") from exc
    sources = raw.get("sources")
    active_id = raw.get("active_id")
    if not isinstance(sources, list) or not sources:
        raise RuntimeError("数据源配置为空或格式无效")
    if active_id not in {item.get("id") for item in sources if isinstance(item, dict)}:
        raise RuntimeError("生效的数据源不存在")
    return {"active_id": active_id, "sources": sources}


def save_source_config(config: Dict[str, Any]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config, ensure_ascii=False, indent=2)
    fd, temporary = tempfile.mkstemp(prefix=".data-sources-", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def public_source_config() -> Dict[str, Any]:
    config = load_source_config()
    sources = []
    for item in config["sources"]:
        key = str(item.get("api_key") or "")
        sources.append({
            "id": item["id"], "provider": item["provider"], "name": item["name"],
            "builtin": bool(item.get("builtin")), "has_api_key": bool(key),
            "api_key_mask": ("•" * 8 + key[-4:]) if key else "", "active": item["id"] == config["active_id"],
        })
    return {"active_id": config["active_id"], "sources": sources, "providers": SUPPORTED_PROVIDERS}


def add_source(provider: str, name: str, api_key: str) -> Dict[str, Any]:
    provider, name, api_key = provider.strip().lower(), name.strip(), api_key.strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("暂不支持这个数据源")
    if not name or len(name) > 64:
        raise ValueError("API 名称不能为空且不能超过 64 个字符")
    if SUPPORTED_PROVIDERS[provider]["requires_key"] and not api_key:
        raise ValueError("Tushare 必须填写 API 密钥")
    if len(api_key) > 512:
        raise ValueError("API 密钥长度不能超过 512 个字符")
    config = load_source_config()
    config["sources"].append({"id": uuid4().hex, "provider": provider, "name": name, "api_key": api_key, "builtin": False})
    save_source_config(config)
    return public_source_config()


def activate_source(source_id: str) -> Dict[str, Any]:
    config = load_source_config()
    if source_id not in {item["id"] for item in config["sources"]}:
        raise KeyError("数据源不存在")
    config["active_id"] = source_id
    save_source_config(config)
    return public_source_config()


def delete_source(source_id: str) -> Dict[str, Any]:
    config = load_source_config()
    target = next((item for item in config["sources"] if item["id"] == source_id), None)
    if target is None:
        raise KeyError("数据源不存在")
    if target.get("builtin"):
        raise ValueError("内置数据源不能删除")
    config["sources"] = [item for item in config["sources"] if item["id"] != source_id]
    if config["active_id"] == source_id:
        config["active_id"] = "builtin-yfinance"
    save_source_config(config)
    return public_source_config()


def active_source() -> Dict[str, Any]:
    config = load_source_config()
    return next(item for item in config["sources"] if item["id"] == config["active_id"])


def yfinance_bars(symbol: str, timeframe: str, api_key: str = "") -> List[Dict[str, Any]]:
    del api_key
    symbol = canonical_symbol(symbol)
    mapping = {"1d": ("2y", "1d"), "60m": ("3mo", "60m"), "30m": ("1mo", "30m"), "5m": ("5d", "5m")}
    if timeframe not in mapping:
        raise ValueError("不支持的周期")
    cache_key = ("yfinance", symbol, timeframe)
    with _MARKET_CACHE_LOCK:
        cached = _MARKET_CACHE.get(cache_key)
        if cached and time.monotonic() - cached[0] < _MARKET_CACHE_TTL_SECONDS:
            return [dict(item) for item in cached[1]]
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("未安装 Yahoo Finance 行情扩展；请运行 pip install 'chanlun-visual[market]'") from exc
    period, interval = mapping[timeframe]
    frame = None
    for attempt in range(2):
        try:
            frame = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
            break
        except Exception as exc:
            translated = _translate_yahoo_error(exc)
            if isinstance(translated, MarketRateLimitError) and attempt == 0:
                time.sleep(1.5)
                continue
            raise translated from exc
    if frame is None:
        raise RuntimeError("Yahoo Finance 行情请求失败")
    if frame.empty:
        raise RuntimeError("Yahoo Finance 没有返回数据")
    bars = _frame_to_bars(frame, {"date": None, "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    with _MARKET_CACHE_LOCK:
        _MARKET_CACHE[cache_key] = (time.monotonic(), bars)
    return [dict(item) for item in bars]


def _translate_yahoo_error(exc: Exception) -> RuntimeError:
    message = str(exc)
    normalized = message.lower()
    if "too many requests" in normalized or "rate limit" in normalized or "429" in normalized:
        return MarketRateLimitError(
            "Yahoo Finance 请求频率受限，请稍后重试，或在“配置数据源”中切换 AKShare/Tushare"
        )
    if "forbidden" in normalized or "403" in normalized:
        return MarketAccessError(
            "当前网络无法访问 Yahoo Finance，请在“配置数据源”中切换 AKShare/Tushare"
        )
    return RuntimeError(message or "Yahoo Finance 行情请求失败")


def _a_share_code(symbol: str) -> str:
    clean = canonical_symbol(symbol)
    if not re.fullmatch(r"\d{6}\.(SZ|SS|BJ)", clean):
        raise ValueError("当前数据源仅支持 A 股六位证券代码")
    return clean[:6]


def _a_share_prefixed_code(symbol: str) -> str:
    clean = canonical_symbol(symbol)
    match = re.fullmatch(r"(\d{6})\.(SZ|SS|BJ)", clean)
    if not match:
        raise ValueError("当前数据源仅支持 A 股六位证券代码")
    prefix = {"SZ": "sz", "SS": "sh", "BJ": "bj"}[match.group(2)]
    return prefix + match.group(1)


def _is_a_share_index(symbol: str) -> bool:
    """Recognize exchange index namespaces that overlap with six-digit equities."""
    clean = canonical_symbol(symbol)
    return bool(
        re.fullmatch(r"399\d{3}\.SZ", clean)
        or re.fullmatch(r"000\d{3}\.SS", clean)
    )


def _bypass_proxy_for_hosts(*hosts: str) -> None:
    """Bypass a broken inherited proxy only for known public market hosts."""
    for variable in ("NO_PROXY", "no_proxy"):
        existing = [item.strip() for item in os.environ.get(variable, "").split(",") if item.strip()]
        known = {item.lower() for item in existing}
        existing.extend(host for host in hosts if host.lower() not in known)
        os.environ[variable] = ",".join(existing)


def instrument_display_name(symbol: str) -> str:
    """Return a Chinese security name when available, otherwise a short English name."""
    canonical = canonical_symbol(symbol)
    with _MARKET_CACHE_LOCK:
        cached = _NAME_CACHE.get(canonical)
        if cached and time.monotonic() - cached[0] < _NAME_CACHE_TTL_SECONDS:
            return str(cached[1])
    request_symbol = _sina_quote_symbol(canonical)
    if not request_symbol:
        return canonical
    _bypass_proxy_for_hosts("hq.sinajs.cn")
    url = "https://hq.sinajs.cn/list=" + urllib.parse.quote(request_symbol, safe="")
    request = urllib.request.Request(
        url,
        headers={
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = response.read().decode("gb18030", errors="replace")
        name = _parse_sina_quote_name(canonical, payload)
    except Exception:
        name = canonical
    with _MARKET_CACHE_LOCK:
        _NAME_CACHE[canonical] = (time.monotonic(), name)
    return name


def _sina_quote_symbol(symbol: str) -> str:
    if symbol.endswith(".SS"):
        return "sh" + symbol[:-3]
    if symbol.endswith(".SZ"):
        return "sz" + symbol[:-3]
    if symbol.endswith(".BJ"):
        return "bj" + symbol[:-3]
    if symbol.endswith(".HK"):
        return "hk" + symbol[:-3].zfill(5)
    if re.fullmatch(r"[A-Z][A-Z0-9.=_^-]{0,23}", symbol):
        return "gb_" + symbol.lower()
    return ""


def _parse_sina_quote_name(symbol: str, payload: str) -> str:
    match = re.search(r'="([^"]*)"', payload)
    if not match or not match.group(1):
        return symbol
    fields = match.group(1).split(",")
    if symbol.endswith(".HK"):
        return (fields[1] if len(fields) > 1 and fields[1].strip() else fields[0]).strip() or symbol
    return fields[0].strip() or symbol


def tushare_bars(symbol: str, timeframe: str, api_key: str) -> List[Dict[str, Any]]:
    if not api_key:
        raise RuntimeError("Tushare API 密钥未配置")
    try:
        import tushare as ts
    except ImportError as exc:
        raise RuntimeError("未安装 Tushare 行情扩展；请运行 pip install 'chanlun-visual[market]'") from exc
    code = canonical_symbol(symbol).replace(".SS", ".SH")
    if not re.fullmatch(r"\d{6}\.(SZ|SH|BJ)", code):
        raise ValueError("Tushare 适配器当前仅支持 A 股六位证券代码")
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=730 if timeframe == "1d" else 120)
    pro = ts.pro_api(api_key)
    if timeframe == "1d":
        frame = pro.daily(ts_code=code, start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"))
    else:
        frequency = {"60m": "60min", "30m": "30min", "5m": "5min"}.get(timeframe)
        if frequency is None:
            raise ValueError("不支持的周期")
        frame = ts.pro_bar(
            api=pro,
            ts_code=code,
            asset="E",
            freq=frequency,
            start_date=start.strftime("%Y-%m-%d 09:00:00"),
            end_date=end.strftime("%Y-%m-%d 16:00:00"),
        )
    if frame is None or frame.empty:
        raise RuntimeError("Tushare 没有返回数据；请检查权限、积分和证券代码")
    date_column = "trade_time" if "trade_time" in frame.columns else "trade_date"
    return _frame_to_bars(frame, {"date": date_column, "open": "open", "high": "high", "low": "low", "close": "close", "volume": "vol"})


def akshare_bars(symbol: str, timeframe: str, api_key: str = "") -> List[Dict[str, Any]]:
    del api_key
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("未安装 AKShare 行情扩展；请运行 pip install 'chanlun-visual[market]'") from exc
    code = _a_share_code(symbol)
    prefixed_code = _a_share_prefixed_code(symbol)
    is_index = _is_a_share_index(symbol)
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
    period = {"60m": "60", "30m": "30", "5m": "5"}.get(timeframe)
    if timeframe != "1d" and period is None:
        raise ValueError("不支持的周期")
    try:
        if timeframe == "1d":
            if is_index:
                frame = ak.index_zh_a_hist(
                    symbol=code, period="daily", start_date=start, end_date=end
                )
            else:
                frame = ak.stock_zh_a_hist(
                    symbol=code, period="daily", start_date=start, end_date=end,
                    adjust="", timeout=15,
                )
            columns = {"date": "日期", "open": "开盘", "high": "最高", "low": "最低", "close": "收盘", "volume": "成交量"}
        else:
            minute_args = {
                "symbol": code,
                "period": period,
                "start_date": (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d 09:00:00"),
                "end_date": datetime.now().strftime("%Y-%m-%d 16:00:00"),
            }
            frame = (
                ak.index_zh_a_hist_min_em(**minute_args)
                if is_index
                else ak.stock_zh_a_hist_min_em(**minute_args, adjust="")
            )
            columns = {"date": "时间", "open": "开盘", "high": "最高", "low": "最低", "close": "收盘", "volume": "成交量"}
        if frame is None or frame.empty:
            raise RuntimeError("东方财富没有返回数据")
        return _frame_to_bars(frame, columns)
    except Exception:
        _bypass_proxy_for_hosts(
            "push2his.eastmoney.com",
            "80.push2.eastmoney.com",
            "quotes.sina.cn",
            "finance.sina.com.cn",
            "proxy.finance.qq.com",
        )
        try:
            if timeframe == "1d":
                if is_index:
                    try:
                        frame = ak.stock_zh_index_daily_tx(
                            symbol=prefixed_code, start_date=start, end_date=end
                        )
                    except Exception:
                        frame = ak.stock_zh_index_daily(symbol=prefixed_code)
                else:
                    frame = ak.stock_zh_a_daily(
                        symbol=prefixed_code, start_date=start, end_date=end, adjust=""
                    )
                columns = {"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"}
            else:
                frame = ak.stock_zh_a_minute(symbol=prefixed_code, period=period, adjust="")
                columns = {"date": "day", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"}
            if frame is None or frame.empty:
                raise RuntimeError("新浪财经没有返回数据")
            return _frame_to_bars(frame, columns)
        except Exception as fallback_exc:
            raise MarketAccessError(
                "AKShare 的东方财富、腾讯和新浪行情均无法访问，请检查网络或代理设置"
            ) from fallback_exc


def _frame_to_bars(frame: Any, columns: Dict[str, Any]) -> List[Dict[str, Any]]:
    bars = []
    for index, row in frame.iterrows():
        raw_date = index if columns["date"] is None else row[columns["date"]]
        at = raw_date.isoformat() if hasattr(raw_date, "isoformat") else str(raw_date)
        volume = row.get(columns["volume"]) if columns.get("volume") else None
        bars.append({"date": at, "open": float(row[columns["open"]]), "high": float(row[columns["high"]]), "low": float(row[columns["low"]]), "close": float(row[columns["close"]]), "volume": float(volume) if volume is not None else None})
    bars.sort(key=lambda item: item["date"])
    return bars


PROVIDER_LOADERS = {"yfinance": yfinance_bars, "tushare": tushare_bars, "akshare": akshare_bars}


def configured_bars(
    symbol: str, timeframe: str, source: Optional[Dict[str, Any]] = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source = source or active_source()
    loader = PROVIDER_LOADERS.get(source["provider"])
    if loader is None:
        raise RuntimeError("当前生效的数据源不受支持")
    api_key = str(source.get("api_key") or "")
    try:
        return loader(symbol, timeframe, api_key), source
    except (MarketRateLimitError, MarketAccessError):
        raise
    except Exception as exc:
        message = str(exc)
        if api_key:
            message = message.replace(api_key, "***")
        raise RuntimeError(message or "数据源请求失败") from exc
