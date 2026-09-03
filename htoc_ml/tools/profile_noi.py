"""Profile NOI forecast pipeline: wall time, tracemalloc peaks, and cProfile stats.

    py -3.13 htoc_ml/tools/profile_noi.py --as-of 20260820
"""
from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import sys
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path

# Package source lives under htoc_ml/src/htoc
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from htoc.noi import runner  # noqa: E402
from htoc.noi.config import ForecastConfig  # noqa: E402


@dataclass
class StepResult:
    name: str
    elapsed_s: float
    peak_mb: float
    notes: list[str] = field(default_factory=list)


def _df_mb(frame) -> float:
    if frame is None:
        return 0.0
    return frame.memory_usage(deep=True).sum() / 1e6


def profile_steps(config: ForecastConfig) -> list[StepResult]:
    results: list[StepResult] = []

    def run_step(name: str, fn, *args, note_fn=None):
        tracemalloc.start()
        t0 = time.perf_counter()
        out = fn(*args)
        elapsed = time.perf_counter() - t0
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        notes: list[str] = []
        if note_fn:
            notes = note_fn(out)
        results.append(StepResult(name, elapsed, peak / 1e6, notes))
        return out

    observations = run_step(
        "1 load_observation_data",
        runner.load_observation_data,
        config,
        note_fn=lambda obs: [
            obs.describe(),
            f"frame {_df_mb(obs.frame):.1f} MB",
            f"indicators {len(obs.labels):,}",
        ],
    )
    health = run_step("2 report_feed_health", runner.report_feed_health, observations, config)
    outage_context = run_step(
        "3 fill_outage_gaps",
        runner.fill_outage_gaps,
        observations,
        health,
        note_fn=lambda _: [f"features index {len(observations.features):,} keys"],
    )
    model, training, as_of_day = run_step(
        "4 fit_model_on_history",
        runner.fit_model_on_history,
        observations,
        health,
        config,
        note_fn=lambda t: [f"as_of_day {t[2]}"],
    )
    scored = run_step(
        "5 score_indicators",
        runner.score_indicators,
        observations,
        training,
        model,
        outage_context,
        as_of_day,
        config,
        note_fn=lambda s: [f"scored rows {len(s):,}", f"frame {_df_mb(s):.1f} MB"],
    )
    run_step(
        "6 write_opdiv_csv",
        runner.write_opdiv_csv,
        scored,
        as_of_day,
        config,
        note_fn=lambda paths: [f"wrote {len(paths)} CSV(s)"],
    )
    return results


def print_step_table(results: list[StepResult]) -> None:
    total = sum(r.elapsed_s for r in results)
    print("\n=== Step timing & tracemalloc peak ===")
    print(f"{'Step':<28} {'Time':>8} {'%':>6} {'Peak MB':>10}")
    print("-" * 56)
    for r in results:
        pct = 100.0 * r.elapsed_s / total if total else 0
        print(f"{r.name:<28} {r.elapsed_s:7.1f}s {pct:5.1f}% {r.peak_mb:9.1f}")
        for note in r.notes:
            print(f"  {note}")
    print("-" * 56)
    print(f"{'TOTAL':<28} {total:7.1f}s")


def run_cprofile(config: ForecastConfig, top_n: int = 40) -> None:
    prof = cProfile.Profile()
    prof.enable()
    runner.run_next_observed_indicator_forecast(config)
    prof.disable()

    print(f"\n=== cProfile top {top_n} by cumulative time ===")
    stream = io.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("cumtime").print_stats(top_n)
    print(stream.getvalue())

    print(f"\n=== cProfile top {top_n} by total time (self) ===")
    stream = io.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("tottime").print_stats(top_n)
    print(stream.getvalue())

    out_path = Path(__file__).resolve().parent / "profile_noi.prof"
    prof.dump_stats(out_path)
    print(f"\nRaw profile saved: {out_path}")
    print("Inspect with: python -m pstats profile_noi.prof")


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile NOI forecast pipeline")
    parser.add_argument("--as-of", default=os.environ.get("NOI_V4_AS_OF", "20260820"))
    parser.add_argument("--skip-eval", action="store_true", default=True)
    parser.add_argument("--with-eval", action="store_true", help="Include eval step")
    parser.add_argument("--steps-only", action="store_true", help="Skip full cProfile run")
    parser.add_argument("--top", type=int, default=40, help="cProfile lines to print")
    args = parser.parse_args()

    os.environ["NOI_V4_AS_OF"] = args.as_of
    if args.with_eval:
        os.environ.pop("NOI_V4_SKIP_EVAL", None)
    else:
        os.environ["NOI_V4_SKIP_EVAL"] = "1"

    config = ForecastConfig.from_env()
    print(f"as_of={config.as_of} save_dir={config.save_dir} run_eval={config.run_eval}")

    results = profile_steps(config)
    print_step_table(results)

    if not args.steps_only:
        print("\nRunning full pipeline under cProfile ...")
        run_cprofile(config, top_n=args.top)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
