# Volume, Turnover, And Money Flow

## Table Of Contents

- Role in Chanlun
- TuShare fields
- Buy-side matching
- Sell-side matching
- 100-stock research result
- Scoring guidance

## Role In Chanlun

Volume, turnover, and money flow are not Chan definitions. Use them after structure:

1. Structure identifies candidate buy/sell point.
2. Volume/turnover judge participation quality.
3. Money flow judges whether pressure is continuing or easing.
4. The final action is adjusted through score, position size, waiting, or veto.

## TuShare Fields

Useful fields:

- `stk_factor` or qfq daily OHLCV: open/high/low/close, `vol`, `amount`.
- `daily_basic`: `turnover_rate`, `turnover_rate_f`, `volume_ratio`, market cap.
- `moneyflow`: `net_mf_amount`, large-order and extra-large-order buy/sell amount.

Derived fields:

- `amount_ratio_20 = amount / MA20(amount)`.
- `amount_ratio_60 = amount / MA60(amount)`.
- `vol_ratio_20 = vol / MA20(vol)`.
- `turnover_f_ratio20 = turnover_rate_f / MA20(turnover_rate_f)`.
- `main_net_amount = buy_lg + buy_elg - sell_lg - sell_elg`.
- `main_net_amount_5d_strength20 = rolling5(main_net_amount) / (MA20(abs(main_net_amount)) * 5)`.
- Upper/lower shadow percentages from OHLC.

## Buy-Side Matching

First buy:

- Helpful: lower shadow, selling volume no longer expanding, main money stops deteriorating.
- Caution: heavy volume down day with no lower-level repair.
- Money flow: best used as veto if main money continues large outflow.

Second buy:

- Best confirmation: pullback volume shrinks and turnover contracts.
- Good: amount/volume around 0.45-1.05 times 20-day average.
- Bad: pullback breaks boundary with expanding amount and hot turnover.
- Money flow: neutral or improving helps; strong continued outflow downgrades.

Third buy:

- Best confirmation: upward leave has force; pullback above center has moderate/contracting amount and turnover.
- Bad: pullback above center has panic amount expansion or hot turnover.
- Money flow: use as warning if main money leaves during pullback.

## Sell-Side Matching

First sell:

- Helpful: new high with divergence plus high volume/turnover, upper shadow, or money outflow.
- Caution: top divergence while main money remains strongly positive can be early.

Second sell:

- Helpful: rebound is weak, volume/turnover contracts, money fails to return.
- Strong: rebound does not make new high and money outflow resumes.

Third sell:

- Helpful: downward leave or failed rebound with volume/turnover confirmation.
- Use primarily for risk control and avoiding buys.

## 100-Stock Research Result

A 100-stock A-share research test (TuShare data):

- Sample: 100 diverse A-shares, 62 industries, 17,760 Chan proxy signals, 868,740 combo events.
- Buy-side strongest broad combos were `base+candle`, `base+volume`, and `base+volume+turnover`.
- `base+volume+turnover` remained useful, but was no longer the clear winner after broader diversification.
- Money flow weakened buy-side A/C separation when added linearly.
- Sell-side signals had short-term value around 20 days; 60-day sell signals were unstable as long-term bearish calls.

Practical conclusion:

- Buy scoring: structure + candle/acceptance + volume, with turnover as auxiliary.
- Buy veto: sustained main-money outflow after candidate buy.
- Sell scoring: structure + volume + turnover; money flow can confirm short-term risk.
- Do not use all factors as a simple additive model without checking A/C separation.

## Scoring Guidance

Suggested factor roles:

- `volume`: core scoring factor.
- `turnover`: auxiliary scoring factor; confirms whether volume reflects healthy participation or overheated churn.
- `money`: veto/risk factor for buys; confirmation factor for sells.
- `candle`: auxiliary acceptance/rejection factor; strongest for first buy and first sell.

For each signal, output:

- `volume_state`: shrinking, normal, expanding, overheated.
- `turnover_state`: contracted, normal, hot.
- `money_state`: improving, neutral, deteriorating.
- `candle_state`: lower-shadow support, upper-shadow pressure, neutral.
- `filter_action`: confirm, neutral, caution, veto.

Avoid:

- Buying only because money flow is positive.
- Selling only because money flow is negative.
- Treating high turnover as always bullish; at high levels it often means distribution or disagreement.
