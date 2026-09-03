import numpy as np

from htoc.noi.features import FEATURE_NAMES, MONOTONIC_CONSTRAINTS, featurize, featurize_window, feature_vector


def test_feature_names_match_constraints_and_featurize_keys():
    values = featurize(lookback_days=100, dates=np.array([0, 1, 2], dtype=int), cutoff_day=2)
    assert FEATURE_NAMES == tuple(MONOTONIC_CONSTRAINTS)
    assert tuple(values) == FEATURE_NAMES
    assert set(MONOTONIC_CONSTRAINTS) == set(FEATURE_NAMES)


def test_empty_window_uses_lookback_defaults():
    values = featurize(lookback_days=100, dates=np.array([0], dtype=int), cutoff_day=200)
    assert values["last_seen"] == 100
    assert values["freq_100"] == 0
    assert values["avg_gap"] == 100.0
    assert values["overdue"] == 1.0


def test_monotonic_vector_puts_horizon_last():
    vector = [MONOTONIC_CONSTRAINTS[name] for name in FEATURE_NAMES] + [1]
    assert vector[-1] == 1
    assert len(vector) == len(FEATURE_NAMES) + 1
    assert all(c == 0 for c in vector[:-1])


def test_featurize_window_matches_featurize():
    lookback_days = 100
    dates = np.array([10, 12, 13, 20, 21, 22, 29], dtype=int)
    cutoff_day = 29
    window_end = np.searchsorted(dates, cutoff_day, side="right")
    window_start = np.searchsorted(dates, cutoff_day - lookback_days + 1, side="left")
    window = dates[window_start:window_end]
    assert featurize_window(lookback_days, window, cutoff_day) == featurize(
        lookback_days, dates, cutoff_day
    )


def test_featurize_matches_legacy_list_order():
    """Same arithmetic as NextObservedIndicatorV4.0.py featurize(), name-keyed."""
    dates = np.array([10, 12, 13, 20, 21, 22, 29], dtype=int)
    cutoff_day = 29
    lookback = 100
    named = featurize(lookback, dates, cutoff_day)
    assert feature_vector(lookback, dates, cutoff_day) == [named[name] for name in FEATURE_NAMES]
    assert named["last_seen"] == 0
    assert named["freq_7"] == 1
    assert named["freq_100"] == 7

    dates = np.arange(0, 30, dtype=int)
    values = featurize(lookback_days=100, dates=dates, cutoff_day=29)
    assert values["last_seen"] == 0
    assert values["freq_7"] == 7
    assert values["freq_14"] == 14
    assert values["freq_30"] == 30
    assert values["freq_100"] == 30
    assert values["avg_gap"] == 1.0
    assert values["overdue"] == 0.0
