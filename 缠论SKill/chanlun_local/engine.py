from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Bar


CHAN_CONFIG = {
    "bi_strict": True,
    "bi_fx_check": "strict",
    "seg_algo": "chan",
    "zs_algo": "normal",
    "zs_combine": True,
    "divergence_rate": 0.9,
    "min_zs_cnt": 1,
    "max_bs2_rate": 0.618,
    "macd_algo": "peak",
    "bs_type": "1,1p,2,2s,3a,3b",
    "print_warning": False,
    "kl_data_check": False,
    "gap_as_kl": False,
}

CONFIG_HASH = hashlib.md5(
    json.dumps(CHAN_CONFIG, sort_keys=True).encode("utf-8")
).hexdigest()[:8]


def _vendor_path() -> Path:
    candidates = [
        os.environ.get("CHANPY_PATH"),
        str(Path.home() / ".codex/skills/chanlun-engine-skill/engine/chanpy"),
        str(Path.home() / ".agents/skills/chanlun-engine-skill/engine/chanpy"),
        str(Path(__file__).resolve().parent / "vendor/chanpy"),
        str(Path(__file__).resolve().parent.parent / "vendor/chanpy"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return Path(candidate).resolve()
    raise RuntimeError(
        "找不到 chan.py 内核。请设置 CHANPY_PATH，或安装 chanlun-engine-skill。"
    )


VENDOR_PATH = _vendor_path()
if str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))

from Chan import CChan  # noqa: E402
from ChanConfig import CChanConfig  # noqa: E402
from Common.CEnum import AUTYPE, DATA_FIELD, KL_TYPE  # noqa: E402
from Common.CTime import CTime  # noqa: E402
from DataAPI.CommonStockAPI import CCommonStockApi  # noqa: E402
from KLine.KLine_Unit import CKLine_Unit  # noqa: E402


_ENGINE_ROWS: list[Bar] = []


class CLocalBars(CCommonStockApi):
    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=None):
        super().__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        for bar in _ENGINE_ROWS:
            ts = bar.ts
            fields = {
                DATA_FIELD.FIELD_TIME: CTime(
                    ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second
                ),
                DATA_FIELD.FIELD_OPEN: float(bar.open),
                DATA_FIELD.FIELD_HIGH: float(bar.high),
                DATA_FIELD.FIELD_LOW: float(bar.low),
                DATA_FIELD.FIELD_CLOSE: float(bar.close),
            }
            if bar.volume is not None:
                fields[DATA_FIELD.FIELD_VOLUME] = float(bar.volume)
            if bar.amount is not None:
                fields[DATA_FIELD.FIELD_TURNOVER] = float(bar.amount)
            yield CKLine_Unit(fields)

    def SetBasciInfo(self):
        pass

    @classmethod
    def do_init(cls):
        pass

    @classmethod
    def do_close(cls):
        pass


def _register_data_source() -> None:
    data_api = importlib.import_module("DataAPI")
    module = sys.modules.setdefault("DataAPI.MEM_API", type(sys)("DataAPI.MEM_API"))
    module.CLocalBars = CLocalBars
    setattr(data_api, "MEM_API", module)


def _iso(ct: CTime) -> str:
    if ct.hour == 0 and ct.minute == 0:
        return f"{ct.year:04d}-{ct.month:02d}-{ct.day:02d}"
    return f"{ct.year:04d}-{ct.month:02d}-{ct.day:02d} {ct.hour:02d}:{ct.minute:02d}:00"


def _extract(kl_list: Any, last_close: float) -> dict[str, Any]:
    bis = [
        {
            "i": item.idx,
            "dir": str(item.dir).split(".")[-1],
            "sure": bool(item.is_sure),
            "b": _iso(item.get_begin_klu().time),
            "e": _iso(item.get_end_klu().time),
            "bv": round(item.get_begin_val(), 3),
            "ev": round(item.get_end_val(), 3),
        }
        for item in list(kl_list.bi_list)[-10:]
    ]
    segments = [
        {
            "i": item.idx,
            "dir": str(item.dir).split(".")[-1],
            "sure": bool(item.is_sure),
            "b": _iso(item.start_bi.get_begin_klu().time),
            "e": _iso(item.end_bi.get_end_klu().time),
            "zs_n": len(item.zs_lst),
        }
        for item in list(kl_list.seg_list)[-6:]
    ]
    centers = [
        {
            "b": _iso(item.begin.time),
            "e": _iso(item.end.time),
            "sure": bool(item.is_sure),
            "zg": round(item.high, 3),
            "zd": round(item.low, 3),
            "gg": round(item.peak_high, 3),
            "dd": round(item.peak_low, 3),
            "bi_n": len(item.bi_lst),
        }
        for item in list(kl_list.zs_list.zs_lst)[-4:]
    ]
    points = [
        {
            "d": _iso(item.klu.time),
            "bs": "B" if item.is_buy else "S",
            "type": item.type2str(),
            "px": round(item.klu.close, 3),
            "sure": bool(item.bi.is_sure),
        }
        for item in kl_list.bs_point_lst.getSortedBspList()[-10:]
    ]
    position = None
    if centers:
        center = centers[-1]
        position = (
            "above_zs"
            if last_close > center["zg"]
            else "below_zs"
            if last_close < center["zd"]
            else "in_zs"
        )
    return {
        "bi": bis,
        "seg": segments,
        "zs": centers,
        "bsp": points,
        "pos_vs_last_zs": position,
    }


