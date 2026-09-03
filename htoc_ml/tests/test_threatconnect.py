"""Unit tests for shared ThreatConnect helpers (no live API)."""
from __future__ import annotations

import json
import urllib.parse
from types import SimpleNamespace

from htoc.core.pipeline import PipelineError
from htoc.core.threatconnect import ThreatConnectClient, _quoted, build_indicator_tql, load_api_config


class _FakeRequest:
    def __init__(self) -> None:
        self.http_method = None
        self.uri = None

    def set_http_method(self, method: str) -> None:
        self.http_method = method

    def set_request_uri(self, uri: str) -> None:
        self.uri = uri


class _FakeSession:
    def __init__(self, responses: list) -> None:
        self.responses = list(responses)
        self.calls: list[_FakeRequest] = []

    def api_request(self, request: _FakeRequest):
        # Capture a snapshot of the URI at call time (request object is reused).
        snap = _FakeRequest()
        snap.http_method = request.http_method
        snap.uri = request.uri
        self.calls.append(snap)
        if not self.responses:
            raise AssertionError("unexpected api_request call")
        return self.responses.pop(0)


def _client_with_session(session: _FakeSession, *, page_size: int = 500) -> ThreatConnectClient:
    client = ThreatConnectClient.__new__(ThreatConnectClient)
    client.result_page_size = page_size
    client._RequestObject = _FakeRequest
    client.session = session
    return client


def _json_response(payload: dict):
    return SimpleNamespace(
        headers={"content-type": "application/json"},
        content=b"{}",
        json=lambda: payload,
    )


def test_quoted_joins_with_double_quotes():
    assert _quoted(["HTOC Org", "CMS_CTI"]) == '"HTOC Org", "CMS_CTI"'


def test_build_indicator_tql_named_filters():
    tql = build_indicator_tql(
        owner_names=["HTOC Org"],
        indicator_types=["Address", "Host"],
        last_observed_on_or_after="2026-01-01T00:00:00Z",
        extra_clauses=['confidence > "50"'],
    )
    assert 'ownerName IN ("HTOC Org")' in tql
    assert 'typeName IN ("Address", "Host")' in tql
    assert 'lastObserved >= "2026-01-01T00:00:00Z"' in tql
    assert 'confidence > "50"' in tql


def test_build_indicator_tql_requires_a_clause():
    try:
        build_indicator_tql()
    except PipelineError as exc:
        assert "at least one" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_load_api_config_reads_required_keys(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "api_secret_key": "sec",
                "api_access_id": "id",
                "api_base_url": "https://example.test",
                "api_default_org": "HTOC Org",
            }
        ),
        encoding="utf-8",
    )
    secret, access_id, base_url, org = load_api_config(path)
    assert secret == "sec"
    assert access_id == "id"
    assert base_url == "https://example.test"
    assert org == "HTOC Org"


def test_load_api_config_missing_file_raises(tmp_path):
    try:
        load_api_config(tmp_path / "missing.json")
    except PipelineError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_load_api_config_missing_keys_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"api_access_id": "only"}), encoding="utf-8")
    try:
        load_api_config(path)
    except PipelineError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_paginate_indicators_builds_request_uri_and_calls_api():
    tql = build_indicator_tql(owner_names=["HTOC Org"], indicator_types=["Address"])
    session = _FakeSession(
        [
            _json_response({"data": [{"summary": "1.2.3.4 Address", "ownerName": "HTOC Org"}]}),
            _json_response({"data": []}),
        ]
    )
    client = _client_with_session(session, page_size=100)

    pages = client.paginate_indicators(
        tql,
        fields=("tags", "threatAssess"),
        page_size=50,
        result_start=0,
        sorting="lastObserved DESC",
    )

    assert len(pages) == 1
    assert len(session.calls) == 2
    assert session.calls[0].http_method == "GET"
    uri = session.calls[0].uri
    assert uri.startswith("/v3/indicators?")
    assert f"tql={urllib.parse.quote(tql)}" in uri
    assert "fields=tags,threatAssess" in uri
    assert "resultStart=0" in uri
    assert "resultLimit=50" in uri
    assert f"sorting={urllib.parse.quote('lastObserved DESC')}" in uri
    assert "resultStart=50" in session.calls[1].uri


def test_query_indicators_returns_normalized_frame_from_api_response():
    session = _FakeSession(
        [
            _json_response(
                {
                    "data": [
                        {"summary": "1.2.3.4 Address", "ownerName": "HTOC Org", "type": "Address"},
                        {"summary": "1.2.3.4 Address", "ownerName": "CMS_CTI", "type": "Address"},
                    ]
                }
            ),
            _json_response({"data": []}),
        ]
    )
    client = _client_with_session(session)

    frame = client.query_indicators(owner_names=["HTOC Org", "CMS_CTI"], indicator_types=["Address"], fields="tags")

    assert not frame.empty
    assert "indicator" in frame.columns
    assert "sources" in frame.columns
    assert set(frame["indicator"]) == {"1.2.3.4"}
    assert session.calls[0].uri.startswith("/v3/indicators?")
    assert "fields=tags" in session.calls[0].uri
    assert 'ownerName IN ("HTOC Org", "CMS_CTI")' in urllib.parse.unquote(session.calls[0].uri)


def test_paginate_indicators_non_json_raises_pipeline_error():
    session = _FakeSession(
        [SimpleNamespace(headers={"content-type": "text/html"}, content=b"<html>nope</html>", json=lambda: {})]
    )
    client = _client_with_session(session)
    try:
        client.paginate_indicators('ownerName = "HTOC Org"')
    except PipelineError as exc:
        assert "Non-JSON" in str(exc)
    else:
        raise AssertionError("expected PipelineError")
