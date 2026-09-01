"""Rows, labels, and the horizon-stacked matrix for one monotone model."""
from __future__ import annotations

import numpy as np
import pandas as pd

from htoc_ml.core.day import Day, to_timestamp
from htoc_ml.core.observations import IndicatorIndex
from htoc_ml.noi.config import ForecastConfig
from htoc_ml.noi.features import FEATURE_NAMES, MONOTONIC_CONSTRAINTS, FeatureBuilder
from htoc_ml.noi.feed_health import FeedHealth


class TrainingSet:
    def __init__(
        self,
        config: ForecastConfig,
        feature_builder: FeatureBuilder,
        labels: IndicatorIndex,
        features: IndicatorIndex,
        health: FeedHealth,
    ) -> None:
        self.config = config
        self.feature_builder = feature_builder
        self.labels = labels
        self.features = features
        self.health = health

    def monotonic_constraint_vector(self) -> list[int]:
        return [MONOTONIC_CONSTRAINTS[name] for name in FEATURE_NAMES] + [1]

    def build_label_mask(self, cutoffs: list[Day], opdivs: list[str]) -> dict[tuple[str, int, int], bool]:
        usable: dict[tuple[str, int, int], bool] = {}
        for opdiv in opdivs:
            for cutoff_day in cutoffs:
                start = to_timestamp(cutoff_day).date()
                for horizon_days in self.config.horizons:
                    ok, _ = self.health.window_usable(
                        opdiv, start, to_timestamp(cutoff_day + horizon_days).date()
                    )
                    usable[(opdiv, cutoff_day, horizon_days)] = ok
        return usable

    def build_rows(self, cutoffs: list[Day], need_label: bool = True) -> pd.DataFrame:
        label_mask = self.build_label_mask(cutoffs, self.labels.opdivs()) if need_label else {}
        recs = []
        lookback = self.config.lookback_days
        label_lookup = self.labels.as_dict()
        feature_lookup = self.features.as_dict()
        for cutoff_day in cutoffs:
            for (opdiv, indicator), dates in label_lookup.items():
                feat_dates = feature_lookup.get((opdiv, indicator), dates)
                window_end = np.searchsorted(feat_dates, cutoff_day, side="right")
                window_start = np.searchsorted(feat_dates, cutoff_day - lookback + 1, side="left")
                if window_end - window_start == 0:
                    continue
                rec = self.feature_builder.featurize(feat_dates, cutoff_day)
                rec["opdiv"] = opdiv
                rec["indicator"] = indicator
                rec["t"] = cutoff_day
                if need_label:
                    for horizon_days in self.config.horizons:
                        rec[f"y_{horizon_days}"] = (
                            float(self.labels.seen_next(dates, cutoff_day, horizon_days))
                            if label_mask.get((opdiv, cutoff_day, horizon_days), True)
                            else np.nan
                        )
                recs.append(rec)
        return pd.DataFrame(recs)

    def stack(self, df: pd.DataFrame, with_label: bool = True, with_weights: bool = False):
        base = df[list(FEATURE_NAMES)].to_numpy(float)
        Xs, ys, ws = [], [], []
        for horizon_days in self.config.horizons:
            Xh = np.hstack([base, np.full((len(df), 1), horizon_days, float)])
            if not with_label:
                Xs.append(Xh)
                continue
            yh = df[f"y_{horizon_days}"].to_numpy(float)
            keep = ~np.isnan(yh)
            y = yh[keep].astype(int)
            Xs.append(Xh[keep])
            ys.append(y)
            if with_weights:
                ws.append(_balanced_group_weights(df["opdiv"].to_numpy()[keep], y))
        X = np.vstack(Xs)
        y = np.concatenate(ys) if with_label else None
        if with_label and with_weights:
            w = np.concatenate(ws)
            return X, y, w
        return X, y


def _balanced_group_weights(opdivs, y) -> np.ndarray:
    opdivs = np.asarray(opdivs)
    y = np.asarray(y).astype(int)
    w = np.ones(len(y), dtype=float)
    for group in np.unique(opdivs):
        mask = opdivs == group
        n = int(mask.sum())
        n_pos = int(y[mask].sum())
        n_neg = n - n_pos
        if n_pos == 0 or n_neg == 0:
            continue
        w[mask & (y == 1)] = n / (2.0 * n_pos)
        w[mask & (y == 0)] = n / (2.0 * n_neg)
    return w