def _fresh_window(timeframe: str) -> int:
    return {"1w": 2, "1d": 3, "30m": 8, "5m": 12}.get(timeframe, 3)


def _time_key(value: str | datetime, timeframe: str) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d" if timeframe in {"1d", "1w"} else "%Y-%m-%d %H:%M")
    return value[:10] if timeframe in {"1d", "1w"} else value[:16]


def _signal_invalidation(
    point: dict[str, Any], level: dict[str, Any], bars: list[Bar], timeframe: str
) -> dict[str, Any] | None:
    centers = level.get("zs") or []
    center = centers[-1] if centers else None
    kind = point["type"]
    is_buy = point["bs"] == "B"
    if ("3a" in kind or "3b" in kind) and center:
        return {
            "rule": (
                "跌回中枢上沿(ZG)之下则三买候选失效"
                if is_buy
                else "升回中枢下沿(ZD)之上则三卖候选失效"
            ),
            "px": center["zg"] if is_buy else center["zd"],
        }
    if "1" in kind:
        point_day = _time_key(point["d"], timeframe)
        matched = [bar for bar in bars if _time_key(bar.ts, timeframe) == point_day]
        if matched:
            return {
                "rule": "跌破一买结构低点则候选失效" if is_buy else "突破一卖结构高点则候选失效",
                "px": round(matched[-1].low if is_buy else matched[-1].high, 3),
            }
    if "2" in kind and center:
        return {
            "rule": "跌破前低(DD)则二买候选失效" if is_buy else "突破前高(GG)则二卖候选失效",
            "px": center["dd"] if is_buy else center["gg"],
        }
    return None


def analyze_level(symbol: str, timeframe: str, bars: list[Bar]) -> dict[str, Any]:
    minimum = 120
    if len(bars) < minimum:
        return {
            "timeframe": timeframe,
            "status": "insufficient_history",
            "bars": len(bars),
            "minimum": minimum,
            "bi": [],
            "seg": [],
            "zs": [],
            "bsp": [],
            "fresh_bsp": [],
            "invalidations": [],
            "pos_vs_last_zs": None,
        }
    global _ENGINE_ROWS
    _ENGINE_ROWS = bars
    _register_data_source()
    config = CChanConfig(dict(CHAN_CONFIG))
    chan = CChan(
        code=symbol,
        begin_time=None,
        end_time=None,
        data_src="custom:MEM_API.CLocalBars",
        lv_list=[KL_TYPE.K_DAY],
        config=config,
        autype=AUTYPE.NONE,
    )
    level = _extract(chan[KL_TYPE.K_DAY], bars[-1].close)
    recent = {_time_key(bar.ts, timeframe) for bar in bars[-_fresh_window(timeframe) :]}
    fresh = [point for point in level["bsp"] if _time_key(point["d"], timeframe) in recent]
    invalidations = []
    for point in fresh:
        invalidation = _signal_invalidation(point, level, bars, timeframe)
        if invalidation:
            invalidations.append({"bsp": point, "invalidation": invalidation})
    level.update(
        {
            "timeframe": timeframe,
            "status": "ok",
            "bars": len(bars),
            "asof": bars[-1].ts.isoformat(sep=" "),
            "fresh_bsp": fresh,
            "invalidations": invalidations,
        }
    )
    return level


def weekly_from_daily(bars: list[Bar]) -> list[Bar]:
    buckets: dict[tuple[int, int], list[Bar]] = {}
    for bar in bars:
        iso = bar.ts.isocalendar()
        buckets.setdefault((iso.year, iso.week), []).append(bar)
    output = []
    for group in buckets.values():
        first, last = group[0], group[-1]
        output.append(
            Bar(
                symbol=first.symbol,
                timeframe="1w",
                ts=last.ts,
                open=first.open,
                high=max(item.high for item in group),
                low=min(item.low for item in group),
                close=last.close,
                volume=sum(item.volume or 0 for item in group) or None,
                amount=sum(item.amount or 0 for item in group) or None,
                source=first.source,
                available_at=last.available_at,
            )
        )
    return output


