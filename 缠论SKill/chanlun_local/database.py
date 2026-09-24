from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .models import Bar
from .secrets import SecretStore


DEFAULT_SETTINGS = {
    "provider": "akshare",
    "daily_years": "5",
    "minute30_years": "2",
    "minute5_days": "180",
    "tushare_token": "",
    "custom_base_url": "",
    "custom_api_key": "",
    "feishu_enabled": "0",
    "feishu_url": "",
    "feishu_secret": "",
    "wecom_enabled": "0",
    "wecom_url": "",
    "automatic_enabled": "1",
    "premarket_time": "08:30",
    "after_close_time": "18:00",
    "default_send_report": "0",
}

SECRET_KEYS = {
    "tushare_token",
    "custom_api_key",
    "feishu_url",
    "feishu_secret",
    "wecom_url",
}


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self.secrets = SecretStore(path.parent / ".secret.key")
        self._init_schema()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _init_schema(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            is_secret INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 1,
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bars (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL,
            amount REAL,
            source TEXT NOT NULL,
            available_at TEXT NOT NULL,
            PRIMARY KEY(symbol, timeframe, ts)
        );
        CREATE INDEX IF NOT EXISTS idx_bars_lookup
            ON bars(symbol, timeframe, ts);
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            session TEXT NOT NULL,
            asof TEXT NOT NULL,
            status TEXT NOT NULL,
            report_text TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_reports_created
            ON reports(created_at DESC);
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            session TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT
        );
        """
        with self._lock, self._conn:
            self._conn.executescript(ddl)
            now = datetime.now().isoformat(timespec="seconds")
            for key, value in DEFAULT_SETTINGS.items():
                stored = self.secrets.encrypt(value) if key in SECRET_KEYS and value else value
                self._conn.execute(
                    "INSERT OR IGNORE INTO settings(key,value,is_secret,updated_at) VALUES(?,?,?,?)",
                    (key, stored, int(key in SECRET_KEYS), now),
                )

    def get_settings(self, reveal_secrets: bool = False) -> dict[str, str]:
        with self._lock:
            rows = self._conn.execute("SELECT key,value,is_secret FROM settings").fetchall()
        result: dict[str, str] = {}
        for row in rows:
            value = self.secrets.decrypt(row["value"]) if row["is_secret"] else row["value"]
            if row["is_secret"] and not reveal_secrets:
                result[row["key"]] = "configured" if value else ""
            else:
                result[row["key"]] = value
        return result

    def set_settings(self, values: dict[str, Any]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock, self._conn:
            for key, raw in values.items():
                if raw is None:
                    continue
                value = str(int(raw)) if isinstance(raw, bool) else str(raw).strip()
                secret = key in SECRET_KEYS
                if secret and not value:
                    continue
                stored = self.secrets.encrypt(value) if secret else value
                self._conn.execute(
                    """INSERT INTO settings(key,value,is_secret,updated_at) VALUES(?,?,?,?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                    is_secret=excluded.is_secret,updated_at=excluded.updated_at""",
                    (key, stored, int(secret), now),
                )

    def list_watchlist(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        sql = "SELECT symbol,name,enabled,source,created_at,updated_at FROM watchlist"
        if enabled_only:
            sql += " WHERE enabled=1"
        sql += " ORDER BY symbol"
        with self._lock:
            rows = self._conn.execute(sql).fetchall()
        return [dict(row) for row in rows]

    def upsert_watch(self, symbol: str, name: str, enabled: bool, source: str | None) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO watchlist(symbol,name,enabled,source,created_at,updated_at)
                VALUES(?,?,?,?,?,?) ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,enabled=excluded.enabled,source=excluded.source,
                updated_at=excluded.updated_at""",
                (symbol, name.strip(), int(enabled), source, now, now),
            )

    def delete_watch(self, symbol: str) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM watchlist WHERE symbol=?", (symbol,))

    def upsert_bars(self, bars: Iterable[Bar]) -> int:
        rows = [
            (
                b.symbol,
                b.timeframe,
                b.ts.isoformat(sep=" "),
                b.open,
                b.high,
                b.low,
                b.close,
                b.volume,
                b.amount,
                b.source,
                (b.available_at or b.ts).isoformat(sep=" "),
            )
            for b in bars
        ]
        if not rows:
            return 0
        with self._lock, self._conn:
            self._conn.executemany(
                """INSERT INTO bars(symbol,timeframe,ts,open,high,low,close,volume,amount,source,available_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(symbol,timeframe,ts) DO UPDATE SET
                open=excluded.open,high=excluded.high,low=excluded.low,close=excluded.close,
                volume=excluded.volume,amount=excluded.amount,source=excluded.source,
                available_at=excluded.available_at""",
                rows,
            )
        return len(rows)

    def last_bar_time(self, symbol: str, timeframe: str) -> datetime | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT MAX(ts) AS ts FROM bars WHERE symbol=? AND timeframe=?",
                (symbol, timeframe),
            ).fetchone()
        return datetime.fromisoformat(row["ts"]) if row and row["ts"] else None

    def load_bars(
        self,
        symbol: str,
        timeframe: str,
        since: datetime | None = None,
        sources: set[str] | None = None,
    ) -> list[Bar]:
        sql = "SELECT * FROM bars WHERE symbol=? AND timeframe=?"
        args: list[Any] = [symbol, timeframe]
        if since:
            sql += " AND ts>=?"
            args.append(since.isoformat(sep=" "))
        if sources:
            placeholders = ",".join("?" for _ in sources)
            sql += f" AND source IN ({placeholders})"
            args.extend(sorted(sources))
        sql += " ORDER BY ts"
        with self._lock:
            rows = self._conn.execute(sql, args).fetchall()
        return [
            Bar(
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                ts=datetime.fromisoformat(row["ts"]),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                amount=row["amount"],
                source=row["source"],
                available_at=datetime.fromisoformat(row["available_at"]),
            )
            for row in rows
        ]

    def save_report(
        self,
        symbol: str,
        name: str,
        session: str,
        asof: str,
        status: str,
        report_text: str,
        result: dict[str, Any],
    ) -> str:
        report_id = uuid.uuid4().hex
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO reports VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    report_id,
                    symbol,
                    name,
                    session,
                    asof,
                    status,
                    report_text,
                    json.dumps(result, ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        return report_id

    def list_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT id,symbol,name,session,asof,status,created_at
                FROM reports ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["result"] = json.loads(result.pop("result_json"))
        return result

    def start_run(self, session: str) -> str:
        run_id = uuid.uuid4().hex
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO runs VALUES(?,?,?,?,?,NULL)",
                (run_id, session, "running", "", datetime.now().isoformat(timespec="seconds")),
            )
        return run_id

    def finish_run(self, run_id: str, status: str, detail: dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE runs SET status=?,detail=?,finished_at=? WHERE id=?",
                (
                    status,
                    json.dumps(detail, ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds"),
                    run_id,
                ),
            )
