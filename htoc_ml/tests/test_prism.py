import pandas as pd

from htoc_ml.core.pipeline import PipelineNoWork
from htoc_ml.prism.config import PrismConfig
from htoc_ml.prism.engine import score_frame
from htoc_ml.prism.tags import evaluate_tagging_boost_reason, has_pb_lower_tag


def test_daily_and_weekly_presets():
    daily = PrismConfig.daily(save_dir=".")
    weekly = PrismConfig.weekly(save_dir=".")
    assert daily.mode == "daily"
    assert weekly.mode == "weekly"
    assert "Stripped URL" in weekly.indicator_types
    assert "Stripped URL" not in daily.indicator_types
    assert "tor node" in weekly.extra_standalone_tags


def test_pb_lower_tag():
    assert has_pb_lower_tag(["SOAR Indicator PB"])
    assert not has_pb_lower_tag(["unrelated"])


def test_tagging_boost_cve():
    row = pd.Series({"threat_cve_nbr": "CVE-2024-1234", "tag_name": []})
    assert evaluate_tagging_boost_reason(row).startswith("cve:")


def test_score_frame_assigns_severity():
    frame = pd.DataFrame([{
        "indicator": "1.2.3.4",
        "type": "Address",
        "obs_count": 3,
        "rating": 3,
        "confidence": 80,
        "calScore": 200,
        "threatAssessScore": 100,
        "sources": "HTOC Org",
        "partners": "FDA",
        "tag_list": [],
        "enrich_vtMaliciousCount": 15,
    }])
    scored = score_frame(frame)
    assert "PRISM Score" in scored.columns
    assert "Severity" in scored.columns
    assert len(scored) == 1
    assert int(scored["PRISM Score"].iloc[0]) >= 0


def test_pipeline_nowork_is_success(capsys):
    from htoc_ml.core.pipeline import Pipeline

    class Empty(Pipeline):
        def execute(self) -> None:
            raise PipelineNoWork("nothing today")

    assert Empty().run() == 0
    out = capsys.readouterr().out
    assert "PIPELINE_OK_NOWORK" in out
