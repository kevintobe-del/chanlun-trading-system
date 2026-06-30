# Empirical Evidence (Large-Sample Proxy Backtest)

This file carries the **hard numbers** behind the skill's framing. Cite it whenever a
user asks "does Chanlun actually work?" — and quote the honest version, not the
flattering one.

> **Scope & honesty notes (read before quoting any number):**
> - Results are **reproducible daily *proxy* signals**, not hand-drawn strict Chanlun.
>   They approximate first/second/third buy & sell points; label everything
>   `structure_proxy` / `proxy_research`, never `strict_chanlun`.
> - Sample = **176 stocks**, current CSI 300 + CSI 500 constituents, history to
>   2026-06-05, cap 180 names. **This has survivorship bias** (today's index members
>   were yesterday's winners) — real-world hit rates are likely *lower*.
> - **19,486 signals total** (10,011 first-buy / 9,020 first-sell — pre-filter count;
>   tradeable-entry rows are fewer because some signals never trigger an entry).
> - Daily-only proxy **cannot replace 30m/60m Chanlun confirmation**. These numbers
>   are an honesty floor, not a performance ceiling.
> - **Not investment advice. No buy/sell signals. No return guarantee.**

---

## Headline (the one conclusion that matters)

**Chanlun, as measured here, is a risk-control / discipline tool — not a stock picker.**

- Buy points earn only **+2~3% excess return over 20 days** in the *idealized* case, and
  the edge **decays to near coin-flip** once you account for realistic, tradeable entry
  timing and transaction costs.
- Sell points are the **more reliable half**: they reliably flag **short-horizon
  downside risk** (avoided loss ~1.9% over 20 days, stronger in down markets).
- So the skill's job is to help users **size down, wait, and avoid bad entries** — not
  to promise upside. This is exactly why the skill outputs "observe / downgrade"
  instead of "buy."

---

## 1. Buy side — a probe, not alpha

`first_buy_proxy`, all signals, by entry method and horizon:

| Entry method | Horizon | n | Direction hit | Excess hit | Mean ret | Mean excess |
|---|---|---|---|---|---|---|
| **`delay_1` (idealized, next-bar)** | 20d | 9,952 | **62.09%** | 57.76% | +4.58% | +3.19% |
| `delay_1` (idealized) | 60d | 9,824 | 57.85% | 54.95% | +8.15% | +5.89% |
| `delay_1` (idealized) | 120d | 9,699 | 56.63% | 54.42% | +13.20% | +9.52% |
| **`reclaim_ma10` (tradeable)** | 20d | 9,574 | **56.93%** | 53.75% | +3.17% | +2.17% |
| `reclaim_ma10` (tradeable) | 60d | 9,447 | 54.66% | 52.56% | +6.69% | +4.79% |
| `reclaim_ma10` (tradeable) | 120d | 9,336 | 53.76% | 51.93% | +11.58% | +8.28% |

**Delay sensitivity (this is the fragile part — quote it):** the headline 62% assumes you
act on the *very next bar* after the fractal confirms. Wait a few days and it collapses:

| Entry (20-day horizon) | Direction hit | Mean excess |
|---|---|---|
| `delay_1` (next bar) | **62.09%** | +3.19% |
| `delay_3` (3 bars later) | 56.43% | +2.10% |
| `delay_5` (5 bars later) | 53.44% | +1.61% |

**How to read this:**
- The "tradeable" entry (wait for a close back above MA10 with MACD histogram turning up)
  is the honest number: **~57% direction, +2.17% excess over 20 days.**
- +2.17% over 20 days is **thin once round-trip costs (~0.2–0.5%) and slippage are
  removed.** Treat a daily first-buy as an **observation zone, not a fill** — require
  lower-level (30m/60m) or MA-reclaim confirmation before any "act" language.

---

## 2. Sell side — the real edge is risk avoidance

`first_sell_proxy`, all signals (`expected_direction = down`; "avoided loss" = drawdown
dodged by exiting):

| Entry method | Horizon | n | Direction hit | Excess hit | Mean ret | Avoided loss |
|---|---|---|---|---|---|---|
| **`delay_1` (idealized)** | 20d | 8,976 | **61.42%** | 62.70% | −1.87% | **+1.87%** |
| `delay_1` (idealized) | 60d | 8,918 | 56.32% | 57.17% | +1.32% | −1.32% |
| `reclaim_ma10` mirror (tradeable) | 20d | 8,710 | 55.06% | 57.07% | +0.09% | −0.09% |
| `reclaim_ma10` mirror (tradeable) | 60d | 8,657 | 52.75% | 53.91% | +3.33% | −3.33% |

**How to read this:**
- The 20-day sell signal **reliably marks short-term downside** (61% direction, ~1.9%
  loss avoided). Beyond 20 days the edge fades and can flip positive (markets drift up),
  so **only use sell signals as a 20-day risk flag, not a long-term short thesis.**
- A sell signal means **de-risk / trim / tighten stop**, not "go short" and not
  "machine-dump everything" — especially if the weekly trend is still strong.

---

## 3. Market regime & filters — where the edge actually lives

| Bucket | Signal | Horizon | n | Direction hit | Excess hit | Avoided loss |
|---|---|---|---|---|---|---|
| `market_down` | first-buy `delay_1` | 20d | 5,939 | 63.21% | 61.00% | — |
| `market_up` | first-buy `reclaim_ma10` | 20d | 3,858 | 55.37% | **50.10%** | — |
| `market_down` | first-sell `delay_1` | 20d | 4,149 | 63.39% | 63.03% | +2.77% |
| **`sell_strong_and_market_down`** | first-sell `delay_1` | 20d | 668 | **64.82%** | **66.56%** | **+3.15%** |
| `strong_divergence` | first-buy `delay_1` | 20d | 2,404 | 61.90% | 57.93% | — |

**How to read this:**
- **Buy edge is mean-reversion, not trend-following.** It is strongest in **down /
  oversold markets** (63% in `market_down`) and **weakest in up markets** — in up
  markets the excess hit drops to **~50% (a coin flip vs benchmark)**: you are just
  riding beta, not adding alpha. Don't oversize first-buys in a hot tape.
- **The single strongest signal in the whole study is a *sell*:** strong divergence +
  down market = **64.82% direction / 66.56% excess / +3.15% avoided loss.** Chanlun's
  most dependable call is "get out of the way," not "get in."
- **Strong-divergence filtering does NOT raise the buy hit rate** (61.90% vs 62.09%
  baseline) — but it **cuts signal count ~4x** (2,404 vs 9,952). Its value is
  **noise reduction, not alpha.** Use it to trade less, not to trade more confidently.

---

## 4. Translating evidence into skill behavior

These rules are downstream of the numbers above; enforce them in output:

1. **Daily first-buy = observation zone, never a fill.** Require lower-level (30m/60m)
   or MA10-reclaim + MACD-histogram confirmation before any "act" wording.
2. **Prefer buys where the 120-day market trend is up and the stock's long-term MAs are
   not deteriorating.** In a primary down-market, cut position size on first-buys.
3. **Sell signals are a 20-day risk flag only.** If the weekly trend is strong, trim or
   trail — do not mechanically liquidate.
4. **Strong divergence improves quality marginally; use it to filter out noise, not to
   add confidence.** Never treat RSI/MACD alone as a buy/sell point.
5. **State the thin excess return honestly.** When a user expects "alpha," tell them the
   measured buy-side excess is ~2% / 20 days before costs — this is discipline, not a
   money machine.

---

## 5. Provenance & reproducibility

- Source study: large-sample Chanlun practicality evaluation v2, generated 2026-06-07,
  on TuShare daily data; entry methods `delay_1/3/5` (idealized) and
  `buy_reclaim_ma10_hist_turn` / `sell_lose_ma10_hist_turn` (tradeable confirmation).
- Companion studies (consistent direction): a 100-stock TuShare factor-combo evaluation
  and per-stock walk-throughs (e.g. Anker / 安克) reached the same qualitative verdict —
  buy points are weak/probe-grade, sell points are useful as short-term risk control.
- **Known limitations to disclose alongside any quote:** survivorship bias (current index
  members), daily-only proxy (no live 30m/60m), no live transaction-cost / slippage model
  on the headline rates, and proxy ≠ strict hand-drawn Chanlun. Numbers are an honesty
  floor; do not present them as a validated trading edge.
