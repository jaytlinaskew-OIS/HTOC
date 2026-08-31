"""python -m htoc_ml.prism   (PRISM_MODE=daily|weekly)"""
from __future__ import annotations

import sys
import warnings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

warnings.filterwarnings("ignore")

from htoc_ml.prism.config import PrismConfig
from htoc_ml.prism.runner import PrismRunner


def main() -> int:
    return PrismRunner(PrismConfig.from_env()).run()


if __name__ == "__main__":
    raise SystemExit(main())
