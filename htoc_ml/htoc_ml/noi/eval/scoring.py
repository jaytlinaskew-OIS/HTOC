"""Join NOI forecasts to observed outcomes and emit workbook rows."""
from __future__ import annotations

import pandas as pd

from htoc_ml.core.eval.metrics import (
    NOT_APPLICABLE,
    BandSpec,
    count_bands,
    parse_probability_percent,
    percent_or_sentinel,
    rates_from_counts,
)
from htoc_ml.noi.eval.config import (
    BACKFILLED_NOTE,
    NOI_BAND_ABSTAIN,
    NOI_BAND_NEGATIVE,
    NOI_BAND_POSITIVE,
    PERF_COLUMNS,
    PERF_OPDIV_COLUMNS,
    PROVISIONAL_NOTE,
    RAW_COLUMNS,
    ZERO_ON_UNSCORED,
)
from htoc_ml.noi.feed_health import UNSETTLED, statuses_in

NOI_BANDS = BandSpec(
    positive_name=NOI_BAND_POSITIVE,
    negative_name=NOI_BAND_NEGATIVE,
    abstain_name=NOI_BAND_ABSTAIN,
)


def week_horizon_coverage(frame: pd.DataFrame, horizon_days: int) -> dict:
    na = NOT_APPLICABLE
    out = {
        "recall_7d": na,
        "recall_union": na,
        "pa_obs_7d_high": na,
        "_raw_recall_7d": float("nan"),
        "_raw_recall_union": float("nan"),
    }
    if int(horizon_days) != 1 or frame is None or frame.empty or "band_7" not in frame.columns:
        return out
    if frame["band_7"].eq("").all():
        return out
    pos = frame["Observed"] == 1
    n_pos = int(pos.sum())
    if n_pos == 0:
        out["pa_obs_7d_high"] = 0
        return out
    high7 = frame["band_7"].eq(NOI_BAND_POSITIVE)
    high1 = frame["band_h"].eq(NOI_BAND_POSITIVE)
    rec7 = float((high7 & pos).sum() / n_pos)
    rec_u = float(((high1 | high7) & pos).sum() / n_pos)
    pa_hi7 = int((frame["band_h"].eq(NOI_BAND_ABSTAIN) & pos & high7).sum())
    out["recall_7d"] = round(rec7 * 100, 2)
    out["recall_union"] = round(rec_u * 100, 2)
    out["pa_obs_7d_high"] = pa_hi7
    out["_raw_recall_7d"] = rec7
    out["_raw_recall_union"] = rec_u
    return out


def sentinel_for_reasons(reasons) -> str:
    from htoc_ml.core.eval.metrics import MISSING_METRIC, NOT_SETTLED

    statuses = statuses_in(reasons)
    if statuses and statuses <= {UNSETTLED}:
        return NOT_SETTLED
    return MISSING_METRIC


def unscorable_row(columns: list[str], base: dict, sentinel: str) -> dict:
    row = dict(base)
    for col in columns:
        if col not in row:
            row[col] = 0 if col in ZERO_ON_UNSCORED else sentinel
    for raw in RAW_COLUMNS:
        row.setdefault(raw, float("nan"))
    return row


def excluded_opdiv_row(
    *,
    eval_date_str: str,
    forecast_date_str: str,
    horizon_days: int,
    opdiv: str,
    unique_indicators: int,
    total_pairs: int,
    reasons: list[str],
) -> dict:
    return unscorable_row(
        PERF_OPDIV_COLUMNS,
        {
            "Evaluation Date": eval_date_str,
            "Forecast Date": forecast_date_str,
            "Horizon (Days)": horizon_days,
            "OpDiv": opdiv,
            "Data Status": (
                f"Not scored - {total_pairs:,} pairs / {unique_indicators:,} indicators "
                f"withheld: {'; '.join(reasons[:4])}"
            ),
        },
        sentinel_for_reasons(reasons),
    )


