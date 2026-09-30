"""Unit tests for ThreatScoreIW helpers (no live API)."""
from __future__ import annotations

import pandas as pd

from htoc.core.pipeline import PipelineError
from htoc.datapipelines.threat_score_iw import (
    ThreatScoreIwConfig,
    attach_tags,
    condense_final_indicators,
    exclude_indicators_by_tags,
    filter_threat_assess_bands,
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
