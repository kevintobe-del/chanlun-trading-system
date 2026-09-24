import {BellRing, Check, Database, KeyRound, Settings2, Trash2, X} from "lucide-react";
import {useEffect, useMemo, useState} from "react";
import type {DataSourceConfig, ReportSettings} from "../types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = "sources" | "analysis" | "automation";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const contentType = response.headers.get("content-type") ?? "";
  if (!response.ok) {
    const body = contentType.includes("json") ? await response.json() : await response.text();
    const detail = typeof body === "object" && body && "detail" in body ? body.detail : body;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

export function DataSourceDialog({isOpen, onClose}: Props) {
  const [tab, setTab] = useState<Tab>("sources");
  const [config, setConfig] = useState<DataSourceConfig | null>(null);
  const [reportSettings, setReportSettings] = useState<ReportSettings | null>(null);
  const [provider, setProvider] = useState("tushare");
  const [name, setName] = useState("Tushare");
  const [apiKey, setApiKey] = useState("");
  const [dailyYears, setDailyYears] = useState(5);
  const [minute30Years, setMinute30Years] = useState(2);
  const [minute5Days, setMinute5Days] = useState(180);
  const [feishuEnabled, setFeishuEnabled] = useState(false);
  const [feishuUrl, setFeishuUrl] = useState("");
  const [feishuSecret, setFeishuSecret] = useState("");
  const [wecomEnabled, setWecomEnabled] = useState(false);
  const [wecomUrl, setWecomUrl] = useState("");
  const [automaticEnabled, setAutomaticEnabled] = useState(true);
  const [defaultSend, setDefaultSend] = useState(false);
  const [premarketTime, setPremarketTime] = useState("08:30");
  const [afterCloseTime, setAfterCloseTime] = useState("18:00");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const active = useMemo(() => config?.sources.find((item) => item.active), [config]);

  const applyReportSettings = (next: ReportSettings) => {
    setReportSettings(next);
    setDailyYears(next.analysis.daily_years);
    setMinute30Years(next.analysis.minute30_years);
    setMinute5Days(next.analysis.minute5_days);
    setFeishuEnabled(next.webhooks.feishu_enabled);
    setWecomEnabled(next.webhooks.wecom_enabled);
    setAutomaticEnabled(next.automation.automatic_enabled);
    setDefaultSend(next.automation.default_send_report);
    setPremarketTime(next.automation.premarket_time);
    setAfterCloseTime(next.automation.after_close_time);
  };

  useEffect(() => {
    if (!isOpen) return;
    setError(null);
    setNotice(null);
    Promise.all([
      request<DataSourceConfig>("/api/data-sources"),
      request<ReportSettings>("/api/report-settings"),
    ]).then(([sourceConfig, settings]) => {
      setConfig(sourceConfig);
      applyReportSettings(settings);
    }).catch((reason) => setError(reason.message));
  }, [isOpen]);

  useEffect(() => {
    const label = config?.providers[provider]?.label;
    if (label) setName(label);
    if (config && !config.providers[provider]?.requires_key) setApiKey("");
  }, [provider, config]);

  if (!isOpen) return null;

  const perform = async (task: () => Promise<void>, fallback: string) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await task();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : fallback);
    } finally {
      setBusy(false);
    }
  };

  const createSource = (event: React.FormEvent) => {
    event.preventDefault();
    void perform(async () => {
      setConfig(await request<DataSourceConfig>("/api/data-sources", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({provider, name, api_key: apiKey}),
      }));
      setApiKey("");
      setNotice("数据源已添加");
    }, "添加数据源失败");
  };

  const activate = (id: string) => void perform(async () => {
    setConfig(await request<DataSourceConfig>(`/api/data-sources/${id}/activate`, {method: "POST"}));
    applyReportSettings(await request<ReportSettings>("/api/report-settings"));
    setNotice("行情与报告已共同切换到新的数据源");
  }, "切换数据源失败");

  const remove = (id: string, sourceName: string) => {
    if (!window.confirm(`确定删除数据源“${sourceName}”吗？`)) return;
    void perform(async () => {
      setConfig(await request<DataSourceConfig>(`/api/data-sources/${id}`, {method: "DELETE"}));
      setNotice("数据源已删除");
    }, "删除数据源失败");
  };

  const saveAnalysis = (event: React.FormEvent) => {
    event.preventDefault();
    void perform(async () => {
      applyReportSettings(await request<ReportSettings>("/api/report-settings/analysis", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({daily_years: dailyYears, minute30_years: minute30Years, minute5_days: minute5Days}),
      }));
      setNotice("多周期报告参数已保存");
    }, "保存报告参数失败");
  };

  const saveNotifications = (event: React.FormEvent) => {
    event.preventDefault();
    void perform(async () => {
      applyReportSettings(await request<ReportSettings>("/api/report-settings/webhooks", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({feishu_enabled: feishuEnabled, feishu_url: feishuUrl || null, feishu_secret: feishuSecret || null, wecom_enabled: wecomEnabled, wecom_url: wecomUrl || null}),
      }));
      setFeishuUrl("");
      setFeishuSecret("");
      setWecomUrl("");
      setNotice("Webhook 配置已保存");
    }, "保存通知配置失败");
  };

  const saveAutomation = (event: React.FormEvent) => {
    event.preventDefault();
    void perform(async () => {
      applyReportSettings(await request<ReportSettings>("/api/report-settings/automation", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({automatic_enabled: automaticEnabled, premarket_time: premarketTime, after_close_time: afterCloseTime, default_send_report: defaultSend}),
      }));
      setNotice("自动报告任务已更新");
    }, "保存自动任务失败");
  };

  const testNotifications = () => {
    if (!window.confirm("将向已启用的 Webhook 发送一条测试消息，继续吗？")) return;
    void perform(async () => {
      const result = await request<{results: Array<{platform: string; ok: boolean; error?: string}>}>("/api/report-settings/webhooks/test", {method: "POST"});
      setNotice(result.results.length ? result.results.map((item) => `${item.platform}: ${item.ok ? "成功" : item.error}`).join("；") : "没有已启用且完成配置的 Webhook");
    }, "Webhook 测试失败");
  };

  return (
    <div className="settings-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <header className="settings-heading">
          <div className="settings-title-icon"><Settings2 size={20} /></div>
          <div><span>WORKBENCH SETTINGS</span><h2 id="settings-title">系统设置</h2></div>
          <button type="button" aria-label="关闭设置" onClick={onClose}><X size={20} /></button>
        </header>
        <nav className="settings-tabs" aria-label="设置分类">
          <button className={tab === "sources" ? "is-active" : ""} onClick={() => setTab("sources")}><Database size={14} />行情数据源</button>
          <button className={tab === "analysis" ? "is-active" : ""} onClick={() => setTab("analysis")}><Settings2 size={14} />报告参数</button>
          <button className={tab === "automation" ? "is-active" : ""} onClick={() => setTab("automation")}><BellRing size={14} />通知与自动化</button>
        </nav>
        {error && <div className="settings-error" role="alert">{error}</div>}
        {notice && <div className="settings-notice" role="status">{notice}</div>}

        {tab === "sources" && <>
          <div className="active-source-summary"><span>行情图与多周期报告共用</span><strong>{active?.name ?? "读取中…"}</strong><small>每次搜索时，两套分析只会调用这一项。</small></div>
          <div className="source-list" aria-label="已配置数据源">
            {config?.sources.map((source) => <article className={source.active ? "source-card is-active" : "source-card"} key={source.id}>
              <div className="source-main"><span className="source-provider">{config.providers[source.provider]?.label ?? source.provider}</span><strong>{source.name}</strong><small>{source.has_api_key ? <><KeyRound size={11} /> {source.api_key_mask}</> : "无需 API 密钥"}</small></div>
              <div className="source-actions">{source.active ? <span className="active-chip"><Check size={12} /> 已生效</span> : <button type="button" disabled={busy} onClick={() => activate(source.id)}>设为生效</button>}{!source.builtin && <button className="delete-source" type="button" aria-label={`删除 ${source.name}`} disabled={busy} onClick={() => remove(source.id, source.name)}><Trash2 size={15} /></button>}</div>
            </article>)}
          </div>
          <form className="source-form" onSubmit={createSource}>
            <div className="form-heading"><strong>添加数据源 API</strong><span>可以保存多个配置，再选择其中一个生效。</span></div>
            <label><span>数据源类型</span><select value={provider} onChange={(event) => setProvider(event.target.value)}>{Object.entries(config?.providers ?? {}).map(([key, value]) => <option key={key} value={key}>{value.label}</option>)}</select></label>
            <label><span>API 名称</span><input value={name} maxLength={64} onChange={(event) => setName(event.target.value)} placeholder="例如：团队 Tushare" required /></label>
            <label><span>API 密钥</span><input type="password" value={apiKey} maxLength={512} onChange={(event) => setApiKey(event.target.value)} placeholder={config?.providers[provider]?.requires_key ? "请输入 API Token" : "此数据源不需要密钥"} required={config?.providers[provider]?.requires_key} disabled={!config?.providers[provider]?.requires_key} autoComplete="new-password" /></label>
            <div className="secret-note"><KeyRound size={13} /><span>密钥只保存在本机；页面不会返回完整密钥。</span></div>
            <button className="add-source" type="submit" disabled={busy || !config}>{busy ? "正在保存…" : "添加数据源"}</button>
          </form>
        </>}

        {tab === "analysis" && <form className="settings-section-form" onSubmit={saveAnalysis}>
          <div className="settings-section-copy"><strong>多周期报告参数</strong><span>搜索 A 股时，报告引擎按这些范围获取日线、30分钟和5分钟行情。</span></div>
          <div className="settings-field-grid">
            <label><span>日线历史（年）</span><input type="number" min={2} max={20} value={dailyYears} onChange={(event) => setDailyYears(Number(event.target.value))} /></label>
            <label><span>30分钟历史（年）</span><input type="number" min={1} max={10} value={minute30Years} onChange={(event) => setMinute30Years(Number(event.target.value))} /></label>
            <label><span>5分钟历史（天）</span><input type="number" min={30} max={3650} value={minute5Days} onChange={(event) => setMinute5Days(Number(event.target.value))} /></label>
          </div>
          <div className="shared-source-note"><Database size={15} /><span>当前共用数据源：<b>{reportSettings?.shared_source.name ?? active?.name ?? "读取中"}</b>。Token 只在“行情数据源”中维护。</span></div>
          <button className="settings-save" type="submit" disabled={busy}>保存报告参数</button>
        </form>}

        {tab === "automation" && <div className="settings-stack">
          <form className="settings-section-form" onSubmit={saveNotifications}>
            <div className="settings-section-copy"><strong>Webhook 通知</strong><span>凭据加密保存在本机。搜索股票只生成报告，不会自动发送。</span></div>
            <div className="webhook-card"><div className="webhook-title"><strong>飞书</strong><span>{reportSettings?.webhooks.feishu_configured ? "已配置" : "未配置"}</span></div><label className="check-field"><input type="checkbox" checked={feishuEnabled} onChange={(event) => setFeishuEnabled(event.target.checked)} />启用飞书通知</label><label><span>机器人 Webhook</span><input type="password" value={feishuUrl} onChange={(event) => setFeishuUrl(event.target.value)} placeholder="留空保留现有配置" /></label><label><span>签名密钥（可选）</span><input type="password" value={feishuSecret} onChange={(event) => setFeishuSecret(event.target.value)} placeholder="留空保留现有配置" /></label></div>
            <div className="webhook-card"><div className="webhook-title"><strong>企业微信</strong><span>{reportSettings?.webhooks.wecom_configured ? "已配置" : "未配置"}</span></div><label className="check-field"><input type="checkbox" checked={wecomEnabled} onChange={(event) => setWecomEnabled(event.target.checked)} />启用企业微信通知</label><label><span>群机器人 Webhook</span><input type="password" value={wecomUrl} onChange={(event) => setWecomUrl(event.target.value)} placeholder="留空保留现有配置" /></label></div>
            <div className="settings-form-actions"><button className="settings-save" type="submit" disabled={busy}>保存通知配置</button><button className="settings-secondary" type="button" disabled={busy} onClick={testNotifications}>发送测试消息</button></div>
          </form>
          <form className="settings-section-form" onSubmit={saveAutomation}>
            <div className="settings-section-copy"><strong>自动报告任务</strong><span>按北京时间分析自选池中的股票；搜索历史不会加入自动任务。</span></div>
            <div className="settings-field-grid two-columns"><label className="check-field"><input type="checkbox" checked={automaticEnabled} onChange={(event) => setAutomaticEnabled(event.target.checked)} />启用交易日自动任务</label><label className="check-field"><input type="checkbox" checked={defaultSend} onChange={(event) => setDefaultSend(event.target.checked)} />生成后发送到已启用 Webhook</label><label><span>盘前分析</span><input type="time" value={premarketTime} onChange={(event) => setPremarketTime(event.target.value)} /></label><label><span>收盘后分析</span><input type="time" value={afterCloseTime} onChange={(event) => setAfterCloseTime(event.target.value)} /></label></div>
            <button className="settings-save" type="submit" disabled={busy}>应用自动任务设置</button>
          </form>
        </div>}
      </section>
    </div>
  );
}
