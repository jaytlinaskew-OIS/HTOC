"""Unit tests for ThreatScoreIW helpers (no live API)."""
from __future__ import annotations

import pandas as pd
import pytest
import runpy
from pathlib import Path

from htoc.core.pipeline import PipelineError
from htoc.datapipelines.threat_score_iw import (
    ThreatScoreIwConfig,
    attach_tags,
    condense_final_indicators,
    exclude_indicators_by_tags,
    filter_threat_assess_bands,
    filter_vt_and_severity,
    write_iw_workbook,
)


def test_filter_threat_assess_bands_keeps_rating_or_ta_and_confidence():
    frame = pd.DataFrame(
        {
            "indicator": ["a", "b", "c", "d"],
            "rating": [3, 1, 1, 4],
            "confidence": [40, 60, 40, 10],
            "threatAssessRating": [None, 3, 2, None],
            "threatAssessConfidence": [50, None, 50, 80],
        }
    )
    out = filter_threat_assess_bands(frame)
    # a: rating>=3 + TA confidence>=50; b: TA rating>=3 + confidence>=50; d: rating>=3 + TA confidence>=50
    assert set(out["indicator"]) == {"a", "b", "d"}


def test_filter_threat_assess_bands_missing_columns_raises():
    try:
        filter_threat_assess_bands(pd.DataFrame({"indicator": ["a"]}))
    except PipelineError as exc:
        assert "Threat Assess" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_attach_tags_combines_csv_and_live_threatconnect_tags(tmp_path):
    tags_path = tmp_path / "tags.csv"
    pd.DataFrame(
        {
            "indicator": ["csv-iw", "csv-iw", "live-iw", "keep"],
            "tag": ["I&W", "malware", "other", "malware"],
        }
    ).to_csv(tags_path, index=False)
    final_indicators = pd.DataFrame(
        {
            "Indicator": ["csv-iw", "live-iw", "keep"],
            "HTOC Threat Score": [10, 9, 8],
        }
    )
    observed = pd.DataFrame(
        {
            "indicator": ["csv-iw", "live-iw", "keep"],
            "tags.data": [
                [{"name": "other"}],
                [{"name": "IW"}],
                [{"name": "clean"}],
            ],
        }
    )
    config = ThreatScoreIwConfig(tags_csv=str(tags_path))

    labeled = attach_tags(final_indicators, observed, config)
    out = exclude_indicators_by_tags(labeled, config)

    assert labeled.loc[labeled["Indicator"] == "csv-iw", "Tags"].iat[0] == "I&W, malware, other"
    assert labeled.loc[labeled["Indicator"] == "live-iw", "Tags"].iat[0] == "other, IW"
    assert "Reported I&W?" not in labeled.columns
    assert out["Indicator"].tolist() == ["keep"]


def test_exclude_indicators_by_tags_matches_all_configured_tags_case_insensitively():
    frame = pd.DataFrame(
        {
            "Indicator": ["keep", "iw", "benign", "tor", "tor-node", "substring", "tor-near"],
            "Tags": ["malware", "Other, I&W", "benign pb, Other", "TOR", "tor node", "iwest", "TOR Exit Node"],
        }
    )

    out = exclude_indicators_by_tags(frame, ThreatScoreIwConfig())

    assert out["Indicator"].tolist() == ["keep", "substring", "tor-near"]


def test_write_iw_workbook_omits_redundant_yes_sheet(tmp_path):
    output_path = tmp_path / "iw.xlsx"
    frame = pd.DataFrame({"Indicator": ["keep"], "Tags": ["clean"]})

    written = write_iw_workbook(frame, output_path)

    assert written == output_path
    with pd.ExcelFile(output_path) as workbook:
        assert workbook.sheet_names == ["I&W_No"]


def test_condense_final_indicators_rolls_dense_subnet():
    rows = []
    for i in range(5):
        rows.append(
            {
                "Indicator": f"10.0.0.{i}",
                "Indicator Type": "Address",
                "Severity": "high",
                "Partners": "CMS",
                "OpDiv": "CMS",
                "Threat Actor": "",
                "Last Observed": pd.Timestamp("2026-08-01"),
                "Explanation": "VT score: 5",
                "Tags": None,
            }
        )
    rows.append(
        {
            "Indicator": "10.0.1.9",
            "Indicator Type": "Address",
            "Severity": "critical",
            "Partners": "VA",
            "OpDiv": "VA",
            "Threat Actor": "",
            "Last Observed": pd.Timestamp("2026-08-01"),
            "Explanation": "VT score: 8",
            "Tags": None,
        }
    )
    out = condense_final_indicators(pd.DataFrame(rows), min_hosts=5)
    assert "10.0.0.0/24" in set(out["Indicator"])
    assert "10.0.1.9" in set(out["Indicator"])
    cidr = out[out["Indicator"] == "10.0.0.0/24"].iloc[0]
    assert cidr["Indicator Type"] == "CIDR"
    assert isinstance(cidr["_member_ips"], list)
    assert len(cidr["_member_ips"]) == 5


def test_tor_explanation_excluded_even_with_high_vt_and_six_partners():
    frame = pd.DataFrame({
        "Indicator": ["tor", "tor-mixed-case", "keep", "missing", "low-vt", "medium"],
        "Severity": ["high", "critical", "high", "high", "critical", "medium"],
        "Partners": ["A, B, C, D, E, F"] * 6,
        "Explanation": [
            "[2026-10-19] Severity: high. VT score: 20. Contextual Drivers: "
            "VT malicious (log-scaled); TOR activity; Reinforcing context bonus. "
            "Observed across 6 partner(s). Observed by 2 sources. "
            "3 reinforcing context signal(s). No PB lower-start rule. "
            "No botnet penalty. No false positive tags. No scanner penalty. "
            "TOR activity detected. No incident/event link. Score: 788/1000.",
            "VT score: 20. tor ACTIVITY detected.",
            "VT score: 20. No TOR activity.",
            None,
            "VT score: 1. No TOR activity.",
            "VT score: 20. No TOR activity.",
        ],
    })

    out = filter_vt_and_severity(frame, ThreatScoreIwConfig())

    assert out["Indicator"].tolist() == ["keep"]


