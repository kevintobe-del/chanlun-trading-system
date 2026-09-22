import {ChevronLeft, ChevronRight, FolderPlus, History, Plus, Star, Trash2} from "lucide-react";
import {useEffect, useState} from "react";
import type {WatchlistConfig, WatchlistItem} from "../types";

interface Props {
  collapsed: boolean;
  current?: WatchlistItem;
  refreshToken: number;
  onToggle: () => void;
  onSelect: (symbol: string) => void;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const contentType = response.headers.get("content-type") ?? "";
  if (!response.ok) {
    const body = contentType.includes("json") ? await response.json() : await response.text();
    const detail = typeof body === "object" && body && "detail" in body ? body.detail : body;
    throw new Error(typeof detail === "string" ? detail : "股票池操作失败");
  }
  return response.json() as Promise<T>;
}

export function WatchlistPanel({collapsed, current, refreshToken, onToggle, onSelect}: Props) {
  const [config, setConfig] = useState<WatchlistConfig | null>(null);
  const [poolName, setPoolName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    request<WatchlistConfig>("/api/watchlists").then(setConfig).catch((reason) => setError(reason.message));
  }, [refreshToken]);

  if (collapsed) {
    return (
      <aside className="watchlist-panel is-collapsed" aria-label="股票池">
        <button className="watchlist-expand" type="button" title="展开股票池" onClick={onToggle}><Star size={18} /><ChevronRight size={14} /></button>
      </aside>
    );
  }

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!poolName.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setConfig(await request<WatchlistConfig>("/api/watchlists", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: poolName}),
      }));
      setPoolName("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "创建股票池失败");
    } finally {
      setBusy(false);
    }
  };

  const addCurrent = async (poolId: string) => {
    if (!current) return;
    setBusy(true);
    setError(null);
    try {
      setConfig(await request<WatchlistConfig>(`/api/watchlists/${poolId}/items`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(current),
      }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "添加自选失败");
    } finally {
      setBusy(false);
    }
  };

  const removeItem = async (poolId: string, symbol: string) => {
    setBusy(true);
    setError(null);
    try {
      setConfig(await request<WatchlistConfig>(`/api/watchlists/${poolId}/items/${encodeURIComponent(symbol)}`, {method: "DELETE"}));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "移除自选失败");
    } finally {
      setBusy(false);
    }
  };

  const removePool = async (poolId: string, name: string) => {
    if (!window.confirm(`确定删除股票池“${name}”吗？`)) return;
    setBusy(true);
    setError(null);
    try {
      setConfig(await request<WatchlistConfig>(`/api/watchlists/${poolId}`, {method: "DELETE"}));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "删除股票池失败");
    } finally {
      setBusy(false);
    }
  };

  const securityButton = (item: WatchlistItem, trailing?: React.ReactNode) => (
    <div className="security-row" key={item.symbol}>
      <button type="button" onClick={() => onSelect(item.symbol)} title={`加载 ${item.name}`}>
        <strong>{item.name || item.symbol}</strong><span>{item.symbol}</span>
      </button>
      {trailing}
    </div>
  );

  return (
    <aside className="watchlist-panel" aria-label="股票池">
      <header className="watchlist-heading"><div><Star size={16} /><strong>股票池</strong></div><button type="button" aria-label="折叠股票池" onClick={onToggle}><ChevronLeft size={17} /></button></header>
      {error && <div className="watchlist-error">{error}</div>}

      <section className="watchlist-section search-history">
        <div className="watchlist-section-title"><span><History size={13} />搜索历史</span><small>{config?.history.length ?? 0}</small></div>
        <div className="security-list">
          {config?.history.slice(0, 12).map((item) => securityButton(item))}
          {config?.history.length === 0 && <p>成功加载过的股票会出现在这里。</p>}
        </div>
      </section>

      <div className="watchlist-pools">
        {config?.pools.map((pool) => (
          <section className="watchlist-section" key={pool.id}>
            <div className="watchlist-section-title">
              <span>{pool.name}</span>
              <div>
                <button type="button" title="加入当前股票" disabled={busy || !current || pool.items.some((item) => item.symbol === current.symbol)} onClick={() => void addCurrent(pool.id)}><Plus size={13} /></button>
                {!pool.builtin && <button type="button" title="删除股票池" disabled={busy} onClick={() => void removePool(pool.id, pool.name)}><Trash2 size={12} /></button>}
              </div>
            </div>
            <div className="security-list">
              {pool.items.map((item) => securityButton(item, <button className="remove-security" type="button" aria-label={`移除 ${item.name}`} disabled={busy} onClick={() => void removeItem(pool.id, item.symbol)}><Trash2 size={12} /></button>))}
              {pool.items.length === 0 && <p>点击右上角＋加入当前股票。</p>}
            </div>
          </section>
        ))}
      </div>

      <form className="create-watchlist" onSubmit={create}>
        <FolderPlus size={14} />
        <input value={poolName} maxLength={32} onChange={(event) => setPoolName(event.target.value)} placeholder="新建自选池" aria-label="新建自选池名称" />
        <button type="submit" disabled={busy || !poolName.trim()}>创建</button>
      </form>
    </aside>
  );
}
