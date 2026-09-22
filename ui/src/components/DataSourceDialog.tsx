import {Check, Database, KeyRound, Trash2, X} from "lucide-react";
import {useEffect, useMemo, useState} from "react";
import type {DataSourceConfig} from "../types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

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
  const [config, setConfig] = useState<DataSourceConfig | null>(null);
  const [provider, setProvider] = useState("tushare");
  const [name, setName] = useState("Tushare");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = useMemo(() => config?.sources.find((item) => item.active), [config]);

  useEffect(() => {
    if (!isOpen) return;
    setError(null);
    request<DataSourceConfig>("/api/data-sources").then(setConfig).catch((reason) => setError(reason.message));
  }, [isOpen]);

  useEffect(() => {
    const label = config?.providers[provider]?.label;
    if (label) setName(label);
    if (config && !config.providers[provider]?.requires_key) setApiKey("");
  }, [provider, config]);

  if (!isOpen) return null;

  const createSource = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const next = await request<DataSourceConfig>("/api/data-sources", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({provider, name, api_key: apiKey}),
      });
      setConfig(next);
      setApiKey("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "添加数据源失败");
    } finally {
      setBusy(false);
    }
  };

  const activate = async (id: string) => {
    setBusy(true);
    setError(null);
    try {
      setConfig(await request<DataSourceConfig>(`/api/data-sources/${id}/activate`, {method: "POST"}));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "切换数据源失败");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string, sourceName: string) => {
    if (!window.confirm(`确定删除数据源“${sourceName}”吗？`)) return;
    setBusy(true);
    setError(null);
    try {
      setConfig(await request<DataSourceConfig>(`/api/data-sources/${id}`, {method: "DELETE"}));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "删除数据源失败");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="settings-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="data-source-title">
        <header className="settings-heading">
          <div className="settings-title-icon"><Database size={20} /></div>
          <div><span>MARKET DATA</span><h2 id="data-source-title">配置数据源</h2></div>
          <button type="button" aria-label="关闭数据源配置" onClick={onClose}><X size={20} /></button>
        </header>

        <div className="active-source-summary">
          <span>当前行情数据源</span>
          <strong>{active?.name ?? "读取中…"}</strong>
          <small>每次加载行情时，系统只会调用这一项。</small>
        </div>

        {error && <div className="settings-error" role="alert">{error}</div>}

        <div className="source-list" aria-label="已配置数据源">
          {config?.sources.map((source) => (
            <article className={source.active ? "source-card is-active" : "source-card"} key={source.id}>
              <div className="source-main">
                <span className="source-provider">{config.providers[source.provider]?.label ?? source.provider}</span>
                <strong>{source.name}</strong>
                <small>{source.has_api_key ? <><KeyRound size={11} /> {source.api_key_mask}</> : "无需 API 密钥"}</small>
              </div>
              <div className="source-actions">
                {source.active ? <span className="active-chip"><Check size={12} /> 已生效</span> : <button type="button" disabled={busy} onClick={() => void activate(source.id)}>设为生效</button>}
                {!source.builtin && <button className="delete-source" type="button" aria-label={`删除 ${source.name}`} disabled={busy} onClick={() => void remove(source.id, source.name)}><Trash2 size={15} /></button>}
              </div>
            </article>
          ))}
        </div>

        <form className="source-form" onSubmit={createSource}>
          <div className="form-heading"><strong>添加数据源 API</strong><span>可以保存多个配置，再选择其中一个生效。</span></div>
          <label><span>数据源类型</span><select value={provider} onChange={(event) => setProvider(event.target.value)}>
            {Object.entries(config?.providers ?? {}).map(([key, value]) => <option key={key} value={key}>{value.label}</option>)}
          </select></label>
          <label><span>API 名称</span><input value={name} maxLength={64} onChange={(event) => setName(event.target.value)} placeholder="例如：团队 Tushare" required /></label>
          <label><span>API 密钥</span><input type="password" value={apiKey} maxLength={512} onChange={(event) => setApiKey(event.target.value)} placeholder={config?.providers[provider]?.requires_key ? "请输入 API Token" : "此数据源不需要密钥"} required={config?.providers[provider]?.requires_key} disabled={!config?.providers[provider]?.requires_key} autoComplete="new-password" /></label>
          <div className="secret-note"><KeyRound size={13} /><span>密钥保存在本机配置文件中，页面不会读取或显示完整密钥。</span></div>
          <button className="add-source" type="submit" disabled={busy || !config}>{busy ? "正在保存…" : "添加数据源"}</button>
        </form>
      </section>
    </div>
  );
}
