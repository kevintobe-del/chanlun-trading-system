# Multi-Level Recursion

## Table Of Contents

- Level discipline
- Interval nesting
- Small-turn-big
- Same-level decomposition
- Large/small conflict
- Practical workflows

## Level Discipline

Every conclusion must state:

- `trade_level`
- `confirm_level`
- `trigger_level`
- `definition_mode`

Never argue like this:

- "Daily is bullish, 5m has a bounce, therefore weekly reversal."

Correct reasoning:

- Operating level signal appears.
- Lower level confirms turn.
- Higher level does not invalidate the trade.
- Invalidation is explicit.

## Interval Nesting

Interval nesting means using lower-level structure inside the final operating-level segment to locate a precise turn.

Use cases:

- First buy: in the last down segment, look for lower-level bottom divergence and lower-level center break upward.
- First sell: in the last up segment, look for lower-level top divergence and lower-level center break downward.
- Second buy/sell: use lower-level first buy/sell during the pullback/rebound.
- Third buy/sell: use lower-level third buy/sell around the pullback/rebound boundary.

Rules:

- Lower-level trigger refines timing; it does not create an operating-level buy/sell point without operating-level context.
- If lower-level structure is not available, use proxy triggers and label approximation loss.

## Small-Turn-Big

Small-level divergence can start a large-level reversal only if it damages the last meaningful lower-level center of the large-level movement.

Bottom case:

- Small-level bottom divergence appears.
- The last lower-level center inside the large-level down segment is broken upward.
- Pullback after the break does not destroy the lower-level reversal.
- Only then can the small turn be considered a candidate for larger-level turn.

Top case:

- Small-level top divergence appears.
- The last lower-level center inside the large-level up segment is broken downward.
- Rebound after the break fails to repair the lower-level structure.

Position rule:

- Small-turn-big permits partial action.
- Full operating-level action waits for operating-level confirmation or key boundary break.

## Same-Level Decomposition

Same-level decomposition fixes one operating level and decomposes all movements into that level's trend/consolidation types.

Why use it:

- Reduces arbitrary level switching.
- Makes backtesting possible.
- Prevents using small-level noise to justify large-level actions.

Basic rhythm:

- In an up sequence, buy before the up leg matures and sell after sell-side structure appears.
- In a down sequence, sell/avoid before the down leg matures and buy after buy-side structure appears.
- Center extension can be treated as repeated consolidation on the operating level, while lower levels still have their own centers.

## Large/Small Conflict

If levels disagree:

- Higher-level downtrend + lower-level buy: `buy_probe` at most; prefer `observe`.
- Higher-level center support + operating-level first buy: better probe conditions.
- Higher-level third sell + operating-level first buy: reject unless explicitly trading a short rebound.
- Operating-level third buy + lower-level overbought: hold or wait for pullback, not automatic sell.
- Operating-level first sell + higher-level uptrend: reduce trading position, do not necessarily exit core.

## Practical Workflows

Daily swing with unavailable 30m:

- Label as `proxy_research`.
- Use daily structure for candidate.
- Use next-day/short MA/MACD only as proxy confirmation.
- Avoid calling it strict second/third buy.

Daily swing with 30m/60m:

- Daily defines trade-level candidate.
- 60m confirms structure.
- 30m or 5m triggers entry.
- Daily invalidation controls risk.

Medium-term with weekly/daily:

- Weekly defines background.
- Daily defines buy/sell point.
- 30m refines trigger if available.

Fast trading:

- 30m defines trade-level.
- 5m confirms.
- 1m triggers.
- Do not reinterpret every 1m move as a 30m reversal.

## Output Checklist

When using multi-level logic, state:

- Larger-level background.
- Operating-level structure.
- Lower-level trigger or missing trigger.
- Whether small-turn-big conditions are met.
- What boundary would prove the interpretation wrong.
