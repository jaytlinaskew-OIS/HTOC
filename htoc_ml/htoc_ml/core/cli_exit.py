"""CLI process exit helper for ``python -m`` entrypoints.

Keeps success/failure markers and exit codes out of the domain modules.
Launch wrappers may look for PIPELINE_OK / PIPELINE_OK_NOWORK in stdout.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from htoc_ml.core.pipeline import PipelineError, PipelineNoWork


def run_and_return_exit_code(work: Callable[[], Sequence[Path]]) -> int:
    """Run work(), confirm returned paths exist on disk, return a process exit code."""
    try:
        written = list(work())
        missing = [fp for fp in written if not fp.is_file()]
        if missing:
            lines = "\n".join(f"  {fp}" for fp in missing)
            raise PipelineError(f"expected output files missing:\n{lines}", exit_code=4)
    except PipelineNoWork as exc:
        message = str(exc).strip()
        if message:
            print(message)
        print("PIPELINE_OK_NOWORK")
        return 0
    except PipelineError as exc:
        print(f"FATAL: {exc}")
        return exc.exit_code
    except Exception as exc:
        print(f"FATAL: unexpected error: {exc}")
        return 2
    print("PIPELINE_OK")
    return 0
