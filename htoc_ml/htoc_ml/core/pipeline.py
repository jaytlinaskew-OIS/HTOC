"""Shared run lifecycle for scheduled jobs: execute, check outputs, PIPELINE_OK."""
from __future__ import annotations

from pathlib import Path


class PipelineError(Exception):
    """Hard failure mapped to a process exit code the .bat launchers understand."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = int(exit_code)


class PipelineNoWork(Exception):
    """Legitimate empty run. Prints PIPELINE_OK_NOWORK and exits 0."""


class Pipeline:
    """Template method. Subclasses implement execute(); this owns the contract."""

    def execute(self) -> None:
        raise NotImplementedError

    def expected_outputs(self) -> list[Path]:
        return []

    def validate_outputs(self) -> None:
        missing = [fp for fp in self.expected_outputs() if not fp.is_file()]
        if missing:
            lines = "\n".join(f"  {fp}" for fp in missing)
            raise PipelineError(f"expected output files missing:\n{lines}", exit_code=4)

    def run(self) -> int:
        try:
            self.execute()
            self.validate_outputs()
        except PipelineNoWork as exc:
            message = str(exc).strip()
            if message:
                print(message)
            print("PIPELINE_OK_NOWORK")
            return 0
        except PipelineError as exc:
            print(f"FATAL: {exc}")
            return exc.exit_code
        print("PIPELINE_OK")
        return 0
