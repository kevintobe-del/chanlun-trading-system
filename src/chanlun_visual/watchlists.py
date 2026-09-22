"""Local search history and user-defined watchlists."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4


_LOCK = threading.RLock()


def _path() -> Path:
    override = os.environ.get("CHANLUN_WATCHLIST_CONFIG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / "chanlun-visual" / "watchlists.json"


def _default() -> Dict[str, Any]:
    return {
        "history": [],
        "pools": [{"id": "default", "name": "我的自选", "builtin": True, "items": []}],
    }


def load_watchlists() -> Dict[str, Any]:
    with _LOCK:
        path = _path()
        if not path.exists():
            return _default()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("股票池配置文件无法读取") from exc
        if not isinstance(data.get("history"), list) or not isinstance(data.get("pools"), list):
            raise RuntimeError("股票池配置格式无效")
        return data


def _save(data: Dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".watchlists-", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def record_search(symbol: str, name: str) -> Dict[str, Any]:
    with _LOCK:
        data = load_watchlists()
        entry = {
            "symbol": symbol,
            "name": name or symbol,
            "last_searched_at": datetime.now(timezone.utc).isoformat(),
        }
        data["history"] = [entry] + [item for item in data["history"] if item.get("symbol") != symbol]
        data["history"] = data["history"][:30]
        _save(data)
        return data


def create_pool(name: str) -> Dict[str, Any]:
    clean = name.strip()
    if not clean or len(clean) > 32:
        raise ValueError("股票池名称不能为空且不能超过 32 个字符")
    with _LOCK:
        data = load_watchlists()
        if any(item.get("name") == clean for item in data["pools"]):
            raise ValueError("已存在同名股票池")
        data["pools"].append({"id": uuid4().hex, "name": clean, "builtin": False, "items": []})
        _save(data)
        return data


def delete_pool(pool_id: str) -> Dict[str, Any]:
    with _LOCK:
        data = load_watchlists()
        target = next((item for item in data["pools"] if item.get("id") == pool_id), None)
        if target is None:
            raise KeyError("股票池不存在")
        if target.get("builtin"):
            raise ValueError("默认股票池不能删除")
        data["pools"] = [item for item in data["pools"] if item.get("id") != pool_id]
        _save(data)
        return data


def add_pool_item(pool_id: str, symbol: str, name: str) -> Dict[str, Any]:
    with _LOCK:
        data = load_watchlists()
        pool = next((item for item in data["pools"] if item.get("id") == pool_id), None)
        if pool is None:
            raise KeyError("股票池不存在")
        item = {"symbol": symbol, "name": name or symbol}
        pool["items"] = [item] + [entry for entry in pool.get("items", []) if entry.get("symbol") != symbol]
        _save(data)
        return data


def remove_pool_item(pool_id: str, symbol: str) -> Dict[str, Any]:
    with _LOCK:
        data = load_watchlists()
        pool = next((item for item in data["pools"] if item.get("id") == pool_id), None)
        if pool is None:
            raise KeyError("股票池不存在")
        pool["items"] = [entry for entry in pool.get("items", []) if entry.get("symbol") != symbol]
        _save(data)
        return data
