"""Daily observation files as a panel plus per-indicator day-index lookups."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from htoc_ml.core.day import Day, to_date, to_day_index, to_timestamp

DATE_FMT = "%Y%m%d"


class IndicatorIndex:
    """Sorted observation-day arrays keyed by (opdiv, indicator)."""

    def __init__(self, lookup: dict[tuple[str, str], np.ndarray]) -> None:
        self._lookup = lookup

    def __len__(self) -> int:
        return len(self._lookup)

    def items(self):
        return self._lookup.items()

    def get(self, opdiv: str, indicator: str, default: np.ndarray | None = None) -> np.ndarray | None:
        return self._lookup.get((opdiv, indicator), default)

    def window(self, dates: np.ndarray, cutoff_day: Day, lookback_days: int) -> np.ndarray:
        window_end = np.searchsorted(dates, cutoff_day, side="right")
        window_start = np.searchsorted(dates, cutoff_day - lookback_days + 1, side="left")
        return dates[window_start:window_end]

    def seen_next(self, dates: np.ndarray, cutoff_day: Day, horizon_days: int) -> int:
        """1 if observed on any day in (cutoff_day, cutoff_day + horizon_days]."""
        after = np.searchsorted(dates, cutoff_day + 1, side="left")
        upto = np.searchsorted(dates, cutoff_day + horizon_days, side="right")
        return 1 if upto > after else 0

    def really_seen(self, opdiv: str, indicator: str, cutoff_day: Day) -> bool:
        dates = self.get(opdiv, indicator)
        if dates is None or not dates.size:
            return False
        i = np.searchsorted(dates, cutoff_day, side="left")
        return bool(i < dates.size and dates[i] == cutoff_day)

    def opdivs(self) -> list[str]:
        return sorted({opdiv for opdiv, _indicator in self._lookup})

    def as_dict(self) -> dict[tuple[str, str], np.ndarray]:
        return self._lookup


class ObservationPanel:
    """Loaded observation rows plus the raw (label-safe) indicator index."""

    def __init__(
        self,
        frame: pd.DataFrame,
        labels: IndicatorIndex,
        expected_files: int,
        found_files: int,
        missing_files: list[str],
        end_date: date,
    ) -> None:
        self.frame = frame
        self.labels = labels
        self.features = labels
        self.expected_files = expected_files
        self.found_files = found_files
        self.missing_files = missing_files
        self.end_date = end_date
        self.day_min: Day = int(frame["d"].min())
        self.day_max: Day = int(frame["d"].max())

    @property
    def file_coverage(self) -> float:
        if self.expected_files <= 0:
            return 1.0
        return self.found_files / self.expected_files

    def set_features(self, lookup: dict[tuple[str, str], np.ndarray]) -> None:
        self.features = IndicatorIndex(lookup)

    @classmethod
    def from_frame(cls, frame: pd.DataFrame, end_date: date | None = None) -> "ObservationPanel":
        lookup: dict[tuple[str, str], np.ndarray] = {}
        for (opdiv, indicator), group in frame.groupby(["opdiv", "indicator"], sort=False):
            lookup[(opdiv, indicator)] = np.sort(group["d"].to_numpy())
        end = end_date or datetime.today().date()
        return cls(
            frame=frame,
            labels=IndicatorIndex(lookup),
            expected_files=0,
            found_files=0,
            missing_files=[],
            end_date=end,
        )

    @classmethod
    def load(
        cls,
        obs_template: str,
        train_days: int,
        end_date: date | None = None,
        min_file_coverage: float = 0.0,
        max_lag_days: int = 2,
    ) -> "ObservationPanel":
        today = end_date or datetime.today().date()
        start = today - timedelta(days=train_days)
        frames: list[pd.DataFrame] = []
        missing: list[str] = []
        expected = 0
        day = start
        while day <= today:
            expected += 1
            path = obs_template.format(date=day.strftime(DATE_FMT))
            if Path(path).exists():
                try:
                    frames.append(pd.read_csv(path, usecols=["indicator", "obs_date", "OpDiv"]))
                except (OSError, ValueError, pd.errors.ParserError) as exc:
                    print("skip", path, exc)
                    missing.append(path)
            else:
                missing.append(path)
            day += timedelta(days=1)

        found = expected - len(missing)
        coverage = found / expected if expected else 0.0
        if coverage < min_file_coverage:
            from htoc_ml.core.pipeline import PipelineError

            raise PipelineError(
                f"observation file coverage {coverage:.0%} is below floor "
                f"{min_file_coverage:.0%} ({found}/{expected} files, template={obs_template})"
            )
        if not frames:
            from htoc_ml.core.pipeline import PipelineError

            raise PipelineError(
                f"No observation files loaded for {start} -> {today} "
                f"(template={obs_template}). Check share path / date coverage."
            )

        panel = pd.concat(frames, ignore_index=True)
        panel["indicator"] = panel["indicator"].astype(str).str.strip()
        panel["opdiv"] = panel["OpDiv"].astype(str).str.strip()
        panel["date"] = pd.to_datetime(panel["obs_date"], errors="coerce").dt.normalize()
        panel = panel[["indicator", "opdiv", "date"]].dropna()
        panel = panel[panel["indicator"].ne("nan") & panel["indicator"].ne("")]
        panel = panel.drop_duplicates(["indicator", "opdiv", "date"])
        if panel.empty:
            from htoc_ml.core.pipeline import PipelineError

            raise PipelineError("Observation files were found, but the cleaned panel is empty.")
        panel["d"] = to_day_index(panel["date"].values.astype("datetime64[D]"))
        loaded = cls.from_frame(panel, end_date=today)
        loaded.expected_files = expected
        loaded.found_files = found
        loaded.missing_files = missing
        lag = (today - to_date(loaded.day_max)).days
        if lag > max_lag_days:
            print(
                f"WARNING: newest observation is {to_date(loaded.day_max)}, "
                f"{lag} days behind {today}"
            )
        return loaded

    def describe(self) -> str:
        return (
            f"panel: {len(self.frame):,} rows | {len(self.labels):,} (opdiv,indicator) | "
            f"{to_timestamp(self.day_min).date()} -> {to_timestamp(self.day_max).date()}"
        )
