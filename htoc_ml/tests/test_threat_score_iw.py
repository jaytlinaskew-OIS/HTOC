"""Unit tests for ThreatScoreIW helpers (no live API)."""
from __future__ import annotations

import pandas as pd

from htoc_ml.core.pipeline import PipelineError
from htoc_ml.datapipelines.threat_score_iw import (
    condense_final_indicators,
    filter_threat_assess_bands,
    has_iw_tag,
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


def test_has_iw_tag():
    assert has_iw_tag([{"name": "I&W"}, {"name": "other"}]) is True
    assert has_iw_tag([{"name": "malware"}]) is False
    assert has_iw_tag(None) is False


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
                "Reported I&W?": "No",
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
            "Reported I&W?": "Yes",
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
