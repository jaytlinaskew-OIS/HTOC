"""Catch-the-sightings band policy for NextObservedIndicator V4.

Target: maximize Recall-High vs All Positives (don't miss sightings).
Constraint: keep Precision-High at or above PREC_FLOOR so High flags stay trusted.

High stays at 0.80 by default. Per-OpDiv cuts below 0.80 are applied only where
settled balanced-model history still holds the precision floor. OpDivs already
under the floor (CDC, DHA, HHS, NIH at 1-day) are not cut further -- that is
noise without enough recovered sightings, and those positives live in Possibly
Active, which is the review queue.

Three jobs: 1-day High is the tomorrow page; 7-day High is the weekly board
(skip-day regulars); Possibly Active is human review, sorted by 1-day p. Do
not lower 1-day High to chase skip-day leftovers, and do not use a global 0.50
cut -- it flooded false positives.
"""
from __future__ import annotations

import os

import pandas as pd

PREC_FLOOR = 0.90
BAND_LOW_P = 0.20
BAND_LABELS = {"H": "Highly likely", "W": "Possibly active", "L": "Low confidence"}

HORIZONS = [1, 7, 14, 30, 45]
BAND_HIGH_P = {1: 0.80, 7: 0.80, 14: 0.80, 30: 0.80, 45: 0.80}

# Priced on OpDiv-balanced, isotonic-calibrated forecasts. Cut only where
# Precision still holds 90% on both the pooled window AND the latest settled
# day (Aug 28). OS 1-day is already under the floor at 0.80 on some days, so
# it is not cut. DHA 7-day 0.70 broke the floor on Aug 28 and was reverted.
# 14/30/45 stay at the default until those horizons have enough scored days.
BAND_HIGH_P_OPDIV = {
    "CMS":  {1: 0.65, 7: 0.65},
    "HRSA": {1: 0.75, 7: 0.70},
    "OS":   {7: 0.65},
    "FDA":  {7: 0.65},
    "HHS":  {7: 0.65},
    "NIH":  {7: 0.65},
    "VA":   {7: 0.70},
    "CDC":  {7: 0.70},
}

PROBNAME = {
    1: "Probability: 1-Day",
    7: "Probability: 7-Day",
    14: "Probability: 14-Day",
    30: "Probability: 30-Day",
    45: "Probability: 45-Day",
}
CONFNAME = {
    1: "Confidence: 1-Day",
    7: "Confidence: 7-Day",
    14: "Confidence: 14-Day",
    30: "Confidence: 30-Day",
    45: "Confidence: 45-Day",
}


def band_high(H, opdiv=None):
    """High-band probability cut for horizon H, optionally per OpDiv."""
    h = int(H)
    if opdiv is not None:
        by_h = BAND_HIGH_P_OPDIV.get(str(opdiv).strip().upper())
        if by_h and h in by_h:
            return float(by_h[h])
    if isinstance(BAND_HIGH_P, dict):
        return float(BAND_HIGH_P.get(h, 0.80))
    return float(BAND_HIGH_P)


def band(p, H, opdiv=None):
    try:
        p = float(p)
    except (TypeError, ValueError):
        return BAND_LABELS["W"]
    if p >= band_high(H, opdiv):
        return BAND_LABELS["H"]
    if p <= BAND_LOW_P:
        return BAND_LABELS["L"]
    return BAND_LABELS["W"]


def parse_prob_pct(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.rstrip("%")
    return pd.to_numeric(s, errors="coerce")


def reband_frame(df: pd.DataFrame, opdiv: str | None = None) -> pd.DataFrame:
    """Rewrite Confidence columns from Probability using the current policy."""
    out = df.copy()
    partners = (
        out["Partner"].astype(str).str.strip()
        if "Partner" in out.columns
        else None
    )
    for H in HORIZONS:
        pcol, ccol = PROBNAME[H], CONFNAME[H]
        if pcol not in out.columns or ccol not in out.columns:
            continue
        p = parse_prob_pct(out[pcol]) / 100.0
        if partners is not None:
            out[ccol] = [
                f"{H}-Day: {band(pi, H, op)}"
                for pi, op in zip(p, partners)
            ]
        else:
            out[ccol] = [f"{H}-Day: {band(pi, H, opdiv)}" for pi in p]
    return out


def possibly_active_review(df: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    """Rows in the abstain band, highest probability first -- the catch queue."""
    ccol = CONFNAME[horizon]
    pcol = PROBNAME[horizon]
    if ccol not in df.columns:
        return pd.DataFrame()
    tag = f"{horizon}-Day: "
    band_h = df[ccol].astype(str).str.replace(tag, "", regex=False).str.strip()
    review = df.loc[band_h.eq(BAND_LABELS["W"])].copy()
    if review.empty:
        return review
    if pcol in review.columns:
        review["_sort_p"] = parse_prob_pct(review[pcol])
        review = review.sort_values("_sort_p", ascending=False).drop(columns=["_sort_p"])
    keep = [
        c for c in (
            "Partner", "Indicator", "Observed Today",
            PROBNAME[1], CONFNAME[1], PROBNAME[7], CONFNAME[7],
            "Frequency (1d)", "Frequency (7d)", "Frequency (30d)", "Basis",
        )
        if c in review.columns
    ]
    return review[keep].reset_index(drop=True)


def reband_saved_outputs(save_root: str, date_str: str) -> list[str]:
    """Reband per-OpDiv CSVs and the consolidated daily report for one stamp."""
    touched: list[str] = []
    for name in os.listdir(save_root):
        sub = os.path.join(save_root, name)
        if not os.path.isdir(sub):
            continue
        fp = os.path.join(sub, f"{name}_output_{date_str}.csv")
        if not os.path.exists(fp):
            continue
        df = pd.read_csv(fp)
        pd.DataFrame(reband_frame(df, opdiv=name)).to_csv(fp, index=False)
        touched.append(fp)
    full_dir = os.path.join(save_root, "Full Daily Reports")
    full_fp = os.path.join(full_dir, f"full_daily_report_{date_str}.csv")
    if os.path.exists(full_fp):
        df = pd.read_csv(full_fp)
        pd.DataFrame(reband_frame(df)).to_csv(full_fp, index=False)
        touched.append(full_fp)
    return touched