def test_tor_tags_excluded_from_both_csv_and_live_data(tmp_path):
    tags_path = tmp_path / "tags.csv"
    pd.DataFrame({
        "indicator": ["csv-tor", "csv-tor", "csv-exit", "live-tor", "keep"],
        "tag": ["ToR", "malware", "torexitnode", "malware", "torpedo"],
    }).to_csv(tags_path, index=False)
    frame = pd.DataFrame({"Indicator": ["csv-tor", "csv-exit", "live-tor", "keep"]})
    observed = pd.DataFrame({
        "indicator": frame["Indicator"],
        "tags.data": [[], [], [{"name": "tOr NoDe"}], []],
    })
    config = ThreatScoreIwConfig(tags_csv=str(tags_path))

    out = exclude_indicators_by_tags(attach_tags(frame, observed, config), config)

    assert out["Indicator"].tolist() == ["keep"]


@pytest.mark.parametrize("exit_code", [0, 3])
def test_legacy_scheduled_entry_uses_package_main(monkeypatch, exit_code):
    from htoc.datapipelines import threat_score_iw

    called = []

    def fake_main():
        called.append(True)
        return exit_code

    monkeypatch.setattr(threat_score_iw, "main", fake_main)
    # The compatibility entry point adjusts sys.path; isolate that side effect.
    import sys
    monkeypatch.setattr(sys, "path", sys.path.copy())
    runner = (Path(__file__).resolve().parents[2] /
              "notebooks/ThreatAssessment Scoring/ThreatScoreIW/ThreatScoreIW.py")

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(runner), run_name="__main__")

    assert exc.value.code == exit_code
    assert called == [True]


@pytest.mark.parametrize("empty_stage", ["tags", "vt", "join"])
def test_zero_eligible_run_writes_headers_only_report(tmp_path, monkeypatch, capsys, empty_stage):
    from htoc.datapipelines import threat_score_iw as pipeline
    from htoc.core.pipeline import PipelineNoWork

    scores = tmp_path / "scores.xlsx"
    tags = tmp_path / "tags.csv"
    frame = pd.DataFrame({
        "Indicator": ["blocked"], "Indicator Type": ["Address"],
        "Severity": ["high"], "Explanation": ["VT score: 20. No TOR activity."],
        "HTOC Threat Score": [600],
    })
    frame.to_excel(scores, index=False)
    pd.DataFrame({"indicator": ["blocked"], "tag": ["I&W"]}).to_csv(tags, index=False)
    config = ThreatScoreIwConfig(scores_xlsx=str(scores), tags_csv=str(tags), save_dir=str(tmp_path))
    observed = pd.DataFrame({"indicator": ["blocked"], "tags.data": [[]]})
    monkeypatch.setattr(pipeline.ThreatScoreIwConfig, "from_env", classmethod(lambda cls: config))
    monkeypatch.setattr(pipeline, "ThreatConnectClient", lambda **kwargs: object())
    monkeypatch.setattr(pipeline, "intake_recent_indicators_from_threatconnect", lambda *args: observed)
    monkeypatch.setattr(pipeline, "filter_threat_assess_bands", lambda data: data)
    monkeypatch.setattr(pipeline, "join_prism_scores", lambda *args: frame)
    monkeypatch.setattr(pipeline, "attach_opdiv_multi_partners", lambda data, config: data)
    if empty_stage == "vt":
        frame["Explanation"] = "VT score: 20. TOR activity detected."
    elif empty_stage == "join":
        def no_overlap(*args):
            raise PipelineNoWork("No overlapping indicators.")
        monkeypatch.setattr(pipeline, "join_prism_scores", no_overlap)

    assert pipeline.main() == 0
    output = capsys.readouterr().out
    assert "PIPELINE_OK_NOWORK" not in output
    assert "PIPELINE_OK" in output
    with pd.ExcelFile(config.output_path()) as workbook:
        assert workbook.sheet_names == ["I&W_No"]
        report = pd.read_excel(workbook, sheet_name="I&W_No")
    assert report.empty
    assert {"Indicator", "Host IP", "PRISM Score", "Severity", "Tags", "OpDiv"} <= set(report.columns)


def test_empty_report_write_failure_does_not_report_success(tmp_path, monkeypatch, capsys):
    from htoc.datapipelines import threat_score_iw as pipeline
    from htoc.core.pipeline import PipelineNoWork

    scores = tmp_path / "scores.xlsx"
    pd.DataFrame(columns=["Indicator", "Severity"]).to_excel(scores, index=False)
    config = ThreatScoreIwConfig(scores_xlsx=str(scores), save_dir=str(tmp_path))
    monkeypatch.setattr(pipeline.ThreatScoreIwConfig, "from_env", classmethod(lambda cls: config))
    monkeypatch.setattr(pipeline, "ThreatConnectClient", lambda **kwargs: object())
    def no_work(*args):
        raise PipelineNoWork("No overlapping indicators.")
    def write_failed(*args):
        raise PipelineError("Workbook write denied", exit_code=4)
    monkeypatch.setattr(pipeline, "intake_recent_indicators_from_threatconnect", no_work)
    monkeypatch.setattr(pipeline, "write_iw_workbook", write_failed)
    assert pipeline.main() == 4
    assert "PIPELINE_OK" not in capsys.readouterr().out
