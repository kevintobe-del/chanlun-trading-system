from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


TIMEFRAMES = ("1d", "30m", "5m")
PROVIDERS = ("akshare", "tushare", "yahoo", "sina")
INDEX_SYMBOL_ALIASES = {
    "1A0001": "000001.SH",
    "上证指数": "000001.SH",
    "上证综指": "000001.SH",
    "SHCOMP": "000001.SH",
    "1B0688": "000688.SH",
    "科创50": "000688.SH",
    "STAR50": "000688.SH",
    "深证成指": "399001.SZ",
}


def normalize_symbol(value: str) -> str:
    raw = value.strip().upper()
    if raw in INDEX_SYMBOL_ALIASES:
        return INDEX_SYMBOL_ALIASES[raw]
    legacy_index = re.fullmatch(r"1[AB](\d{4})", raw)
    if legacy_index:
        return f"00{legacy_index.group(1)}.SH"
    explicit = re.fullmatch(r"(\d{6})\.(SH|SS|SZ|BJ)", raw)
    if explicit:
        code, market = explicit.groups()
        return f"{code}.{'SH' if market == 'SS' else market}"
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) != 6:
        raise ValueError("请输入6位A股代码")
    if digits.startswith(("60", "68")):
        suffix = "SH"
    elif digits.startswith(("00", "30", "399")):
        suffix = "SZ"
    else:
        suffix = "BJ"
    return f"{digits}.{suffix}"


@dataclass(slots=True)
class Bar:
    symbol: str
    timeframe: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    amount: float | None = None
    source: str = ""
    available_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ts"] = self.ts.isoformat(sep=" ")
        data["available_at"] = (
            self.available_at.isoformat(sep=" ") if self.available_at else data["ts"]
        )
        return data


class WatchlistInput(BaseModel):
    symbol: str
    name: str = ""
    enabled: bool = True
    source: str | None = None

    @field_validator("symbol")
    @classmethod
    def valid_symbol(cls, value: str) -> str:
        return normalize_symbol(value)

    @field_validator("source")
    @classmethod
    def valid_source(cls, value: str | None) -> str | None:
        if value in (None, "", "default"):
            return None
        if value not in PROVIDERS:
            raise ValueError("不支持的数据源")
        return value


class DataSettingsInput(BaseModel):
    provider: str = "akshare"
    tushare_token: str | None = None
    custom_base_url: str | None = None
    custom_api_key: str | None = None
    daily_years: int = Field(default=5, ge=2, le=20)
    minute30_years: int = Field(default=2, ge=1, le=10)
    minute5_days: int = Field(default=180, ge=30, le=3650)

    @field_validator("provider")
    @classmethod
    def valid_provider(cls, value: str) -> str:
        if value not in PROVIDERS:
            raise ValueError("不支持的数据源")
        return value


class AutomationSettingsInput(BaseModel):
    automatic_enabled: bool = True
    premarket_time: str = "08:30"
    after_close_time: str = "18:00"
    default_send_report: bool = False

    @field_validator("premarket_time", "after_close_time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise ValueError("时间必须是 HH:MM 格式")
        return value


class WebhookSettingsInput(BaseModel):
    feishu_enabled: bool = False
    feishu_url: str | None = None
    feishu_secret: str | None = None
    wecom_enabled: bool = False
    wecom_url: str | None = None


class RunInput(BaseModel):
    session: str = "manual"
    symbols: list[str] | None = None
    notify: bool = False

    @field_validator("session")
    @classmethod
    def valid_session(cls, value: str) -> str:
        if value not in {"manual", "premarket", "after_close"}:
            raise ValueError("未知分析时段")
        return value

    @field_validator("symbols")
    @classmethod
    def valid_symbols(cls, value: list[str] | None) -> list[str] | None:
        return [normalize_symbol(item) for item in value] if value else value
