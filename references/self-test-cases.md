# Self-Test Cases

Use these checks before finalizing important Chanlun conclusions or strategy rules.

## Common False Positives

First buy false positives:

- MACD divergence but no same-level downtrend.
- New low with expanding panic volume and no lower-level turn.
- Tiny lower-level bounce treated as operating-level reversal.

Second buy false positives:

- No prior first buy context.
- Pullback breaks first-buy low.
- Pullback volume and turnover expand sharply.
- Rebound after pullback cannot exceed first rebound high.

Third buy false positives:

- Breakout without pullback.
- Pullback re-enters center intraday.
- Late third buy after multiple centers and higher-level divergence.
- Pullback above center but main money exits aggressively.

Sell false positives:

- First sell inside a strong higher-level uptrend with no operating-level destruction.
- Second sell called before a rebound after first sell.
- Third sell where rebound actually re-enters center and causes expansion.

## Real Counterexamples (daily-box proxy scan)

These are real A-share episodes flagged by a heuristic daily box/range scan — **not
hand-labeled strict Chanlun**, so treat them as illustrative traps, not authoritative
signals. Each one is a pattern the skill is built to refuse.

False breakout that returns into the box (fake third buy):

- 600717 around 2023-05-04 (box ~3.76–4.59): price broke above the range, then fell back
  in. A breakout without a holding pullback is not a third buy.
- 601222 around 2022-07-14 (box ~7.03–8.21): same trap — the "突破当三买" pattern Rule 13 forbids.

False breakdown that recovers (fake sell / faked-out break):

- 600717 around 2022-03-15 (box ~3.73–4.37): broke below the range, then recovered back in.
- 601222 around 2022-04-25 (box ~5.87–7.90): a breakdown that round-trips — selling the
  break here gets faked out; a break alone is not operating-level destruction.

Indicator-only false positive (high RSI + volume, no structure):

- 600717 around 2023-04-18 (box ~3.76–4.43): high RSI and volume expansion, but the move
  failed. RSI/volume alone is not a buy point (Rule 6 / Rule 11).
- 601222 around 2022-05-19 (box ~5.29–7.09): same — an indicator spike with no same-level
  structure context.

Lesson: each of these looks tradeable but fails. The gates (structure → pullback →
lower-level trigger) exist precisely to reject breakout-chasing and indicator-only entries.

## Review Checklist

For any signal:

- What is the operating level?
- What is the latest valid center?
- Is price inside, above, or below the center?
- Which exact buy/sell class is claimed?
- Which two same-level movements are compared for divergence?
- What lower-level trigger exists?
- What invalidates the signal?
- Do volume/turnover/money flow confirm, caution, or veto?
- Is the action probe, confirmed, hold, reduce, exit, or wait?

## Backtest Sanity Checks

Before trusting a rule:

- Does A bucket outperform C bucket?
- Does it work on more than one stock and one industry?
- Does it work on both 20-day and 60-day horizons, or is it horizon-specific?
- Does adding a factor improve separation or merely move more signals into A?
- Does sell-side performance decay after 20 days?
- Are results dominated by a few outliers?
- Are transaction costs and execution constraints considered?
- Is the measured buy-side excess actually above realistic round-trip costs, or is the
  "edge" just a few percent that costs eat? (Large-sample first-buy excess ≈ +2% / 20d.)
- Are you framing Chanlun as alpha (stock picking) when the evidence says its dependable
  use is risk control — exit / de-risk timing? See `references/empirical-evidence.md`.

## Example Prompts For This Skill

- "用缠论分析安克创新当前日线结构，明确级别、最新中枢、买卖点和失效条件。"
- "把这个K线截图按缠论拆成分型、笔、线段、中枢和三类买卖点。"
- "把一买/二买/三买做成可回测代理，并标注严格定义损失。"
- "用TuShare量能、换手率和资金流增强二买评分，先做10只股票消融测试。"
- "复盘某次失败买点，判断是结构错、级别错、触发早，还是过滤器被忽略。"