def _directional_fresh(level: dict[str, Any], direction: str) -> list[dict[str, Any]]:
    return [item for item in level.get("fresh_bsp", []) if item["bs"] == direction]


def build_multilevel_verdict(levels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    day = levels["1d"]
    minute30 = levels["30m"]
    minute5 = levels["5m"]
    missing = [
        name
        for name, level in (("日线", day), ("30分钟", minute30), ("5分钟", minute5))
        if level.get("status") != "ok"
    ]
    approximation_loss = []
    if missing:
        approximation_loss.append("缺少足量" + "、".join(missing) + "结构")
    approximation_loss.append("中枢采用段内结构代理，未实现原文完整走势类型递归")

    day_buys = _directional_fresh(day, "B")
    day_sells = _directional_fresh(day, "S")
    direction = "S" if day_sells else "B" if day_buys else None
    candidate = (day_sells or day_buys or [None])[-1]
    confirm = bool(direction and _directional_fresh(minute30, direction))
    trigger = bool(direction and _directional_fresh(minute5, direction))

    if direction == "B" and confirm and trigger:
        action = "buy_candidate"
        verdict = "日线买点候选已获得30分钟确认与5分钟触发；仅作结构研究候选。"
    elif direction == "S" and confirm and trigger:
        action = "sell_risk"
        verdict = "日线卖点风险已获得30分钟确认与5分钟触发；仅作结构风控提示。"
    elif direction:
        action = "observe"
        lack = []
        if not confirm:
            lack.append("30分钟确认")
        if not trigger:
            lack.append("5分钟触发")
        verdict = f"存在日线候选，但缺少{'、'.join(lack)}，按纪律等待观察。"
    else:
        action = "observe"
        verdict = "日线最近窗口没有新鲜买卖点，低级别信号不得独立升级，等待观察。"

    invalidations = day.get("invalidations", []) if candidate else []
    return {
        "action": action,
        "verdict": verdict,
        "day_candidate": candidate,
        "confirmation_30m": confirm,
        "trigger_5m": trigger,
        "invalidations": invalidations,
        "next_observation": _next_observation(day),
        "definition_mode": "structure_proxy" if not missing else "proxy_research",
        "structure_completeness": {
            "week": levels["1w"].get("status") == "ok",
            "day": day.get("status") == "ok",
            "minute30": minute30.get("status") == "ok",
            "minute5": minute5.get("status") == "ok",
        },
        "approximation_loss": approximation_loss,
        "execution_allowed": False,
    }


def _next_observation(day: dict[str, Any]) -> list[str]:
    centers = day.get("zs") or []
    if not centers:
        return ["等待形成可复核的日线中枢与新鲜买卖点"]
    center = centers[-1]
    position = day.get("pos_vs_last_zs")
    if position == "in_zs":
        return [
            f"向上离开并回抽不回中枢上沿 {center['zg']}",
            f"向下离开并反抽不回中枢下沿 {center['zd']}",
        ]
    if position == "above_zs":
        return [f"回抽是否守住中枢上沿 {center['zg']}"]
    return [f"反抽能否收复中枢下沿 {center['zd']}"]


def analyze_multilevel(symbol: str, bars_by_level: dict[str, list[Bar]]) -> dict[str, Any]:
    levels = {
        "1d": analyze_level(symbol, "1d", bars_by_level.get("1d", [])),
        "30m": analyze_level(symbol, "30m", bars_by_level.get("30m", [])),
        "5m": analyze_level(symbol, "5m", bars_by_level.get("5m", [])),
    }
    levels["1w"] = analyze_level(
        symbol, "1w", weekly_from_daily(bars_by_level.get("1d", []))
    )
    verdict = build_multilevel_verdict(levels)
    asof_candidates = [
        level.get("asof") for level in levels.values() if level.get("asof")
    ]
    return {
        "contract": "chanlun_multilevel_v1",
        "meta": {
            "symbol": symbol,
            "asof": max(asof_candidates) if asof_candidates else None,
            "engine": "chan.py@429d6ed(local)",
            "config_hash": CONFIG_HASH,
            "trade_level": "1d",
            "confirm_level": "30m",
            "trigger_level": "5m",
            "review_level": "1w",
            "ai_tokens": 0,
        },
        "levels": levels,
        "verdict": verdict,
        "caveats": [
            "固定口径：严格笔、特征序列线段、段内中枢、MACD peak背驰(rate<0.9)",
            "低级别只确认或触发日线候选，不能独立制造日线买卖点",
            "sure=false 是当前帧候选，新K线可能使其消失或位移",
            "仅用于结构研究，不构成投资建议或自动交易授权",
        ],
    }
