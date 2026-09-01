from htoc_ml.core.pipeline import PipelineError
from htoc_ml.noi.config import ForecastConfig


def test_default_config_is_valid():
    config = ForecastConfig()
    assert config.lookback_days == 100
    assert config.max_horizon == 45
    assert config.cutoff_step % 7 != 0


def test_horizon_cannot_exceed_lookback():
    try:
        ForecastConfig(lookback_days=10, horizons=(1, 14))
    except PipelineError as exc:
        assert "undercount" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_cutoff_step_cannot_be_multiple_of_seven():
    try:
        ForecastConfig(cutoff_step=7)
    except PipelineError as exc:
        assert "weekday" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_from_env_bad_as_of_is_pipeline_error(monkeypatch):
    monkeypatch.setenv("NOI_V4_AS_OF", "not-a-date")
    try:
        ForecastConfig.from_env()
    except PipelineError as exc:
        assert "invalid NOI env config" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_from_env_bad_coverage_is_pipeline_error(monkeypatch):
    monkeypatch.setenv("NOI_V4_MIN_FILE_COVERAGE", "abc")
    try:
        ForecastConfig.from_env()
    except PipelineError as exc:
        assert "invalid NOI env config" in str(exc)
    else:
        raise AssertionError("expected PipelineError")
