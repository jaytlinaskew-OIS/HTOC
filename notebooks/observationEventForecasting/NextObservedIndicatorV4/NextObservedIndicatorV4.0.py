r"""
NextObservedIndicatorV4.0 — scheduled runner (test outputs).

Source notebook: NextObservedIndicatorV4.0.ipynb
Writes per-OpDiv CSVs under:
  \\10.1.4.22\data\HTOC\JA\NextObserveV4Test\{OpDiv}\{OpDiv}_output_YYYYMMDD.csv

Does NOT replace the existing Next Observed Daily Reports scheduled tasks.

Exit contract:
  - print PIPELINE_OK and exit 0 on success
  - non-zero exit on hard failure
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import HistGradientBoostingClassifier

warnings.filterwarnings("ignore")

# ------------------------------- CONFIG -------------------------------
OBS_TEMPLATE = os.environ.get(
    "HTOC_OBS_TEMPLATE",
    r"\\10.1.4.22\data\HTOC\Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv",
)
DATE_FMT = "%Y%m%d"

L = 100
HORIZONS = [1, 7, 14, 30, 45]
TRAIN_DAYS = 220
CUTOFF_STEP = 7

BAND_HIGH_P = 0.80
BAND_LOW_P = 0.20
BAND_LABELS = {"H": "Highly likely", "W": "Possibly active", "L": "Low confidence"}

INFER_DATE = None
SAVE_OUTPUT = True

# cnt(k) features are computed inside an L-day window; keep horizons inside that window.
if max(HORIZONS) > L:
    print(f"FATAL: max(HORIZONS)={max(HORIZONS)} exceeds lookback L={L}; cnt(k) would undercount.")
    sys.exit(2)

EPOCH = np.datetime64("2020-01-01")


def _to_int(d):
    return (np.asarray(d, dtype="datetime64[D]") - EPOCH).astype(int)


def _to_ts(i):
    return pd.Timestamp(EPOCH + np.timedelta64(int(i), "D"))


def load_panel(days):
    """Load the daily 'seen' panel (indicator, opdiv, date) over the last `days` days."""
    today = datetime.today().date()
    start = today - timedelta(days=days)
    frames, d = [], start
    while d <= today:
        fp = OBS_TEMPLATE.format(date=d.strftime(DATE_FMT))
        if os.path.exists(fp):
            try:
                frames.append(pd.read_csv(fp, usecols=["indicator", "obs_date", "OpDiv"]))
            except Exception as e:
                print("skip", fp, e)
        d += timedelta(days=1)
    if not frames:
        print(
            f"FATAL: No observation files loaded for {start} -> {today} "
            f"(template={OBS_TEMPLATE}). Check share path / date coverage."
        )
        sys.exit(2)
    p = pd.concat(frames, ignore_index=True)
    p["indicator"] = p["indicator"].astype(str).str.strip()
    p["opdiv"] = p["OpDiv"].astype(str).str.strip()
    p["date"] = pd.to_datetime(p["obs_date"], errors="coerce").dt.normalize()
    p = p[["indicator", "opdiv", "date"]].dropna()
    p = p[p["indicator"].ne("nan") & p["indicator"].ne("")]
    p = p.drop_duplicates(["indicator", "opdiv", "date"])
    if p.empty:
        print("FATAL: Observation files were found, but the cleaned panel is empty.")
        sys.exit(2)
    p["d"] = _to_int(p["date"].values.astype("datetime64[D]"))
    return p


panel = load_panel(TRAIN_DAYS)
lookup = {}
for (opd, ind), g in panel.groupby(["opdiv", "indicator"], sort=False):
    lookup[(opd, ind)] = np.sort(g["d"].to_numpy())
DAY_MIN, DAY_MAX = int(panel["d"].min()), int(panel["d"].max())
print(
    f"panel: {len(panel):,} rows | {len(lookup):,} (opdiv,indicator) | "
    f"{_to_ts(DAY_MIN).date()} -> {_to_ts(DAY_MAX).date()}"
)

FEATS = [
    "last_seen", "freq_1", "freq_7", "freq_14", "freq_30", "freq_45", "freq_100",
    "avg_gap", "burstiness", "active_frac", "dow",
    "overdue", "mom", "tenure",
]


def featurize(dates, t):
    """Behavioral features from observations <= t. Leakage-safe."""
    hi = np.searchsorted(dates, t, side="right")
    lo = np.searchsorted(dates, t - L + 1, side="left")
    prior = dates[:hi]
    win = dates[lo:hi]
    tenure = int(t - prior[0]) if prior.size else L
    if win.size == 0:
        return [L, 0, 0, 0, 0, 0, 0, L, 0.0, 0.0, t % 7, 1.0, 0.0, tenure]

    def cnt(k):
        return int(win.size - np.searchsorted(win, t - k + 1, side="left"))

    gaps = np.diff(win)
    if gaps.size >= 1:
        ag = float(gaps.mean())
        sd = float(gaps.std())
        bu = (sd - ag) / (sd + ag) if (sd + ag) > 0 else 0.0
    else:
        ag, bu = float(L), 0.0
    last_seen = int(t - win[-1])
    overdue = last_seen / ag if ag > 0 else 0.0
    mom = cnt(7) / 7.0 - cnt(30) / 30.0
    return [
        last_seen, 1 if win[-1] == t else 0,
        cnt(7), cnt(14), cnt(30), cnt(45), win.size, ag, bu, win.size / L, t % 7,
        overdue, mom, tenure,
    ]


def seen_next(dates, t, H):
    """Forward label: 1 if observed on any day in (t, t+H]."""
    return 1 if np.searchsorted(dates, t + H, side="right") > np.searchsorted(dates, t + 1, side="left") else 0


def build_rows(cutoffs, need_label=True):
    """One row per (opdiv, indicator, cutoff) for indicators active within the lookback window."""
    recs = []
    for t in cutoffs:
        for (opd, ind), dates in lookup.items():
            hi = np.searchsorted(dates, t, side="right")
            lo = np.searchsorted(dates, t - L + 1, side="left")
            if hi - lo == 0:
                continue
            rec = dict(zip(FEATS, featurize(dates, t)))
            rec["opdiv"], rec["indicator"], rec["t"] = opd, ind, t
            if need_label:
                for H in HORIZONS:
                    rec[f"y_{H}"] = seen_next(dates, t, H)
            recs.append(rec)
    return pd.DataFrame(recs)


maxH = max(HORIZONS)
train_cutoffs = list(range(DAY_MIN + L, DAY_MAX - maxH + 1, CUTOFF_STEP))
if not train_cutoffs:
    print(
        f"FATAL: Not enough history for training cutoffs "
        f"(DAY_MIN={DAY_MIN}, DAY_MAX={DAY_MAX}, L={L}, maxH={maxH}). Increase TRAIN_DAYS."
    )
    sys.exit(2)

train_df = build_rows(train_cutoffs, need_label=True)
if train_df.empty:
    print("FATAL: Training frame is empty after feature build.")
    sys.exit(2)
print(
    f"training rows: {len(train_df):,} from {len(train_cutoffs)} cutoffs "
    f"({_to_ts(train_cutoffs[0]).date()} -> {_to_ts(train_cutoffs[-1]).date()})"
)


def stack(df, with_label=True):
    """Stack once per horizon, appending horizon as a feature -> ONE model for all horizons."""
    base = df[FEATS].to_numpy(float)
    Xs, ys = [], []
    for H in HORIZONS:
        Xs.append(np.hstack([base, np.full((len(df), 1), H, float)]))
        if with_label:
            ys.append(df[f"y_{H}"].to_numpy())
    return np.vstack(Xs), (np.concatenate(ys) if with_label else None)


mono = [0] * len(FEATS) + [1]


def new_model():
    return HistGradientBoostingClassifier(
        max_depth=4, learning_rate=0.08, max_iter=400, l2_regularization=1.0,
        monotonic_cst=mono, random_state=0,
    )


# Scheduled runner: train production model only.
# Notebook diagnostics (model_val / held-out band checks) are skipped here.
Xtr, ytr = stack(train_df)
model = new_model().fit(Xtr, ytr)
print("trained production model (all cutoffs)")

infer_t = DAY_MAX if INFER_DATE is None else int(_to_int(np.datetime64(pd.Timestamp(INFER_DATE).date())))
infer_df = build_rows([infer_t], need_label=False)
print(f"scoring {len(infer_df):,} indicators as-of {_to_ts(infer_t).date()}")
if infer_df.empty:
    print(f"FATAL: No candidate indicators to score as-of {_to_ts(infer_t).date()}.")
    sys.exit(3)

Xinf, _ = stack(infer_df, with_label=False)
P = model.predict_proba(Xinf)[:, 1].reshape(len(HORIZONS), len(infer_df)).T
P = np.maximum.accumulate(P, axis=1)


def band(p, H):
    if p >= BAND_HIGH_P:
        return BAND_LABELS["H"]
    if p <= BAND_LOW_P:
        return BAND_LABELS["L"]
    return BAND_LABELS["W"]


out = infer_df[["opdiv", "indicator", "freq_1", "freq_7", "freq_30"]].copy()
for j, H in enumerate(HORIZONS):
    out[f"prob_{H}"] = P[:, j]
    out[f"band_{H}"] = [band(p, H) for p in P[:, j]]

PROBNAME = {
    1: "Probability: 1-Day", 7: "Probability: 7-Day", 14: "Probability: 14-Day",
    30: "Probability: 30-Day", 45: "Probability: 45-Day",
}


def to_production(g):
    d = pd.DataFrame({
        "Indicator": g["indicator"].values,
        "Observed Today": (g["freq_1"].values > 0).astype(int),
        "Frequency (1d)": g["freq_1"].values,
        "Frequency (7d)": g["freq_7"].values,
        "Frequency (30d)": g["freq_30"].values,
    })
    for H in HORIZONS:
        d[PROBNAME[H]] = (g[f"prob_{H}"].values * 100).round(2).astype(str) + "%"
        d[f"Confidence: {H}-Day"] = [f"{H}-Day: {b}" for b in g[f"band_{H}"].values]
    cols = ["Indicator", "Observed Today", "Frequency (1d)", "Frequency (7d)", "Frequency (30d)"]
    for H in [1, 7, 14, 30]:
        cols += [f"Probability: {H}-Day", f"Confidence: {H}-Day"]
    cols += ["Probability: 45-Day", "Confidence: 45-Day"]
    return d[cols]


opdiv_outputs = {opd: to_production(g).reset_index(drop=True) for opd, g in out.groupby("opdiv")}
print("OpDivs:", list(opdiv_outputs.keys()))
if opdiv_outputs:
    print(opdiv_outputs[list(opdiv_outputs)[0]].head(10))

if not SAVE_OUTPUT:
    print("FATAL: SAVE_OUTPUT is False in scheduled runner")
    sys.exit(2)
if not opdiv_outputs:
    print("FATAL: no OpDiv outputs produced")
    sys.exit(3)

SAVE_DIR = os.environ.get(
    "NOI_V4_SAVE_DIR",
    r"\\10.1.4.22\data\HTOC\JA\NextObserveV4Test",
)
stamp = _to_ts(infer_t).strftime("%Y%m%d")
os.makedirs(SAVE_DIR, exist_ok=True)
for opd, df_out in opdiv_outputs.items():
    sub = os.path.join(SAVE_DIR, opd)
    os.makedirs(sub, exist_ok=True)
    df_out.to_csv(os.path.join(sub, f"{opd}_output_{stamp}.csv"), index=False)
print("saved to", SAVE_DIR)

missing = []
for opd in opdiv_outputs:
    fp = os.path.join(SAVE_DIR, opd, f"{opd}_output_{stamp}.csv")
    if not os.path.exists(fp):
        missing.append(fp)
if missing:
    print("FATAL: expected output files missing:")
    for fp in missing:
        print(" ", fp)
    sys.exit(4)

print(f"Wrote {len(opdiv_outputs)} OpDiv files under {SAVE_DIR}")
print("PIPELINE_OK")
sys.exit(0)
