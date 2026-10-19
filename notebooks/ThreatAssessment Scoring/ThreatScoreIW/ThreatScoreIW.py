"""Compatibility entry point for the existing ThreatScoreIW scheduled task.

Production I&W processing lives in htoc.datapipelines.threat_score_iw.
Keep this file as a wrapper so legacy Task Scheduler actions use the same
TOR/tag exclusions as run_threat_score_iw.bat. The adjacent notebook is for
exploration; do not regenerate this runner from notebook cells.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    source_root = Path(__file__).resolve().parents[3] / "htoc_ml" / "src"
    pipeline = source_root / "htoc" / "datapipelines" / "threat_score_iw.py"
    if not pipeline.is_file():
        print(f"FATAL: I&W package source missing: {pipeline}")
        return 1
    # Use this checkout's exclusions rather than an older installed package.
    sys.path.insert(0, str(source_root))
    from htoc.datapipelines.threat_score_iw import main as run_pipeline

    print(f"I&W pipeline: {pipeline}")
    return run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
