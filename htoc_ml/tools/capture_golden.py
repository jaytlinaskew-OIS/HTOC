"""Run the untouched V4 production script into a scratch directory.

Does not write to NextObserveV4Test. Observations still come from the share.

    py -3.13 htoc_ml/tools/capture_golden.py
    py -3.13 htoc_ml/tools/capture_golden.py --dates 20260822 20260826 20260828
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_SCRIPT = (
    REPO_ROOT
    / "notebooks"
    / "observationEventForecasting"
    / "NextObservedIndicatorV4"
    / "NextObservedIndicatorV4.0.py"
)
GOLDEN_ROOT = Path(__file__).resolve().parents[1] / "golden"
DEFAULT_DATES = ("20260822", "20260826", "20260828")


def capture_one(as_of: str, python_exe: str) -> int:
    save_dir = GOLDEN_ROOT / "legacy" / as_of
    save_dir.mkdir(parents=True, exist_ok=True)
    log_path = save_dir / "capture.log"
    env = os.environ.copy()
    env["NOI_V4_AS_OF"] = as_of
    env["NOI_V4_SAVE_DIR"] = str(save_dir)
    env["PYTHONUNBUFFERED"] = "1"
    print(f"capturing as-of {as_of} -> {save_dir}")
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            [python_exe, str(LEGACY_SCRIPT)],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=str(LEGACY_SCRIPT.parent),
        )
    print(f"  exit {proc.returncode}  log {log_path}")
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture golden CSVs from the live V4 runner.")
    parser.add_argument("--dates", nargs="+", default=list(DEFAULT_DATES))
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    if not LEGACY_SCRIPT.is_file():
        print(f"FATAL: legacy script not found: {LEGACY_SCRIPT}")
        return 2
    GOLDEN_ROOT.mkdir(parents=True, exist_ok=True)
    failed = 0
    for as_of in args.dates:
        rc = capture_one(as_of, args.python)
        if rc != 0:
            failed += 1
    if failed:
        print(f"FATAL: {failed} of {len(args.dates)} captures failed")
        return 1
    print("GOLDEN_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
