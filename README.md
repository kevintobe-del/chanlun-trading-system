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

### 1. 直接运行可视工作台

安装 [`uv`](https://docs.astral.sh/uv/getting-started/installation/) 后，可以从固定版本一次性运行，不污染现有 Python 环境：

```bash
uvx --from "git+https://github.com/kevintobe-del/chanlun-trading-system.git@v0.1.1" chanlun-visual
```

需要长期使用：

```bash
uv tool install "git+https://github.com/kevintobe-del/chanlun-trading-system.git@v0.1.1"
chanlun-visual doctor --json
chanlun-visual
```

上述远端命令以 GitHub `v0.1.1` tag 已发布为前提；未发布前请使用下方“本地开发安装”。公开行情是可选便利入口，CSV 与内置示例不依赖它：

```bash
uv tool install --with yfinance --with tushare --with akshare "git+https://github.com/kevintobe-del/chanlun-trading-system.git@v0.1.1"
```

### 2. 安装 AI Skill

Codex/OpenAI 用户可以让 `$skill-installer` 从本 GitHub 仓库安装 `chanlun-trading-system`，或从 GitHub Release 下载 `chanlun-trading-system-skill.zip` 后执行：

```bash
mkdir -p "$HOME/.agents/skills"
unzip chanlun-trading-system-skill.zip -d "$HOME/.agents/skills"
```

腾讯 SkillHub 使用同一 Release 中的 `chanlun-trading-system-skillhub.zip`；它只比通用包多出 SkillHub 要求的分发元数据，规则正文和脚本保持一致。

Skill 与可视工作台运行时是两个安装单元：只装 Skill 可以进行规则化文字研究；要打开交互图表，还需要安装上面的 `chanlun-visual`。Skill 会先运行 `doctor`，缺失时只提示安装，不会静默修改环境。

**Claude Code** 可以把同一个发布版 Skill 解压到 `~/.claude/skills/`。本地克隆安装方式：

```bash
git clone https://github.com/kevintobe-del/chanlun-trading-system.git
cp -r chanlun-trading-system ~/.claude/skills/
# 新开一个会话，问它"用缠论帮我看下 XXXX 的日线走势"即可自动触发
```

其他 Agent / 本地模型也可以把 `SKILL.md` 作为系统提示加载，需要细节时再按表读取 `references/*.md`。

**任意 AI / 完全不会写代码**：打开 **`缠论Skill_完整版_通用AI.md`**（中文通用版，最详细、含调度协议+实战示例，适配 DeepSeek/豆包/Kimi/元宝/千问/ChatGPT/Claude 等任意 AI），整段复制进对话框，开头加一句：
> "按这套规则帮我分析【标的】的走势，先定级别、先认结构、先写失效点，不要直接给我买卖建议。"

## 可视研究工作台（v0.1）

仓库同时提供一个**本地优先、可交互、可分享**的研究工作台。它把 OHLCV 数据标成分型、笔、线段代理、中枢、背驰证据与买卖点候选，并明确展示每个对象的确认时间、可用时间、定义模式和近似损失。

![缠论可视工作台桌面概念稿](./docs/design/chanlun-workbench-desktop-concept.png)

> 上图为使用合成数据的交互设计概念稿，不是实时行情截图；[查看移动端概念稿](./docs/design/chanlun-workbench-mobile-concept.png)。

### 3. 本地开发安装

```bash
git clone https://github.com/kevintobe-del/chanlun-trading-system.git
cd chanlun-trading-system
uv sync --all-extras
uv run chanlun-visual doctor --json
uv run chanlun-visual
```

浏览器打开 `http://127.0.0.1:8791`。内置合成示例无需网络；导入 CSV 时至少需要 `date,open,high,low,close`，`volume` 可选。公开行情入口接受 `300684`、`600519`、`399001`（深证成指）、`1A0001`/`上证指数`、`1B0688`/`科创50`、`0700`、`AAPL` 等常见写法并自动补齐市场后缀。要使用这个便利入口，再安装：

工作台的公开行情入口是非权威可选适配器；失败时请回到 CSV。它不创建账户、不上传数据、不接券商、不下单。当前线段/中枢/背驰属于 `research_proxy`，不能称为严格原著等价实现。详细说明见 [`references/visual-workbench.md`](./references/visual-workbench.md)。

顶部导航的“设置”支持保存多个 Yahoo Finance、Tushare 或 AKShare 配置，并从中选择唯一一个生效项。K 线与多周期报告共用该数据源；Tushare Token 只保存在本机 `~/.config/chanlun-visual/data-sources.json`（文件权限为当前用户可读写），接口只向页面返回掩码。Tushare 与 AKShare 当前适配 A 股六位代码，分钟行情的可用范围与权限仍由对应服务决定。

Yahoo Finance 可能按网络出口临时限流或拒绝访问。工作台会对短期限流有限重试、缓存成功结果，并在确认受限后停止后续周期请求；若提示当前网络不可用，请切换 AKShare/Tushare，而不要连续点击重试。

行情成功加载后，图表标题会显示证券简称和代码，并自动记入左侧“股票池”的搜索历史。股票池可以折叠；用户可创建多个本地自选池、把当前证券加入任意自选池，或从历史和自选池中再次加载。数据保存在 `~/.config/chanlun-visual/watchlists.json`，不会上传。

搜索 A 股后，页面右侧会异步生成日线、30 分钟线和 5 分钟线的确定性缠论分析报告；K 线会先显示，不必等待报告计算完成。右栏可折叠，并可在“缠论报告”和“结构证据”之间切换。报告严格保留引擎的结构状态、机械判定和失效条件，仅供研究，不会自动下单；搜索触发的报告也不会自动发送通知。

“设置”里的“报告参数”和“通知与自动化”来自子项目配置能力，可调整三周期回看范围、配置加密保存的飞书/企业微信 Webhook，并按自选池在交易日定时生成报告。报告历史、行情缓存和加密配置保存在 `~/.config/chanlun-visual/reports/chanlun-reports.sqlite3`；容器部署时统一持久化到 `/config/reports/`。

## 目录结构

```
chanlun-trading-system/
├── SKILL.md            # 主文件：规则 + 自检门 + 工作流 + 输出模板
├── agents/openai.yaml  # OpenAI/Codex Skill 展示元数据
├── scripts/            # Skill 侧只读检查与启动助手
├── src/chanlun_visual/ # 本地计算/API、多周期报告编排 + 已构建前端
├── src/chanlun_local/  # 子项目确定性报告引擎（含本地化 chan.py）
├── ui/                 # React/Astryx/ECharts 开发源码
├── tests/              # 数据门、无未来函数、API 测试
├── tools/              # Skill 归档与版本发布检查
├── .github/workflows/  # CI 与人工复核后的 Release 草稿
└── references/         # 按需加载的细则（13 篇）
    ├── concepts.md             # 定义 / 源头层级 / 术语 / 状态分类
    ├── strict-original-system.md  # 原文自检门 / 降级矩阵
    ├── structure-engine.md     # 包含 / 分型 / 笔 / 线段 / 中枢
    ├── buy-sell-playbooks.md   # 一二三类买卖点流程
    ├── multi-level-recursion.md   # 区间套 / 小转大 / 同级别分解
    ├── filters.md              # MACD / RSI / 均线 / 筹码 / 板块
    ├── volume-turnover-money.md   # 量 / 换手 / 资金流匹配
    ├── invalidation-risk.md    # 失效模式 / 止损 / 仓位
    ├── backtest-proxies.md     # 缠论→可复现代理规则
    ├── empirical-evidence.md   # 大样本回测硬数字 / 风控非选股
    ├── visual-reading.md       # 读图（截图 / 书图）
    ├── visual-workbench.md     # 可视工作台安装 / CSV / 图层 / 数据契约
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

## 群晖 NAS 部署

仓库提供了 `Dockerfile` 与 `docker-compose.synology.yml`。完整的持久化目录、反向代理、安全边界、更新和排错步骤见 [`docs/nas-deployment.md`](./docs/nas-deployment.md)。应用没有内置登录鉴权，不要把服务端口直接暴露到公网。

## 贡献

欢迎提交：更准的概念校订、新的假阳性 case、回测代理规则、读图示例。提 PR 时请保持"研究口径、不荐股"的底线。
