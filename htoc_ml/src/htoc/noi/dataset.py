"""Rows, labels, and the horizon-stacked matrix for one monotone model."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from htoc.core.day import Day, to_timestamp
from htoc.core.observations import IndicatorIndex
from htoc.noi.config import ForecastConfig
from htoc.noi.features import FEATURE_NAMES, MONOTONIC_CONSTRAINTS, featurize, featurize_window
from htoc.noi.feed_health import FeedHealth


class TrainingSet:
    def __init__(self, config: ForecastConfig, labels: IndicatorIndex, features: IndicatorIndex, health: FeedHealth) -> None:
        self.config = config
        self.labels = labels
        self.features = features
        self.health = health

    def monotonic_constraint_vector(self) -> list[int]:
        return [MONOTONIC_CONSTRAINTS[name] for name in FEATURE_NAMES] + [1]

    def build_label_mask(self, cutoffs: list[Day], opdivs: list[str]) -> dict[tuple[str, int, int], bool]:
        if not cutoffs or not opdivs:
            return {}

        min_date = to_timestamp(min(cutoffs)).date()
        max_date = to_timestamp(max(cutoffs) + max(self.config.horizons)).date()
        day_usable: dict[tuple[str, date], bool] = {}
        for opdiv in opdivs:
            cur = min_date
            while cur <= max_date:
                day_usable[(opdiv, cur)] = self.health.is_usable(opdiv, cur)
                cur += timedelta(days=1)

        usable: dict[tuple[str, int, int], bool] = {}
        for opdiv in opdivs:
            for cutoff_day in cutoffs:
                start = to_timestamp(cutoff_day).date()
                for horizon_days in self.config.horizons:
                    end = to_timestamp(cutoff_day + horizon_days).date()
                    ok = True
                    cur = start + timedelta(days=1)
                    while cur <= end:
                        if not day_usable.get((opdiv, cur), False):
                            ok = False
                            break
                        cur += timedelta(days=1)
                    usable[(opdiv, cutoff_day, horizon_days)] = ok
        return usable

    def build_rows(self, cutoffs: list[Day], need_label: bool = True) -> pd.DataFrame:
        label_mask = self.build_label_mask(cutoffs, self.labels.opdivs()) if need_label else {}
        recs = []
        lookback = self.config.lookback_days
        horizons = self.config.horizons
        label_lookup = self.labels.as_dict()
        feature_lookup = self.features.as_dict()
        for (opdiv, indicator), dates in label_lookup.items():
            feat_dates = feature_lookup.get((opdiv, indicator), dates)
            for cutoff_day in cutoffs:
                window_end = np.searchsorted(feat_dates, cutoff_day, side="right")
                window_start = np.searchsorted(feat_dates, cutoff_day - lookback + 1, side="left")
                if window_end - window_start == 0:
                    continue
                rec = featurize_window(
                    lookback, feat_dates[window_start:window_end], cutoff_day
                )
                rec["opdiv"] = opdiv
                rec["indicator"] = indicator
                rec["t"] = cutoff_day
                if need_label:
                    horizon_labels = self.labels.seen_next_horizons(dates, cutoff_day, horizons)
                    for horizon_days in horizons:
                        key = (opdiv, cutoff_day, horizon_days)
                        rec[f"y_{horizon_days}"] = (
                            float(horizon_labels[horizon_days])
                            if label_mask.get(key, True)
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
