"""NOI display schema, thresholds, and legend copy for the performance workbooks."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from htoc_ml.core.eval.metrics import MISSING_METRIC, NOT_APPLICABLE, NOT_SETTLED
from htoc_ml.core.eval.workbook import LegendSpec
from htoc_ml.noi.feed_health import SETTLE_DAYS

DATE_FMT = "%Y%m%d"
BACKFILL_MARKER_NAME = "backfilled_forecasts.txt"
BACKFILLED_NOTE = "forecast backfilled by as-of replay, not produced live"
PROVISIONAL_NOTE = "provisional - scored before the label window settled"

NOI_BAND_POSITIVE = "Highly likely"
NOI_BAND_NEGATIVE = "Low confidence"
NOI_BAND_ABSTAIN = "Possibly active"

HORIZON_FILE_LABELS = {1: "1day", 7: "7day", 14: "14day", 30: "30day", 45: "45day"}
EXCLUDE_FOLDERS = {
    "automation scripts",
    "Logs",
    "LogsBackup",
    "Full Daily Reports",
    "Performance",
    "Possibly Active Review",
    "Alerts",
}

PERF_COLUMNS = [
    "Evaluation Date",
    "Forecast Date",
    "Horizon (Days)",
    "Data Status",
    "Unique Indicators Scored",
    "Scored Pairs (Indicator-OpDiv)",
    "Decided (High + Low)",
    "Undecided (Possibly Active)",
    "Coverage (%)",
    "Actual Positives",
    "Actual Negatives",
    "Observed Positive Rate (%)",
    "Predicted High Count",
    "True Positives (High)",
    "False Positives (High)",
    "False Negatives (High)",
    "Precision - High (%)",
    "Recall - High vs All Positives (%)",
    "Recall - 7-Day High vs 1-Day Positives (%)",
    "Recall - 1-Day or 7-Day High vs All Positives (%)",
    "Accuracy - High (%)",
    "Recall - High (%)",
    "Predicted High Rate (%)",
    "Predicted Low Count",
    "True Negatives (Low)",
    "False Positives (Low)",
    "Negative Precision - Low (%)",
    "Predicted Low Rate (%)",
    "Possibly Active Count",
    "Possibly Active Ended High (Observed)",
    "Possibly Active Ended Low (Not Observed)",
    "Possibly Active Ended High Rate (%)",
    "Avg Prob - Possibly Active (%)",
    "Avg Prob - Possibly Active Ended High (%)",
    "Avg Prob - Possibly Active Ended Low (%)",
    "Possibly Active Observed already 7-Day High",
    "Accuracy (%)",
    "Specificity - True Negative Rate (%)",
    "Balanced Accuracy (%)",
    "F1 Score - High (%)",
    "Excluded OpDivs (Incomplete Labels)",
    "Excluded Pairs (Incomplete Labels)",
]

PERF_OPDIV_COLUMNS = [
    "Evaluation Date",
    "Forecast Date",
    "Horizon (Days)",
    "OpDiv",
    "Data Status",
    "Unique Indicators Scored",
    "Scored Pairs (Indicator-OpDiv)",
    "Decided (High + Low)",
    "Undecided (Possibly Active)",
    "Coverage (%)",
    "Actual Positives",
    "Actual Negatives",
    "Observed Positive Rate (%)",
    "Predicted High Count",
    "True Positives (High)",
    "False Positives (High)",
    "False Negatives (High)",
    "Precision - High (%)",
    "Recall - High vs All Positives (%)",
    "Recall - 7-Day High vs 1-Day Positives (%)",
    "Recall - 1-Day or 7-Day High vs All Positives (%)",
    "Accuracy - High (%)",
    "Recall - High (%)",
    "Predicted High Rate (%)",
    "Predicted Low Count",
    "True Negatives (Low)",
    "False Positives (Low)",
    "Negative Precision - Low (%)",
    "Predicted Low Rate (%)",
    "Possibly Active Count",
    "Possibly Active Ended High (Observed)",
    "Possibly Active Ended Low (Not Observed)",
    "Possibly Active Ended High Rate (%)",
    "Avg Prob - Possibly Active (%)",
    "Avg Prob - Possibly Active Ended High (%)",
    "Avg Prob - Possibly Active Ended Low (%)",
    "Possibly Active Observed already 7-Day High",
    "Accuracy (%)",
    "Specificity - True Negative Rate (%)",
    "Balanced Accuracy (%)",
    "F1 Score - High (%)",
]

RAW_COLUMNS = [
    "_raw_precision",
    "_raw_accuracy_high",
    "_raw_recall",
    "_raw_recall_all",
    "_raw_recall_7d",
    "_raw_recall_union",
    "_raw_neg_prec",
    "_raw_accuracy",
    "_raw_balanced_acc",
    "_raw_fn_all",
]

ZERO_ON_UNSCORED = frozenset({
    "Unique Indicators Scored",
    "Scored Pairs (Indicator-OpDiv)",
})

METRIC_TRAFFIC_LIGHTS = {
    "Precision - High (%)": (90.0, 85.0),
    "Recall - High vs All Positives (%)": (75.0, 60.0),
    "Recall - 7-Day High vs 1-Day Positives (%)": (85.0, 75.0),
    "Recall - 1-Day or 7-Day High vs All Positives (%)": (85.0, 75.0),
    "Accuracy - High (%)": (85.0, 70.0),
    "Negative Precision - Low (%)": (94.0, 90.0),
    "Accuracy (%)": (95.0, 90.0),
    "Specificity - True Negative Rate (%)": (95.0, 90.0),
    "Balanced Accuracy (%)": (88.0, 80.0),
    "Recall - High (%)": (85.0, 70.0),
    "F1 Score - High (%)": (90.0, 85.0),
    "Coverage (%)": (85.0, 75.0),
}

METRIC_DESCRIPTIONS = {
    "Precision - High (%)": (
        "Of indicators labeled Highly likely, the percent that were actually observed within the "
        "horizon. Correct High calls divided by all High calls.",
        "This is the noise floor, not the objective. Keep it at or above 90% so analysts still "
        "trust High flags. Do not maximize it: 100% precision with half the sightings missed is "
        "the wrong trade for a catch-the-sightings mission.",
    ),
    "Accuracy - High (%)": (
        "High-class accuracy: True Positives / (True Positives + False Positives + False Negatives). "
        "The Low band's true negatives are left out of the denominator entirely.",
        "This is the number to read instead of Accuracy (%) when judging the High band. Overall "
        "Accuracy is (TP + TN) / decided, and TN usually dwarfs everything else.",
    ),
    "Negative Precision - Low (%)": (
        "Of indicators labeled Low confidence, the percent that stayed unobserved within the horizon.",
        "Shows the Low band is trustworthy for deprioritization.",
    ),
    "Accuracy (%)": (
        "Overall correct rate on decided cases (High + Low bands only; Possibly active is excluded).",
        "Do not use this to judge High-band performance. Use Accuracy - High (%) for that.",
    ),
    "Specificity - True Negative Rate (%)": (
        "Of the indicators that did NOT recur, the percent correctly labeled Low confidence.",
        "The negative-class counterpart to Recall.",
    ),
    "Balanced Accuracy (%)": (
        "The average of Recall - High and Specificity, giving both classes equal weight.",
        "Accuracy is dominated by the larger Low band; Balanced Accuracy removes that free credit.",
    ),
    "Recall - High (%)": (
        "Of observed indicators that received a firm High or Low label, the percent labeled Highly likely.",
        "Does not count positives left in Possibly active. Use Recall - High vs All Positives (%) "
        "to judge missed sightings.",
    ),
    "Recall - High vs All Positives (%)": (
        "Of every indicator that was actually observed, the percent labeled Highly likely on this horizon.",
        "This is the 1-day High / tomorrow-page target. Precision is the floor; this is the number to raise.",
    ),
    "Recall - 7-Day High vs 1-Day Positives (%)": (
        "Of indicators actually observed the next day, the percent already Highly likely on the 7-day horizon.",
        "Skip-day / weekly-board metric. 1-day eval only; N/A on other horizons.",
    ),
    "Recall - 1-Day or 7-Day High vs All Positives (%)": (
        "Of next-day recurrences, the percent Highly likely on 1-day High OR 7-day High. 1-day eval only.",
        "On-the-board coverage: metronomes caught tomorrow plus skip-day regulars already flagged for the week.",
    ),
    "Possibly Active Observed already 7-Day High": (
        "Count of 1-day Possibly Active rows that were observed the next day and already Highly likely on 7-day.",
        "Leftover recurrences a 1-day High cut cannot take without breaking 90% precision.",
    ),
    "F1 Score - High (%)": (
        "Balance of Precision - High and Recall - High (decided-only recall; harmonic mean).",
        "Uses decided-only recall. Read Recall - High vs All Positives (%) instead.",
    ),
    "Coverage (%)": (
        "Percent of scored pairs placed in High or Low (not Possibly active).",
        "The complement is the Possibly Active abstain band.",
    ),
    "Possibly Active Ended High Rate (%)": (
        "Of Possibly active predictions, the percent that were later observed within the horizon.",
        "Leftover 1-day recurrences the High band did not take.",
    ),
    "Avg Prob - Possibly Active (%)": (
        "Average model probability for all Possibly active predictions.",
        "Shows where the middle band sits between Low and High thresholds.",
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
        "Count of distinct indicators scored on the forecast date.",
        "Volume context for other rates.",
    ),
    "Scored Pairs (Indicator-OpDiv)": (
        "Count of Indicator–OpDiv pairs scored.",
        "Denominator for most rates.",
    ),
    "Decided (High + Low)": (
        "Count of pairs in Highly likely or Low confidence.",
        "Sample size behind Accuracy, Precision, and Negative Precision.",
    ),
    "Undecided (Possibly Active)": (
        "Count of pairs left in the middle / abstain band.",
        "How much of the scored set is neither a firm High nor Low call.",
    ),
    "Excluded OpDivs (Incomplete Labels)": (
        "OpDivs dropped because their observation feed was missing, empty, or not yet settled.",
        "A missing label is not a negative label. Excluding them keeps the metrics honest.",
    ),
    "Excluded Pairs (Incomplete Labels)": (
        "Number of Indicator-OpDiv pairs removed from scoring by the exclusions above.",
        "Size of the blind spot.",
    ),
    "Data Status": (
        "Whether this OpDiv was scored on this date, and if not, why not.",
        "'Scored' means the metrics on the row are real. Anything else names the days that blocked scoring.",
    ),
    MISSING_METRIC: (
        "Placeholder meaning the ground truth for this window is genuinely absent.",
        "Does not fix itself: the upstream data has to be re-pulled, then the row corrected with a backfill.",
    ),
    NOT_SETTLED: (
        "Placeholder meaning the observations exist but the upstream job is still rewriting the file.",
        "These rows correct themselves once the day ages past the settle window.",
    ),
    NOT_APPLICABLE: (
        "Placeholder meaning the day was scored, but this metric has no population to measure.",
        "Blanked rather than shown as 100%, which would look like a perfect score for an untested day.",
    ),
}

LEGEND_INTRO = (
    "Mission: catch real indicator sightings without missing them, while keeping High flags "
    "trusted. The target metric for the tomorrow page is Recall - High vs All Positives (%). "
    "Precision - High is the floor (green at 90%), not a number to maximize. Do not lower "
    "1-day High to chase skip-day leftovers -- those are the 7-Day High coverage columns. "
    "Accuracy (%) is dominated by Low-band true negatives and is not a High-band signal. "
    "Three jobs: 1-day High = page for tomorrow; 7-day High = already on the weekly board; "
    "Possibly active = abstain (not a worklist). Bands: Highly likely = predicted positive, "
    "Low confidence = predicted negative, Possibly active = abstain."
)

LEGEND_OTHER_METRICS = (
    "Unique Indicators Scored",
    "Scored Pairs (Indicator-OpDiv)",
    "Decided (High + Low)",
    "Undecided (Possibly Active)",
    "Possibly Active Ended High Rate (%)",
    "Avg Prob - Possibly Active (%)",
    "Avg Prob - Possibly Active Ended High (%)",
    "Avg Prob - Possibly Active Ended Low (%)",
    "Possibly Active Observed already 7-Day High",
    "Excluded OpDivs (Incomplete Labels)",
    "Excluded Pairs (Incomplete Labels)",
    "Data Status",
    MISSING_METRIC,
    NOT_SETTLED,
    NOT_APPLICABLE,
)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    return float(raw) if raw else default


def _parse_horizons(raw: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class EvalConfig:
    save_root: str
    htoc_share_root: str
    obs_template: str
    horizons: tuple[int, ...] = (1, 7, 14, 30, 45)
    rolling_baseline_days: int = 14
    min_decided_count: int = 50
    high_prec_abs_min: float = 0.90
    high_prec_drop_pp_rolling: float = 0.05
    low_neg_prec_abs_min: float = 0.85
    low_neg_prec_drop_pp_rolling: float = 0.05
    recall_all_abs_min: float = 0.60
    recall_all_opdiv_abs_min: float = 0.50
    recall_all_drop_pp_rolling: float = 0.05
    coverage_lookback_days: int = 14
    coverage_alert_days: int = 3
    backfill_start: str = ""
    backfill_end: str = ""

    @property
    def daily_report_dir(self) -> Path:
        return Path(self.save_root) / "Full Daily Reports"

    @property
    def performance_dir(self) -> Path:
        return Path(self.save_root) / "Performance"

    @property
    def alerts_dir(self) -> Path:
        return self.performance_dir / "Alerts"

    @property
    def logs_dir(self) -> Path:
        return self.performance_dir / "Logs"

    def legend(self) -> LegendSpec:
        settle = SETTLE_DAYS
        footnotes = (
            f"Each daily run scores the evaluation date {settle} days back, not today. The upstream "
            "observation feed keeps rewriting each day's file for about two to three mornings, so scoring a "
            "day before it settles counts late-arriving observations as misses and understates precision by "
            "roughly 5 percentage points.",
            "Rows are upserted on (Evaluation Date, Forecast Date, Horizon). A row therefore gets rewritten "
            f"if a later run happens to score the same date -- which is why the {settle} most recent "
            "evaluation dates self-correct as the lag window catches up to them.",
            "IMPORTANT: rows older than the lag window are never revisited automatically. If you see old "
            "outliers that never corrected themselves, they were written by an earlier run against unsettled "
            "or broken data and can only be fixed by a backfill "
            "(set NOI_V4_PERF_BACKFILL_START / NOI_V4_PERF_BACKFILL_END and rerun).",
            "An OpDiv is dropped from a row when its observation feed was missing, empty, or unsettled "
            "anywhere in the label window -- see the two Excluded columns above. A missing label is not a "
            "negative label, so scoring through a feed outage would blame the model for a data problem.",
        )
        return LegendSpec(
            title="Performance workbook legend",
            intro=LEGEND_INTRO,
            traffic_lights=METRIC_TRAFFIC_LIGHTS,
            descriptions=METRIC_DESCRIPTIONS,
            other_metrics=LEGEND_OTHER_METRICS,
            footnotes=footnotes,
        )

    @classmethod
    def from_paths(cls, save_root: str, htoc_share_root: str, obs_template: str = "") -> "EvalConfig":
        share = (htoc_share_root or os.environ.get("HTOC_SHARE_ROOT", r"\\cscso1fsappv01\data\HTOC")).strip()
        template = obs_template or os.environ.get(
            "HTOC_OBS_TEMPLATE",
            str(Path(share) / r"Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"),
        )
        horizons_raw = os.environ.get("NOI_V4_EVAL_HORIZONS", "").strip()
        try:
            horizons = _parse_horizons(horizons_raw) if horizons_raw else (1, 7, 14, 30, 45)
        except ValueError:
            horizons = (1, 7, 14, 30, 45)
        return cls(
            save_root=save_root.strip(),
            htoc_share_root=share,
            obs_template=template,
            horizons=horizons or (1, 7, 14, 30, 45),
            rolling_baseline_days=_env_int("NOI_V4_PERF_ROLLING_BASELINE_DAYS", 14),
            min_decided_count=_env_int("NOI_V4_PERF_MIN_DECIDED_COUNT", 50),
            high_prec_abs_min=_env_float("NOI_V4_PERF_HIGH_PREC_ABS_MIN", 0.90),
            high_prec_drop_pp_rolling=_env_float("NOI_V4_PERF_HIGH_PREC_DROP_PP_ROLLING", 0.05),
            low_neg_prec_abs_min=_env_float("NOI_V4_PERF_LOW_NEG_PREC_ABS_MIN", 0.85),
            low_neg_prec_drop_pp_rolling=_env_float("NOI_V4_PERF_LOW_NEG_PREC_DROP_PP_ROLLING", 0.05),
            recall_all_abs_min=_env_float("NOI_V4_PERF_RECALL_ALL_ABS_MIN", 0.60),
            recall_all_opdiv_abs_min=_env_float("NOI_V4_PERF_RECALL_ALL_OPDIV_ABS_MIN", 0.50),
            recall_all_drop_pp_rolling=_env_float("NOI_V4_PERF_RECALL_ALL_DROP_PP_ROLLING", 0.05),
            coverage_lookback_days=_env_int("NOI_V4_PERF_COVERAGE_LOOKBACK_DAYS", 14),
            coverage_alert_days=_env_int("NOI_V4_PERF_COVERAGE_ALERT_DAYS", 3),
            backfill_start=os.environ.get("NOI_V4_PERF_BACKFILL_START", "").strip(),
            backfill_end=os.environ.get("NOI_V4_PERF_BACKFILL_END", "").strip(),
        )