def metrics_row(
    *,
    eval_date_str: str,
    forecast_date_str: str,
    horizon_days: int,
    counts,
    rates,
    week_cov: dict | None = None,
    opdiv: str | None = None,
) -> dict:
    week = week_cov or {}
    row = {
        "Evaluation Date": eval_date_str,
        "Forecast Date": forecast_date_str,
        "Horizon (Days)": horizon_days,
        "Unique Indicators Scored": counts.unique_items,
        "Scored Pairs (Indicator-OpDiv)": counts.total,
        "Decided (High + Low)": counts.decided,
        "Undecided (Possibly Active)": counts.abstain_n,
        "Coverage (%)": percent_or_sentinel(rates.coverage, rates.coverage_defined),
        "Actual Positives": counts.actual_positive,
        "Actual Negatives": counts.actual_negative,
        "Observed Positive Rate (%)": percent_or_sentinel(
            rates.actual_positive_rate, rates.rates_defined
        ),
        "Predicted High Count": counts.positive_n,
        "True Positives (High)": counts.true_positive,
        "False Positives (High)": counts.false_positive,
        "False Negatives (High)": counts.missed_positive,
        "Precision - High (%)": percent_or_sentinel(rates.precision, rates.precision_defined),
        "Accuracy - High (%)": percent_or_sentinel(
            rates.accuracy_positive, rates.accuracy_positive_defined
        ),
        "Recall - High (%)": percent_or_sentinel(rates.recall_decided, rates.recall_decided_defined),
        "Recall - High vs All Positives (%)": percent_or_sentinel(
            rates.recall_all, rates.recall_all_defined
        ),
        "Recall - 7-Day High vs 1-Day Positives (%)": week.get("recall_7d", NOT_APPLICABLE),
        "Recall - 1-Day or 7-Day High vs All Positives (%)": week.get(
            "recall_union", NOT_APPLICABLE
        ),
        "Predicted High Rate (%)": percent_or_sentinel(
            rates.predicted_positive_rate, rates.rates_defined
        ),
        "Predicted Low Count": counts.negative_n,
        "True Negatives (Low)": counts.true_negative,
        "False Positives (Low)": counts.missed_positive,
        "Negative Precision - Low (%)": percent_or_sentinel(
            rates.negative_precision, rates.negative_precision_defined
        ),
        "Predicted Low Rate (%)": percent_or_sentinel(
            rates.predicted_negative_rate, rates.rates_defined
        ),
        "Possibly Active Count": counts.abstain_n,
        "Possibly Active Ended High (Observed)": int(counts.abstain_ended_positive),
        "Possibly Active Ended Low (Not Observed)": int(counts.abstain_ended_negative),
        "Possibly Active Ended High Rate (%)": percent_or_sentinel(
            rates.abstain_ended_positive_rate, rates.abstain_rate_defined
        ),
        "Avg Prob - Possibly Active (%)": counts.avg_prob_abstain,
        "Avg Prob - Possibly Active Ended High (%)": counts.avg_prob_abstain_ended_positive,
        "Avg Prob - Possibly Active Ended Low (%)": counts.avg_prob_abstain_ended_negative,
        "Possibly Active Observed already 7-Day High": week.get("pa_obs_7d_high", NOT_APPLICABLE),
        "Accuracy (%)": percent_or_sentinel(rates.accuracy, rates.accuracy_defined),
        "Specificity - True Negative Rate (%)": percent_or_sentinel(
            rates.specificity, rates.specificity_defined
        ),
        "Balanced Accuracy (%)": percent_or_sentinel(
            rates.balanced_accuracy, rates.balanced_accuracy_defined
        ),
        "F1 Score - High (%)": percent_or_sentinel(rates.f1, rates.f1_defined),
        "_raw_precision": rates.precision if rates.precision_defined else float("nan"),
        "_raw_accuracy_high": (
            rates.accuracy_positive if rates.accuracy_positive_defined else float("nan")
        ),
        "_raw_recall": rates.recall_decided if rates.recall_decided_defined else float("nan"),
        "_raw_recall_all": rates.recall_all if rates.recall_all_defined else float("nan"),
        "_raw_recall_7d": week.get("_raw_recall_7d", float("nan")),
        "_raw_recall_union": week.get("_raw_recall_union", float("nan")),
        "_raw_neg_prec": (
            rates.negative_precision if rates.negative_precision_defined else float("nan")
        ),
        "_raw_accuracy": rates.accuracy if rates.accuracy_defined else float("nan"),
        "_raw_balanced_acc": (
            rates.balanced_accuracy if rates.balanced_accuracy_defined else float("nan")
        ),
        "_raw_fn_all": counts.false_negative_all,
        "Data Status": "Scored",
    }
    if opdiv is not None:
        row["OpDiv"] = opdiv
    return row


def strip_horizon_prefix(series: pd.Series, horizon_days: int) -> pd.Series:
    prefix = f"{horizon_days}-Day:"
    return series.astype(str).str.replace(prefix, "", regex=False).str.strip()


