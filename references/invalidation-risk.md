# Invalidation And Risk

## Table Of Contents

- Core rule
- Invalidation by signal class
- Position logic
- Holding logic
- Failure-review taxonomy

## Core Rule

Every action must include:

- Entry basis.
- Trigger.
- Structural invalidation.
- Risk action if invalidated.
- Next observation point.

If invalidation cannot be named, action must be `wait` or `observe`.

## Invalidation By Signal Class

First buy:

- Breaks first-buy low after trigger.
- Rebound cannot reach nearest center/consolidation reference.
- New same-level down center forms below the candidate.
- Lower-level third sell appears after supposed lower-level reversal.

Second buy:

- Pullback breaks first-buy structural low.
- Pullback expands into larger downtrend.
- Turn-up fails and creates lower-level third sell.

Third buy:

- Pullback re-enters center.
- Breakout fails and center expands.
- Large-level sell-side divergence appears immediately above.

First sell:

- Price continues upward with stronger same-level structure.
- New higher center forms and holds.
- Lower-level sell is quickly invalidated.

Second sell:

- Rebound exceeds first-sell high.
- Rebound repairs lower-level structure and forms higher center.

Third sell:

- Rebound re-enters center.
- Downward leave is absorbed and center expands.

## Position Logic

Position actions:

- `observe`: no trade; structure incomplete.
- `buy_probe`: small position for first buy or uncertain second buy.
- `buy_confirmed`: structure, trigger, and filters align.
- `hold`: valid third buy or no operating-level sell signal.
- `reduce`: sell-side signal on operating level or strong lower-level risk.
- `sell_exit`: operating-level sell with invalidation of bullish structure.
- `rebuy`: after sell/reduce, lower-level buy reappears without violating operating-level logic.

Risk sizing:

- First buy: smallest unless higher-level support is strong.
- Second buy: normal if pullback is controlled.
- Third buy: normal if early in trend; smaller if late after multiple centers.
- Sell-side lower-level signal: reduce trading position before core unless operating-level invalidates.

## Holding Logic

After first buy:

- Expect rebound to test prior center/consolidation.
- If rebound is weak, treat as failed first buy.

After second buy:

- Expect price to exceed first rebound high or at least form stronger structure.
- Failure suggests transition or renewed downtrend.

After third buy:

- Shift from oscillation trading to trend holding.
- Hold until new center, upward divergence, or lower-level third sell after small-turn-big check.

After first/second/third sell:

- Use as short-term risk control first.
- Do not assume long-term bearish trend unless same-level or higher-level structure confirms.

## Failure-Review Taxonomy

Record failures as:

- `structure_wrong`: center/stroke/segment was misidentified.
- `level_mismatch`: used lower-level signal as operating-level reversal.
- `no_trigger`: acted before lower-level trigger.
- `filter_veto_ignored`: volume/turnover/money flow warned but was ignored.
- `late_signal`: third buy/sell was too late in larger-level trend.
- `market_regime`: broad market overwhelmed structure.
- `execution_gap`: limit-up/down, suspension, liquidity, slippage, lot-size issue.

For backtests, store failure reason distribution, not only win rate.
