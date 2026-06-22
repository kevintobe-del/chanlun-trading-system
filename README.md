# chanlun-trading-system · 缠论分析 Skill

把**缠中说禅（缠论）**的技术分析体系，做成一个可以直接装进 AI Agent 的 **Skill**——让 AI 帮你看 A 股 / 港股 / ETF / 指数 / 期货的走势时，**先定级别、先认结构、先写失效点**，而不是张口就喊"必涨买点"。

> ⚠️ **仅供技术研究与学习，不构成投资建议，不给买卖指令，不承诺收益。** 缠论存在主观性与失效风险，盈亏自负。

## 这个 Skill 到底做什么

| 不是 | 是 |
|---|---|
| ❌ 一个"必涨信号"机器 | ✅ 一套**强制纪律**的分析流程 |
| ❌ 指标金叉就喊买 | ✅ 走完 包含→分型→笔→线段→中枢→背驰→买卖点 才下结论 |
| ❌ 把突破当三买 | ✅ 中枢离开+回拉+不回 全部点名才认三买 |
| ❌ 假装看得懂任何图 | ✅ 数据不够就**降级**为"观察"，并说明近似损失 |

核心是一道**自检门（Audit Gate）**：级别门 → 结构门 → 类型门 → 比较门 → 买卖点门 → 触发门 → 风险门 → 降级门。任何一步缺失，输出自动从"确认买入"退回"观察"。

## 安装

**Claude Code**：
```bash
git clone https://github.com/noahnan-max/chanlun-trading-system.git
cp -r chanlun-trading-system ~/.claude/skills/
# 新开一个会话，问它"用缠论帮我看下 XXXX 的日线走势"即可自动触发
```

**其他 Agent / Codex / 本地模型**：把 `SKILL.md` 作为系统提示加载，需要细节时再按表喂入 `references/*.md`。

**完全不会写代码**：直接把 `SKILL.md` 全文复制进你的 AI 对话框，开头加一句：
> "按这套规则帮我分析【标的】的走势，先定级别、先认结构、先写失效点，不要直接给我买卖建议。"

## 目录结构

```
chanlun-trading-system/
├── SKILL.md            # 主文件：规则 + 自检门 + 工作流 + 输出模板
└── references/         # 按需加载的细则（11 篇）
    ├── concepts.md             # 定义 / 源头层级 / 术语 / 状态分类
    ├── strict-original-system.md  # 原文自检门 / 降级矩阵
    ├── structure-engine.md     # 包含 / 分型 / 笔 / 线段 / 中枢
    ├── buy-sell-playbooks.md   # 一二三类买卖点流程
    ├── multi-level-recursion.md   # 区间套 / 小转大 / 同级别分解
    ├── filters.md              # MACD / RSI / 均线 / 筹码 / 板块
    ├── volume-turnover-money.md   # 量 / 换手 / 资金流匹配
    ├── invalidation-risk.md    # 失效模式 / 止损 / 仓位
    ├── backtest-proxies.md     # 缠论→可复现代理规则
    ├── visual-reading.md       # 读图（截图 / 书图）
    └── self-test-cases.md      # 常见假阳性 / 复核清单
```

## 设计原则

1. **结构优先于指标**——指标只调信心和仓位，永远不定义买卖点。
2. **诚实优先于好看**——严格原文定义 vs 可测代理，分层标注，绝不混为一谈。
3. **失效点优先于收益**——先写"什么情况下我错了"，再谈赚多少。
4. **宁等勿赌**——结构不清就输出"观察"。

## 来源与许可

- 缠论技术分析体系原创归属 **缠中说禅**；本 Skill 是对其公开理论的操作化整理与研究性解读，用于学习交流。
- Skill 文件（SKILL.md 及 references）以 **MIT 许可**开源，欢迎 fork / 改进 / 提 issue。
- 二次分享请保留来源致谢与免责声明。

## 贡献

欢迎提交：更准的概念校订、新的假阳性 case、回测代理规则、读图示例。提 PR 时请保持"研究口径、不荐股"的底线。
