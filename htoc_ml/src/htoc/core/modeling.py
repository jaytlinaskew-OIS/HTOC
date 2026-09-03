"""Shared model builders. Pass hyperparameters at the call site per use case."""
from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator


def build_hist_gradient_boosting_classifier(*, max_depth: int = 4, learning_rate: float = 0.08, max_iter: int = 400, l2_regularization: float = 1.0, early_stopping: bool = False, random_state: int = 0, monotonic_constraints: Sequence[int] | None = None) -> HistGradientBoostingClassifier:
    """Return an unfitted ``HistGradientBoostingClassifier``."""
    kwargs: dict = {
        "max_depth": max_depth,
        "learning_rate": learning_rate,
        "max_iter": max_iter,
        "l2_regularization": l2_regularization,
        "early_stopping": early_stopping,
        "random_state": random_state,
    }
    if monotonic_constraints is not None:
        kwargs["monotonic_cst"] = list(monotonic_constraints)
    return HistGradientBoostingClassifier(**kwargs)


def fit_isotonic_calibrated_classifier(fitted_classifier: HistGradientBoostingClassifier, X_val, y_val) -> CalibratedClassifierCV:
    """Calibrate a fitted classifier on a holdout set (isotonic).

    Uses sklearn's frozen wrapper so the fitted classifier is not refit.
    Fold count is capped by holdout size so small validation sets still work.
    """
    y = np.asarray(y_val)
    n_samples = len(y)
    _, counts = np.unique(y, return_counts=True)
    n_splits = int(max(2, min(5, n_samples, int(counts.min()))))
    calibrated = CalibratedClassifierCV(
        FrozenEstimator(fitted_classifier),
        method="isotonic",
        cv=n_splits,
    )
    calibrated.fit(X_val, y_val)
    return calibrated
