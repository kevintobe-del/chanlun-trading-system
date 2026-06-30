[中文版 / Chinese](./README.md)

# chanlun-trading-system · Chanlun Analysis Skill

> ⚠️ **Disclaimer: for technical research & study only; NOT investment advice; no buy/sell signals; no return guarantee.** Chanlun has subjectivity and failure risk. You are responsible for your own gains and losses.

This project turns the technical analysis system of **Chanlun (缠中说禅 / Chan theory)** into a **Skill** that can be loaded directly into an AI Agent. When an AI helps you review the trend of A-shares, Hong Kong stocks, ETFs, indices, or futures, this Skill forces it to **define the level first, identify the structure first, and write the invalidation point first**, instead of blurting out a "must-rise buy point."

## What This Skill Actually Does

| It is not | It is |
|---|---|
| ❌ A "must-rise signal" machine | ✅ A disciplined analysis workflow |
| ❌ Calling buy whenever an indicator crosses upward | ✅ Requiring the full chain of inclusion → fractal (fenxing / 分型) → stroke/pen (bi / 笔) → segment (xianduan / 线段) → center (zhongshu / 中枢) → divergence (beichi / 背驰) → buy/sell point before drawing a conclusion |
| ❌ Treating every breakout as a 3rd-class buy point | ✅ Recognizing a 3rd-class buy only after the center departure, pullback, and non-return are all explicitly named |
| ❌ Pretending to understand every chart | ✅ Downgrading to "observe" when data is insufficient, while explaining the approximation loss |

The core is an **Audit Gate**: level gate → structure gate → type gate → comparison gate → buy/sell-point gate → trigger gate → risk gate → downgrade gate. If any step is missing, the output is automatically downgraded from "confirmed buy" to "observe."

Chanlun's three classes of trade locations are referred to as **1st/2nd/3rd-class buy/sell points (三类买卖点)**. They are research labels for structural analysis only, not buy/sell signals or investment instructions.

## Installation

**Claude Code**:

```bash
git clone https://github.com/noahnan-max/chanlun-trading-system.git
cp -r chanlun-trading-system ~/.claude/skills/
# Start a new session and ask:
# "Use Chanlun to help me review the daily trend of XXXX"
# The Skill should be triggered automatically.
```

**Other Agents / Codex / local models**: load `SKILL.md` as the system prompt. When details are needed, feed in the relevant `references/*.md` files according to the table.

**Any AI / no coding required**: open **`缠论Skill_完整版_通用AI.md`**. It is the most detailed Chinese general-purpose version, including the scheduling protocol and practical examples, and is suitable for DeepSeek, Doubao, Kimi, Yuanbao, Qwen, ChatGPT, Claude, and other AIs. Copy the whole file into the chat box and start with:

> "Analyze the trend of [symbol] according to this rule set. Define the level first, identify the structure first, write the invalidation point first, and do not give me direct buy/sell advice."

## Directory Structure

```text
chanlun-trading-system/
├── SKILL.md            # Main file: rules + audit gate + workflow + output template
└── references/         # Details loaded on demand (12 articles)
    ├── concepts.md             # Definitions / source hierarchy / terminology / state taxonomy
    ├── strict-original-system.md  # Original-text audit gate / downgrade matrix
    ├── structure-engine.md     # Inclusion / fractal / stroke / segment / center
    ├── buy-sell-playbooks.md   # Workflows for 1st/2nd/3rd-class buy/sell points
    ├── multi-level-recursion.md   # Nested levels / small-turns-large / same-level decomposition
    ├── filters.md              # MACD / RSI / moving averages / chips / sector
    ├── volume-turnover-money.md   # Volume / turnover / money-flow matching
    ├── invalidation-risk.md    # Failure modes / stop loss / position sizing
    ├── backtest-proxies.md     # Chanlun → reproducible proxy rules
    ├── empirical-evidence.md   # Large-sample backtest hard numbers / risk-control, not stock-picking
    ├── visual-reading.md       # Chart reading (screenshots / book figures)
    └── self-test-cases.md      # Common false positives / review checklist
```

## Design Principles

1. **Structure before indicators**: indicators only adjust confidence and position sizing; they never define buy/sell points.
2. **Honesty before polish**: strict original definitions and testable proxies must be labeled separately and never mixed together.
3. **Invalidation before return**: first write "under what conditions I am wrong," then discuss possible profit.
4. **Wait rather than gamble**: when the structure is unclear, output "observe."

## Sources and License

- The Chanlun technical analysis system was originally created by **Chan Zhong Shuo Chan (缠中说禅)**. This Skill is an operational organization and research commentary based on that publicly available theory, intended for study and exchange.
- The Skill files (`SKILL.md` and `references`) are open-sourced under the **MIT License**. Forks, improvements, and issues are welcome.
- For redistribution or derivative sharing, please keep the source acknowledgment and disclaimer.

## Contributing

Contributions are welcome: more accurate concept corrections, new false-positive cases, backtest proxy rules, and chart-reading examples. When submitting a PR, keep the baseline of "research framing, no stock tips."
