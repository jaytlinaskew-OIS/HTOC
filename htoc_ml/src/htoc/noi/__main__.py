"""python -m htoc.noi"""
from __future__ import annotations

import sys
import warnings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

warnings.filterwarnings("ignore")

from htoc.core.cli_exit import run_and_return_exit_code
from htoc.noi.config import ForecastConfig
from htoc.noi.runner import run_next_observed_indicator_forecast


def main() -> int:
    return run_and_return_exit_code(lambda: run_next_observed_indicator_forecast(ForecastConfig.from_env()))


if __name__ == "__main__":
    raise SystemExit(main())
