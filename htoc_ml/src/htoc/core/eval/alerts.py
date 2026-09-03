"""Absolute-floor and rolling-drop alerts on numeric metric columns."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import pandas as pd

from htoc.core.eval.metrics import as_percent_str


@dataclass(frozen=True)
class MetricAlertRule:
    raw_column: str
    n_column: str
    min_n: int
    abs_min: float | None = None
    drop_pp: float | None = None
    rolling_days: int = 14
    require_actual_positives: bool = False
    overall_only: bool = False
    drop_only_when_below_floor: bool = False
    floor_template: str = ""
    drop_template: str = ""
    actual_positives_column: str = "Actual Positives"


def rolling_mean(history: pd.DataFrame, column: str, days: int) -> float:
    if history is None or history.empty or column not in history.columns:
        return float("nan")
    window = history.tail(days)
    return float(pd.to_numeric(window[column], errors="coerce").mean())


def collect_alerts(
    history: pd.DataFrame,
    row: dict,
    rules: Sequence[MetricAlertRule],
    *,
    tag: str,
    slice_id: str | None = None,
    skip_if: Callable[[dict], bool] | None = None,
) -> list[str]:
    if skip_if is not None and skip_if(row):
        return []
    alerts: list[str] = []
    for rule in rules:
        if rule.overall_only and slice_id:
            continue
        n_value = pd.to_numeric(row.get(rule.n_column), errors="coerce")
        if pd.isna(n_value) or int(n_value) < rule.min_n:
            continue
        value = pd.to_numeric(row.get(rule.raw_column), errors="coerce")
        if pd.isna(value):
            continue
        actual_pos = pd.to_numeric(row.get(rule.actual_positives_column), errors="coerce")
        actual_pos_n = int(actual_pos) if pd.notna(actual_pos) else 0
        if rule.require_actual_positives and actual_pos_n <= 0:
            continue
        below_floor = rule.abs_min is not None and float(value) < rule.abs_min
        rolling = rolling_mean(history, rule.raw_column, rule.rolling_days)
        dropped = (
            rule.drop_pp is not None
            and pd.notna(rolling)
            and float(value) < (rolling - rule.drop_pp)
        )
        fields = {
            "tag": tag,
            "value": as_percent_str(float(value)),
            "floor": as_percent_str(rule.abs_min) if rule.abs_min is not None else "",
            "rolling": as_percent_str(rolling) if pd.notna(rolling) else "",
            "drop_pp": f"{(rule.drop_pp or 0) * 100:.0f}",
            "n": int(n_value),
            "positives": actual_pos_n,
            "rolling_days": rule.rolling_days,
        }
        if below_floor and rule.floor_template:
            alerts.append(rule.floor_template.format(**fields))
        fire_drop = dropped and (below_floor if rule.drop_only_when_below_floor else True)
        if fire_drop and rule.drop_template:
            alerts.append(rule.drop_template.format(**fields))
    return alerts
