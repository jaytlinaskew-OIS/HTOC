"""Drop-in production CSV schema for per-OpDiv forecast files."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from htoc_ml.core.pipeline import PipelineError
from htoc_ml.noi.bands import CONFNAME, PROBNAME


class ProductionReport:
    def __init__(self, horizons: tuple[int, ...]) -> None:
        self.horizons = horizons

    def format_opdiv(self, group: pd.DataFrame) -> pd.DataFrame:
        frame = pd.DataFrame(
            {
                "Indicator": group["indicator"].values,
                "Observed Today": group["observed_today"].values.astype(int),
                "Frequency (1d)": (group["last_seen"].values == 0).astype(int),
                "Frequency (7d)": group["freq_7"].values,
                "Frequency (30d)": group["freq_30"].values,
            }
        )
        for horizon_days in self.horizons:
            frame[PROBNAME[horizon_days]] = (
                group[f"prob_{horizon_days}"].values * 100
            ).round(2).astype(str) + "%"
            frame[CONFNAME[horizon_days]] = [
                f"{horizon_days}-Day: {band}" for band in group[f"band_{horizon_days}"].values
            ]
        frame["Basis"] = group["basis"].values
        cols = ["Indicator", "Observed Today", "Frequency (1d)", "Frequency (7d)", "Frequency (30d)"]
        for horizon_days in [1, 7, 14, 30]:
            if horizon_days in self.horizons:
                cols += [PROBNAME[horizon_days], CONFNAME[horizon_days]]
        if 45 in self.horizons:
            cols += [PROBNAME[45], CONFNAME[45]]
        cols += ["Basis"]
        return frame[cols]

    def write(self, outputs: dict[str, pd.DataFrame], save_dir: str, stamp: str) -> list[Path]:
        root = Path(save_dir)
        written: list[Path] = []
        try:
            root.mkdir(parents=True, exist_ok=True)
            for opdiv, frame in outputs.items():
                sub = root / opdiv
                sub.mkdir(parents=True, exist_ok=True)
                path = sub / f"{opdiv}_output_{stamp}.csv"
                frame.to_csv(path, index=False)
                written.append(path)
        except OSError as exc:
            raise PipelineError(
                f"failed writing OpDiv CSVs under {save_dir}: {exc}",
                exit_code=4,
            ) from exc
        return written
