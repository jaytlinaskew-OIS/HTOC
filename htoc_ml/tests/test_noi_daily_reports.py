"""Tests for htoc_ml.noi.daily_reports entry point."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from htoc_ml.core.pipeline import PipelineError
from htoc_ml.noi.config import ForecastConfig
from htoc_ml.noi.daily_reports import main, run_next_observed_daily_reports


@pytest.fixture
def forecast_config(tmp_path: Path) -> ForecastConfig:
    return ForecastConfig(save_dir=str(tmp_path), htoc_share_root=str(tmp_path))


def _mock_eval(backfill_start: str = "", backfill_end: str = ""):
    eval_config = MagicMock()
    eval_config.save_root = "/data/save"
    eval_config.daily_report_dir = Path("/data/save/Full Daily Reports")
    eval_config.backfill_start = backfill_start
    eval_config.backfill_end = backfill_end
    evaler = MagicMock()
    evaler.run.return_value = True
    return eval_config, evaler


@patch("htoc_ml.noi.daily_reports._eval_config")
def test_main_backfill_only(mock_eval_cfg, capsys):
    eval_config, evaler = _mock_eval(backfill_start="20260801", backfill_end="20260810")
    mock_eval_cfg.return_value = (MagicMock(), eval_config, evaler)

    assert main() == 0
    evaler.consolidate_daily_report.assert_not_called()
    evaler.run.assert_called_once()
    assert "PIPELINE_OK" in capsys.readouterr().out


@patch("htoc_ml.noi.daily_reports._eval_config")
def test_main_nowork(mock_eval_cfg, capsys):
    eval_config, evaler = _mock_eval()
    evaler.consolidate_daily_report.return_value = None
    mock_eval_cfg.return_value = (MagicMock(), eval_config, evaler)

    assert main() == 0
    out = capsys.readouterr().out
    assert "No data to save." in out
    assert "PIPELINE_OK_NOWORK" in out
    evaler.run.assert_not_called()


@patch("htoc_ml.noi.daily_reports._eval_config")
def test_main_consolidate_then_eval(mock_eval_cfg, tmp_path: Path, capsys):
    report = tmp_path / "full_daily_report_20260828.csv"
    report.write_text("Indicator,Partner\n", encoding="utf-8")
    eval_config, evaler = _mock_eval()
    evaler.consolidate_daily_report.return_value = str(report)
    mock_eval_cfg.return_value = (MagicMock(), eval_config, evaler)

    assert main() == 0
    assert "PIPELINE_OK" in capsys.readouterr().out
    evaler.consolidate_daily_report.assert_called_once()
    evaler.run.assert_called_once()


@patch("htoc_ml.noi.daily_reports._eval_config")
def test_main_missing_report(mock_eval_cfg, capsys):
    eval_config, evaler = _mock_eval()
    evaler.consolidate_daily_report.return_value = "/missing/full_daily_report_20260828.csv"
    mock_eval_cfg.return_value = (MagicMock(), eval_config, evaler)

    assert main() == 3
    assert "FATAL: expected report missing" in capsys.readouterr().out


@patch("htoc_ml.noi.daily_reports._eval_config")
def test_run_next_observed_daily_reports_returns_path(mock_eval_cfg, tmp_path: Path, forecast_config):
    report = tmp_path / "full_daily_report.csv"
    report.write_text("x\n", encoding="utf-8")
    eval_config, evaler = _mock_eval()
    evaler.consolidate_daily_report.return_value = str(report)
    mock_eval_cfg.return_value = (forecast_config, eval_config, evaler)

    assert run_next_observed_daily_reports(forecast_config) == report
    evaler.run.assert_called_once()
