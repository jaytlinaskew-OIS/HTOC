"""Byte-compare per-OpDiv CSVs from a new run against captured legacy output.

    py -3.13 htoc_ml/tools/compare_golden.py --as-of 20260822
"""
from __future__ import annotations

import argparse
import filecmp
from pathlib import Path

GOLDEN_ROOT = Path(__file__).resolve().parents[1] / "golden"


def compare_one(as_of: str) -> list[str]:
    legacy = GOLDEN_ROOT / "legacy" / as_of
    new = GOLDEN_ROOT / "new" / as_of
    if not legacy.is_dir():
        return [f"missing legacy dir: {legacy}"]
    if not new.is_dir():
        return [f"missing new dir: {new}"]
    problems: list[str] = []
    legacy_csvs = sorted(legacy.glob("*/*_output_*.csv"))
    if not legacy_csvs:
        return [f"no legacy CSVs under {legacy}"]
    for old_fp in legacy_csvs:
        new_fp = new / old_fp.parent.name / old_fp.name
        if not new_fp.is_file():
            problems.append(f"missing: {new_fp}")
            continue
        if not filecmp.cmp(old_fp, new_fp, shallow=False):
            problems.append(f"differ: {old_fp.name} ({old_fp.parent.name})")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff new package CSVs against golden captures.")
    parser.add_argument("--as-of", nargs="+", required=True)
    args = parser.parse_args(argv)
    any_fail = False
    for as_of in args.as_of:
        problems = compare_one(as_of)
        if problems:
            any_fail = True
            print(f"{as_of}: FAIL")
            for p in problems:
                print(f"  {p}")
        else:
            print(f"{as_of}: OK")
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
