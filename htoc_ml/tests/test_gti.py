"""Unit tests for Google TI lookup and enrich-column flattening (no live API)."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from htoc.core.gti import (
    attach_gti_enrichment,
    classify_ioc,
    flatten_gti_report,
    gti_get,
    gti_path,
    kind_from_tc_type,
    load_gti_api_key,
)
from htoc.core.pipeline import PipelineError


def _report(*, malicious: int = 8, verdict: str = "VERDICT_MALICIOUS", mandiant_malware: bool = False, families: list[str] | None = None, actors: list[str] | None = None) -> dict:
    relationships = {
        "related_threat_actors": {"data": [{"type": "collection", "id": a} for a in (actors or [])]},
        "malware_families": {"data": [{"type": "collection", "id": f} for f in (families or [])]},
        "campaigns": {"data": []},
    }
    factors = {"safebrowsing_verdict": "harmless"}
    if mandiant_malware:
        factors["mandiant_association_malware"] = True
        factors["mandiant_confidence_score"] = 80
    return {
        "data": {
            "id": "1.2.3.4",
            "type": "ip_address",
            "attributes": {
                "last_analysis_stats": {"malicious": malicious, "suspicious": 1, "harmless": 40},
                "gti_assessment": {
                    "verdict": {"value": verdict},
                    "severity": {"value": "SEVERITY_MEDIUM"},
                    "threat_score": {"value": 55},
                    "description": "example",
                    "contributing_factors": factors,
                },
            },
            "relationships": relationships,
        }
    }


def test_classify_ioc_ip_domain_hash_url():
    assert classify_ioc("8.8.8.8") == "ip"
    assert classify_ioc("example.com") == "domain"
    assert classify_ioc("a" * 32) == "file"
    assert classify_ioc("https://evil.example/path") == "url"


def test_kind_from_tc_type():
    assert kind_from_tc_type("Address", "1.2.3.4") == "ip"
    assert kind_from_tc_type("Host", "foo.bar") == "domain"
    assert kind_from_tc_type("SHA256", "ab") == "file"
    assert kind_from_tc_type("", "8.8.8.8") == "ip"


def test_gti_path_ip():
    assert gti_path("8.8.8.8", "ip") == "/ip_addresses/8.8.8.8"


def test_flatten_maps_malicious_count_and_gti_fields():
    row = flatten_gti_report(_report(malicious=12), indicator="1.2.3.4")
    assert row["enrich_vtMaliciousCount"] == 12
    assert row["enrich_gti_verdict"] == "VERDICT_MALICIOUS"
    assert row["enrich_gti_severity"] == "SEVERITY_MEDIUM"
    assert row["enrich_gti_threat_score"] == 55
    assert row["enrich_gti_description"] == "example"
    assert row["enrich_gti_mandiant"] is False


def test_flatten_mandiant_from_contributing_factor():
    row = flatten_gti_report(_report(mandiant_malware=True), indicator="1.2.3.4")
    assert row["enrich_gti_mandiant"] is True


def test_flatten_mandiant_from_related_descriptors():
    row = flatten_gti_report(
        _report(families=["malware--abc"], actors=["threat-actor--xyz"]),
        indicator="1.2.3.4",
    )
    assert row["enrich_gti_mandiant"] is True
    assert "malware--abc" in row["enrich_gti_malware_families"]
    assert "threat-actor--xyz" in row["enrich_gti_threat_actors"]


def test_load_gti_api_key_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GTI_API_KEY", "env-key-value")
    assert load_gti_api_key(start=tmp_path) == "env-key-value"


def test_load_gti_api_key_from_config(monkeypatch, tmp_path):
    monkeypatch.delenv("GTI_API_KEY", raising=False)
    monkeypatch.delenv("VT_API_KEY", raising=False)
    monkeypatch.delenv("VT_APIKEY", raising=False)
    cfg = tmp_path / "notebooks" / "GoogleThreatIntel"
    cfg.mkdir(parents=True)
    (cfg / "config.json").write_text('{"api_key": "file-key"}', encoding="utf-8")
    (tmp_path / "htoc_ml" / "src" / "htoc").mkdir(parents=True)
    with patch("htoc.core.gti.find_htoc_src", return_value=tmp_path / "htoc_ml" / "src"):
        assert load_gti_api_key(start=tmp_path) == "file-key"


def test_load_gti_api_key_missing_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("GTI_API_KEY", raising=False)
    monkeypatch.delenv("VT_API_KEY", raising=False)
    monkeypatch.delenv("VT_APIKEY", raising=False)
    with patch("htoc.core.gti.find_htoc_src", return_value=tmp_path / "htoc_ml" / "src"):
        try:
            load_gti_api_key(start=tmp_path)
        except PipelineError as exc:
            assert "API key missing" in str(exc)
        else:
            raise AssertionError("expected PipelineError")


class _FakeHttp:
    def __init__(self, responses: list) -> None:
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


def test_load_gti_api_key_from_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("GTI_API_KEY", raising=False)
    monkeypatch.delenv("VT_API_KEY", raising=False)
    monkeypatch.delenv("VT_APIKEY", raising=False)
    (tmp_path / ".env").write_text("VT_API_KEY=dotenv-key\n", encoding="utf-8")
    (tmp_path / "htoc_ml" / "src" / "htoc").mkdir(parents=True)
    with patch("htoc.core.gti.find_htoc_src", return_value=tmp_path / "htoc_ml" / "src"):
        assert load_gti_api_key(start=tmp_path) == "dotenv-key"


def test_attach_fail_open_without_key():
    frame = pd.DataFrame([{"indicator": "1.2.3.4", "type": "Address"}])
    with patch("htoc.core.gti.load_gti_api_key", side_effect=PipelineError("Google TI API key missing")):
        out = attach_gti_enrichment(frame, use_cache=False, max_workers=1)
    assert list(out.columns) == list(frame.columns)
    assert out["indicator"].iloc[0] == "1.2.3.4"


def test_attach_uses_fresh_cache(monkeypatch, tmp_path):
    cache_file = tmp_path / "gti_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "1.2.3.4": {
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "enrich_vtMaliciousCount": 9,
                    "enrich_gti_verdict": "VERDICT_MALICIOUS",
                    "enrich_gti_mandiant": True,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GTI_CACHE_PATH", str(cache_file))
    frame = pd.DataFrame([{"indicator": "1.2.3.4", "type": "Address"}])
    with patch("htoc.core.gti.load_gti_api_key", return_value="k"):
        with patch("htoc.core.gti.lookup_ioc") as lookup:
            out = attach_gti_enrichment(frame, max_workers=1)
    lookup.assert_not_called()
    assert int(out["enrich_vtMaliciousCount"].iloc[0]) == 9
    assert out["enrich_gti_verdict"].iloc[0] == "VERDICT_MALICIOUS"


def test_gti_get_retries_429_then_succeeds():
    http = _FakeHttp(
        [
            SimpleNamespace(status_code=429, headers={"Retry-After": "0"}, text="slow", ok=False),
            SimpleNamespace(status_code=200, headers={}, text="{}", ok=True, json=lambda: {"data": {}}),
        ]
    )
    with patch("htoc.core.gti._headers", return_value={"x-apikey": "k"}):
        with patch("htoc.core.gti.time.sleep"):
            payload = gti_get("/ip_addresses/1.2.3.4", session=http)
    assert payload == {"data": {}}
    assert http.calls == 2
