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

Large-sample daily proxy results:

- First buy had positive 20/60/120-day value but should be treated as probe.
- Second buy was theoretically attractive but daily-only proxy needed volume/turnover confirmation.
- Third buy was broadly positive but A-bucket saturation showed the proxy was too permissive.
- Sell signals were useful as short-term risk management, not as long-term short signals.

TuShare 100-stock factor-combo result:

- Buy-side: `base+candle`, `base+volume`, and `base+volume+turnover` were strongest broad combinations.
- Money flow should be a buy-side veto/risk factor rather than simple additive alpha.
- Sell-side: short-term 20-day risk signals were useful; 60-day sell signals were unstable.

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
