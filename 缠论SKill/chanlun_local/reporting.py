from __future__ import annotations

from typing import Any


POSITION_TEXT = {
    "above_zs": "中枢上方",
    "in_zs": "中枢区间内",
    "below_zs": "中枢下方",
    None: "暂无有效中枢定位",
}


def _level_line(label: str, level: dict[str, Any]) -> str:
    if level.get("status") != "ok":
        return f"- {label}：数据不足（{level.get('bars', 0)}/{level.get('minimum', 120)}根）"
    last_bi = (level.get("bi") or [None])[-1]
    last_center = (level.get("zs") or [None])[-1]
    last_point = (level.get("bsp") or [None])[-1]
    parts = [f"{level.get('bars')}根K线"]
    if last_bi:
        parts.append(
            f"最近一笔{'向上' if last_bi['dir'] == 'UP' else '向下'}"
            f"（{last_bi['b']}→{last_bi['e']}，{'确认' if last_bi['sure'] else '未确认'}）"
        )
    if last_center:
        parts.append(
            f"中枢[{last_center['zd']}, {last_center['zg']}]，"
            f"现价位于{POSITION_TEXT.get(level.get('pos_vs_last_zs'))}"
        )
    if last_point:
        parts.append(
            f"最近{'买' if last_point['bs'] == 'B' else '卖'}点"
            f"{last_point['type']}@{last_point['d']}"
            f"（{'确认' if last_point['sure'] else '当前帧'}）"
        )
    return f"- {label}：" + "；".join(parts)


def build_report(name: str, result: dict[str, Any], session: str) -> str:
    meta = result["meta"]
    levels = result["levels"]
    verdict = result["verdict"]
    session_text = {
        "premarket": "盘前",
        "after_close": "收盘后",
        "manual": "手动",
    }.get(session, session)
    lines = [
        f"# {name or meta['symbol']}（{meta['symbol']}）缠论分析 · {session_text}",
        "",
        f"数据截至：{meta.get('asof') or '无可用行情'}",
        "",
        "## 级别与口径",
        "",
        "- 回看级别：周线；操作级别：日线；确认级别：30分钟；触发级别：5分钟",
        f"- 定义模式：{verdict['definition_mode']}",
        "- 固定口径：严格笔、特征序列线段、段内中枢、MACD peak背驰（rate<0.9）",
        "- AI token：0；execution_allowed=false",
        "",
        "## 结构",
        "",
        _level_line("周线", levels["1w"]),
        _level_line("日线", levels["1d"]),
        _level_line("30分钟", levels["30m"]),
        _level_line("5分钟", levels["5m"]),
        "",
        "## 买卖点门控",
        "",
        f"- 机械判定：{verdict['verdict']}",
        f"- 30分钟确认：{'有' if verdict['confirmation_30m'] else '缺失'}",
        f"- 5分钟触发：{'有' if verdict['trigger_5m'] else '缺失'}",
    ]
    candidate = verdict.get("day_candidate")
    if candidate:
        lines.append(
            f"- 日线候选：{'买' if candidate['bs'] == 'B' else '卖'}点"
            f" {candidate['type']}，日期={candidate['d']}，"
            f"状态={'确认' if candidate['sure'] else '当前帧候选'}"
        )
    else:
        lines.append("- 日线候选：最近窗口无新鲜买卖点")
    lines.extend(["", "## 失效条件（先于收益讨论）", ""])
    if verdict["invalidations"]:
        for item in verdict["invalidations"]:
            invalidation = item["invalidation"]
            lines.append(f"- {invalidation['rule']}：{invalidation['px']}")
    else:
        lines.append("- 当前没有新鲜日线信号，因此不生成虚假的信号止损价。")
    lines.extend(["", "## 下一观察点", ""])
    lines.extend(f"- {item}" for item in verdict["next_observation"])
    lines.extend(["", "## 结构完整度与近似损失", ""])
    completeness = verdict["structure_completeness"]
    lines.append(
        "- "
        + " / ".join(
            f"{key}={'完整' if value else '不足'}" for key, value in completeness.items()
        )
    )
    lines.extend(f"- {item}" for item in verdict["approximation_loss"])
    lines.extend(
        [
            "",
            "## 提示",
            "",
            "本报告由本地确定性规则生成，仅用于技术研究；不调用大模型，不构成投资建议。",
        ]
    )
    return "\n".join(lines)

