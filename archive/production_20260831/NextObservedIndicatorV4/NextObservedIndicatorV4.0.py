r"""
NextObservedIndicatorV4.0 — scheduled runner (test outputs).

Source notebook: NextObservedIndicatorV4.0.ipynb
Writes per-OpDiv CSVs under:
  \\cscso1fsappv01\data\HTOC\JA\NextObserveV4Test\{OpDiv}\{OpDiv}_output_YYYYMMDD.csv

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
from sklearn.calibration import CalibratedClassifierCV

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from noi_v4_bands import PROBNAME, band  # noqa: E402
from noi_v4_feed_health import FeedHealth  # noqa: E402
from noi_v4_outage_impute import (  # noqa: E402
    OutageImputer,
    format_findings,
    format_report,
)

warnings.filterwarnings("ignore")

# ------------------------------- CONFIG -------------------------------
HTOC_SHARE_ROOT = os.environ.get("HTOC_SHARE_ROOT", r"\\cscso1fsappv01\data\HTOC")
OBS_TEMPLATE = os.environ.get(
    "HTOC_OBS_TEMPLATE",
    os.path.join(HTOC_SHARE_ROOT, r"Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"),
)
DATE_FMT = "%Y%m%d"

L = 100
HORIZONS = [1, 7, 14, 30, 45]
TRAIN_DAYS = 220
CUTOFF_STEP = 5  # must be coprime with 7 (see guard below)
VAL_TAIL_FRAC = 0.25  # later cutoffs used to recalibrate after class reweighting

# Catch-the-sightings: default High 0.80, per-OpDiv cuts only where Precision
# still holds 90%. Policy lives in noi_v4_bands. 0.50 globally flooded FPs.

INFER_DATE = None
SAVE_OUTPUT = True

# Historical replay. NOI_V4_AS_OF=YYYYMMDD reruns the pipeline as it would have
# run that morning, to fill a day the scheduled job missed.
#
# The leakage control is that everything downstream keys off the panel's last
# day: truncating the panel at the as-of date pulls DAY_MAX back with it, and
# train_cutoffs stops at DAY_MAX - maxH, so the model is fit only on label
# windows that had already closed by then. Nothing is trained on the future it
# is about to be scored against.
#
# One honest caveat remains. The observation files are read as they exist now,
# fully settled, whereas the real run that morning would have seen the last few
# days still filling. Features at the cutoff are therefore slightly better than
# they were in life, so a replayed day scores a little optimistically and is not
# strictly comparable to a live one. That is why replays are recorded in
# BACKFILL_MARKER and tagged in the performance sheets rather than passed off as
# ordinary rows.
AS_OF = os.environ.get("NOI_V4_AS_OF", "").strip()
AS_OF_DATE = datetime.strptime(AS_OF, "%Y%m%d").date() if AS_OF else None
if AS_OF_DATE:
    INFER_DATE = AS_OF_DATE.strftime("%Y-%m-%d")
    print(f"AS-OF REPLAY: rebuilding {AS_OF_DATE} using only data available then")

# cnt(k) features are computed inside an L-day window; keep horizons inside that window.
if max(HORIZONS) > L:
    print(f"FATAL: max(HORIZONS)={max(HORIZONS)} exceeds lookback L={L}; cnt(k) would undercount.")
    sys.exit(2)

# `dow` is no longer a feature (held-out permutation did not pay), but a step
# that is a multiple of 7 still locks every cutoff onto one weekday and aliases
# last_seen / gap structure. Any step coprime with 7 walks all seven weekdays.
if CUTOFF_STEP % 7 == 0:
    print(
        f"FATAL: CUTOFF_STEP={CUTOFF_STEP} is a multiple of 7; every training cutoff "
        f"would lock every cutoff onto one weekday and alias last_seen / gap structure."
    )
    sys.exit(2)

EPOCH = np.datetime64("2020-01-01")


def _to_int(d):
    return (np.asarray(d, dtype="datetime64[D]") - EPOCH).astype(int)


def _to_ts(i):
    return pd.Timestamp(EPOCH + np.timedelta64(int(i), "D"))


def load_panel(days, end_date=None):
    """Load the daily 'seen' panel (indicator, opdiv, date) over the last `days` days.

    `end_date` truncates the panel for an as-of replay; it is the single lever
    that keeps the rest of the pipeline from seeing past that day.
    """
    today = end_date or datetime.today().date()
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


panel = load_panel(TRAIN_DAYS, end_date=AS_OF_DATE)
lookup = {}
for (opd, ind), g in panel.groupby(["opdiv", "indicator"], sort=False):
    lookup[(opd, ind)] = np.sort(g["d"].to_numpy())
DAY_MIN, DAY_MAX = int(panel["d"].min()), int(panel["d"].max())
print(
    f"panel: {len(panel):,} rows | {len(lookup):,} (opdiv,indicator) | "
    f"{_to_ts(DAY_MIN).date()} -> {_to_ts(DAY_MAX).date()}"
)

# Built from the panel already in memory, so no observation file is read twice.
FEED_HEALTH = FeedHealth.from_panel(panel, today=AS_OF_DATE)
_health = FEED_HEALTH.summarize(
    sorted(panel["opdiv"].unique()), _to_ts(DAY_MAX - 30).date(), _to_ts(DAY_MAX).date()
)
_unhealthy = _health[(_health["outage"] > 0) | (_health["missing"] > 0) | (_health["degraded"] > 0)]
if _unhealthy.empty:
    print("feed health: all OpDivs nominal over the last 30 days")
else:
    print("feed health: issues over the last 30 days")
    for _, r in _unhealthy.iterrows():
        print(
            f"  {r['OpDiv']}: outage={r['outage']} degraded={r['degraded']} "
            f"missing={r['missing']} | {r['unusable_days']}"
        )

# A dark feed drags every one of its indicators toward "gone quiet", so an OpDiv
# mid-outage emits a confident all-clear rather than an obvious gap. Refilling
# its near-certain regulars keeps the forecast standing. LOOKUP_FEAT is for
# features only -- labels stay on `lookup`, because a label built from an
# assumption is the poisoning the health mask exists to stop.
IMPUTER = OutageImputer(panel, FEED_HEALTH)
LOOKUP_FEAT, _impute_report = IMPUTER.build(lookup)
if _impute_report:
    print("outage imputation:")
    for _line in format_report(_impute_report):
        print(_line)
else:
    print("outage imputation: no outages in the panel window")

# Retrospective, and deliberately so: while a feed is dark there is nothing to
# check it against. This fires on the first day back and catches the case where
# a feed returns at full volume having silently dropped part of its content.
_findings = IMPUTER.verify_recovery()
if _findings:
    print("WARNING: feed composition changed across an outage")
    for _line in format_findings(_findings):
        print(_line)

# Held-out permutation (31 Aug 2026): last_seen is ~73% of AUC drop; horizon,
# avg_gap, overdue, freq_100, burstiness, and the 7/14/30 windows pay rent.
# Dropped as dead or redundant with last_seen / freq_100: freq_1, freq_45,
# active_frac (exactly freq_100/L), dow, mom, tenure, weekday_hit, skip_gap_frac.
FEATS = [
    "last_seen", "freq_7", "freq_14", "freq_30", "freq_100",
    "avg_gap", "burstiness", "overdue",
]


def featurize(dates, t):
    """Behavioral features from observations <= t. Leakage-safe."""
    hi = np.searchsorted(dates, t, side="right")
    lo = np.searchsorted(dates, t - L + 1, side="left")
    win = dates[lo:hi]
    if win.size == 0:
        return [L, 0, 0, 0, 0, float(L), 0.0, 1.0]

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
    return [last_seen, cnt(7), cnt(14), cnt(30), win.size, ag, bu, overdue]


def seen_next(dates, t, H):
    """Forward label: 1 if observed on any day in (t, t+H]."""
    return 1 if np.searchsorted(dates, t + H, side="right") > np.searchsorted(dates, t + 1, side="left") else 0


def build_label_mask(cutoffs, opdivs):
    """Which (opdiv, cutoff, horizon) label windows rest on trustworthy data.

    seen_next() cannot tell "this indicator went quiet" from "the feed that
    would have reported it was down", so a label drawn from a window with an
    outage in it is not a negative -- it is a fabrication. Emitting those
    teaches the model that a whole OpDiv stopped recurring. The check is per
    OpDiv rather than per indicator, so it costs |opdivs| x |cutoffs| x
    |horizons| lookups regardless of panel size.
    """
    usable: dict[tuple[str, int, int], bool] = {}
    for opd in opdivs:
        for t in cutoffs:
            start = _to_ts(t).date()
            for H in HORIZONS:
                ok, _ = FEED_HEALTH.window_usable(opd, start, _to_ts(t + H).date())
                usable[(opd, t, H)] = ok
    return usable


def build_rows(cutoffs, need_label=True):
    """One row per (opdiv, indicator, cutoff) for indicators active within the lookback window.

    Two lookups, and the split is the point: features read LOOKUP_FEAT, which may
    contain imputed outage days, while labels read `lookup`, which never does.
    Keeping them separate structurally is what stops the pipeline from scoring
    itself against its own assumptions.
    """
    label_mask = build_label_mask(cutoffs, sorted({o for o, _ in lookup})) if need_label else {}
    recs = []
    for t in cutoffs:
        for (opd, ind), dates in lookup.items():
            feat_dates = LOOKUP_FEAT.get((opd, ind), dates)
            hi = np.searchsorted(feat_dates, t, side="right")
            lo = np.searchsorted(feat_dates, t - L + 1, side="left")
            if hi - lo == 0:
                continue
            rec = dict(zip(FEATS, featurize(feat_dates, t)))
            rec["opdiv"], rec["indicator"], rec["t"] = opd, ind, t
            if need_label:
                for H in HORIZONS:
                    # NaN marks "no trustworthy ground truth"; stack() drops
                    # these per horizon so they never reach the model.
                    rec[f"y_{H}"] = (
                        float(seen_next(dates, t, H))
                        if label_mask.get((opd, t, H), True)
                        else np.nan
                    )
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


def stack(df, with_label=True, with_weights=False):
    """Stack once per horizon, appending horizon as a feature -> ONE model for all horizons.

    Rows whose label was withheld by the feed-health mask carry NaN and are
    dropped for that horizon only; the same row can still train the horizons
    whose windows were clean.

    `with_weights` balances positives and negatives inside each OpDiv, per
    horizon slice. Global class_weight='balanced' is too weak: stacked labels
    sit near one-in-three positive, while DHA at 1-day is one-in-twenty-five.
    """
    base = df[FEATS].to_numpy(float)
    Xs, ys, ws = [], [], []
    dropped = 0
    for H in HORIZONS:
        Xh = np.hstack([base, np.full((len(df), 1), H, float)])
        if not with_label:
            Xs.append(Xh)
            continue
        yh = df[f"y_{H}"].to_numpy(float)
        keep = ~np.isnan(yh)
        dropped += int((~keep).sum())
        y = yh[keep].astype(int)
        Xs.append(Xh[keep])
        ys.append(y)
        if with_weights:
            ws.append(_balanced_group_weights(df["opdiv"].to_numpy()[keep], y))
    if with_label and dropped:
        total = len(df) * len(HORIZONS)
        print(
            f"feed-health mask withheld {dropped:,} of {total:,} training labels "
            f"({dropped / total * 100:.2f}%) -- windows containing a feed outage"
        )
    X = np.vstack(Xs)
    y = np.concatenate(ys) if with_label else None
    if with_label and with_weights:
        w = np.concatenate(ws)
        if y is not None and y.size:
            print(
                f"OpDiv-balanced sample weights: mean w(y=1)={w[y == 1].mean():.2f}  "
                f"mean w(y=0)={w[y == 0].mean():.2f}  "
                f"(unweighted pos rate {y.mean() * 100:.1f}%)"
            )
        return X, y, w
    return X, y


def _balanced_group_weights(opdivs, y):
    """n / (2 * n_class) inside each OpDiv so a 4% positive rate is not ignored."""
    opdivs = np.asarray(opdivs)
    y = np.asarray(y).astype(int)
    w = np.ones(len(y), dtype=float)
    for g in np.unique(opdivs):
        m = opdivs == g
        n = int(m.sum())
        n_pos = int(y[m].sum())
        n_neg = n - n_pos
        if n_pos == 0 or n_neg == 0:
            continue
        w[m & (y == 1)] = n / (2.0 * n_pos)
        w[m & (y == 0)] = n / (2.0 * n_neg)
    return w


mono = [0] * len(FEATS) + [1]


# early_stopping is OFF deliberately. sklearn's default ('auto') turns it on above
# 10k rows and holds out a RANDOM 10%, but stack() emits each (opdiv, indicator, t)
# once per horizon and cutoffs are only CUTOFF_STEP days apart, so a row's own
# near-duplicates end up on the training side of that split. The internal score is
# then optimistic and the stopping point is meaningless. Capacity is bounded by
# max_iter / max_depth / l2 instead, which also makes the tree count reproducible.
def new_model():
    return HistGradientBoostingClassifier(
        max_depth=4, learning_rate=0.08, max_iter=400, l2_regularization=1.0,
        monotonic_cst=mono, early_stopping=False, random_state=0,
    )


# Weighted training so rare-OpDiv positives are not ignored, then isotonic
# calibration on a later time split so p = 0.80 still means 80%. Random CV
# calibration is off-limits for the same reason early_stopping is: stacked
# near-duplicate rows would leak. Weights go on the earlier cutoffs only;
# the calibrator sees real unweighted frequencies.
n_val = max(1, int(len(train_cutoffs) * VAL_TAIL_FRAC))
val_cutoffs = set(train_cutoffs[-n_val:]) if len(train_cutoffs) > n_val else set()
fit_df = train_df[~train_df["t"].isin(val_cutoffs)]
val_df = train_df[train_df["t"].isin(val_cutoffs)]
if fit_df.empty or val_df.empty:
    print("WARN: val split empty; fitting weighted model on all cutoffs, no recalibration")
    Xtr, ytr, wtr = stack(train_df, with_weights=True)
    model = new_model().fit(Xtr, ytr, sample_weight=wtr)
else:
    Xf, yf, wf = stack(fit_df, with_weights=True)
    base = new_model().fit(Xf, yf, sample_weight=wf)
    Xv, yv = stack(val_df)
    model = CalibratedClassifierCV(base, method="isotonic", cv="prefit")
    model.fit(Xv, yv)
    print(
        f"trained OpDiv-balanced model on {len(fit_df):,} rows, "
        f"isotonic-calibrated on {len(val_df):,} later rows "
        f"(val pos rate {yv.mean() * 100:.1f}%, "
        f"mean predicted p {model.predict_proba(Xv)[:, 1].mean() * 100:.1f}%)"
    )

infer_t = DAY_MAX if INFER_DATE is None else int(_to_int(np.datetime64(pd.Timestamp(INFER_DATE).date())))
infer_df = build_rows([infer_t], need_label=False)
print(f"scoring {len(infer_df):,} indicators as-of {_to_ts(infer_t).date()}")
if infer_df.empty:
    print(f"FATAL: No candidate indicators to score as-of {_to_ts(infer_t).date()}.")
    sys.exit(3)

Xinf, _ = stack(infer_df, with_label=False)
P = model.predict_proba(Xinf)[:, 1].reshape(len(HORIZONS), len(infer_df)).T
P = np.maximum.accumulate(P, axis=1)


out = infer_df[["opdiv", "indicator", "last_seen", "freq_7", "freq_30"]].copy()
for j, H in enumerate(HORIZONS):
    out[f"prob_{H}"] = P[:, j]
    out[f"band_{H}"] = [band(p, H, opd) for p, opd in zip(P[:, j], out["opdiv"])]


def _really_seen(opd, ind, t):
    """Was this actually observed on `t`, ignoring anything imputed.

    last_seen on features may rest on a filled day; "Observed Today" is a
    statement of fact on a report someone reads, so it comes off the raw panel.
    """
    dates = lookup.get((opd, ind))
    if dates is None or not dates.size:
        return False
    i = np.searchsorted(dates, t, side="left")
    return bool(i < dates.size and dates[i] == t)


_imputed_pairs = IMPUTER.imputed_indicators(lookup, upto_di=infer_t)
out["observed_today"] = [
    _really_seen(o, i, infer_t) for o, i in zip(out["opdiv"], out["indicator"])
]
out["basis"] = [
    "est" if (o, i) in _imputed_pairs else ""
    for o, i in zip(out["opdiv"], out["indicator"])
]
if _imputed_pairs:
    print(
        f"forecast rests on imputed days for {int((out['basis'] == 'est').sum()):,} "
        f"indicators (marked 'est' in the Basis column)"
    )

def to_production(g):
    d = pd.DataFrame({
        "Indicator": g["indicator"].values,
        "Observed Today": g["observed_today"].values.astype(int),
        "Frequency (1d)": (g["last_seen"].values == 0).astype(int),
        "Frequency (7d)": g["freq_7"].values,
        "Frequency (30d)": g["freq_30"].values,
    })
    for H in HORIZONS:
        d[PROBNAME[H]] = (g[f"prob_{H}"].values * 100).round(2).astype(str) + "%"
        d[f"Confidence: {H}-Day"] = [f"{H}-Day: {b}" for b in g[f"band_{H}"].values]
    d["Basis"] = g["basis"].values
    cols = ["Indicator", "Observed Today", "Frequency (1d)", "Frequency (7d)", "Frequency (30d)"]
    for H in [1, 7, 14, 30]:
        cols += [f"Probability: {H}-Day", f"Confidence: {H}-Day"]
    cols += ["Probability: 45-Day", "Confidence: 45-Day", "Basis"]
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
    os.path.join(HTOC_SHARE_ROOT, r"JA\NextObserveV4Test"),
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

# A replayed day is indistinguishable from a live one once written, so record it
# here and let the eval tag the rows it produces. Without this the sheets would
# imply the scheduled job ran on days it did not.
BACKFILL_MARKER = os.path.join(SAVE_DIR, "backfilled_forecasts.txt")
if AS_OF_DATE:
    try:
        seen = set()
        if os.path.exists(BACKFILL_MARKER):
            with open(BACKFILL_MARKER, encoding="utf-8") as fh:
                seen = {ln.strip() for ln in fh if ln.strip()}
        if stamp not in seen:
            with open(BACKFILL_MARKER, "a", encoding="utf-8") as fh:
                fh.write(f"{stamp}\n")
        print(f"AS-OF REPLAY: recorded {stamp} in {BACKFILL_MARKER}")
    except Exception as e:
        print(f"WARN: could not record backfill marker: {e}")

# Performance evaluation (non-fatal — forecast outputs already saved)
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from noi_v4_performance_eval import run_eval_after_forecast  # noqa: E402

if not run_eval_after_forecast(
    stamp, SAVE_DIR, HTOC_SHARE_ROOT, consolidate_only=bool(AS_OF_DATE)
):
    print("PERF: evaluation completed with errors (see Performance/Logs on share)")

print("PIPELINE_OK")
sys.exit(0)
