"""Behavioral features from observations at or before a cutoff day."""
from __future__ import annotations

import numpy as np

from htoc_ml.core.day import Day

FEATURE_NAMES: tuple[str, ...] = (
    "last_seen",
    "freq_7",
    "freq_14",
    "freq_30",
    "freq_100",
    "avg_gap",
    "burstiness",
    "overdue",
)

# 0 = unconstrained, +1 = non-decreasing, -1 = non-increasing.
# Horizon is appended by TrainingSet.stack and is always +1.
MONOTONIC_CONSTRAINTS: dict[str, int] = {name: 0 for name in FEATURE_NAMES}


class FeatureBuilder:
    def __init__(self, lookback_days: int) -> None:
        self.lookback_days = lookback_days

    def featurize(self, dates: np.ndarray, cutoff_day: Day) -> dict[str, float]:
        lookback = self.lookback_days
        window_end = np.searchsorted(dates, cutoff_day, side="right")
        window_start = np.searchsorted(dates, cutoff_day - lookback + 1, side="left")
        return self.featurize_window(dates[window_start:window_end], cutoff_day)

    def featurize_window(self, window: np.ndarray, cutoff_day: Day) -> dict[str, float]:
        """Featurize a pre-sliced lookback window (avoids redundant searchsorted)."""
        lookback = self.lookback_days
        if window.size == 0:
            return {
                "last_seen": lookback,
                "freq_7": 0,
                "freq_14": 0,
                "freq_30": 0,
                "freq_100": 0,
                "avg_gap": float(lookback),
                "burstiness": 0.0,
                "overdue": 1.0,
            }

        def count_within(days: int) -> int:
            return int(window.size - np.searchsorted(window, cutoff_day - days + 1, side="left"))

        gaps = np.diff(window)
        if gaps.size >= 1:
            mean_gap = float(gaps.mean())
            gap_std = float(gaps.std())
            burstiness = (gap_std - mean_gap) / (gap_std + mean_gap) if (gap_std + mean_gap) > 0 else 0.0
        else:
            mean_gap, burstiness = float(lookback), 0.0
        last_seen = int(cutoff_day - window[-1])
        overdue = last_seen / mean_gap if mean_gap > 0 else 0.0
        return {
            "last_seen": last_seen,
            "freq_7": count_within(7),
            "freq_14": count_within(14),
            "freq_30": count_within(30),
            "freq_100": int(window.size),
            "avg_gap": mean_gap,
            "burstiness": burstiness,
            "overdue": overdue,
        }

    def as_vector(self, dates: np.ndarray, cutoff_day: Day) -> list[float]:
        values = self.featurize(dates, cutoff_day)
        return [values[name] for name in FEATURE_NAMES]
