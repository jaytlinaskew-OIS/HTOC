r"""
NextObservedIndicator V4 — performance evaluation module.

Evaluates forecast bands against observed outcomes and writes growing
Excel workbooks under {SAVE_ROOT}\Performance:
  - performance_1day.xlsx (overall + OpDiv sheets)
  - performance_7day.xlsx, etc.

Call init_performance_eval(save_root) before run_performance_evaluation().
"""

from __future__ import annotations

import os
import re
import sys
import traceback
from datetime import datetime, timedelta

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HTOC_SHARE_ROOT = os.environ.get("HTOC_SHARE_ROOT", r"\\cscso1fsappv01\data\HTOC").strip()
SAVE_ROOT = os.environ.get(
    "NOI_V4_SAVE_DIR",
    os.path.join(HTOC_SHARE_ROOT, r"JA\NextObserveV4Test"),
).strip()
DATA_PATH = SAVE_ROOT
SAVE_PATH = os.path.join(SAVE_ROOT, "Full Daily Reports")
PERF_DIR = os.path.join(SAVE_ROOT, "Performance")
PERF_ALERTS_DIR = os.path.join(PERF_DIR, "Alerts")
PERF_LOG_DIR = os.path.join(PERF_DIR, "Logs")
EXCLUDE_FOLDERS = {"automation scripts", "Logs", "LogsBackup", "Full Daily Reports",
                   "Performance"}


