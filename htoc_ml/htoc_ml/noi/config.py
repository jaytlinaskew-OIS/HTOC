"""Tunables for the Next Observed Indicator forecast. Validated at construction."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from htoc_ml.core.pipeline import PipelineError

DATE_FMT = "%Y%m%d"
DEFAULT_SHARE = r"\\cscso1fsappv01\data\HTOC"
DEFAULT_HORIZONS = (1, 7, 14, 30, 45)


@dataclass(frozen=True)
class ForecastConfig:
    lookback_days: int = 100
    horizons: tuple[int, ...] = DEFAULT_HORIZONS
    train_days: int = 220
    cutoff_step: int = 5
    val_tail_frac: float = 0.25
    htoc_share_root: str = DEFAULT_SHARE
    obs_template: str = ""
    save_dir: str = ""
    as_of: date | None = None
    save_output: bool = True
    min_file_coverage: float = 0.0
    max_lag_days: int = 2
    run_eval: bool = True

    def __post_init__(self) -> None:
        if max(self.horizons) > self.lookback_days:
            raise PipelineError(
                f"max(horizons)={max(self.horizons)} exceeds lookback_days="
                f"{self.lookback_days}; count_within would undercount."
            )
        if self.cutoff_step % 7 == 0:
            raise PipelineError(
                f"cutoff_step={self.cutoff_step} is a multiple of 7; every training "
                f"cutoff would land on the same weekday."
            )
        if not 0.0 < self.val_tail_frac < 1.0:
            raise PipelineError(f"val_tail_frac={self.val_tail_frac} must be between 0 and 1.")
        object.__setattr__(self, "htoc_share_root", self.htoc_share_root.strip() or DEFAULT_SHARE)
        if not self.obs_template:
            object.__setattr__(
                self,
                "obs_template",
                str(
                    Path(self.htoc_share_root)
                    / r"Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"
                ),
            )
        if not self.save_dir:
            object.__setattr__(
                self,
                "save_dir",
                str(Path(self.htoc_share_root) / r"JA\NextObserveV4Test"),
            )

    @property
    def max_horizon(self) -> int:
        return max(self.horizons)

    @classmethod
    def from_env(cls) -> "ForecastConfig":
        share = os.environ.get("HTOC_SHARE_ROOT", DEFAULT_SHARE)
        as_of_raw = os.environ.get("NOI_V4_AS_OF", "").strip()
        as_of = datetime.strptime(as_of_raw, DATE_FMT).date() if as_of_raw else None
        coverage_raw = os.environ.get("NOI_V4_MIN_FILE_COVERAGE", "").strip()
        lag_raw = os.environ.get("NOI_V4_MAX_LAG_DAYS", "").strip()
        skip_eval = os.environ.get("NOI_V4_SKIP_EVAL", "").strip().lower() in ("1", "true", "yes")
        return cls(
            htoc_share_root=share,
            obs_template=os.environ.get("HTOC_OBS_TEMPLATE", ""),
            save_dir=os.environ.get("NOI_V4_SAVE_DIR", ""),
            as_of=as_of,
            min_file_coverage=float(coverage_raw) if coverage_raw else 0.0,
            max_lag_days=int(lag_raw) if lag_raw else 2,
            run_eval=not skip_eval,
        )
