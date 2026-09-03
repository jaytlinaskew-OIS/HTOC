"""python -m htoc.prism   (PRISM_MODE=daily|weekly)"""
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
from htoc.prism.config import PrismConfig
from htoc.prism.runner import run_prism_indicator_scoring


def main() -> int:
    return run_and_return_exit_code(lambda: run_prism_indicator_scoring(PrismConfig.from_env()))


if __name__ == "__main__":
    raise SystemExit(main())