def _perf_log(message: str, level: str = "INFO") -> None:
    """Print and append to the daily performance log on the share."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[PERF {ts}] {level}: {message}"
    print(line, flush=True)
    try:
        os.makedirs(PERF_LOG_DIR, exist_ok=True)
        log_fp = os.path.join(PERF_LOG_DIR, f"perf_eval_{datetime.today().strftime('%Y%m%d')}.log")
        with open(log_fp, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as log_err:
        print(f"[PERF {ts}] WARNING: could not write perf log: {log_err}", flush=True)


def log_perf_error(context: str, exc: BaseException | None = None) -> None:
    """Log an eval error with full traceback to stdout and Performance/Logs."""
    if exc is None:
        tb = traceback.format_exc().strip()
        summary = context
    else:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
        summary = f"{context}: {exc}"
    _perf_log(summary, level="ERROR")
    if tb and tb != "NoneType: None":
        for tb_line in tb.splitlines():
            _perf_log(tb_line, level="ERROR")


def init_performance_eval(save_root: str, htoc_share_root: str | None = None) -> None:
    """Configure paths for evaluation (call once before running eval)."""
    global SAVE_ROOT, DATA_PATH, SAVE_PATH, PERF_DIR, PERF_ALERTS_DIR, PERF_LOG_DIR, OBS_TEMPLATE, HTOC_SHARE_ROOT
    SAVE_ROOT = save_root.strip()
    DATA_PATH = SAVE_ROOT
    SAVE_PATH = os.path.join(SAVE_ROOT, "Full Daily Reports")
    PERF_DIR = os.path.join(SAVE_ROOT, "Performance")
    PERF_ALERTS_DIR = os.path.join(PERF_DIR, "Alerts")
    PERF_LOG_DIR = os.path.join(PERF_DIR, "Logs")
    if htoc_share_root:
        HTOC_SHARE_ROOT = htoc_share_root.strip()
    OBS_TEMPLATE = os.environ.get(
        "HTOC_OBS_TEMPLATE",
        os.path.join(HTOC_SHARE_ROOT, r"Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"),
    )

V4_NAME = re.compile(r"^.+_output_(\d{8})\.csv$", re.IGNORECASE)
LEGACY_NAME = re.compile(r"^(\d{8})\.csv$", re.IGNORECASE)

OBS_TEMPLATE = os.environ.get(
    "HTOC_OBS_TEMPLATE",
    os.path.join(HTOC_SHARE_ROOT, r"Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"),
)
DATE_FMT = "%Y%m%d"
EVAL_HORIZONS = [1, 7, 14, 30, 45]
_horizons_override = os.environ.get("NOI_V4_EVAL_HORIZONS")
if _horizons_override:
    try:
        EVAL_HORIZONS = [int(x.strip()) for x in _horizons_override.split(",") if x.strip()]
    except Exception:
        _perf_log(
            f"could not parse NOI_V4_EVAL_HORIZONS={_horizons_override}; using default {EVAL_HORIZONS}",
            level="WARNING",
        )

ROLLING_BASELINE_DAYS = int(os.environ.get("NOI_V4_PERF_ROLLING_BASELINE_DAYS", "14"))
MIN_DECIDED_COUNT = int(os.environ.get("NOI_V4_PERF_MIN_DECIDED_COUNT", "50"))
HIGH_PREC_ABS_MIN = float(os.environ.get("NOI_V4_PERF_HIGH_PREC_ABS_MIN", "0.85"))
HIGH_PREC_DROP_PP_ROLLING = float(os.environ.get("NOI_V4_PERF_HIGH_PREC_DROP_PP_ROLLING", "0.05"))
HIGH_PREC_DROP_PP_DAY = float(os.environ.get("NOI_V4_PERF_HIGH_PREC_DROP_PP_DAY", "0.03"))
LOW_NEG_PREC_ABS_MIN = float(os.environ.get("NOI_V4_PERF_LOW_NEG_PREC_ABS_MIN", "0.85"))
LOW_NEG_PREC_DROP_PP_ROLLING = float(os.environ.get("NOI_V4_PERF_LOW_NEG_PREC_DROP_PP_ROLLING", "0.05"))
ACC_ABS_MIN = float(os.environ.get("NOI_V4_PERF_ACC_ABS_MIN", "0.80"))
ACC_DROP_PP_ROLLING = float(os.environ.get("NOI_V4_PERF_ACC_DROP_PP_ROLLING", "0.05"))
RECALL_ABS_MIN = float(os.environ.get("NOI_V4_PERF_RECALL_ABS_MIN", "0.60"))

# Traffic-light thresholds for percentage metric columns (stored as 0-100 floats).
# Tuple is (green_min, yellow_min): value >= green -> green; >= yellow -> yellow; else red.
METRIC_TRAFFIC_LIGHTS = {
    "Precision - High (%)": (94.0, 90.0),
    "Negative Precision - Low (%)": (94.0, 90.0),
    "Accuracy (%)": (95.0, 90.0),
    "Recall - High (%)": (85.0, 70.0),
    "Recall - High vs All Positives (%)": (75.0, 60.0),
    "F1 Score - High (%)": (90.0, 85.0),
    "Coverage (%)": (85.0, 75.0),
}

# Legend copy: what each measure is and why it matters.
METRIC_DESCRIPTIONS = {
    "Precision - High (%)": (
        "Of indicators labeled Highly likely, the percent that were actually observed within the horizon.",
        "Protects analysts from false alarms. Low precision means too many High predictions that never show up.",
    ),
    "Negative Precision - Low (%)": (
        "Of indicators labeled Low confidence, the percent that stayed unobserved within the horizon.",
        "Shows the Low band is trustworthy for deprioritization. Low values mean we are wrongly dismissing real activity.",
    ),
    "Accuracy (%)": (
        "Overall correct rate on decided cases (High + Low bands only; Possibly active is excluded).",
        "Quick health check for the model’s firm calls. Useful for day-to-day trend watching.",
    ),
    "Recall - High (%)": (
        "Of observed indicators that received a firm High or Low label (Possibly active excluded), "
        "the percent correctly labeled Highly likely. Denominator = High TP + positives wrongly labeled Low.",
        "Shows how often firm positives land in High vs Low. Does not penalize for positives left in Possibly active "
        "(those are tracked separately in Possibly Active Ended High).",
    ),
    "Recall - High vs All Positives (%)": (
        "Of all indicators that were actually observed (including those left in Possibly active), "
        "the percent correctly labeled Highly likely. Denominator = all actual positives.",
        "Standard/full recall. Lower than Recall - High when many true positives sit in the gray / Possibly active band.",
    ),
    "F1 Score - High (%)": (
        "Balance of Precision - High and Recall - High (decided-only recall; harmonic mean).",
        "Single score when you care about both avoiding false High alerts and not missing real observations among firm calls.",
    ),
    "Coverage (%)": (
        "Percent of scored pairs placed in High or Low (not Possibly active).",
        "Shows how decisive the model is. Very low coverage means most cases sit in the gray zone and need manual review.",
    ),
    "Possibly Active Ended High Rate (%)": (
        "Of Possibly active predictions, the percent that were later observed within the horizon.",
        "Describes the gray zone mix. A rising rate can mean more real activity is landing in the middle band instead of High.",
    ),
    "Avg Prob - Possibly Active (%)": (
        "Average model probability for all Possibly active predictions.",
        "Shows where the middle band sits between Low and High thresholds (typically ~20–80%).",
    ),
    "Avg Prob - Possibly Active Ended High (%)": (
        "Average probability among Possibly active cases that later became observed.",
        "If much higher than Ended Low, probability ranking inside the gray zone is informative.",
    ),
    "Avg Prob - Possibly Active Ended Low (%)": (
        "Average probability among Possibly active cases that stayed unobserved.",
        "Compare with Ended High average to see if mid-band probabilities separate outcomes.",
    ),
    "Unique Indicators Scored": (
        "Count of distinct indicators scored on the forecast date (100-day lookback set).",
        "Volume context for other rates; large swings can change precision/recall even if the model quality is stable.",
    ),
    "Scored Pairs (Indicator-OpDiv)": (
        "Count of Indicator–OpDiv pairs scored (one indicator can appear under multiple OpDivs).",
        "Denominator for most rates. Use this—not unique indicators—when interpreting pair-level precision/recall.",
    ),
    "Decided (High + Low)": (
        "Count of pairs in Highly likely or Low confidence (abstain / Possibly active excluded).",
        "Sample size behind Accuracy, Precision, and Negative Precision. Small n makes daily swings less reliable.",
    ),
    "Undecided (Possibly Active)": (
        "Count of pairs left in the middle / abstain band.",
        "Workload and uncertainty signal: how much of the scored set is neither a firm High nor Low call.",
    ),
}

FILL_GREEN = PatternFill(fill_type="solid", fgColor="C6EFCE")
FILL_YELLOW = PatternFill(fill_type="solid", fgColor="FFEB9C")
FILL_RED = PatternFill(fill_type="solid", fgColor="FFC7CE")
FONT_GREEN = Font(color="006100")
FONT_YELLOW = Font(color="9C5700")
FONT_RED = Font(color="9C0006")
FILL_HEADER = PatternFill(fill_type="solid", fgColor="D9E2F3")
FONT_HEADER = Font(bold=True)

# ---- Human-readable column definitions for the performance workbook ----
PERF_COLUMNS = [
    "Evaluation Date",
    "Forecast Date",
    "Horizon (Days)",
    "Unique Indicators Scored",
    "Scored Pairs (Indicator-OpDiv)",
    "Decided (High + Low)",
    "Undecided (Possibly Active)",
    "Coverage (%)",
    "Actual Positives",
    "Actual Negatives",
    "Observed Positive Rate (%)",
    # HIGH band
    "Predicted High Count",
    "True Positives (High)",
    "False Positives (High)",
    "False Negatives (High)",
    "Precision - High (%)",
    "Recall - High (%)",
    "Recall - High vs All Positives (%)",
    "Predicted High Rate (%)",
    # LOW band
    "Predicted Low Count",
    "True Negatives (Low)",
    "False Positives (Low)",
    "Negative Precision - Low (%)",
    "Predicted Low Rate (%)",
    # Possibly active band outcomes
    "Possibly Active Count",
    "Possibly Active Ended High (Observed)",
    "Possibly Active Ended Low (Not Observed)",
    "Possibly Active Ended High Rate (%)",
    "Avg Prob - Possibly Active (%)",
    "Avg Prob - Possibly Active Ended High (%)",
    "Avg Prob - Possibly Active Ended Low (%)",
    # Overall
    "Accuracy (%)",
    "F1 Score - High (%)",
]

PERF_OPDIV_COLUMNS = [
    "Evaluation Date",
    "Forecast Date",
    "Horizon (Days)",
    "OpDiv",
    "Unique Indicators Scored",
    "Scored Pairs (Indicator-OpDiv)",
    "Decided (High + Low)",
    "Undecided (Possibly Active)",
    "Coverage (%)",
    "Actual Positives",
    "Actual Negatives",
    "Observed Positive Rate (%)",
    # HIGH band
    "Predicted High Count",
    "True Positives (High)",
    "False Positives (High)",
    "False Negatives (High)",
    "Precision - High (%)",
    "Recall - High (%)",
    "Recall - High vs All Positives (%)",
    "Predicted High Rate (%)",
    # LOW band
    "Predicted Low Count",
    "True Negatives (Low)",
    "False Positives (Low)",
    "Negative Precision - Low (%)",
    "Predicted Low Rate (%)",
    # Possibly active band outcomes
    "Possibly Active Count",
    "Possibly Active Ended High (Observed)",
    "Possibly Active Ended Low (Not Observed)",
    "Possibly Active Ended High Rate (%)",
    "Avg Prob - Possibly Active (%)",
    "Avg Prob - Possibly Active Ended High (%)",
    "Avg Prob - Possibly Active Ended Low (%)",
    # Overall
    "Accuracy (%)",
    "F1 Score - High (%)",
]

_HORIZON_FILE_LABELS = {
    1: "1day", 7: "7day", 14: "14day", 30: "30day", 45: "45day",
}


def _pct(v: float) -> str:
    """Format a 0-1 ratio as a percentage string like '91.25%', or '' if NaN."""
    if pd.isna(v):
        return ""
    return f"{v * 100:.2f}%"


def _pct_f(v: float) -> float:
    """Round a 0-1 ratio to a percentage float like 91.25, or NaN."""
    if pd.isna(v):
        return float("nan")
    return round(v * 100, 2)


def _parse_prob_pct(series: pd.Series) -> pd.Series:
    """Parse '29.57%' / '29.57' / 0.2957 into a 0-100 percentage float series."""
    if series is None or series.empty:
        return pd.Series(dtype=float)
    s = series.astype(str).str.strip().str.replace("%", "", regex=False)
    vals = pd.to_numeric(s, errors="coerce")
    # If values look like 0-1 probabilities, convert to percent.
    if vals.notna().any() and float(vals.max(skipna=True)) <= 1.0:
        vals = vals * 100.0
    return vals


def _mean_prob(series: pd.Series) -> float:
    if series is None or len(series) == 0:
        return float("nan")
    if pd.api.types.is_numeric_dtype(series):
        vals = pd.to_numeric(series, errors="coerce")
    else:
        vals = _parse_prob_pct(series)
    if vals.notna().sum() == 0:
        return float("nan")
    return round(float(vals.mean()), 2)


def _build_metrics_row(
    *,
    eval_date_str: str,
    forecast_date_str: str,
    horizon_days: int,
    unique_indicators: int,
    total_pairs: int,
    high_n: int,
    high_tp: int,
    high_fp: int,
    low_n: int,
    low_tn: int,
    low_fp: int,
    actual_pos: int,
    actual_neg: int,
    poss_n: int = 0,
    poss_ended_high: int = 0,
    poss_ended_low: int = 0,
    avg_prob_poss: float = float("nan"),
    avg_prob_poss_high: float = float("nan"),
    avg_prob_poss_low: float = float("nan"),
    opdiv: str | None = None,
) -> dict:
    """Build one overall or OpDiv performance row with grouped HIGH/LOW/Possibly metrics."""
    decided = int(high_n + low_n)
    undecided = int(poss_n if poss_n else max(total_pairs - decided, 0))
    high_fn = int(low_fp)  # positives missed because labeled Low confidence
    # Standard FN vs all positives also includes Possibly active that became observed.
    high_fn_all = int(low_fp + poss_ended_high)

    precision = (high_tp / high_n) if high_n else float("nan")
    recall = (high_tp / (high_tp + high_fn)) if (high_tp + high_fn) else float("nan")
    recall_all = (high_tp / actual_pos) if actual_pos else float("nan")
    neg_prec = (low_tn / low_n) if low_n else float("nan")
    accuracy = ((high_tp + low_tn) / decided) if decided else float("nan")
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if pd.notna(precision) and pd.notna(recall) and (precision + recall) > 0
        else float("nan")
    )
    coverage = (decided / total_pairs) if total_pairs else float("nan")
    pred_high_rate = (high_n / total_pairs) if total_pairs else float("nan")
    obs_pos_rate = (actual_pos / total_pairs) if total_pairs else float("nan")
    pred_low_rate = (low_n / total_pairs) if total_pairs else float("nan")
    poss_high_rate = (poss_ended_high / undecided) if undecided else float("nan")

    row = {
        "Evaluation Date": eval_date_str,
        "Forecast Date": forecast_date_str,
        "Horizon (Days)": horizon_days,
        "Unique Indicators Scored": unique_indicators,
        "Scored Pairs (Indicator-OpDiv)": total_pairs,
        "Decided (High + Low)": decided,
        "Undecided (Possibly Active)": undecided,
        "Coverage (%)": _pct_f(coverage),
        "Actual Positives": actual_pos,
        "Actual Negatives": actual_neg,
        "Observed Positive Rate (%)": _pct_f(obs_pos_rate),
        "Predicted High Count": high_n,
        "True Positives (High)": high_tp,
        "False Positives (High)": high_fp,
        "False Negatives (High)": high_fn,
        "Precision - High (%)": _pct_f(precision),
        "Recall - High (%)": _pct_f(recall),
        "Recall - High vs All Positives (%)": _pct_f(recall_all),
        "Predicted High Rate (%)": _pct_f(pred_high_rate),
        "Predicted Low Count": low_n,
        "True Negatives (Low)": low_tn,
        "False Positives (Low)": low_fp,
        "Negative Precision - Low (%)": _pct_f(neg_prec),
        "Predicted Low Rate (%)": _pct_f(pred_low_rate),
        "Possibly Active Count": undecided,
        "Possibly Active Ended High (Observed)": int(poss_ended_high),
        "Possibly Active Ended Low (Not Observed)": int(poss_ended_low),
        "Possibly Active Ended High Rate (%)": _pct_f(poss_high_rate),
        "Avg Prob - Possibly Active (%)": avg_prob_poss,
        "Avg Prob - Possibly Active Ended High (%)": avg_prob_poss_high,
        "Avg Prob - Possibly Active Ended Low (%)": avg_prob_poss_low,
        "Accuracy (%)": _pct_f(accuracy),
        "F1 Score - High (%)": _pct_f(f1),
        "_raw_precision": precision,
        "_raw_recall": recall,
        "_raw_recall_all": recall_all,
        "_raw_neg_prec": neg_prec,
        "_raw_accuracy": accuracy,
        "_raw_fn_all": high_fn_all,
    }
    if opdiv is not None:
        row["OpDiv"] = opdiv
    return row


# ========================== data loading ==========================

def load_all_csvs_from_folders(
    root_path: str,
    today_only: bool = True,
    file_date: str | None = None,
) -> pd.DataFrame:
    all_dfs: list[pd.DataFrame] = []
    target_date = file_date or datetime.today().strftime("%Y%m%d")

    if not os.path.isdir(root_path):
        _perf_log(f"data root does not exist: {root_path}", level="WARNING")
        return pd.DataFrame()

    for dirpath, dirnames, filenames in os.walk(root_path):
        parts = set(os.path.normpath(dirpath).split(os.sep))
        if parts & EXCLUDE_FOLDERS:
            continue
        partner = os.path.basename(dirpath)
        for fname in filenames:
            m = V4_NAME.match(fname) or LEGACY_NAME.match(fname)
            if not m:
                continue
            found_date = m.group(1)
            if today_only and found_date != target_date:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                df = pd.read_csv(fpath)
                df["Partner"] = partner
                df["FileDate"] = file_date
                all_dfs.append(df)
                print(f"loaded {fpath} ({len(df)} rows)")
            except Exception as e:
                _perf_log(f"Skipping {fpath}: {e}", level="WARNING")

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    print("No CSV files found for today.")
    return pd.DataFrame()


def save_daily_report(df: pd.DataFrame, save_path: str, today_str: str) -> str:
    os.makedirs(save_path, exist_ok=True)
    output_path = os.path.join(save_path, f"full_daily_report_{today_str}.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path} ({len(df)} rows)")
    return output_path


def consolidate_daily_report(date_str: str | None = None) -> str | None:
    """Build full_daily_report_{date}.csv from per-OpDiv forecast CSVs."""
    date_str = date_str or datetime.today().strftime(DATE_FMT)
    daily_search = load_all_csvs_from_folders(DATA_PATH, today_only=True, file_date=date_str)
    if daily_search.empty:
        _perf_log(f"no OpDiv forecast files found for {date_str}; skip consolidate.", level="WARNING")
        return None
    try:
        return save_daily_report(daily_search, SAVE_PATH, date_str)
    except Exception as e:
        log_perf_error(f"consolidation failed for {date_str}", e)
        return None


# ========================== observation ground truth ==========================

def _load_observations_as_df(obs_date_str: str) -> pd.DataFrame:
    obs_fp = OBS_TEMPLATE.format(date=obs_date_str)
    if not os.path.exists(obs_fp):
        _perf_log(f"observation file missing for {obs_date_str}: {obs_fp}", level="WARNING")
        return pd.DataFrame(columns=["Indicator", "Partner", "Observed"])

    p = pd.read_csv(obs_fp, usecols=["indicator", "obs_date", "OpDiv"])
    p["Indicator"] = p["indicator"].astype(str).str.strip()
    p["Partner"] = p["OpDiv"].astype(str).str.strip()
    p["date"] = pd.to_datetime(p["obs_date"], errors="coerce").dt.normalize()
    p = p[p["Indicator"].ne("") & p["Indicator"].ne("nan") & p["Partner"].ne("") & p["Partner"].ne("nan")]
    if p.empty:
        return pd.DataFrame(columns=["Indicator", "Partner", "Observed"])

    eval_date = pd.to_datetime(obs_date_str, format=DATE_FMT, errors="coerce")
    if pd.notna(eval_date):
        p = p[p["date"] == eval_date]

    p = p.drop_duplicates(["Indicator", "Partner"])[["Indicator", "Partner"]]
    p["Observed"] = 1
    return p


def _load_observed_union_between(start_date_exclusive, end_date_inclusive) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    cur = start_date_exclusive + timedelta(days=1)
    while cur <= end_date_inclusive:
        dstr = cur.strftime(DATE_FMT)
        obs = _load_observations_as_df(dstr)
        if not obs.empty:
            frames.append(obs[["Indicator", "Partner"]])
        cur += timedelta(days=1)

    if not frames:
        return pd.DataFrame(columns=["Indicator", "Partner", "Observed"])

    out = pd.concat(frames, ignore_index=True).drop_duplicates(["Indicator", "Partner"])
    out["Observed"] = 1
    return out


# ========================== evaluation ==========================

def _evaluate_horizon(horizon_days: int, eval_date) -> dict | None:
    forecast_date = eval_date - timedelta(days=horizon_days)
    forecast_date_str = forecast_date.strftime(DATE_FMT)
    eval_date_str = eval_date.strftime(DATE_FMT)
    forecast_fp = os.path.join(SAVE_PATH, f"full_daily_report_{forecast_date_str}.csv")
    if not os.path.exists(forecast_fp):
        _perf_log(f"forecast daily report missing: {forecast_fp}", level="WARNING")
        return None

    df_pred = pd.read_csv(forecast_fp)

    conf_col = f"Confidence: {horizon_days}-Day"
    prob_col = f"Probability: {horizon_days}-Day"
    required_cols = {"Indicator", "Partner", conf_col}
    missing = required_cols - set(df_pred.columns)
    if missing:
        raise RuntimeError(f"PERF: missing columns in {forecast_fp}: {sorted(missing)}")

    df_obs = _load_observed_union_between(
        start_date_exclusive=forecast_date,
        end_date_inclusive=eval_date,
    )
    if df_obs.empty:
        _perf_log(
            "no observation ground-truth in window "
            f"({forecast_date_str}, {eval_date_str}] for H={horizon_days}; skipping eval.",
            level="WARNING",
        )
        return None

    df_pred["Indicator"] = df_pred["Indicator"].astype(str).str.strip()
    df_pred["Partner"] = df_pred["Partner"].astype(str).str.strip()
    df_scored = df_pred.merge(df_obs, on=["Indicator", "Partner"], how="left")
    df_scored["Observed"] = df_scored["Observed"].fillna(0).astype(int)

    tag_prefix = f"{horizon_days}-Day:"
    df_scored["band_h"] = (
        df_scored[conf_col]
        .astype(str)
        .str.replace(tag_prefix, "", regex=False)
        .str.strip()
    )
    if prob_col in df_scored.columns:
        df_scored["_prob_pct"] = _parse_prob_pct(df_scored[prob_col])
    else:
        df_scored["_prob_pct"] = float("nan")
        _perf_log(f"probability column missing: {prob_col}; avg probs will be blank", level="WARNING")

    total = int(len(df_scored))
    unique_indicators = int(df_scored["Indicator"].nunique())

    high = df_scored[df_scored["band_h"].eq("Highly likely")]
    high_n = len(high)
    high_tp = int(high["Observed"].sum()) if high_n else 0
    high_fp = int((high["Observed"] == 0).sum()) if high_n else 0

    low = df_scored[df_scored["band_h"].eq("Low confidence")]
    low_n = len(low)
    low_tn = int((low["Observed"] == 0).sum()) if low_n else 0
    low_fp = int((low["Observed"] == 1).sum()) if low_n else 0

    poss = df_scored[df_scored["band_h"].eq("Possibly active")]
    poss_n = len(poss)
    poss_ended_high = int(poss["Observed"].sum()) if poss_n else 0
    poss_ended_low = int((poss["Observed"] == 0).sum()) if poss_n else 0
    avg_prob_poss = _mean_prob(poss["_prob_pct"]) if poss_n else float("nan")
    avg_prob_poss_high = (
        _mean_prob(poss.loc[poss["Observed"] == 1, "_prob_pct"]) if poss_ended_high else float("nan")
    )
    avg_prob_poss_low = (
        _mean_prob(poss.loc[poss["Observed"] == 0, "_prob_pct"]) if poss_ended_low else float("nan")
    )

    actual_pos = int(df_scored["Observed"].sum())
    actual_neg = int(total - actual_pos)

    def _poss_stats(g: pd.DataFrame) -> tuple[int, int, int, float, float, float]:
        g_poss = g[g["band_h"].eq("Possibly active")]
        n = len(g_poss)
        ended_high = int(g_poss["Observed"].sum()) if n else 0
        ended_low = int((g_poss["Observed"] == 0).sum()) if n else 0
        avg_all = _mean_prob(g_poss["_prob_pct"]) if n else float("nan")
        avg_high = (
            _mean_prob(g_poss.loc[g_poss["Observed"] == 1, "_prob_pct"]) if ended_high else float("nan")
        )
        avg_low = (
            _mean_prob(g_poss.loc[g_poss["Observed"] == 0, "_prob_pct"]) if ended_low else float("nan")
        )
        return n, ended_high, ended_low, avg_all, avg_high, avg_low

    # Per-OpDiv (Partner) breakdown
    opdiv_rows: list[dict] = []
    for opdiv, g in df_scored.groupby("Partner"):
        g_total = int(len(g))
        g_high = g[g["band_h"].eq("Highly likely")]
        g_high_n = len(g_high)
        g_high_tp = int(g_high["Observed"].sum()) if g_high_n else 0
        g_high_fp = int((g_high["Observed"] == 0).sum()) if g_high_n else 0

        g_low = g[g["band_h"].eq("Low confidence")]
        g_low_n = len(g_low)
        g_low_tn = int((g_low["Observed"] == 0).sum()) if g_low_n else 0
        g_low_fp = int((g_low["Observed"] == 1).sum()) if g_low_n else 0

        g_poss_n, g_poss_hi, g_poss_lo, g_avg, g_avg_hi, g_avg_lo = _poss_stats(g)

        opdiv_rows.append(
            _build_metrics_row(
                eval_date_str=eval_date_str,
                forecast_date_str=forecast_date_str,
                horizon_days=horizon_days,
                unique_indicators=int(g["Indicator"].nunique()),
                total_pairs=g_total,
                high_n=g_high_n,
                high_tp=g_high_tp,
                high_fp=g_high_fp,
                low_n=g_low_n,
                low_tn=g_low_tn,
                low_fp=g_low_fp,
                actual_pos=int(g["Observed"].sum()),
                actual_neg=int(g_total - g["Observed"].sum()),
                poss_n=g_poss_n,
                poss_ended_high=g_poss_hi,
                poss_ended_low=g_poss_lo,
                avg_prob_poss=g_avg,
                avg_prob_poss_high=g_avg_hi,
                avg_prob_poss_low=g_avg_lo,
                opdiv=opdiv,
            )
        )

    overall = _build_metrics_row(
        eval_date_str=eval_date_str,
        forecast_date_str=forecast_date_str,
        horizon_days=horizon_days,
        unique_indicators=unique_indicators,
        total_pairs=total,
        high_n=high_n,
        high_tp=high_tp,
        high_fp=high_fp,
        low_n=low_n,
        low_tn=low_tn,
        low_fp=low_fp,
        actual_pos=actual_pos,
        actual_neg=actual_neg,
        poss_n=poss_n,
        poss_ended_high=poss_ended_high,
        poss_ended_low=poss_ended_low,
        avg_prob_poss=avg_prob_poss,
        avg_prob_poss_high=avg_prob_poss_high,
        avg_prob_poss_low=avg_prob_poss_low,
    )
    overall["_opdiv_rows"] = opdiv_rows
    return overall


def _print_summary(row: dict) -> None:
    h = row["Horizon (Days)"]
    print(
        f"PERF SUMMARY  Horizon={h}-Day  "
        f"Eval={row['Evaluation Date']}  Forecast={row['Forecast Date']}  "
        f"UniqueIndicators={row['Unique Indicators Scored']}  "
        f"Pairs={row['Scored Pairs (Indicator-OpDiv)']}  "
        f"Decided={row['Decided (High + Low)']}  "
        f"Coverage={row['Coverage (%)']}%"
    )
    print(
        f"  Accuracy={row['Accuracy (%)']}%  "
        f"Precision={row['Precision - High (%)']}%  "
        f"Recall(decided)={row['Recall - High (%)']}%  "
        f"Recall(all)={row['Recall - High vs All Positives (%)']}%  "
        f"F1={row['F1 Score - High (%)']}%"
    )
    print(
        f"  HIGH band: TP={row['True Positives (High)']}/{row['Predicted High Count']}  "
        f"FP={row['False Positives (High)']}  FN={row['False Negatives (High)']}"
    )
    print(
        f"  LOW  band: TN={row['True Negatives (Low)']}/{row['Predicted Low Count']}  "
        f"FP={row['False Positives (Low)']}  "
        f"Neg Precision={row['Negative Precision - Low (%)']}%"
    )
    print(
        f"  POSS band: n={row['Possibly Active Count']}  "
        f"EndedHigh={row['Possibly Active Ended High (Observed)']}  "
        f"EndedLow={row['Possibly Active Ended Low (Not Observed)']}  "
        f"EndedHighRate={row['Possibly Active Ended High Rate (%)']}%  "
        f"AvgProb={row['Avg Prob - Possibly Active (%)']}%  "
        f"(EndedHighAvg={row['Avg Prob - Possibly Active Ended High (%)']}%, "
        f"EndedLowAvg={row['Avg Prob - Possibly Active Ended Low (%)']}%)"
    )


# ========================== alerting ==========================

def _maybe_alert(perf_df: pd.DataFrame, row: dict) -> list[str]:
    h = int(row["Horizon (Days)"])
    precision = float(row["_raw_precision"])
    recall = float(row["_raw_recall"])
    neg_prec = float(row["_raw_neg_prec"])
    accuracy = float(row["_raw_accuracy"])
    decided = int(row["Decided (High + Low)"])
    low_n = int(row["Predicted Low Count"])

    if not perf_df.empty:
        prev = perf_df.iloc[-1]
        prev_prec = float(prev.get("_raw_precision", float("nan")))
        rolling = perf_df.tail(ROLLING_BASELINE_DAYS)
        roll_prec = float(rolling["_raw_precision"].mean())
        roll_neg = float(rolling["_raw_neg_prec"].mean())
        roll_acc = float(rolling["_raw_accuracy"].mean())
    else:
        prev_prec = float("nan")
        roll_prec = float("nan")
        roll_neg = float("nan")
        roll_acc = float("nan")

    alerts: list[str] = []

    if decided >= MIN_DECIDED_COUNT:
        if precision < HIGH_PREC_ABS_MIN:
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Precision dropped to {_pct(precision)} "
                f"(minimum standard: {_pct(HIGH_PREC_ABS_MIN)}, n={decided})"
            )
        if pd.notna(roll_prec) and precision < (roll_prec - HIGH_PREC_DROP_PP_ROLLING):
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Precision {_pct(precision)} fell below "
                f"{ROLLING_BASELINE_DAYS}-day rolling average {_pct(roll_prec)} "
                f"by more than {HIGH_PREC_DROP_PP_ROLLING*100:.0f}pp (n={decided})"
            )
        if pd.notna(prev_prec) and precision < (prev_prec - HIGH_PREC_DROP_PP_DAY):
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Precision dropped day-to-day from "
                f"{_pct(prev_prec)} to {_pct(precision)} "
                f"(>{HIGH_PREC_DROP_PP_DAY*100:.0f}pp drop, n={decided})"
            )
        if accuracy < ACC_ABS_MIN:
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Accuracy dropped to {_pct(accuracy)} "
                f"(minimum standard: {_pct(ACC_ABS_MIN)}, n={decided})"
            )
        if pd.notna(roll_acc) and accuracy < (roll_acc - ACC_DROP_PP_ROLLING):
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Accuracy {_pct(accuracy)} fell below "
                f"{ROLLING_BASELINE_DAYS}-day rolling average {_pct(roll_acc)} "
                f"by more than {ACC_DROP_PP_ROLLING*100:.0f}pp (n={decided})"
            )
        if recall < RECALL_ABS_MIN:
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Recall dropped to {_pct(recall)} "
                f"(minimum standard: {_pct(RECALL_ABS_MIN)}, n={decided})"
            )

    if low_n >= MIN_DECIDED_COUNT:
        if neg_prec < LOW_NEG_PREC_ABS_MIN:
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Low-band negative precision dropped to "
                f"{_pct(neg_prec)} (minimum standard: {_pct(LOW_NEG_PREC_ABS_MIN)}, n={low_n})"
            )
        if pd.notna(roll_neg) and neg_prec < (roll_neg - LOW_NEG_PREC_DROP_PP_ROLLING):
            alerts.append(
                f"PERFORMANCE_ALERT ({h}-Day): Low-band negative precision {_pct(neg_prec)} "
                f"fell below {ROLLING_BASELINE_DAYS}-day rolling average {_pct(roll_neg)} "
                f"by more than {LOW_NEG_PREC_DROP_PP_ROLLING*100:.0f}pp (n={low_n})"
            )

    return alerts


# ========================== persist + run loop ==========================

def _perf_file_name(horizon_days: int) -> str:
    label = _HORIZON_FILE_LABELS.get(horizon_days, f"{horizon_days}day")
    return f"performance_{label}.csv"


def _normalize_perf_history(df: pd.DataFrame) -> pd.DataFrame:
    """Map legacy column names when reloading workbook history."""
    if df.empty:
        return df
    if "Total Indicators Scored" in df.columns:
        if "Scored Pairs (Indicator-OpDiv)" not in df.columns:
            df = df.rename(columns={"Total Indicators Scored": "Scored Pairs (Indicator-OpDiv)"})
        else:
            df = df.drop(columns=["Total Indicators Scored"])
        if "Unique Indicators Scored" not in df.columns:
            df["Unique Indicators Scored"] = pd.NA
    if "False Negatives (Low)" in df.columns and "False Negatives (High)" not in df.columns:
        df = df.rename(columns={"False Negatives (Low)": "False Negatives (High)"})
    if "F1 Score (%)" in df.columns and "F1 Score - High (%)" not in df.columns:
        df = df.rename(columns={"F1 Score (%)": "F1 Score - High (%)"})
    return df


def _traffic_light_for_value(value, green_min: float, yellow_min: float):
    """Return (fill, font) for a metric value, or None if not colorable."""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v >= green_min:
        return FILL_GREEN, FONT_GREEN
    if v >= yellow_min:
        return FILL_YELLOW, FONT_YELLOW
    return FILL_RED, FONT_RED


def _apply_perf_sheet_formatting(ws) -> None:
    """Bold header, freeze pane, traffic-light color key metric cells."""
    if ws.max_row < 1 or ws.max_column < 1:
        return

    headers = {}
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(1, col)
        name = str(cell.value) if cell.value is not None else ""
        headers[name] = col
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.row_dimensions[1].height = 36

    for col_name, (green_min, yellow_min) in METRIC_TRAFFIC_LIGHTS.items():
        col_idx = headers.get(col_name)
        if not col_idx:
            continue
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row, col_idx)
            style = _traffic_light_for_value(cell.value, green_min, yellow_min)
            if style is None:
                continue
            fill, font = style
            cell.fill = fill
            cell.font = font

    # Reasonable column widths for readability
    for col in range(1, ws.max_column + 1):
        header = str(ws.cell(1, col).value or "")
        width = min(max(len(header) + 2, 12), 42)
        ws.column_dimensions[get_column_letter(col)].width = width


def _write_legend_sheet(wb) -> None:
    """Add/replace a Legend sheet explaining traffic lights and each measure."""
    if "Legend" in wb.sheetnames:
        del wb["Legend"]
    ws = wb.create_sheet("Legend", 0)

    ws["A1"] = "Performance workbook legend"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = (
        "Green / yellow / red highlighting applies to key percentage metrics on the overall and OpDiv sheets. "
        "Bands: Highly likely = predicted positive, Low confidence = predicted negative, "
        "Possibly active = abstain (not counted in Accuracy / Precision / Recall)."
    )
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 48

    ws["A4"] = "Color key"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = "Color"
    ws["B5"] = "Meaning"
    ws["C5"] = "Rule"
    for col in range(1, 4):
        ws.cell(5, col).fill = FILL_HEADER
        ws.cell(5, col).font = FONT_HEADER

    ws["A6"] = "Green"
    ws["A6"].fill = FILL_GREEN
    ws["A6"].font = FONT_GREEN
    ws["B6"] = "Good"
    ws["C6"] = "At or above the green threshold"

    ws["A7"] = "Yellow"
    ws["A7"].fill = FILL_YELLOW
    ws["A7"].font = FONT_YELLOW
    ws["B7"] = "Watch / middle"
    ws["C7"] = "At or above yellow, below green"

    ws["A8"] = "Red"
    ws["A8"].fill = FILL_RED
    ws["A8"].font = FONT_RED
    ws["B8"] = "Bad"
    ws["C8"] = "Below the yellow threshold"

    ws["A10"] = "Traffic-light metrics"
    ws["A10"].font = Font(bold=True, size=12)
    headers = [
        "Metric",
        "What it measures",
        "Why it matters",
        "Green >=",
        "Yellow >=",
        "Red <",
    ]
    for col, title in enumerate(headers, start=1):
        cell = ws.cell(11, col, title)
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    row = 12
    for metric, (green_min, yellow_min) in METRIC_TRAFFIC_LIGHTS.items():
        what, why = METRIC_DESCRIPTIONS.get(metric, ("", ""))
        ws.cell(row, 1, metric)
        ws.cell(row, 2, what).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row, 3, why).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row, 4, green_min)
        ws.cell(row, 5, yellow_min)
        ws.cell(row, 6, yellow_min)
        ws.row_dimensions[row].height = 60
        row += 1

    row += 1
    ws.cell(row, 1, "Other key measures (not traffic-lighted)")
    ws.cell(row, 1).font = Font(bold=True, size=12)
    row += 1
    other_headers = ["Metric", "What it measures", "Why it matters"]
    for col, title in enumerate(other_headers, start=1):
        cell = ws.cell(row, col, title)
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    row += 1

    other_metrics = [
        "Unique Indicators Scored",
        "Scored Pairs (Indicator-OpDiv)",
        "Decided (High + Low)",
        "Undecided (Possibly Active)",
        "Possibly Active Ended High Rate (%)",
        "Avg Prob - Possibly Active (%)",
        "Avg Prob - Possibly Active Ended High (%)",
        "Avg Prob - Possibly Active Ended Low (%)",
    ]
    for metric in other_metrics:
        what, why = METRIC_DESCRIPTIONS.get(metric, ("", ""))
        ws.cell(row, 1, metric)
        ws.cell(row, 2, what).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row, 3, why).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 48
        row += 1

    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 55
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 12
    ws.freeze_panes = "A12"


def _format_perf_workbook(wb) -> None:
    """Apply legend + traffic-light formatting to all data sheets."""
    _write_legend_sheet(wb)
    for name in wb.sheetnames:
        if name == "Legend":
            continue
        _apply_perf_sheet_formatting(wb[name])


def _horizon_workbook_path(horizon_days: int) -> str:
    label = _HORIZON_FILE_LABELS.get(horizon_days, f"{horizon_days}day")
    return os.path.join(PERF_DIR, f"performance_{label}.xlsx")

def _safe_sheet_name(name: str) -> str:
    # Excel sheet constraints: <=31 chars, no []:*?/\
    bad = "[]:*?/\\"
    for ch in bad:
        name = name.replace(ch, "_")
    return name[:31]


def _export_horizon_workbooks() -> None:
    """
    Exports one growing workbook per horizon.
    For each horizon workbook:
      - sheet 'overall' with day-by-day aggregate metrics
      - one sheet per OpDiv with that OpDiv's day-by-day metrics
    """
    # Workbook is now written directly in _run_eval_loop.
    return

    try:
        for horizon_days in EVAL_HORIZONS:
            label = _HORIZON_FILE_LABELS.get(horizon_days, f"{horizon_days}day")
            overall_fp = os.path.join(PERF_DIR, _perf_file_name(horizon_days))
            opdiv_fp = os.path.join(PERF_DIR, f"_tmp_performance_{label}_by_opdiv.csv")

            # Only create workbook when we have at least one source file.
            if not os.path.exists(overall_fp) and not os.path.exists(opdiv_fp):
                continue

            horizon_xlsx = os.path.join(PERF_DIR, f"performance_{label}.xlsx")
            with pd.ExcelWriter(horizon_xlsx) as writer:
                if os.path.exists(overall_fp):
                    df_overall = pd.read_csv(overall_fp)
                    if "Evaluation Date" in df_overall.columns:
                        df_overall = df_overall.sort_values("Evaluation Date")
                    df_overall.to_excel(writer, sheet_name="overall", index=False)

                if os.path.exists(opdiv_fp):
                    df_opdiv = pd.read_csv(opdiv_fp)
                    if "Evaluation Date" in df_opdiv.columns:
                        df_opdiv = df_opdiv.sort_values(["OpDiv", "Evaluation Date"])

                    if "OpDiv" in df_opdiv.columns:
                        for opdiv, g in df_opdiv.groupby("OpDiv", dropna=False):
                            sheet = _safe_sheet_name(str(opdiv) if pd.notna(opdiv) else "UNKNOWN")
                            g.to_excel(writer, sheet_name=sheet, index=False)
                    try:
                        os.remove(opdiv_fp)
                    except Exception:
                        pass
    except Exception as e:
        # Non-fatal: the pipeline is still useful with the CSVs.
        print(f"PERF: Excel export skipped (non-fatal): {e}")


def _run_eval_loop(eval_date, all_alerts: list[str]) -> int:
    """Evaluate all horizons for one eval date. Returns error count."""
    error_count = 0
    for horizon_days in EVAL_HORIZONS:
        try:
            row = _evaluate_horizon(horizon_days=horizon_days, eval_date=eval_date)
            if row is None:
                continue

            wb_path = _horizon_workbook_path(horizon_days)
            overall_hist = pd.DataFrame()
            opdiv_hist = pd.DataFrame()
            if os.path.exists(wb_path):
                try:
                    with pd.ExcelFile(wb_path) as xf:
                        if "overall" in xf.sheet_names:
                            overall_hist = _normalize_perf_history(
                                pd.read_excel(wb_path, sheet_name="overall")
                            )
                    opdiv_frames = []
                    for sn in xf.sheet_names:
                        if sn in {"overall", "Legend"}:
                            continue
                        d = _normalize_perf_history(pd.read_excel(wb_path, sheet_name=sn))
                        if "OpDiv" not in d.columns:
                            d["OpDiv"] = sn
                        opdiv_frames.append(d)
                        if opdiv_frames:
                            opdiv_hist = pd.concat(opdiv_frames, ignore_index=True)
                except Exception as e:
                    log_perf_error(f"could not read existing workbook {wb_path}; starting fresh", e)
                    overall_hist = pd.DataFrame()
                    opdiv_hist = pd.DataFrame()

            perf_df = overall_hist.copy()
            perf_df_new = pd.concat([overall_hist, pd.DataFrame([row])], ignore_index=True)
            save_cols = [c for c in PERF_COLUMNS if c in perf_df_new.columns]
            raw_cols = [c for c in perf_df_new.columns if c.startswith("_raw_")]
            dedupe_keys = [k for k in ["Evaluation Date", "Forecast Date", "Horizon (Days)"] if k in perf_df_new.columns]
            for k in dedupe_keys:
                perf_df_new[k] = perf_df_new[k].astype(str).str.strip()
            if dedupe_keys:
                perf_df_new = perf_df_new.drop_duplicates(subset=dedupe_keys, keep="last")
            if "Evaluation Date" in perf_df_new.columns:
                perf_df_new = perf_df_new.assign(
                    _sort_eval_date=perf_df_new["Evaluation Date"].astype(str).str.strip()
                ).sort_values("_sort_eval_date").drop(columns=["_sort_eval_date"])
            perf_df_new = perf_df_new.reindex(columns=save_cols + raw_cols)

            _print_summary(row)

            alerts = _maybe_alert(perf_df, row)
            if alerts:
                for line in alerts:
                    print(line)
                all_alerts.extend(alerts)

            opdiv_rows = row.get("_opdiv_rows", [])
            opdiv_df_new = opdiv_hist.copy()
            if opdiv_rows:
                opdiv_df_new = pd.concat([opdiv_df_new, pd.DataFrame(opdiv_rows)], ignore_index=True)
                save_cols = [c for c in PERF_OPDIV_COLUMNS if c in opdiv_df_new.columns]
                raw_cols = [c for c in opdiv_df_new.columns if c.startswith("_raw_")]
                dedupe_keys = [k for k in ["Evaluation Date", "Forecast Date", "Horizon (Days)", "OpDiv"] if k in opdiv_df_new.columns]
                for k in dedupe_keys:
                    opdiv_df_new[k] = opdiv_df_new[k].astype(str).str.strip()
                if dedupe_keys:
                    opdiv_df_new = opdiv_df_new.drop_duplicates(subset=dedupe_keys, keep="last")
                if {"OpDiv", "Evaluation Date"}.issubset(set(opdiv_df_new.columns)):
                    opdiv_df_new = opdiv_df_new.assign(
                        _sort_eval_date=opdiv_df_new["Evaluation Date"].astype(str).str.strip()
                    ).sort_values(["OpDiv", "_sort_eval_date"]).drop(columns=["_sort_eval_date"])
                opdiv_df_new = opdiv_df_new.reindex(columns=save_cols + raw_cols)

            with pd.ExcelWriter(wb_path, engine="openpyxl") as writer:
                perf_df_new.to_excel(writer, sheet_name="overall", index=False)
                if not opdiv_df_new.empty and "OpDiv" in opdiv_df_new.columns:
                    for opdiv, g in opdiv_df_new.groupby("OpDiv", dropna=False):
                        sheet = _safe_sheet_name(str(opdiv) if pd.notna(opdiv) else "UNKNOWN")
                        g.to_excel(writer, sheet_name=sheet, index=False)
                _format_perf_workbook(writer.book)
        except Exception as e:
            log_perf_error(
                f"{horizon_days}-day horizon failed for eval_date={eval_date.strftime(DATE_FMT)}",
                e,
            )
            error_count += 1
    return error_count


def run_performance_evaluation(eval_date=None) -> bool:
    """
    Evaluate all configured horizons for eval_date (default today).
    Supports backfill via NOI_V4_PERF_BACKFILL_START / END env vars.

    Returns True when no errors occurred; False if any horizon/day failed.
    Never raises — all failures are logged to stdout and Performance/Logs.
    """
    total_errors = 0
    today_str = datetime.today().strftime(DATE_FMT)
    try:
        os.makedirs(PERF_DIR, exist_ok=True)
        os.makedirs(PERF_ALERTS_DIR, exist_ok=True)
        os.makedirs(PERF_LOG_DIR, exist_ok=True)
        _perf_log("starting performance evaluation")

        backfill_start_str = os.environ.get("NOI_V4_PERF_BACKFILL_START")
        backfill_end_str = os.environ.get("NOI_V4_PERF_BACKFILL_END")
        if backfill_start_str:
            backfill_start_str = backfill_start_str.strip()
        if backfill_end_str:
            backfill_end_str = backfill_end_str.strip()

        if backfill_start_str and backfill_end_str:
            start_date = datetime.strptime(backfill_start_str, DATE_FMT).date()
            end_date = datetime.strptime(backfill_end_str, DATE_FMT).date()
            if end_date < start_date:
                raise RuntimeError("NOI_V4_PERF_BACKFILL_END must be >= NOI_V4_PERF_BACKFILL_START")
            cur = start_date
            while cur <= end_date:
                all_alerts: list[str] = []
                try:
                    total_errors += _run_eval_loop(eval_date=cur, all_alerts=all_alerts)
                    if all_alerts:
                        alert_fp = os.path.join(PERF_ALERTS_DIR, f"alert_{cur.strftime(DATE_FMT)}.txt")
                        with open(alert_fp, "w", encoding="utf-8") as f:
                            for line in all_alerts:
                                f.write(line + "\n")
                except Exception as e:
                    log_perf_error(f"backfill day {cur.strftime(DATE_FMT)} failed", e)
                    total_errors += 1
                cur += timedelta(days=1)
        else:
            if eval_date is None:
                eval_date = datetime.today().date()
            all_alerts: list[str] = []
            total_errors += _run_eval_loop(eval_date=eval_date, all_alerts=all_alerts)
            if all_alerts:
                alert_fp = os.path.join(PERF_ALERTS_DIR, f"alert_{today_str}.txt")
                with open(alert_fp, "w", encoding="utf-8") as f:
                    for line in all_alerts:
                        f.write(line + "\n")
                _perf_log(f"wrote metric alerts to {alert_fp}")

        if total_errors:
            _perf_log(f"evaluation finished with {total_errors} error(s)", level="WARNING")
            return False
        _perf_log("evaluation finished successfully")
        return True
    except Exception as e:
        log_perf_error("performance evaluation aborted", e)
        return False


def run_eval_after_forecast(stamp: str, save_dir: str, htoc_share_root: str | None = None) -> bool:
    """
    Consolidate today's forecasts and run evaluation.
    Non-fatal wrapper for the forecast scheduled task; logs all issues.
    """
    try:
        init_performance_eval(save_dir, htoc_share_root)
        _perf_log(f"starting post-forecast evaluation (stamp={stamp})")
        out = consolidate_daily_report(stamp)
        if out is None:
            _perf_log(f"consolidation produced no report for stamp={stamp}", level="WARNING")
        else:
            _perf_log(f"consolidated daily report: {out}")
        return run_performance_evaluation()
    except Exception as e:
        log_perf_error("post-forecast evaluation failed (non-fatal)", e)
        return False
