import os
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

import chanlun_visual.api as api_module
from chanlun_visual import __version__
from chanlun_visual.api import app
from chanlun_visual.providers import (
    MarketRateLimitError,
    _parse_sina_quote_name,
    _translate_yahoo_error,
    akshare_bars,
    canonical_symbol,
)


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "execution_allowed": False}


def test_demo_and_html_export():
    demo = client.get("/api/demo").json()
    assert demo["name"] == "演示标的"
    analysis = demo["frames"]["1d"]
    response = client.post("/api/export/html", json={"analysis": analysis})
    assert response.status_code == 200
    assert "NO_ACTION" in response.text
    assert "execution_allowed=false" in response.text
    assert "<svg" in response.text


def test_bad_input_is_422():
    response = client.post(
        "/api/analyze",
        json={
            "symbol": "X",
            "timeframe": "1d",
            "bars": [{"date": "2026-01-01", "open": 2, "high": 1, "low": 0.5, "close": 2}],
        },
    )
    assert response.status_code == 422


def test_common_market_symbols_are_canonicalized():
    assert canonical_symbol("300684") == "300684.SZ"
    assert canonical_symbol("600519") == "600519.SS"
    assert canonical_symbol("0700") == "0700.HK"
    assert canonical_symbol("AAPL") == "AAPL"


def test_data_sources_can_be_added_activated_and_deleted(tmp_path, monkeypatch):
    config_path = tmp_path / "sources.json"
    monkeypatch.setenv("CHANLUN_DATA_SOURCE_CONFIG", str(config_path))

    initial = client.get("/api/data-sources")
    assert initial.status_code == 200
    assert initial.json()["active_id"] == "builtin-yfinance"

    created = client.post(
        "/api/data-sources",
        json={"provider": "tushare", "name": "我的 Tushare", "api_key": "secret-token-1234"},
    )
    assert created.status_code == 201
    body = created.json()
    custom = next(item for item in body["sources"] if item["provider"] == "tushare")
    assert custom["has_api_key"] is True
    assert custom["api_key_mask"].endswith("1234")
    assert "secret-token-1234" not in created.text

    activated = client.post(f"/api/data-sources/{custom['id']}/activate")
    assert activated.status_code == 200
    assert activated.json()["active_id"] == custom["id"]
    assert sum(item["active"] for item in activated.json()["sources"]) == 1

    deleted = client.delete(f"/api/data-sources/{custom['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["active_id"] == "builtin-yfinance"


def test_tushare_requires_an_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("CHANLUN_DATA_SOURCE_CONFIG", str(tmp_path / "sources.json"))
    response = client.post(
        "/api/data-sources",
        json={"provider": "tushare", "name": "Tushare", "api_key": ""},
    )
    assert response.status_code == 422
    assert "必须填写" in response.json()["detail"]


def test_yahoo_rate_limit_is_friendly_and_stops_followup_requests(monkeypatch):
    calls = []
    monkeypatch.setattr(
        api_module,
        "active_source",
        lambda: {"id": "builtin-yfinance", "provider": "yfinance", "name": "Yahoo Finance", "api_key": ""},
    )

    def rate_limited(symbol, timeframe, source):
        calls.append((symbol, timeframe, source["provider"]))
        raise MarketRateLimitError("Yahoo Finance 请求频率受限，请稍后重试")

    monkeypatch.setattr(api_module, "configured_bars", rate_limited)
    response = client.get("/api/quote?symbol=AAPL")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["message"] == "Yahoo Finance 请求频率受限，请稍后重试"
    assert detail["retryable"] is True
    assert calls == [("AAPL", "1d", "yfinance")]


def test_yahoo_errors_are_translated_for_users():
    rate_limit = _translate_yahoo_error(RuntimeError("Too Many Requests. Rate limited."))
    forbidden = _translate_yahoo_error(RuntimeError("HTTP Error 403: Forbidden"))
    assert isinstance(rate_limit, MarketRateLimitError)
    assert "配置数据源" in str(rate_limit)
    assert "当前网络无法访问" in str(forbidden)


def test_akshare_falls_back_to_sina_and_bypasses_broken_proxy(monkeypatch):
    class FakeFrame:
        empty = False

        def iterrows(self):
            yield 0, {
                "date": "2026-09-22",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "volume": 1000,
            }

    def eastmoney_failure(**kwargs):
        raise RuntimeError("ProxyError: remote disconnected")

    calls = []

    def sina_daily(**kwargs):
        calls.append(kwargs)
        return FakeFrame()

    fake_akshare = SimpleNamespace(
        stock_zh_a_hist=eastmoney_failure,
        stock_zh_a_daily=sina_daily,
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)
    monkeypatch.setenv("NO_PROXY", "localhost")
    monkeypatch.setenv("no_proxy", "localhost")

    bars = akshare_bars("600893.SS", "1d")
    assert len(bars) == 1
    assert calls[0]["symbol"] == "sh600893"
    assert "quotes.sina.cn" in os.environ["NO_PROXY"]


def test_sina_names_prefer_chinese_then_english():
    assert _parse_sina_quote_name("600893.SS", 'var hq_str_sh600893="航发动力,40.2";') == "航发动力"
    assert _parse_sina_quote_name("0700.HK", 'var hq_str_hk00700="TENCENT,腾讯控股,442";') == "腾讯控股"
    assert _parse_sina_quote_name("0700.HK", 'var hq_str_hk00700="TENCENT,,442";') == "TENCENT"
    assert _parse_sina_quote_name("AAPL", 'var hq_str_gb_aapl="苹果,340";') == "苹果"


def test_watchlist_history_and_custom_pool_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("CHANLUN_WATCHLIST_CONFIG", str(tmp_path / "watchlists.json"))

    initial = client.get("/api/watchlists")
    assert initial.status_code == 200
    assert initial.json()["pools"][0]["name"] == "我的自选"

    created = client.post("/api/watchlists", json={"name": "军工观察"})
    assert created.status_code == 201
    pool = next(item for item in created.json()["pools"] if item["name"] == "军工观察")

    added = client.post(
        f"/api/watchlists/{pool['id']}/items",
        json={"symbol": "600893", "name": "航发动力"},
    )
    assert added.status_code == 200
    custom = next(item for item in added.json()["pools"] if item["id"] == pool["id"])
    assert custom["items"] == [{"symbol": "600893.SS", "name": "航发动力"}]

    removed = client.delete(f"/api/watchlists/{pool['id']}/items/600893.SS")
    assert removed.status_code == 200
    assert next(item for item in removed.json()["pools"] if item["id"] == pool["id"])["items"] == []

    deleted = client.delete(f"/api/watchlists/{pool['id']}")
    assert deleted.status_code == 200
    assert all(item["id"] != pool["id"] for item in deleted.json()["pools"])
