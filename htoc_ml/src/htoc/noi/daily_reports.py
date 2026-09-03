"""Next Observed Daily Reports — consolidate OpDiv CSVs and run performance eval.

Reads per-OpDiv forecast CSVs from ``NOI_V4_SAVE_DIR`` and writes
``Full Daily Reports/full_daily_report_YYYYMMDD.csv``, then scores horizons.

Separate scheduled job from the forecast runner; does not touch production
``OpDiv_Predictions`` / legacy Daily Reports.

Run::

  py -3.13 -m htoc.noi.daily_reports
  htoc-noi-daily-reports
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

from htoc.core.cli_exit import run_daily_reports_exit_code
from htoc.core.pipeline import PipelineError
from htoc.noi.config import DATE_FMT, ForecastConfig
from htoc.noi.eval.config import EvalConfig
from htoc.noi.eval.runner import PerformanceEval


def _eval_config(config: ForecastConfig | None = None) -> tuple[ForecastConfig, EvalConfig, PerformanceEval]:
    forecast = config or ForecastConfig.from_env()
    eval_cfg = EvalConfig.from_paths(forecast.save_dir, forecast.htoc_share_root, forecast.obs_template)
    return forecast, eval_cfg, PerformanceEval(eval_cfg)


def run_next_observed_daily_reports(config: ForecastConfig | None = None) -> Path | None:
    """Consolidate today's OpDiv forecasts; run eval after ``PIPELINE_OK`` marker."""
    _, eval_config, evaler = _eval_config(config)
    today_str = datetime.today().strftime(DATE_FMT)

    if eval_config.backfill_start and eval_config.backfill_end:
        evaler.run()
        return None

    out = evaler.consolidate_daily_report(today_str)
    if out is None:
        return None

    path = Path(out)
    if not path.is_file():
        raise PipelineError(f"expected report missing: {path}", exit_code=3)

    evaler.run()
    return path


def main() -> int:
    _, eval_config, evaler = _eval_config()
    today_str = datetime.today().strftime(DATE_FMT)
    print(f"DATA_PATH={eval_config.save_root}")
    print(f"SAVE_PATH={eval_config.daily_report_dir}")
    print(f"today={today_str}")

    backfill = bool(eval_config.backfill_start and eval_config.backfill_end)

    def consolidate() -> Path | None:
        out = evaler.consolidate_daily_report(today_str)
        return Path(out) if out else None

    return run_daily_reports_exit_code(
        backfill=backfill,
        backfill_work=lambda: bool(evaler.run()),
        consolidate=consolidate,
        after_ok=lambda: bool(evaler.run()),
    )


if __name__ == "__main__":
    raise SystemExit(main())
