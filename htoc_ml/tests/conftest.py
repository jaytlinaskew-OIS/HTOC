from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from htoc_ml.core.day import to_day_index


@pytest.fixture
def synthetic_observation_frame() -> pd.DataFrame:
    """Small in-memory observation rows. No share mount required."""
    start = date(2026, 1, 1)
    rows = []
    for offset in range(60):
        day = start + timedelta(days=offset)
        rows.append({"indicator": "daily.example", "opdiv": "FDA", "date": pd.Timestamp(day)})
        if offset % 7 == 0:
            rows.append({"indicator": "weekly.example", "opdiv": "FDA", "date": pd.Timestamp(day)})
        if offset >= 50:
            rows.append({"indicator": "new.example", "opdiv": "CMS", "date": pd.Timestamp(day)})
    frame = pd.DataFrame(rows)
    frame["d"] = to_day_index(frame["date"].values.astype("datetime64[D]"))
    return frame
