import pandas as pd

from htoc.prism.config import PrismConfig
from htoc.prism.engine import score_frame
from htoc.prism.tags import evaluate_tagging_boost_reason, has_pb_lower_tag


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


def test_from_env_bad_mode_is_pipeline_error(monkeypatch):
    from htoc.core.pipeline import PipelineError

    monkeypatch.setenv("PRISM_MODE", "monthly")
    try:
        PrismConfig.from_env()
    except PipelineError as exc:
        assert "PRISM_MODE" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_paths_shared_with_noi():
    from htoc.core.paths import DEFAULT_SHARE_ROOT, opdiv_obs_template, share_root

    cfg = PrismConfig.daily(save_dir=".")
    assert cfg.htoc_share_root == DEFAULT_SHARE_ROOT or cfg.htoc_share_root == str(share_root())
    assert cfg.opdiv_template == opdiv_obs_template(cfg.htoc_share_root)


def test_pipeline_nowork_is_success(capsys):
    from htoc.core.cli_exit import run_and_return_exit_code
    from htoc.core.pipeline import PipelineNoWork

    def empty():
        raise PipelineNoWork("nothing today")

    assert run_and_return_exit_code(empty) == 0
    assert "PIPELINE_OK_NOWORK" in capsys.readouterr().out