def score_banded_forecast(
    predictions: pd.DataFrame,
    observations: pd.DataFrame,
    *,
    horizon_days: int,
    eval_date_str: str,
    forecast_date_str: str,
    excluded_info: dict,
    provisional_info: dict,
    excluded_pairs: int,
    excluded_pop: dict,
    backfilled: bool = False,
) -> dict:
    scored = predictions.merge(observations, on=["Indicator", "Partner"], how="left")
    scored["Observed"] = scored["Observed"].fillna(0).astype(int)
    conf_col = f"Confidence: {horizon_days}-Day"
    prob_col = f"Probability: {horizon_days}-Day"
    scored["band_h"] = strip_horizon_prefix(scored[conf_col], horizon_days)
    conf7 = "Confidence: 7-Day"
    if conf7 in scored.columns:
        scored["band_7"] = strip_horizon_prefix(scored[conf7], 7)
    else:
        scored["band_7"] = ""
    if prob_col in scored.columns:
        scored["_prob_pct"] = parse_probability_percent(scored[prob_col])
    else:
        scored["_prob_pct"] = float("nan")

    overall_counts = count_bands(
        scored,
        prediction_col="band_h",
        label_col="Observed",
        spec=NOI_BANDS,
        probability_col="_prob_pct",
        unique_col="Indicator",
    )
    opdiv_rows: list[dict] = []
    for opdiv, group in scored.groupby("Partner"):
        counts = count_bands(
            group,
            prediction_col="band_h",
            label_col="Observed",
            spec=NOI_BANDS,
            probability_col="_prob_pct",
            unique_col="Indicator",
        )
        opdiv_rows.append(
            metrics_row(
                eval_date_str=eval_date_str,
                forecast_date_str=forecast_date_str,
                horizon_days=horizon_days,
                counts=counts,
                rates=rates_from_counts(counts),
                week_cov=week_horizon_coverage(group, horizon_days),
                opdiv=opdiv,
            )
        )
    for opdiv, reasons in sorted(excluded_info.items()):
        pop = excluded_pop.get(opdiv, {"pairs": 0, "uniq": 0})
        opdiv_rows.append(
            excluded_opdiv_row(
                eval_date_str=eval_date_str,
                forecast_date_str=forecast_date_str,
                horizon_days=horizon_days,
                opdiv=opdiv,
                unique_indicators=int(pop["uniq"]),
                total_pairs=int(pop["pairs"]),
                reasons=reasons,
            )
        )
    overall = metrics_row(
        eval_date_str=eval_date_str,
        forecast_date_str=forecast_date_str,
        horizon_days=horizon_days,
        counts=overall_counts,
        rates=rates_from_counts(overall_counts),
        week_cov=week_horizon_coverage(scored, horizon_days),
    )
    overall["Excluded OpDivs (Incomplete Labels)"] = (
        ", ".join(sorted(excluded_info)) if excluded_info else "(none)"
    )
    overall["Excluded Pairs (Incomplete Labels)"] = excluded_pairs
    overall["_opdiv_rows"] = opdiv_rows
    tag_provisional(overall, provisional_info)
    if backfilled:
        tag_backfilled(overall)
    return overall


def nothing_scorable_row(
    *,
    eval_date_str: str,
    forecast_date_str: str,
    horizon_days: int,
    excluded_info: dict,
    excluded_pairs: int,
    excluded_pop: dict,
    backfilled: bool = False,
) -> dict:
    all_reasons = [reason for reasons in excluded_info.values() for reason in reasons]
    overall = unscorable_row(
        PERF_COLUMNS,
        {
            "Evaluation Date": eval_date_str,
            "Forecast Date": forecast_date_str,
            "Horizon (Days)": horizon_days,
            "Data Status": (
                f"Not scored - no OpDiv has a complete label window over "
                f"({forecast_date_str}, {eval_date_str}]; "
                f"blocked by: {', '.join(sorted(statuses_in(all_reasons)))}"
            ),
            "Excluded OpDivs (Incomplete Labels)": ", ".join(sorted(excluded_info)),
            "Excluded Pairs (Incomplete Labels)": excluded_pairs,
        },
        sentinel_for_reasons(all_reasons),
    )
    overall["_opdiv_rows"] = [
        excluded_opdiv_row(
            eval_date_str=eval_date_str,
            forecast_date_str=forecast_date_str,
            horizon_days=horizon_days,
            opdiv=opdiv,
            unique_indicators=int(excluded_pop.get(opdiv, {}).get("uniq", 0)),
            total_pairs=int(excluded_pop.get(opdiv, {}).get("pairs", 0)),
            reasons=reasons,
        )
        for opdiv, reasons in sorted(excluded_info.items())
    ]
    if backfilled:
        tag_backfilled(overall)
    return overall


def tag_backfilled(overall: dict) -> dict:
    for row in [overall, *overall.get("_opdiv_rows", [])]:
        row["Data Status"] = f"{row.get('Data Status', 'Scored')} ({BACKFILLED_NOTE})"
    return overall


def tag_provisional(overall: dict, provisional_info: dict) -> dict:
    if not provisional_info:
        return overall
    for row in overall.get("_opdiv_rows", []):
        days = provisional_info.get(str(row.get("OpDiv", "")).strip())
        if days:
            row["Data Status"] = (
                f"{row.get('Data Status', 'Scored')} ({PROVISIONAL_NOTE}; "
                f"{'; '.join(days[:4])})"
            )
    overall["Data Status"] = (
        f"{overall.get('Data Status', 'Scored')} ({PROVISIONAL_NOTE} for "
        f"{', '.join(sorted(provisional_info))})"
    )
    return overall
