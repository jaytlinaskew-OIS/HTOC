"""One monotone HistGradientBoosting model across all horizons, then isotonic calibration."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier

from htoc_ml.noi.config import ForecastConfig
from htoc_ml.noi.dataset import TrainingSet
from htoc_ml.noi.schedule import CutoffSchedule


class HorizonModel:
    def __init__(self, config: ForecastConfig, training: TrainingSet) -> None:
        self.config = config
        self.training = training
        self.estimator = None

    def _new_estimator(self) -> HistGradientBoostingClassifier:
        return HistGradientBoostingClassifier(
            max_depth=4,
            learning_rate=0.08,
            max_iter=400,
            l2_regularization=1.0,
            monotonic_cst=self.training.monotonic_constraint_vector(),
            early_stopping=False,
            random_state=0,
        )

    def fit(self, train_df: pd.DataFrame, schedule: CutoffSchedule) -> "HorizonModel":
        val_cutoffs = schedule.val_cutoffs
        fit_df = train_df[~train_df["t"].isin(val_cutoffs)]
        val_df = train_df[train_df["t"].isin(val_cutoffs)]
        if fit_df.empty or val_df.empty:
            print("WARN: val split empty; fitting weighted model on all cutoffs, no recalibration")
            Xtr, ytr, wtr = self.training.stack(train_df, with_weights=True)
            self.estimator = self._new_estimator().fit(Xtr, ytr, sample_weight=wtr)
            return self
        Xf, yf, wf = self.training.stack(fit_df, with_weights=True)
        base = self._new_estimator().fit(Xf, yf, sample_weight=wf)
        Xv, yv = self.training.stack(val_df)
        self.estimator = CalibratedClassifierCV(base, method="isotonic", cv="prefit")
        self.estimator.fit(Xv, yv)
        print(
            f"trained OpDiv-balanced model on {len(fit_df):,} rows, "
            f"isotonic-calibrated on {len(val_df):,} later rows "
            f"(val pos rate {yv.mean() * 100:.1f}%, "
            f"mean predicted p {self.estimator.predict_proba(Xv)[:, 1].mean() * 100:.1f}%)"
        )
        return self

    def predict(self, infer_df: pd.DataFrame) -> np.ndarray:
        if self.estimator is None:
            raise RuntimeError("HorizonModel.predict called before fit")
        Xinf, _ = self.training.stack(infer_df, with_label=False)
        n_horizons = len(self.config.horizons)
        n_rows = len(infer_df)
        probabilities = self.estimator.predict_proba(Xinf)[:, 1].reshape(n_horizons, n_rows).T
        if probabilities.shape != (n_rows, n_horizons):
            raise RuntimeError(
                f"probability matrix shape {probabilities.shape} != {(n_rows, n_horizons)}"
            )
        if np.any((probabilities < 0) | (probabilities > 1)):
            raise RuntimeError("predicted probabilities fell outside [0, 1]")
        probabilities = np.maximum.accumulate(probabilities, axis=1)
        if np.any(np.diff(probabilities, axis=1) < -1e-12):
            raise RuntimeError("predicted probabilities decreased across horizons")
        return probabilities
