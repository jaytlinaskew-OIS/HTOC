"""Runner orchestration and CLI exit contract tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from htoc.core.cli_exit import run_daily_reports_exit_code
from htoc.core.pipeline import PipelineNoWork
from htoc.noi.config import ForecastConfig
from htoc.prism.config import PrismConfig


def test_run_daily_reports_backfill(capsys):
    rc = run_daily_reports_exit_code(
        backfill=True,
        backfill_work=lambda: True,
        consolidate=lambda: None,
        after_ok=lambda: True,
    )
    assert rc == 0
    assert "PIPELINE_OK" in capsys.readouterr().out


def test_run_daily_reports_nowork(capsys):
    rc = run_daily_reports_exit_code(
        backfill=False,
        backfill_work=lambda: True,
        consolidate=lambda: None,
        after_ok=lambda: True,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "PIPELINE_OK_NOWORK" in out


def test_run_daily_reports_missing_report(capsys, tmp_path: Path):
    missing = tmp_path / "missing.csv"
    rc = run_daily_reports_exit_code(
        backfill=False,
        backfill_work=lambda: True,
        consolidate=lambda: missing,
        after_ok=lambda: True,
    )
    assert rc == 3
    assert "FATAL: expected report missing" in capsys.readouterr().out


@patch("htoc.noi.runner.write_opdiv_eval")
@patch("htoc.noi.runner.write_opdiv_csv")
@patch("htoc.noi.runner.score_indicators")
@patch("htoc.noi.runner.fit_model_on_history")
@patch("htoc.noi.runner.fill_outage_gaps")
@patch("htoc.noi.runner.report_feed_health")
@patch("htoc.noi.runner.load_observation_data")
def test_noi_runner_calls_steps_in_order(
    mock_load,
    mock_health,
    mock_fill,
    mock_fit,
    mock_score,
    mock_write,
    mock_eval,
    tmp_path: Path,
):
    from htoc.noi.runner import run_next_observed_indicator_forecast

    out = tmp_path / "CDC_output.csv"
    mock_load.return_value = MagicMock()
    mock_health.return_value = MagicMock()
    mock_fill.return_value = MagicMock()
    mock_fit.return_value = (MagicMock(), MagicMock(), 123)
    mock_score.return_value = pd.DataFrame({"opdiv": ["CDC"]})
    mock_write.return_value = [out]

    config = ForecastConfig(save_dir=str(tmp_path), htoc_share_root=str(tmp_path))
    written = run_next_observed_indicator_forecast(config)

    assert written == [out]
    mock_load.assert_called_once()
    mock_health.assert_called_once()
    mock_fill.assert_called_once()
    mock_fit.assert_called_once()
    mock_score.assert_called_once()
    mock_write.assert_called_once()
    mock_eval.assert_called_once()


@patch("htoc.prism.runner.write_prism_workbook")
@patch("htoc.prism.runner.score_prism_indicators")
@patch("htoc.prism.runner.enrich_with_local_and_partner_context")
@patch("htoc.prism.runner.intake_indicators_from_threatconnect")
@patch("htoc.prism.runner.connect_threatconnect")
def test_prism_runner_calls_steps_in_order(
    mock_connect,
    mock_intake,
    mock_enrich,
    mock_score,
    mock_write,
    tmp_path: Path,
):
    from htoc.prism.runner import run_prism_indicator_scoring

    workbook = tmp_path / "Threat_Assessment_Scores.xlsx"
    mock_connect.return_value = MagicMock()
    mock_intake.return_value = pd.DataFrame({"indicator": ["1.2.3.4"]})
    mock_enrich.return_value = pd.DataFrame({"indicator": ["1.2.3.4"]})
    mock_score.return_value = pd.DataFrame({"indicator": ["1.2.3.4"], "PRISM Score": [50]})
    mock_write.return_value = [workbook]

    config = PrismConfig.daily(save_dir=str(tmp_path))
    written = run_prism_indicator_scoring(config)

    assert written == [workbook]
    mock_intake.assert_called_once()
    mock_enrich.assert_called_once()
    mock_score.assert_called_once()
    mock_write.assert_called_once()


def test_prism_runner_nowork_on_empty_daily_intake():
    from htoc.prism.runner import run_prism_indicator_scoring

    config = PrismConfig.daily(save_dir=".")
    with patch("htoc.prism.runner.connect_threatconnect", return_value=MagicMock()):
        with patch("htoc.prism.runner.intake_indicators_from_threatconnect", return_value=pd.DataFrame()):
            with pytest.raises(PipelineNoWork):
                run_prism_indicator_scoring(config)
