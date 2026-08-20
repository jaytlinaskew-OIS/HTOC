r"""
Next Observed Daily Reports — V4 test consolidator.

Reads per-OpDiv forecast CSVs from NextObserveV4Test and writes a single
full_daily_report_YYYYMMDD.csv under NextObserveV4Test\Full Daily Reports,
then runs day-to-day performance evaluation.

Does NOT touch production OpDiv_Predictions / existing Daily Reports task.

Expected inputs (from NextObservedIndicatorV4):
  {SAVE_ROOT}\{OpDiv}\{OpDiv}_output_YYYYMMDD.csv
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from noi_v4_performance_eval import (  # noqa: E402
    DATA_PATH,
    DATE_FMT,
    SAVE_PATH,
    consolidate_daily_report,
    init_performance_eval,
    run_performance_evaluation,
)


def main() -> int:
    today_str = datetime.today().strftime(DATE_FMT)
    print(f"DATA_PATH={DATA_PATH}")
    print(f"SAVE_PATH={SAVE_PATH}")
    print(f"today={today_str}")

    init_performance_eval(DATA_PATH)

    backfill_start = os.environ.get("NOI_V4_PERF_BACKFILL_START", "").strip()
    backfill_end = os.environ.get("NOI_V4_PERF_BACKFILL_END", "").strip()
    if backfill_start and backfill_end:
        if not run_performance_evaluation():
            print("PERF: evaluation completed with errors (see Performance/Logs on share)")
        print("PIPELINE_OK")
        return 0

    out = consolidate_daily_report(today_str)
    if out is None:
        print("No data to save.")
        print("PIPELINE_OK_NOWORK")
        return 0

    if not os.path.exists(out):
        print(f"FATAL: expected report missing: {out}")
        return 3

    print("PIPELINE_OK")

    if not run_performance_evaluation():
        print("PERF: evaluation completed with errors (see Performance/Logs on share)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
