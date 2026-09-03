"""Domain process failures. Map to process exit codes when run as a CLI."""
from __future__ import annotations


class PipelineError(Exception):
    """Hard failure. exit_code is used when the process is started from a CLI entrypoint."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = int(exit_code)


class PipelineNoWork(Exception):
    """Nothing to do this run (empty input, no candidates). Not a failure."""
