import {AlertTriangle, CheckCircle2, Clock3, RefreshCw} from "lucide-react";
import Markdown from "react-markdown";
import type {MultilevelReport} from "../types";

interface Props {
  report: MultilevelReport | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

const ACTION_LABELS: Record<string, string> = {
  buy_candidate: "买点候选",
  sell_risk: "卖点风险",
  observe: "等待观察",
};

const LEVEL_LABELS: Record<string, string> = {
  "1w": "周线",
  "1d": "日线",
  "30m": "30分钟",
  "5m": "5分钟",
};

export function ReportPanel({report, loading, error, onRetry}: Props) {
  if (loading) {
    return (
      <div className="report-state">
        <RefreshCw className="spin" size={22} />
        <strong>正在生成多周期报告</strong>
        <span>依次拉取日线、30分钟和5分钟行情，并运行本地确定性引擎。</span>
      </div>
    );
  }
  if (error) {
    return (
      <div className="report-state is-error">
        <AlertTriangle size={22} />
        <strong>报告生成失败</strong>
        <span>{error}</span>
        <button type="button" onClick={onRetry}>重新生成</button>
      </div>
    );
  }
  if (!report) {
    return (
      <div className="report-state">
        <Clock3 size={22} />
        <strong>等待搜索股票</strong>
        <span>加载一只 A 股后，这里会自动生成日线、30分钟与5分钟缠论报告。</span>
      </div>
    );
  }

  const verdict = report.result.verdict;
  return (
    <div className="report-content">
      <section className={`report-verdict action-${report.status}`}>
        <div><span>机械判定</span><strong>{ACTION_LABELS[report.status] ?? report.status}</strong></div>
        <p>{verdict.verdict}</p>
        <small>execution_allowed=false · 仅用于结构研究</small>
      </section>

      <section className="report-levels" aria-label="多周期结构完整度">
        {(["1d", "30m", "5m"] as const).map((key) => {
          const level = report.result.levels[key];
          return (
            <div key={key} className={level.status === "ok" ? "is-ok" : "is-warn"}>
              <span>{LEVEL_LABELS[key]}</span>
              <strong>{level.status === "ok" ? `${level.bars} 根` : "数据不足"}</strong>
              {level.status === "ok" ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
            </div>
          );
        })}
      </section>

      <section className="report-gates">
        <div><span>30分钟确认</span><b>{verdict.confirmation_30m ? "有" : "缺失"}</b></div>
        <div><span>5分钟触发</span><b>{verdict.trigger_5m ? "有" : "缺失"}</b></div>
      </section>

      <section className="report-section">
        <h3>失效条件</h3>
        {verdict.invalidations.length ? verdict.invalidations.map((item, index) => (
          <p key={`${item.invalidation.rule}-${index}`}>{item.invalidation.rule}：<b>{item.invalidation.px}</b></p>
        )) : <p>当前没有新鲜日线信号，不生成虚假的信号止损价。</p>}
      </section>

      <section className="report-section">
        <h3>下一观察点</h3>
        {verdict.next_observation.map((item) => <p key={item}>{item}</p>)}
      </section>

      <details className="report-raw">
        <summary>
          <span>查看完整报告</span>
          <small>Markdown 排版</small>
        </summary>
        <article className="report-markdown">
          <Markdown>{report.report_text}</Markdown>
        </article>
      </details>

      <div className="report-meta">
        <span>{report.source.name}</span>
        <span>截至 {report.result.meta.asof ?? "暂无"}</span>
        <span>生成于 {report.created_at}</span>
      </div>
    </div>
  );
}
