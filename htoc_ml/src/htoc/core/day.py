"""Epoch-integer days used by every searchsorted hot path."""
from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd

Day = int
EPOCH = np.datetime64("2020-01-01")


def to_day_index(value) -> np.ndarray:
    """Convert dates to days since EPOCH. Accepts scalars or arrays."""
    return (np.asarray(value, dtype="datetime64[D]") - EPOCH).astype(int)


def to_timestamp(day: Day) -> pd.Timestamp:
    return pd.Timestamp(EPOCH + np.timedelta64(int(day), "D"))


def to_date(day: Day) -> date:
    return to_timestamp(day).date()


def as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()
