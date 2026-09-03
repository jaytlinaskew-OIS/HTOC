"""Tests for cross-partner spread analysis helpers."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis" / "noi"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

from partner_relationships import (  # noqa: E402
    SEVERITY_KEEP,
    _active_within,
    _seen_on_day,
    severity_filter_summary,
    temporal_split,
)


def test_active_within_and_seen_on_day():
    dates = np.array([100, 105, 110])
    assert _active_within(dates, 110, 7)
    assert _seen_on_day(dates, 110)
    assert not _seen_on_day(dates, 111)


def test_temporal_split_and_severity_filter():
    events = pd.DataFrame(
        {
            "cutoff_day": [1, 2, 98, 99, 100],
            "indicator": ["a", "b", "c", "d", "e"],
            "spread_7d": [0, 1, 0, 1, 0],
        }
    )
    train, eval_df = temporal_split(events, eval_tail_days=2)
    assert len(train) == 2
    assert len(eval_df) == 3

    prism = pd.DataFrame(
        {
            "indicator": ["a", "b", "c"],
            "severity": ["medium", "low", "high"],
        }
    )
    summary = severity_filter_summary(events, prism)
    assert "included_in_analysis" in summary.columns
    assert SEVERITY_KEEP == frozenset({"medium", "high", "critical"})
