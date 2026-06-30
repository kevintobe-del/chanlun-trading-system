# Backtest Proxies

Strict Chan drawing is difficult to reproduce. Start with proxy systems, label approximation loss, and keep strict/proxy columns separate.

## Minimum Data

Preferred:

- Daily + 30m/60m OHLCV.
- MACD, RSI.
- Volume, turnover, money flow for A-shares.
- Benchmark/index regime.

Fallback:

- Daily OHLCV only.
- Label as `proxy_research`.
- Use lower-level confirmation only if actually available.

## Proxy Signal Families

First buy proxy:

1. Detect prior down segment A.
2. Detect center/consolidation B.
3. Detect second down segment C that makes a new low.
4. Require weaker force in C versus A by MACD area, slope, or length.
5. Entry variants: next bar, lower-level turn, close above short MA, or reclaim lower-level center boundary.

Second buy proxy:

1. First buy proxy appears.
2. Rebound appears.
3. Pullback does not break first-buy low.
4. Score by pullback volume, turnover contraction, and money-flow deterioration/repair.

Third buy proxy:

1. Detect center proxy.
2. Price leaves above center.
3. Pullback low remains above center boundary.
4. Score by leave force, pullback volume/turnover, and absence of strong money outflow.

Sell-side proxies mirror the above.

## Current Research Lessons

Hard numbers and full tables live in `references/empirical-evidence.md` — cite that file,
not this summary. Headline findings from the 176-stock large-sample daily proxy study
(survivorship-biased; proxy ≠ strict Chan):

First buy — a probe, not alpha:

- Idealized next-bar entry: **62.09% direction / +3.19% excess** over 20 days.
- Realistic tradeable entry (reclaim MA10 + MACD histogram turn): **56.93% / +2.17% excess**.
- Delay-sensitive: 62.09% (`delay_1`) → 56.43% (`delay_3`) → 53.44% (`delay_5`) at 20 days.
- +2% excess over 20 days is thin after costs — treat a daily first buy as an
  observation zone, not a fill.

Sell side — the reliable half:

- First sell, 20 days: **61.42% direction, ~1.87% avoided loss**; the edge fades past 20 days.
- The single strongest signal in the study is a sell: strong divergence + down market =
  **64.82% direction / 66.56% excess / +3.15% avoided loss**.
- Use sell signals as a 20-day risk flag, not a long-term short thesis.

Filters and regime:

- Buy edge is mean-reversion: strong in down/oversold markets (~63%), but ~coin-flip on
  excess in up markets (you are just riding beta).
- Strong-divergence filter does NOT raise the buy hit rate (61.9% vs 62.1% baseline) — it
  cuts signal count ~4x. Use it to trade less, not to trade more confidently.
- Money flow should be a buy-side veto/risk factor rather than simple additive alpha.

Bottom line: as measured, Chanlun is a **risk-control / discipline tool, not a stock picker**.

## Evaluation Metrics

For each signal:

- Signal type.
- Definition mode.
- Trade level.
- Entry kind.
- Horizon.
- Return.
- Direction hit.
- Excess return.
- Score bucket.
- Failure reason if available.

Core summaries:

- Win/hit rate.
- Mean/median return.
- A/B/C bucket separation.
- A minus C value.
- Stock coverage.
- Signal density.
- Regime sensitivity.
- Transaction feasibility.

## Engineering Rules

- Never code every Chan concept at once.
- Implement one closed loop, test, then add filters.
- Keep thresholds configurable.
- Record `definition_mode` and approximation loss in every signal.
- Exclude or flag ST, suspension, hard limit-up/down, illiquidity, and survivorship bias.
- Do not accept results without comparing base vs factor-enhanced vs veto variants.

## Recommended Iteration Path

1. Strictly define daily proxy signal generation.
2. Add 30m/60m confirmation when data access is stable.
3. Add volume/turnover/candle scoring.
4. Add money-flow veto.
5. Expand sample.
6. Test transaction costs and execution constraints.
7. Convert only stable rules into strategy code.
