# Buy/Sell Playbooks

## Table Of Contents

- Buy-side map
- First buy
- Second buy
- Third buy
- Sell-side mirror
- Profit-max mode
- False positives

## Buy-Side Map

The three buy points answer different questions:

- First buy: Has the prior downtrend likely exhausted?
- Second buy: Did the first buy survive its first test?
- Third buy: Has price left a center upward and refused to return?

Practical ranking:

- First buy has better price but lower confirmation.
- Second buy is often the most practical balance of risk and confirmation.
- Third buy is right-side confirmation but can be late if the larger level is exhausted.

## First Buy

Structural setup:

- Prior same-level structure is downtrend, or `down + center + down`.
- The final down segment makes a new low relative to the previous same-direction segment.
- The final down segment is weaker by at least one structural force measure.
- A prior center or consolidation area exists as rebound reference if possible.

Divergence checks:

- Compare the last down segment with the prior same-level down segment.
- MACD area, slope, segment length, and lower-level interval nesting should not contradict each other severely.
- Best case: price makes a lower low, but MACD area shrinks, slope weakens, and lower-level bottom divergence appears.

Trigger:

- Lower-level first buy inside the final down segment.
- Or lower-level center forms and is broken upward.
- Or proxy trigger: close reclaims short MA after divergence while invalidation remains nearby.

Action:

- `buy_probe` if only first-buy structure exists.
- `observe` if lower-level trigger is missing.
- Prefer small position unless higher-level support and filters align.

Invalidation:

- Break below first-buy low after trigger.
- Rebound cannot reach the nearest prior center lower boundary or reference area.
- A new same-level downtrend center forms below the first-buy area.
- Volume/turnover shows continued panic expansion with no lower-level repair.

False positives:

- Catching a falling knife without lower-level turn.
- Calling any MACD bottom divergence a first buy without a same-level downtrend.
- Treating a single long lower shadow as enough.

## Second Buy

Structural setup:

- A first buy candidate has appeared.
- Price has produced the first upward movement after the first buy.
- The first pullback after that upward movement does not break the first-buy structural boundary.
- Ideally the pullback forms a lower-level first buy.

Trigger:

- Lower-level first buy during pullback.
- Pullback low stays above first-buy low or agreed structural boundary.
- Price turns up from the pullback with a clear invalidation level.

Action:

- `buy_confirmed` if pullback is controlled and lower-level trigger appears.
- `buy_probe` if structure holds but lower-level trigger is weak.
- It can add to a first-buy probe position.

Invalidation:

- Pullback breaks the first-buy low or destroys the first-buy logic.
- Pullback expands into a larger downtrend.
- Rebound after second buy fails immediately and creates a new lower-level third sell.

Quality boosters:

- Pullback volume shrinks.
- Turnover contracts rather than overheats.
- Money flow stops deteriorating or turns neutral.
- RSI/MACD improves versus first-buy low.

False positives:

- Calling a rebound chase a second buy before the pullback.
- Ignoring a pullback that breaks structural low.
- Treating every higher low as a second buy without the first-buy context.

## Third Buy

Structural setup:

- A valid center exists.
- Price leaves the center upward.
- Pullback does not re-enter the center under the chosen definition.
- Best case: first center's third buy after a long consolidation; weaker case: late third buy after many centers.

Trigger:

- Pullback completes and turns upward.
- Lower-level third buy or lower-level first buy appears on the pullback.
- Proxy trigger: pullback low remains above `zg`, then price reclaims short MA or breaks pullback high.

Action:

- `buy_confirmed` if center, leave, pullback, and trigger are all clear.
- `hold` if already positioned from first/second buy and third buy confirms trend.
- Avoid chasing a vertical leave before pullback unless using a smaller-level third buy.

Invalidation:

- Pullback re-enters the center.
- Breakout fails and center expands.
- A lower-level third sell appears after the attempted third buy.
- Larger-level divergence appears near the same area.

Quality boosters:

- Leave has enough force but is not blow-off.
- Pullback volume and turnover contract.
- Pullback does not show sustained main-money outflow.
- MACD remains above zero or starts improving quickly.

False positives:

- Calling any breakout a third buy before pullback.
- Ignoring that a late third buy may be part of higher-level exhaustion.
- Using close-only data to claim a strict non-return to center when intraday data contradicts it.

## Sell-Side Mirror

First sell:

- Prior same-level structure is uptrend, or `up + center + up`.
- Final up segment makes a new high but weakens.
- Lower-level first sell appears inside the final up segment.
- Action is usually `reduce` or `sell_exit` for trading position, not necessarily long-term bearish.

Second sell:

- First sell has appeared.
- Price drops, then rebounds.
- Rebound fails to make a new high or fails to repair structure.
- High-quality second sell often has weak volume/turnover on rebound and money flow deterioration.

Third sell:

- Price leaves center downward.
- Rebound does not re-enter center.
- Strong short-term risk signal; often used to avoid buying or to cut remaining position.

Sell invalidation:

- First sell invalidated if price continues upward with stronger lower-level structure and forms new center above.
- Second sell invalidated if rebound exceeds first-sell high and repairs structure.
- Third sell invalidated if rebound re-enters center and center expands.

## Profit-Max Mode

For a fixed symbol and operating level:

1. Find the latest valid center.
2. If price is inside center, trade oscillation only if skilled; otherwise wait.
3. If price is below center and no third sell exists, look for center-oscillation buy via divergence.
4. If price is below center after third sell, avoid the operating-level downtrend.
5. If price is above center without third buy, wait for pullback or smaller-level setup.
6. If price is above center after third buy, hold until a new center forms or upward movement diverges.
7. Reduce when sell-side structure appears on operating level; do not exit core solely on tiny lower-level noise.

## Decision Tree

Buy-side:

1. Is there a valid operating-level center/trend context?
2. Is the signal first/second/third buy by structure, not by indicator?
3. Is there a lower-level trigger?
4. Is invalidation close and explicit?
5. Do filters confirm, neutralize, or veto?
6. Is larger-level context supportive or hostile?
7. Choose action: `wait`, `observe`, `buy_probe`, `buy_confirmed`, `hold`.

Sell-side:

1. Is the signal first/second/third sell by structure?
2. Is the position trading, core, or observation-only?
3. Is the sell signal operating-level or lower-level noise?
4. Does volume/turnover/money flow confirm risk?
5. Choose action: `reduce`, `sell_exit`, `hold_core_reduce_trading`, `wait_rebuy`.
