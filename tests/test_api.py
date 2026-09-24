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
from chanlun_visual.multilevel_reports import close_report_database


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
    assert canonical_symbol("1A0001") == "000001.SS"
    assert canonical_symbol("上证指数") == "000001.SS"
    assert canonical_symbol("1B0688") == "000688.SS"
    assert canonical_symbol("科创50") == "000688.SS"
    assert canonical_symbol("深证成指") == "399001.SZ"


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


def test_akshare_routes_shenzhen_index_to_index_and_tencent_apis(monkeypatch):
    class FakeFrame:
        empty = False

        def __init__(self, row):
            self.row = row

        def iterrows(self):
            yield 0, self.row

    calls = []

    def eastmoney_index_failure(**kwargs):
        calls.append(("eastmoney-index", kwargs))
        raise RuntimeError("index endpoint unavailable")

    def tencent_index(**kwargs):
        calls.append(("tencent-index", kwargs))
        return FakeFrame(
            {
                "date": "2026-09-22",
                "open": 13200,
                "high": 13300,
                "low": 13100,
                "close": 13250,
                "amount": 1000000,
            }
        )

    def stock_api_must_not_run(**kwargs):
        raise AssertionError(f"index incorrectly routed to stock API: {kwargs}")

    fake_akshare = SimpleNamespace(
        index_zh_a_hist=eastmoney_index_failure,
        stock_zh_index_daily_tx=tencent_index,
        stock_zh_index_daily=stock_api_must_not_run,
        stock_zh_a_hist=stock_api_must_not_run,
        stock_zh_a_daily=stock_api_must_not_run,
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    bars = akshare_bars("399001.SZ", "1d")

    assert len(bars) == 1
    assert bars[0]["close"] == 13250
    assert calls[0][0] == "eastmoney-index"
    assert calls[1][0] == "tencent-index"
    assert calls[1][1]["symbol"] == "sz399001"


def test_akshare_routes_shenzhen_index_minutes_to_index_api(monkeypatch):
    class FakeFrame:
        empty = False

        def iterrows(self):
            yield 0, {
                "时间": "2026-09-22 10:00:00",
                "开盘": 13200,
                "最高": 13300,
                "最低": 13100,
                "收盘": 13250,
                "成交量": 100000,
            }

    calls = []

    def index_minutes(**kwargs):
        calls.append(kwargs)
        return FakeFrame()

    fake_akshare = SimpleNamespace(
        index_zh_a_hist_min_em=index_minutes,
        stock_zh_a_hist_min_em=lambda **kwargs: (_ for _ in ()).throw(
            AssertionError(f"index incorrectly routed to stock API: {kwargs}")
        ),
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    bars = akshare_bars("399001.SZ", "30m")

    assert len(bars) == 1
    assert calls[0]["symbol"] == "399001"
    assert calls[0]["period"] == "30"


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


def test_report_settings_share_the_active_market_source(tmp_path, monkeypatch):
    close_report_database()
    monkeypatch.setenv("CHANLUN_REPORT_HOME", str(tmp_path / "reports"))
    monkeypatch.setenv("CHANLUN_DATA_SOURCE_CONFIG", str(tmp_path / "sources.json"))

    response = client.get("/api/report-settings")
    assert response.status_code == 200
    assert response.json()["shared_source"]["provider"] == "yfinance"

    updated = client.put(
        "/api/report-settings/analysis",
        json={"daily_years": 8, "minute30_years": 3, "minute5_days": 240},
    )
    assert updated.status_code == 200
    assert updated.json()["analysis"] == {
        "daily_years": 8,
        "minute30_years": 3,
        "minute5_days": 240,
    }
    close_report_database()


def test_search_report_endpoint_returns_engine_contract(monkeypatch):
    expected = {
        "id": "report-1",
        "symbol": "600893.SH",
        "name": "航发动力",
        "status": "observe",
        "report_text": "deterministic report",
        "result": {"contract": "chanlun_multilevel_v1"},
        "source": {"provider": "akshare", "name": "AKShare"},
        "created_at": "2026-09-24T09:00:00",
    }
    calls = []

    def fake_generate(symbol, name, session, notify):
        calls.append((symbol, name, session, notify))
        return expected

    monkeypatch.setattr(api_module, "generate_report", fake_generate)
    response = client.post(
        "/api/reports/analyze",
        json={"symbol": "600893", "name": "航发动力"},
    )
    assert response.status_code == 200
    assert response.json() == expected
    assert calls == [("600893", "航发动力", "manual", False)]
