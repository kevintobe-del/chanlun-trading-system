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

## Example Prompts For This Skill

- "用缠论分析安克创新当前日线结构，明确级别、最新中枢、买卖点和失效条件。"
- "把这个K线截图按缠论拆成分型、笔、线段、中枢和三类买卖点。"
- "把一买/二买/三买做成可回测代理，并标注严格定义损失。"
- "用TuShare量能、换手率和资金流增强二买评分，先做10只股票消融测试。"
- "复盘某次失败买点，判断是结构错、级别错、触发早，还是过滤器被忽略。"
