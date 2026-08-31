from pathlib import Path

from htoc_ml.core.pipeline import Pipeline, PipelineError


class _Ok(Pipeline):
    def __init__(self, path: Path) -> None:
        self.path = path

    def execute(self) -> None:
        self.path.write_text("ok", encoding="utf-8")

    def expected_outputs(self) -> list[Path]:
        return [self.path]


class _Empty(Pipeline):
    def execute(self) -> None:
        raise PipelineError("No candidate indicators to score as-of 2026-08-26.", exit_code=3)


def test_success_prints_pipeline_ok(tmp_path, capsys):
    out = tmp_path / "out.csv"
    rc = _Ok(out).run()
    assert rc == 0
    assert "PIPELINE_OK" in capsys.readouterr().out


def test_missing_output_is_exit_4(tmp_path, capsys):
    class Missing(Pipeline):
        def execute(self) -> None:
            return None

        def expected_outputs(self) -> list[Path]:
            return [tmp_path / "missing.csv"]

    rc = Missing().run()
    assert rc == 4
    assert "FATAL" in capsys.readouterr().out


def test_no_candidates_is_exit_3(capsys):
    rc = _Empty().run()
    assert rc == 3
    assert "FATAL" in capsys.readouterr().out
