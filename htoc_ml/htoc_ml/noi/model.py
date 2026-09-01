"""NOI multi-horizon forecast model (fit / calibrate / predict)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from htoc_ml.core.modeling import (
    build_hist_gradient_boosting_classifier,
    fit_isotonic_calibrated_classifier,
)
from htoc_ml.core.pipeline import PipelineError
from htoc_ml.noi.config import ForecastConfig
from htoc_ml.noi.dataset import TrainingSet
from htoc_ml.noi.schedule import CutoffSchedule


class HorizonModel:
    def __init__(self, config: ForecastConfig, training: TrainingSet) -> None:
        self.config = config
        self.training = training
        self.classifier = None

    def fit(self, train_df: pd.DataFrame, schedule: CutoffSchedule) -> "HorizonModel":
        val_cutoffs = schedule.val_cutoffs
        fit_df = train_df[~train_df["t"].isin(val_cutoffs)]
        val_df = train_df[train_df["t"].isin(val_cutoffs)]

        def fresh_classifier():
            return build_hist_gradient_boosting_classifier(
                max_depth=4,
                learning_rate=0.08,
                max_iter=400,
                l2_regularization=1.0,
                monotonic_constraints=self.training.monotonic_constraint_vector(),
            )

        try:
            if fit_df.empty or val_df.empty:
                print("WARN: val split empty; fitting weighted model on all cutoffs, no recalibration")
                Xtr, ytr, wtr = self.training.stack(train_df, with_weights=True)
                self.classifier = fresh_classifier().fit(Xtr, ytr, sample_weight=wtr)
                return self

            Xf, yf, wf = self.training.stack(fit_df, with_weights=True)
            base = fresh_classifier().fit(Xf, yf, sample_weight=wf)
            Xv, yv = self.training.stack(val_df)
            self.classifier = fit_isotonic_calibrated_classifier(base, Xv, yv)
            return self
        except PipelineError:
            raise
        except Exception as exc:
            raise PipelineError(f"model fit failed: {exc}") from exc

    def predict(self, infer_df: pd.DataFrame) -> np.ndarray:
        if self.classifier is None:
            raise PipelineError("HorizonModel.predict called before fit")
        Xinf, _ = self.training.stack(infer_df, with_label=False)
        n_horizons = len(self.config.horizons)
        n_rows = len(infer_df)
        probabilities = self.classifier.predict_proba(Xinf)[:, 1].reshape(n_horizons, n_rows).T
        if probabilities.shape != (n_rows, n_horizons):
            raise PipelineError(
                f"probability matrix shape {probabilities.shape} != {(n_rows, n_horizons)}"
            )
        if np.any((probabilities < 0) | (probabilities > 1)):
            raise PipelineError("predicted probabilities fell outside [0, 1]")
        probabilities = np.maximum.accumulate(probabilities, axis=1)
        if np.any(np.diff(probabilities, axis=1) < -1e-12):
            raise PipelineError("predicted probabilities decreased across horizons")
        return probabilities
