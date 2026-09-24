import {Badge} from "@astryxdesign/core/Badge";
import {Button} from "@astryxdesign/core/Button";
import {Switch} from "@astryxdesign/core/Switch";
import {TextInput} from "@astryxdesign/core/TextInput";
import {Database, Download, FileJson, FileText, FlaskConical, Layers3, Menu, PanelRightClose, PanelRightOpen, Search, Upload} from "lucide-react";
import {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {ChanlunChart} from "./components/ChanlunChart";
import {DataSourceDialog} from "./components/DataSourceDialog";
import {EvidencePanel} from "./components/EvidencePanel";
import {ReportPanel} from "./components/ReportPanel";
import {WatchlistPanel} from "./components/WatchlistPanel";
import {parseOhlcvCsv} from "./lib/csv";
import {boundedReplayCount} from "./lib/replay";
import type {Analysis, AnalysisBundle, LayerVisibility, MultilevelReport, Timeframe} from "./types";

const TIMEFRAMES: Array<{key: Timeframe; label: string}> = [
  {key: "1d", label: "日线"},
  {key: "60m", label: "60 分"},
  {key: "30m", label: "30 分"},
  {key: "5m", label: "5 分"},
];

const STRUCTURE_LABEL: Record<string, string> = {
  center_oscillation: "中枢震荡",
  trend_up: "中枢上方 / 上行",
  trend_down: "中枢下方 / 下行",
  insufficient_history: "历史不足",
  unknown: "结构未明",
};

const initialLayers: LayerVisibility = {
  fractals: false,
  strokes: true,
  segments: false,
  centers: true,
  divergence: true,
  signals: true,
  volume: true,
  macd: true,
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const contentType = response.headers.get("content-type") ?? "";
  if (!response.ok) {
    const body = contentType.includes("json") ? await response.json() : await response.text();
    const detail = typeof body === "object" && body && "detail" in body ? body.detail : body;
    const message = typeof detail === "object" && detail && "message" in detail && typeof detail.message === "string"
      ? detail.message
      : typeof detail === "string" ? detail : "请求失败，请稍后重试";
    throw new Error(message);
  }
  return (contentType.includes("json") ? response.json() : response.text()) as Promise<T>;
}

function saveBlob(blob: Blob, filename: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

export default function App() {
  const [bundle, setBundle] = useState<AnalysisBundle | null>(null);
  const fullFrames = useRef<AnalysisBundle["frames"]>({});
  const [timeframe, setTimeframe] = useState<Timeframe>("1d");
  const [symbol, setSymbol] = useState("DEMO");
  const [layers, setLayers] = useState(initialLayers);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [useU1, setUseU1] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [dataSourceOpen, setDataSourceOpen] = useState(false);
  const [watchlistCollapsed, setWatchlistCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [rightTab, setRightTab] = useState<"report" | "evidence">("report");
  const [report, setReport] = useState<MultilevelReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [watchlistVersion, setWatchlistVersion] = useState(0);
  const [asOfCount, setAsOfCount] = useState(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const reportRequestId = useRef(0);

  const active = bundle?.frames[timeframe];
  const availableFrames = useMemo(
    () => TIMEFRAMES.filter((item) => Boolean(bundle?.frames[item.key])),
    [bundle],
  );

  const acceptBundle = useCallback((next: AnalysisBundle) => {
    setBundle(next);
    fullFrames.current = next.frames;
    const first = TIMEFRAMES.find((item) => next.frames[item.key])?.key ?? "1d";
    setTimeframe(first);
    setSymbol(next.symbol);
    setAsOfCount(next.frames[first]?.bars.length ?? 0);
    setSelectedId(null);
  }, []);

  useEffect(() => {
    api<AnalysisBundle>("/api/demo")
      .then(acceptBundle)
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [acceptBundle]);

  const generateReport = async (target: AnalysisBundle) => {
    const requestId = ++reportRequestId.current;
    setReportLoading(true);
    setReportError(null);
    setRightTab("report");
    setRightCollapsed(false);
    try {
      const nextReport = await api<MultilevelReport>("/api/reports/analyze", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({symbol: target.symbol, name: target.name ?? target.symbol, session: "manual", notify: false}),
      });
      if (requestId === reportRequestId.current) setReport(nextReport);
    } catch (reason) {
      if (requestId === reportRequestId.current) {
        setReport(null);
        setReportError(reason instanceof Error ? reason.message : "多周期报告生成失败");
      }
    } finally {
      if (requestId === reportRequestId.current) setReportLoading(false);
    }
  };

  const loadQuoteForSymbol = async (requestedSymbol: string) => {
    const clean = requestedSymbol.trim();
    if (!clean) return;
    setSymbol(clean);
    setLoading(true);
    setError(null);
    try {
      const next = await api<AnalysisBundle>(`/api/quote?symbol=${encodeURIComponent(clean)}`);
      acceptBundle(next);
      setWatchlistVersion((value) => value + 1);
      void generateReport(next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "行情加载失败");
    } finally {
      setLoading(false);
    }
  };

  const loadQuote = () => void loadQuoteForSymbol(symbol);

  const importCsv = async (file: File) => {
    reportRequestId.current += 1;
    setReportLoading(false);
    setLoading(true);
    setError(null);
    try {
      const bars = parseOhlcvCsv(await file.text());
      const analysis = await api<Analysis>("/api/analyze", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({symbol: symbol || file.name.replace(/\.csv$/i, ""), timeframe, source: "user_csv", bars}),
      });
      acceptBundle({symbol: analysis.meta.symbol, name: analysis.meta.symbol, source: "user_csv", is_synthetic: false, frames: {[timeframe]: analysis}});
      setReport(null);
      setReportError("CSV 导入只包含单周期数据，未自动生成日线/30分钟/5分钟报告");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "CSV 导入失败");
    } finally {
      setLoading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const changeTimeframe = (next: Timeframe) => {
    setTimeframe(next);
    setAsOfCount(fullFrames.current[next]?.bars.length ?? 0);
    setSelectedId(null);
  };

  const commitAsOf = async (requestedCount = asOfCount) => {
    const full = fullFrames.current[timeframe];
    if (!full) return;
    const targetCount = boundedReplayCount(requestedCount, full.bars.length);
    setAsOfCount(targetCount);
    if (targetCount >= full.bars.length) {
      if (full && bundle) setBundle({...bundle, frames: {...bundle.frames, [timeframe]: full}});
      return;
    }
    try {
      const sliced = await api<Analysis>("/api/analyze", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          symbol: full.meta.symbol,
          timeframe,
          source: `${full.meta.source}:as_of_replay`,
          bars: full.bars.slice(0, targetCount),
        }),
      });
      if (bundle) setBundle({...bundle, frames: {...bundle.frames, [timeframe]: sliced}});
      setSelectedId(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "时点回放失败");
    }
  };

  const exportJson = () => {
    if (!active) return;
    saveBlob(new Blob([JSON.stringify(active, null, 2)], {type: "application/json"}), `${active.meta.symbol}-${timeframe}-chanlun.json`);
  };

  const exportHtml = async () => {
    if (!active) return;
    try {
      const result = await api<string>("/api/export/html", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({analysis: active}),
      });
      saveBlob(new Blob([result], {type: "text/html;charset=utf-8"}), `${active.meta.symbol}-${timeframe}-chanlun.html`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "HTML 导出失败");
    }
  };

  const selectEvidence = useCallback((id: string) => {
    setSelectedId(id);
    setRightTab("evidence");
    setRightCollapsed(false);
    if (window.matchMedia("(max-width: 900px)").matches) setDrawerOpen(true);
  }, []);

  if (!active) {
    return (
      <main className="loading-screen">
        <FlaskConical size={34} />
        <h1>缠论可视研究工作台</h1>
        <p>{loading ? "正在生成本地示例…" : error ?? "没有可用数据"}</p>
      </main>
    );
  }

  const currentCenter = active.layers.centers.find((item) => item.id === active.state.current_center_id);
  const divergence = active.layers.divergences.at(-1);
  const fullCount = fullFrames.current[timeframe]?.bars.length ?? active.bars.length;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><Layers3 size={19} /></div>
          <div><strong>缠论可视研究</strong><span>CHANLUN WORKBENCH</span></div>
        </div>
        <div className="symbol-search">
          <TextInput label="证券代码" isLabelHidden value={symbol} onChange={setSymbol} onEnter={loadQuote} placeholder="600519 / 1A0001 / 科创50" size="lg" width="100%" />
          <Button label="加载行情" variant="primary" size="lg" icon={<Search size={16} />} onClick={loadQuote} isLoading={loading} />
        </div>
        <div className="top-actions">
          <input ref={fileInput} type="file" accept=".csv,text/csv" hidden onChange={(event) => event.target.files?.[0] && importCsv(event.target.files[0])} />
          <Button label="导入 CSV" variant="secondary" icon={<Upload size={16} />} onClick={() => fileInput.current?.click()} />
          <Button label="导出 JSON" variant="ghost" icon={<FileJson size={16} />} onClick={exportJson} />
          <Button label="导出 HTML" variant="ghost" icon={<Download size={16} />} onClick={exportHtml} />
          <Button label="设置" variant="ghost" icon={<Database size={16} />} onClick={() => setDataSourceOpen(true)} />
          <button className="mobile-evidence" aria-label="打开报告与证据" onClick={() => { setRightTab("report"); setDrawerOpen(true); }}><Menu size={20} /></button>
        </div>
      </header>

      {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError(null)}>关闭</button></div>}

      <section className="status-strip" aria-label="当前研究状态">
        <div><span>结构状态</span><strong>{STRUCTURE_LABEL[active.state.structure] ?? active.state.structure}</strong></div>
        <div><span>当前中枢</span><strong>{currentCenter ? `${currentCenter.zd.toFixed(2)} — ${currentCenter.zg.toFixed(2)}` : "未完成"}</strong></div>
        <div><span>背驰</span><strong>{divergence?.decision === "candidate" ? "候选 · 待复核" : divergence ? "未见基线背驰" : "证据不足"}</strong></div>
        <div><span>数据</span><strong>{active.quality.row_count} bars · {active.quality.status.toUpperCase()}</strong></div>
        <div className="governance-state"><span>治理</span><Badge variant="warning" label="DRAFT_REVIEW · NO_ACTION" /></div>
      </section>

      <section className={`workspace ${watchlistCollapsed ? "watchlist-collapsed" : ""} ${rightCollapsed ? "right-collapsed" : ""}`}>
        <WatchlistPanel
          collapsed={watchlistCollapsed}
          current={{symbol: bundle.symbol, name: bundle.name ?? bundle.symbol}}
          refreshToken={watchlistVersion}
          onToggle={() => setWatchlistCollapsed((value) => !value)}
          onSelect={(nextSymbol) => void loadQuoteForSymbol(nextSymbol)}
        />
        <div className="chart-column">
          <div className="chart-toolbar">
            <div className="timeframe-tabs" role="tablist" aria-label="周期">
              {TIMEFRAMES.map((item) => (
                <button key={item.key} role="tab" disabled={!bundle.frames[item.key]} aria-selected={timeframe === item.key} onClick={() => changeTimeframe(item.key)}>
                  {item.label}
                </button>
              ))}
            </div>
            <div className="source-meta">
              <span>{bundle.is_synthetic ? "内置合成示例" : active.meta.source}</span>
              <i className={`quality-dot ${active.quality.status}`} />
              <span>as of {active.meta.as_of.slice(0, 16)}</span>
            </div>
          </div>

          <div className="layer-row" aria-label="图层控制">
            {(
              [
                ["fractals", "分型"], ["strokes", "笔"], ["segments", "线段 β"], ["centers", "中枢"],
                ["divergence", "背驰"], ["signals", "买卖点候选"], ["volume", "成交量"], ["macd", "MACD"],
              ] as Array<[keyof LayerVisibility, string]>
            ).map(([key, label]) => (
              <button key={key} className={layers[key] ? "is-active" : ""} onClick={() => setLayers({...layers, [key]: !layers[key]})} aria-pressed={layers[key]}>{label}</button>
            ))}
            <div className="u1-switch"><Switch label="U1 力度对照" value={useU1} onChange={setUseU1} size="sm" /></div>
          </div>

          <div className="chart-frame">
            <div className="chart-caption">
              <div className="instrument-caption"><strong>{bundle.name ?? active.meta.symbol}</strong><b>{active.meta.symbol}</b><span>{TIMEFRAMES.find((item) => item.key === timeframe)?.label} · {active.meta.definition_mode}</span></div>
              <div className="legend"><span className="up">上涨</span><span className="down">下跌</span><span className="stroke">笔</span><span className="center">中枢</span></div>
            </div>
            <ChanlunChart analysis={active} layers={layers} selectedId={selectedId} onSelect={selectEvidence} />
          </div>

          <div className="replay-bar">
            <div><strong>时点回放</strong><span>拖到历史时点后松开，结构将重新计算，不读取未来确认。</span></div>
            <div className="replay-control">
              <input
                aria-label="时点回放"
                type="range"
                min={Math.min(20, fullCount)}
                max={fullCount}
                value={asOfCount || fullCount}
                onChange={(event) => setAsOfCount(Number(event.target.value))}
                onPointerUp={() => void commitAsOf()}
                onKeyUp={() => void commitAsOf()}
              />
              <div className="replay-actions">
                <button type="button" onClick={() => void commitAsOf(asOfCount - 20)} disabled={asOfCount <= Math.min(20, fullCount)}>回退 20 根</button>
                <button type="button" onClick={() => void commitAsOf(fullCount)} disabled={asOfCount >= fullCount}>恢复全部</button>
              </div>
            </div>
            <output>{asOfCount || fullCount} / {fullCount}</output>
          </div>

          {active.quality.warnings.length > 0 && (
            <div className="quality-warnings"><strong>数据提示</strong>{active.quality.warnings.map((warning) => <span key={warning}>{warning}</span>)}</div>
          )}
        </div>

        <aside className={`research-rail ${drawerOpen ? "is-open" : ""} ${rightCollapsed ? "is-collapsed" : ""}`} aria-label="报告与证据">
          {rightCollapsed ? (
            <button className="research-expand" type="button" onClick={() => setRightCollapsed(false)}><PanelRightOpen size={17} /><span>报告</span></button>
          ) : <>
            <div className="research-tabs">
              <button className={rightTab === "report" ? "is-active" : ""} onClick={() => setRightTab("report")}><FileText size={14} />缠论报告</button>
              <button className={rightTab === "evidence" ? "is-active" : ""} onClick={() => setRightTab("evidence")}><Layers3 size={14} />结构证据</button>
              <button className="research-collapse" aria-label="折叠右侧面板" onClick={() => { setRightCollapsed(true); setDrawerOpen(false); }}><PanelRightClose size={17} /></button>
            </div>
            {rightTab === "report" ? (
              <ReportPanel report={report} loading={reportLoading} error={reportError} onRetry={() => bundle && void generateReport(bundle)} />
            ) : (
              <EvidencePanel analysis={active} selectedId={selectedId} useU1={useU1} isOpen onSelect={selectEvidence} onClose={() => setDrawerOpen(false)} />
            )}
          </>}
        </aside>
      </section>
      {drawerOpen && <button className="drawer-scrim" aria-label="关闭证据抽屉" onClick={() => setDrawerOpen(false)} />}
      <DataSourceDialog isOpen={dataSourceOpen} onClose={() => setDataSourceOpen(false)} />
      <footer><span>{active.meta.schema_version} · engine {active.meta.engine_version}</span><span>本地运行 · 无遥测 · 不连接券商</span></footer>
    </main>
  );
}
