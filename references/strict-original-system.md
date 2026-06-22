# Strict Original Chanlun System

## Purpose

This reference prevents Chanlun research from drifting into indicator trading.  Use it before accepting any buy/sell point as strict Chanlun.

## Four-Layer Contract

Layer 1: `original_definition`

- Center is built from at least three continuous sublevel trend types.
- Trend/consolidation is judged through same-level decomposition.
- Divergence compares named same-level movements.
- Buy/sell points are derived from structure, not from scores or indicators.

Layer 2: `segment_proxy`

- K-line inclusion, fractals, strokes, segments, and centers are reproducible.
- Centers may be built from strokes/segment proxies rather than fully recursive sublevel trend types.
- Valid for systematic research if approximation loss is stated.

Layer 3: `swing_proxy`

- Swing highs/lows approximate strokes and centers.
- Useful for broad scans and hypothesis generation.
- Not sufficient for strict first/second/third buy/sell labels.

Layer 4: `indicator_proxy`

- MA/MACD/RSI/volume/turnover/money-flow confirm, veto, or size a trade.
- They never define a Chanlun structure or buy/sell point.

## Required Structure Chain

Do not skip steps:

1. Clean OHLCV data and align trading sessions.
2. Apply K-line inclusion handling.
3. Detect top/bottom fractals after inclusion.
4. Build valid alternating strokes.
5. Build segment or segment proxy from strokes.
6. Build same-level center from named lower-level components.
7. Classify current state: center oscillation, center extension, center break, trend, transition, or unclear.
8. Compare same-level movements if divergence is claimed.
9. Locate first/second/third buy/sell.
10. Name invalidation and next observation point.

If any step is missing, downgrade `definition_mode`.

## Buy/Sell Point Strictness

First buy:

- Prior same-level state must be a downtrend or `down + center + down`.
- The final down movement must make a new low or otherwise complete a comparable terminal move.
- Weakness must be compared against the prior same-direction movement at the same level.
- Lower-level turn should appear inside the final down movement.
- Invalidation is the terminal low or explicitly named structural boundary.

Second buy:

- A first-buy candidate must exist.
- The first upward movement after the first buy must be named.
- The following pullback must not destroy the first-buy structure.
- Lower-level first buy/turn during pullback is preferred.
- Invalidation is the first-buy low or pullback structural low.

Third buy:

- A valid center must exist with `zg/zd/gg/dd`.
- Price must leave above `zg`.
- Pullback must not re-enter the center under the selected definition.
- Lower-level structure around the pullback must confirm turn or at least not contradict it.
- Invalidation is re-entry into center or destruction of the pullback structure.

Sell-side rules mirror the above.

## Downgrade Matrix

Use these labels:

- `strict_chanlun`: all structure gates pass at the chosen levels.
- `structure_proxy`: inclusion/fractal/stroke/center are reproducible, but segment/trend recursion is simplified.
- `signal_proxy`: a daily signal resembles a buy/sell point but lacks lower-level recursive proof.
- `indicator_proxy`: only indicator or factor confirmation exists.
- `untradable_unclear`: structure cannot be named.

Required wording:

- "This is strict" only when `strict_chanlun`.
- "This is a structure proxy" when segments or centers are approximated.
- "This is not a strict Chanlun buy/sell point" when using scores, MA, MACD, volume, turnover, or money flow as the main signal.

## Backtest Signal Columns

Any generated signal table should include:

- `code`
- `trade_date`
- `available_date`
- `exec_date`
- `trade_level`
- `confirm_level`
- `trigger_level`
- `definition_mode`
- `structure_completeness`
- `approximation_loss`
- `current_state`
- `center_id`
- `zg`
- `zd`
- `gg`
- `dd`
- `signal_class`
- `compared_move_a`
- `compared_move_b`
- `divergence_type`
- `lower_level_trigger`
- `invalidation`
- `next_observation`

## Refactor Priority

1. Build 30m/60m structure agents from bars.
2. Replace 30m/60m MA/MACD proxies with structure-state features.
3. Rebuild daily buy/sell labels from structure, not score buckets.
4. Add multi-level recursion: daily candidate -> 60m confirmation -> 30m trigger.
5. Only after structural labels are stable, add volume/turnover/money-flow as veto or sizing.

## Acceptance Test

A strategy cannot be called original-system aligned unless it can answer:

1. What is the trade level?
2. What is the latest valid center?
3. Is price inside center, leaving center, returning to center, or trending away?
4. Which two movements are compared for divergence?
5. Which buy/sell point class is this?
6. What lower-level structure confirms the trigger?
7. What exact boundary invalidates it?
8. What would make the current interpretation downgrade to observe?
