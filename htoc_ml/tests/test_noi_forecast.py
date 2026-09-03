"""Unit tests for NOI forecast CSV output and synthetic end-to-end pipeline."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from htoc.core.day import to_day_index, to_timestamp
from htoc.core.observations import ObservationData
from htoc.core.pipeline import PipelineError
from htoc.noi.bands import CONFNAME, PROBNAME
from htoc.noi.config import DATE_FMT, ForecastConfig
from htoc.noi.report import ProductionReport
from htoc.noi.runner import (
    fill_outage_gaps,
    fit_model_on_history,
    report_feed_health,
    run_next_observed_indicator_forecast,
    score_indicators,
    write_opdiv_csv,
)


def _sample_scored_frame(horizons: tuple[int, ...] = (1, 7)) -> pd.DataFrame:
    rows = [
        {
            "opdiv": "FDA",
            "indicator": "daily.example",
            "last_seen": 0,
            "freq_7": 7,
            "freq_30": 30,
            "observed_today": 1,
            "basis": "",
        },
        {
            "opdiv": "FDA",
            "indicator": "weekly.example",
            "last_seen": 3,
            "freq_7": 1,
            "freq_30": 4,
            "observed_today": 0,
            "basis": "est",
        },
    ]
    frame = pd.DataFrame(rows)
    for horizon_days in horizons:
        frame[f"prob_{horizon_days}"] = 0.5 + (horizon_days * 0.01)
        frame[f"band_{horizon_days}"] = "Possibly active"
    return frame


def _expected_report_columns(horizons: tuple[int, ...]) -> list[str]:
    cols = [
        "Indicator",
        "Observed Today",
        "Frequency (1d)",
        "Frequency (7d)",
        "Frequency (30d)",
    ]
    for horizon_days in (1, 7, 14, 30, 45):
        if horizon_days in horizons:
            cols += [PROBNAME[horizon_days], CONFNAME[horizon_days]]
    cols += ["Basis"]
    return cols


@pytest.fixture
def small_forecast_config(tmp_path: Path) -> ForecastConfig:
    return ForecastConfig(
        lookback_days=14,
        horizons=(1, 7),
        train_days=60,
        cutoff_step=5,
        save_dir=str(tmp_path),
        htoc_share_root=str(tmp_path),
        run_eval=False,
    )


def test_production_report_format_opdiv_columns():
    report = ProductionReport((1, 7, 14, 30, 45))
    formatted = report.format_opdiv(_sample_scored_frame((1, 7, 14, 30, 45)))
    assert list(formatted.columns) == _expected_report_columns((1, 7, 14, 30, 45))
    assert formatted.loc[0, "Indicator"] == "daily.example"
    assert formatted.loc[0, "Observed Today"] == 1
    assert formatted.loc[0, "Frequency (1d)"] == 1
    assert formatted.loc[0, PROBNAME[1]] == "51.0%"
    assert formatted.loc[0, CONFNAME[7]] == "7-Day: Possibly active"
    assert formatted.loc[1, "Basis"] == "est"


def test_production_report_write_creates_opdiv_paths(tmp_path: Path):
    report = ProductionReport((1, 7))
    outputs = {
        "FDA": report.format_opdiv(_sample_scored_frame((1, 7))),
        "CMS": report.format_opdiv(_sample_scored_frame((1, 7)).head(1)),
    }
    written = report.write(outputs, str(tmp_path), "20260301")
    assert len(written) == 2
    assert (tmp_path / "FDA" / "FDA_output_20260301.csv").exists()
    assert (tmp_path / "CMS" / "CMS_output_20260301.csv").exists()
    loaded = pd.read_csv(tmp_path / "FDA" / "FDA_output_20260301.csv")
    assert list(loaded.columns) == _expected_report_columns((1, 7))


def test_write_opdiv_csv_from_scored_frame(small_forecast_config: ForecastConfig, tmp_path: Path):
    as_of_day = int(to_day_index(pd.Timestamp("2026-03-01").to_datetime64()))
    scored = _sample_scored_frame(small_forecast_config.horizons)
    written = write_opdiv_csv(scored, as_of_day, small_forecast_config)
    assert len(written) == 1
    path = tmp_path / "FDA" / "FDA_output_20260301.csv"
    assert path in written
    assert path.exists()
    assert len(pd.read_csv(path)) == 2


def test_write_opdiv_csv_records_backfill_marker(small_forecast_config: ForecastConfig, tmp_path: Path):
    as_of_day = int(to_day_index(pd.Timestamp("2026-03-01").to_datetime64()))
    config = ForecastConfig(
        lookback_days=small_forecast_config.lookback_days,
        horizons=small_forecast_config.horizons,
        train_days=small_forecast_config.train_days,
        cutoff_step=small_forecast_config.cutoff_step,
        save_dir=small_forecast_config.save_dir,
        htoc_share_root=small_forecast_config.htoc_share_root,
        as_of=date(2026, 3, 1),
        run_eval=False,
    )
    write_opdiv_csv(_sample_scored_frame(config.horizons), as_of_day, config)
    marker = tmp_path / "backfilled_forecasts.txt"
    assert marker.read_text(encoding="utf-8").strip() == "20260301"


def test_write_opdiv_csv_rejects_empty_outputs(small_forecast_config: ForecastConfig):
    as_of_day = int(to_day_index(pd.Timestamp("2026-03-01").to_datetime64()))
    empty = _sample_scored_frame(small_forecast_config.horizons).iloc[0:0]
    with pytest.raises(PipelineError, match="no OpDiv outputs"):
        write_opdiv_csv(empty, as_of_day, small_forecast_config)


def test_noi_pipeline_on_synthetic_observations(
    synthetic_observation_frame: pd.DataFrame,
    small_forecast_config: ForecastConfig,
    tmp_path: Path,
):
    observations = ObservationData.from_frame(synthetic_observation_frame, end_date=date(2026, 3, 1))
    health = report_feed_health(observations, small_forecast_config)
    outage_context = fill_outage_gaps(observations, health)
    model, training, as_of_day = fit_model_on_history(observations, health, small_forecast_config)
    scored = score_indicators(
        observations,
        training,
        model,
        outage_context,
        as_of_day,
        small_forecast_config,
    )
    written = write_opdiv_csv(scored, as_of_day, small_forecast_config)

    assert scored["opdiv"].nunique() >= 1
    assert len(written) == scored["opdiv"].nunique()
    stamp = to_timestamp(as_of_day).strftime(DATE_FMT)
    for opdiv in scored["opdiv"].unique():
        path = tmp_path / opdiv / f"{opdiv}_output_{stamp}.csv"
        assert path.exists()
        loaded = pd.read_csv(path)
        assert list(loaded.columns) == _expected_report_columns(small_forecast_config.horizons)
        assert loaded["Indicator"].tolist() == sorted(
            scored.loc[scored["opdiv"] == opdiv, "indicator"].tolist()
        )


@patch("htoc.noi.runner.load_observation_data")
def test_run_next_observed_indicator_forecast_on_synthetic(
    mock_load,
    synthetic_observation_frame: pd.DataFrame,
    small_forecast_config: ForecastConfig,
    tmp_path: Path,
):
    mock_load.return_value = ObservationData.from_frame(
        synthetic_observation_frame,
        end_date=date(2026, 3, 1),
    )
    written = run_next_observed_indicator_forecast(small_forecast_config)
    assert written
    for path in written:
        assert path.exists()
        assert path.parent.parent == tmp_path
