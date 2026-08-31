"""Banded binary classification: positive / negative / abstain vs a 0/1 label.

Any model that emits those three calls and later observes a binary outcome
uses this module. Workbook column names, band strings, and how labels are
joined stay in the model package.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

MISSING_METRIC = "Missing Data to compute"
NOT_SETTLED = "Not settled yet"
NOT_APPLICABLE = "Not applicable"
SENTINELS = frozenset({MISSING_METRIC, NOT_SETTLED, NOT_APPLICABLE})


@dataclass(frozen=True)
class BandSpec:
    positive_name: str = "positive"
    negative_name: str = "negative"
    abstain_name: str = "abstain"


@dataclass(frozen=True)
class BandCounts:
    total: int
    unique_items: int
    positive_n: int
    true_positive: int
    false_positive: int
    negative_n: int
    true_negative: int
    missed_positive: int
    abstain_n: int
    abstain_ended_positive: int
    abstain_ended_negative: int
    actual_positive: int
    actual_negative: int
    avg_prob_abstain: float = float("nan")
    avg_prob_abstain_ended_positive: float = float("nan")
    avg_prob_abstain_ended_negative: float = float("nan")

    @property
    def decided(self) -> int:
        return int(self.positive_n + self.negative_n)

    @property
    def false_negative_all(self) -> int:
        return int(self.missed_positive + self.abstain_ended_positive)

    @property
    def positive_union(self) -> int:
        return int(self.true_positive + self.false_positive + self.missed_positive)

    @property
    def decided_negative(self) -> int:
        return int(self.true_negative + self.false_positive)


@dataclass(frozen=True)
class BandRates:
    precision: float
    recall_decided: float
    recall_all: float
    accuracy_positive: float
    negative_precision: float
    accuracy: float
    specificity: float
    balanced_accuracy: float
    f1: float
    coverage: float
    predicted_positive_rate: float
    actual_positive_rate: float
    predicted_negative_rate: float
    abstain_ended_positive_rate: float
    precision_defined: bool
    recall_decided_defined: bool
    recall_all_defined: bool
    accuracy_positive_defined: bool
    negative_precision_defined: bool
    accuracy_defined: bool
    specificity_defined: bool
    balanced_accuracy_defined: bool
    f1_defined: bool
    coverage_defined: bool
    rates_defined: bool
    abstain_rate_defined: bool


def as_percent(value: float) -> float:
    if pd.isna(value):
        return float("nan")
    return round(float(value) * 100, 2)


def as_percent_str(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value) * 100:.2f}%"


def percent_or_sentinel(value: float, defined: bool):
    if not defined:
        return NOT_APPLICABLE
    return as_percent(value)


def parse_probability_percent(series: pd.Series) -> pd.Series:
    if series is None or series.empty:
        return pd.Series(dtype=float)
    stripped = series.astype(str).str.strip().str.replace("%", "", regex=False)
    values = pd.to_numeric(stripped, errors="coerce")
    if values.notna().any() and float(values.max(skipna=True)) <= 1.0:
        values = values * 100.0
    return values


def mean_probability(series: pd.Series) -> float:
    if series is None or len(series) == 0:
        return float("nan")
    if pd.api.types.is_numeric_dtype(series):
        values = pd.to_numeric(series, errors="coerce")
    else:
        values = parse_probability_percent(series)
    if values.notna().sum() == 0:
        return float("nan")
    return round(float(values.mean()), 2)


def count_bands(
    frame: pd.DataFrame,
    *,
    prediction_col: str,
    label_col: str,
    spec: BandSpec,
    probability_col: str | None = None,
    unique_col: str | None = None,
) -> BandCounts:
    if frame is None or frame.empty:
        return BandCounts(
            total=0,
            unique_items=0,
            positive_n=0,
            true_positive=0,
            false_positive=0,
            negative_n=0,
            true_negative=0,
            missed_positive=0,
            abstain_n=0,
            abstain_ended_positive=0,
            abstain_ended_negative=0,
            actual_positive=0,
            actual_negative=0,
        )

    predicted = frame[prediction_col].astype(str).str.strip()
    observed = pd.to_numeric(frame[label_col], errors="coerce").fillna(0).astype(int)
    positive = predicted.eq(spec.positive_name)
    negative = predicted.eq(spec.negative_name)
    abstain = predicted.eq(spec.abstain_name)

    positive_n = int(positive.sum())
    negative_n = int(negative.sum())
    abstain_n = int(abstain.sum())
    true_positive = int(observed[positive].sum()) if positive_n else 0
    false_positive = int((observed[positive] == 0).sum()) if positive_n else 0
    true_negative = int((observed[negative] == 0).sum()) if negative_n else 0
    missed_positive = int((observed[negative] == 1).sum()) if negative_n else 0
    abstain_ended_positive = int(observed[abstain].sum()) if abstain_n else 0
    abstain_ended_negative = int((observed[abstain] == 0).sum()) if abstain_n else 0
    total = int(len(frame))
    actual_positive = int(observed.sum())

    avg_all = avg_pos = avg_neg = float("nan")
    if probability_col and probability_col in frame.columns and abstain_n:
        probs = frame.loc[abstain, probability_col]
        avg_all = mean_probability(probs)
        if abstain_ended_positive:
            avg_pos = mean_probability(frame.loc[abstain & observed.eq(1), probability_col])
        if abstain_ended_negative:
            avg_neg = mean_probability(frame.loc[abstain & observed.eq(0), probability_col])

    unique_items = int(frame[unique_col].nunique()) if unique_col else total
    return BandCounts(
        total=total,
        unique_items=unique_items,
        positive_n=positive_n,
        true_positive=true_positive,
        false_positive=false_positive,
        negative_n=negative_n,
        true_negative=true_negative,
        missed_positive=missed_positive,
        abstain_n=abstain_n,
        abstain_ended_positive=abstain_ended_positive,
        abstain_ended_negative=abstain_ended_negative,
        actual_positive=actual_positive,
        actual_negative=int(total - actual_positive),
        avg_prob_abstain=avg_all,
        avg_prob_abstain_ended_positive=avg_pos,
        avg_prob_abstain_ended_negative=avg_neg,
    )


def rates_from_counts(counts: BandCounts) -> BandRates:
    precision = (counts.true_positive / counts.positive_n) if counts.positive_n else float("nan")
    recall_den = counts.true_positive + counts.missed_positive
    recall_decided = (counts.true_positive / recall_den) if recall_den else float("nan")
    recall_all = (
        (counts.true_positive / counts.actual_positive) if counts.actual_positive else float("nan")
    )
    accuracy_positive = (
        (counts.true_positive / counts.positive_union) if counts.positive_union else float("nan")
    )
    negative_precision = (
        (counts.true_negative / counts.negative_n) if counts.negative_n else float("nan")
    )
    accuracy = (
        ((counts.true_positive + counts.true_negative) / counts.decided)
        if counts.decided
        else float("nan")
    )
    specificity = (
        (counts.true_negative / counts.decided_negative) if counts.decided_negative else float("nan")
    )
    balanced = (
        (recall_decided + specificity) / 2
        if pd.notna(recall_decided) and pd.notna(specificity)
        else float("nan")
    )
    f1 = (
        (2 * precision * recall_decided) / (precision + recall_decided)
        if pd.notna(precision) and pd.notna(recall_decided) and (precision + recall_decided) > 0
        else float("nan")
    )
    has_pairs = counts.total > 0
    has_pos = counts.actual_positive > 0
    has_decided_pos = recall_den > 0
    return BandRates(
        precision=precision,
        recall_decided=recall_decided,
        recall_all=recall_all,
        accuracy_positive=accuracy_positive,
        negative_precision=negative_precision,
        accuracy=accuracy,
        specificity=specificity,
        balanced_accuracy=balanced,
        f1=f1,
        coverage=(counts.decided / counts.total) if has_pairs else float("nan"),
        predicted_positive_rate=(counts.positive_n / counts.total) if has_pairs else float("nan"),
        actual_positive_rate=(counts.actual_positive / counts.total) if has_pairs else float("nan"),
        predicted_negative_rate=(counts.negative_n / counts.total) if has_pairs else float("nan"),
        abstain_ended_positive_rate=(
            (counts.abstain_ended_positive / counts.abstain_n) if counts.abstain_n else float("nan")
        ),
        precision_defined=counts.positive_n > 0,
        recall_decided_defined=has_decided_pos,
        recall_all_defined=has_pos,
        accuracy_positive_defined=counts.positive_union > 0,
        negative_precision_defined=counts.negative_n > 0 and has_pos,
        accuracy_defined=counts.decided > 0 and has_pos,
        specificity_defined=counts.decided_negative > 0,
        balanced_accuracy_defined=has_decided_pos and counts.decided_negative > 0,
        f1_defined=counts.positive_n > 0 and has_decided_pos,
        coverage_defined=has_pairs,
        rates_defined=has_pairs,
        abstain_rate_defined=counts.abstain_n > 0,
    )
