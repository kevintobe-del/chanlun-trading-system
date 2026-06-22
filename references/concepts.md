# Chanlun Concepts

## Table Of Contents

- Source hierarchy
- Definition modes
- Core chain
- Levels
- State taxonomy
- Divergence taxonomy
- Practical discipline

## Source Hierarchy

Use this hierarchy when books or interpretations conflict:

1. `缠中说禅教你炒股票`: primary baseline for level, center, trend/consolidation, divergence, and buy/sell logic.
2. Thematic reorganizations/new explanations: useful for learning order, not superior to the original definitions.
3. Technical exegesis books: useful for inclusion, fractals, strokes, segments, and center-construction disputes.
4. Diagram books: useful for visual pattern recognition and operational examples.
5. Practical trading books: useful for filters, execution, and risk, but their indicators do not redefine Chan structure.

## Definition Modes

Always label the mode:

- `original_definition`: center is overlap of at least three continuous sublevel trend types.
- `segment_proxy`: center is overlap of at least three continuous sublevel segments or strokes. Use for reproducible research.
- `swing_proxy`: center is approximated from swing highs/lows. Use for quick chart diagnosis.
- `kline_proxy`: lowest-level structure from merged K-lines. Use only when finer data is unavailable.
- `indicator_proxy`: MACD/RSI/MA-only approximation. Never call it strict Chanlun.

Approximation loss:

- Original definitions are recursive and level-bound.
- Daily-only proxies can find useful swing structure but cannot prove lower-level buy/sell points.
- A strict buy/sell point requires the lower-level structure inside the operating-level segment.

## Core Chain

The complete structure chain:

1. K-line inclusion handling.
2. Top/bottom fractals.
3. Strokes.
4. Segments.
5. Centers.
6. Trend/consolidation type.
7. Divergence or non-divergence.
8. First/second/third buy/sell point.
9. Invalidation, position, and next observation.

Do not skip from indicators directly to buy/sell points.

## Levels

Key roles:

- `trade_level`: level whose buy/sell point is being traded.
- `confirm_level`: usually one lower level, used to check lower-level structure.
- `trigger_level`: execution level for timing.
- `review_level`: one higher level, used to avoid trading against a larger invalidated structure.

Defaults:

- Medium-term: weekly / daily / 30m.
- Swing: daily / 30m / 5m.
- Short-term: 30m / 5m / 1m.

Rules:

- No level, no valid signal.
- Do not freely mix levels to justify a trade after the fact.
- If the lower level contradicts the trade level, downgrade action from `buy_confirmed` to `observe` or `buy_probe`.

## State Taxonomy

Use one current-state label:

- `center_oscillation`: price is inside or repeatedly returning to the latest center.
- `center_extension`: same center continues; no true departure.
- `center_breakout`: price leaves center but pullback/rebound confirmation is not complete.
- `uptrend`: at least two same-level centers moving upward or a valid third buy followed by continuation.
- `downtrend`: mirror of uptrend.
- `transition_zhongyin`: old trend likely ended, but new trend is not born; usually after first buy/sell or divergence.
- `first_buy_candidate`, `second_buy_candidate`, `third_buy_candidate`: candidate only until trigger and invalidation are named.
- `first_sell_candidate`, `second_sell_candidate`, `third_sell_candidate`: sell-side mirrors.
- `untradable_unclear`: structure cannot be named.

## Center States

- `forming`: first three sublevel movements are building overlap.
- `oscillating`: price repeatedly leaves and returns to center.
- `extension`: additional moves keep overlapping the same center.
- `newborn`: a new same-level center appears away from the prior center.
- `expansion`: separated structures overlap at a higher level.
- `broken_up`: upward leave plus pullback not re-entering center.
- `broken_down`: downward leave plus rebound not re-entering center.

Boundaries:

- `zg`: upper boundary of center overlap.
- `zd`: lower boundary of center overlap.
- `gg`: highest high in center construction.
- `dd`: lowest low in center construction.

## Divergence Taxonomy

Divergence must name compared structures:

- `trend_divergence`: compare last same-direction segment after a center with the earlier same-direction segment in the same trend.
- `consolidation_divergence`: compare same-direction oscillation legs inside or around the same center.
- `class_divergence`: weaker force without a complete textbook trend structure; useful as caution, not as strict first buy/sell.
- `indicator_divergence`: MACD/RSI only. Requires structural confirmation before action.

Force comparison dimensions:

- Segment length and slope.
- MACD histogram area.
- DIF/DEA position and zero-axis behavior.
- Volume/turnover follow-through.
- Whether lower-level center has been broken in the reversal direction.

## Practical Discipline

- First buy/sell is often left-side and fragile.
- Second buy/sell is often more practical because it tests the first signal.
- Third buy/sell is right-side confirmation, but late third buys after multiple centers can be vulnerable to larger-level consolidation.
- Inside center oscillation, only skilled short-difference operators should trade actively.
- After a valid third buy, shift from center oscillation to trend holding until a new center or divergence appears.
