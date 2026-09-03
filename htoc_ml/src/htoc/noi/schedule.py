"""Legal training cutoff days: full lookback behind, matured max-horizon label ahead."""
from __future__ import annotations

from htoc.core.day import Day, to_timestamp
from htoc.noi.config import ForecastConfig


class CutoffSchedule:
    def __init__(self, cutoffs: list[Day], val_count: int) -> None:
        self.cutoffs = cutoffs
        self.val_count = val_count

    @classmethod
    def build(cutoff_schedule_class, day_min: Day, day_max: Day, config: ForecastConfig) -> "CutoffSchedule":
        cutoffs = list(
            range(
                day_min + config.lookback_days,
                day_max - config.max_horizon + 1,
                config.cutoff_step,
            )
        )
        if not cutoffs:
            from htoc.core.pipeline import PipelineError

            raise PipelineError(
                f"Not enough history for training cutoffs "
                f"(day_min={day_min}, day_max={day_max}, "
                f"lookback_days={config.lookback_days}, max_horizon={config.max_horizon}). "
                f"Increase train_days."
            )
        val_count = max(1, int(len(cutoffs) * config.val_tail_frac))
        return cutoff_schedule_class(cutoffs, val_count)

    @property
    def val_cutoffs(self) -> set[Day]:
        if len(self.cutoffs) > self.val_count:
            return set(self.cutoffs[-self.val_count :])
        return set()

    def describe(self) -> str:
        return (
            f"{len(self.cutoffs)} cutoffs "
            f"({to_timestamp(self.cutoffs[0]).date()} -> {to_timestamp(self.cutoffs[-1]).date()})"
        )
