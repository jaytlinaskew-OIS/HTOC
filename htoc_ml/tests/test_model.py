"""Unit tests for core model builders and NOI HorizonModel."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier

from htoc_ml.core.modeling import (
    build_hist_gradient_boosting_classifier,
    fit_isotonic_calibrated_classifier,
)
from htoc_ml.core.pipeline import PipelineError
from htoc_ml.noi.config import ForecastConfig
from htoc_ml.noi.features import FEATURE_NAMES
from htoc_ml.noi.model import HorizonModel
from htoc_ml.noi.schedule import CutoffSchedule


class _FakeTraining:
    """Minimal TrainingSet stand-in: stack + monotonic vector only."""

    def __init__(self, config: ForecastConfig) -> None:
        self.config = config

    def monotonic_constraint_vector(self) -> list[int]:
        return [0] * len(FEATURE_NAMES) + [1]

    def stack(self, df: pd.DataFrame, with_label: bool = True, with_weights: bool = False):
        base = df[list(FEATURE_NAMES)].to_numpy(float)
        Xs, ys, ws = [], [], []
        for horizon_days in self.config.horizons:
            Xh = np.hstack([base, np.full((len(df), 1), float(horizon_days))])
            if not with_label:
                Xs.append(Xh)
                continue
            y = df[f"y_{horizon_days}"].to_numpy(int)
            Xs.append(Xh)
            ys.append(y)
            if with_weights:
                ws.append(np.ones(len(y), dtype=float))
        X = np.vstack(Xs)
        if not with_label:
            return X, None
        y = np.concatenate(ys)
        if with_weights:
            return X, y, np.concatenate(ws)
        return X, y


def _train_frame(config: ForecastConfig, cutoffs: list[int]) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for i, t in enumerate(cutoffs):
        row = {name: float(rng.normal()) for name in FEATURE_NAMES}
        row["opdiv"] = "FDA"
        row["t"] = t
        # Mild signal so HGB can fit both classes
        pos = 1 if (row["freq_7"] + row["freq_30"]) > 0 else 0
        for horizon_days in config.horizons:
            row[f"y_{horizon_days}"] = int(pos if horizon_days == config.horizons[0] else min(1, pos + (i % 2)))
        rows.append(row)
    # Guarantee both classes for every horizon
    for horizon_days in config.horizons:
        rows[0][f"y_{horizon_days}"] = 0
        rows[1][f"y_{horizon_days}"] = 1
        rows[-2][f"y_{horizon_days}"] = 0
        rows[-1][f"y_{horizon_days}"] = 1
    return pd.DataFrame(rows)


def test_build_classifier_applies_call_site_params():
    clf = build_hist_gradient_boosting_classifier(
        max_depth=3,
        learning_rate=0.2,
        max_iter=50,
        l2_regularization=0.5,
        random_state=7,
        monotonic_constraints=[0, 0, 1],
    )
    assert isinstance(clf, HistGradientBoostingClassifier)
    assert clf.max_depth == 3
    assert clf.learning_rate == 0.2
    assert clf.max_iter == 50
    assert clf.l2_regularization == 0.5
    assert clf.random_state == 7
    assert list(clf.monotonic_cst) == [0, 0, 1]


def test_build_classifier_omits_monotonic_when_not_passed():
    clf = build_hist_gradient_boosting_classifier(max_iter=25)
    assert clf.monotonic_cst is None
    assert clf.max_iter == 25


def test_fit_isotonic_calibrated_classifier_returns_calibrated_model():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(40, 3))
    y = (X[:, 0] > 0).astype(int)
    base = build_hist_gradient_boosting_classifier(max_iter=40, max_depth=2).fit(X, y)
    calibrated = fit_isotonic_calibrated_classifier(base, X, y)
    assert isinstance(calibrated, CalibratedClassifierCV)
    probs = calibrated.predict_proba(X)[:, 1]
    assert probs.shape == (40,)
    assert np.all((probs >= 0) & (probs <= 1))


def test_horizon_model_fit_calibrates_and_predict_is_monotone():
    config = ForecastConfig(horizons=(1, 7), lookback_days=20, train_days=60, cutoff_step=5)
    cutoffs = list(range(100, 180, 5))  # enough fit + val rows for calibration CV
    schedule = CutoffSchedule(cutoffs=cutoffs, val_count=6)
    train_df = _train_frame(config, cutoffs)
    model = HorizonModel(config, _FakeTraining(config)).fit(train_df, schedule)

    assert isinstance(model.classifier, CalibratedClassifierCV)
    infer_df = train_df.iloc[:3].copy()
    probs = model.predict(infer_df)
    assert probs.shape == (3, 2)
    assert np.all((probs >= 0) & (probs <= 1))
    assert np.all(np.diff(probs, axis=1) >= -1e-12)


def test_horizon_model_empty_val_fits_without_calibration(capsys):
    config = ForecastConfig(horizons=(1, 7), lookback_days=20, train_days=60, cutoff_step=5)
    # val_count >= len(cutoffs) => val_cutoffs is empty => no calibration path
    cutoffs = [100, 105, 110]
    schedule = CutoffSchedule(cutoffs=cutoffs, val_count=3)
    assert schedule.val_cutoffs == set()
    train_df = _train_frame(config, cutoffs)
    model = HorizonModel(config, _FakeTraining(config)).fit(train_df, schedule)

    assert isinstance(model.classifier, HistGradientBoostingClassifier)
    assert "val split empty" in capsys.readouterr().out
    probs = model.predict(train_df.iloc[:2].copy())
    assert probs.shape == (2, 2)
    assert np.all(np.diff(probs, axis=1) >= -1e-12)


def test_horizon_model_predict_before_fit_raises():
    config = ForecastConfig(horizons=(1, 7), lookback_days=20)
    model = HorizonModel(config, _FakeTraining(config))
    try:
        model.predict(pd.DataFrame([{name: 0.0 for name in FEATURE_NAMES}]))
    except PipelineError as exc:
        assert "before fit" in str(exc)
    else:
        raise AssertionError("expected PipelineError")
