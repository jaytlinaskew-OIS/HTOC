from htoc.core.pipeline import PipelineError
from htoc.noi.config import ForecastConfig
from htoc.noi.schedule import CutoffSchedule


def test_cutoffs_need_lookback_and_horizon_runway():
    config = ForecastConfig(lookback_days=3, horizons=(1, 2), train_days=8, cutoff_step=1, val_tail_frac=0.25)
    schedule = CutoffSchedule.build(day_min=1, day_max=8, config=config)
    assert schedule.cutoffs == [4, 5, 6]


def test_empty_span_raises():
    config = ForecastConfig(lookback_days=100, horizons=(1, 45), cutoff_step=5)
    try:
        CutoffSchedule.build(day_min=1, day_max=10, config=config)
    except PipelineError as exc:
        assert "Not enough history" in str(exc)
    else:
        raise AssertionError("expected PipelineError")
