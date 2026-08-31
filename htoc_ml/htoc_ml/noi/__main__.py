"""python -m htoc_ml.noi"""
from __future__ import annotations

import sys
import warnings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

warnings.filterwarnings("ignore")

from htoc_ml.noi.config import ForecastConfig
from htoc_ml.noi.runner import ForecastRunner


def main() -> int:
    return ForecastRunner(ForecastConfig.from_env()).run()


if __name__ == "__main__":
    raise SystemExit(main())
