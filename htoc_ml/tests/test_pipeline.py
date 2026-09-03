from pathlib import Path

from htoc.core.cli_exit import run_and_return_exit_code
from htoc.core.pipeline import PipelineError, PipelineNoWork


def test_success_prints_pipeline_ok(tmp_path, capsys):
    out = tmp_path / "out.csv"

    def write_ok() -> list[Path]:
        out.write_text("ok", encoding="utf-8")
        return [out]

    rc = run_and_return_exit_code(write_ok)
    assert rc == 0
    assert "PIPELINE_OK" in capsys.readouterr().out


def test_missing_output_is_exit_4(tmp_path, capsys):
    missing = tmp_path / "missing.csv"
    rc = run_and_return_exit_code(lambda: [missing])
    assert rc == 4
    assert "FATAL" in capsys.readouterr().out


def test_no_candidates_is_exit_3(capsys):
    def fail() -> list[Path]:
        raise PipelineError("No candidate indicators to score as-of 2026-08-26.", exit_code=3)

    rc = run_and_return_exit_code(fail)
    assert rc == 3
    assert "FATAL" in capsys.readouterr().out


def test_nowork_is_success(capsys):
    def empty() -> list[Path]:
        raise PipelineNoWork("nothing today")

    assert run_and_return_exit_code(empty) == 0
    assert "PIPELINE_OK_NOWORK" in capsys.readouterr().out


def test_unexpected_error_is_exit_2(capsys):
    def boom() -> list[Path]:
        raise RuntimeError("boom")

    rc = run_and_return_exit_code(boom)
    assert rc == 2
    assert "FATAL: unexpected error: boom" in capsys.readouterr().out
