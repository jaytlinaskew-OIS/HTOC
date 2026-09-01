from pathlib import Path

from htoc_ml.datapipelines.make_launcher import JOBS, main, render_bat, render_vbs, write_job


def test_vbs_is_relative_not_unc():
    text = render_vbs("run_noi.bat")
    assert "GetParentFolderName(WScript.ScriptFullName)" in text
    assert "cscso1fsappv01" not in text
    assert "run_noi.bat" in text


def test_noi_bat_contract():
    text = render_bat(JOBS["noi"])
    assert "py -3.13" in text
    assert "-m htoc_ml.noi" in text
    assert "ensure_htoc_data_share.bat" in text
    assert r"PYTHONUSERBASE=%USERPROFILE%\AppData\Roaming\Python" in text
    assert "PIPELINE_OK" in text
    assert "C:\\Users\\jaskew" not in text
    assert "exit /b 3" in text


def test_prism_daily_allows_nowork():
    text = render_bat(JOBS["prism-daily"])
    assert 'set "PRISM_MODE=daily"' in text
    assert "PIPELINE_OK_NOWORK" in text
    assert "Data_Analytics\\threatconnect" in text
    assert "-m htoc_ml.prism" in text


def test_threat_score_iw_bat_allows_nowork():
    text = render_bat(JOBS["threat-score-iw"])
    assert "-m htoc_ml.datapipelines.threat_score_iw" in text
    assert "PIPELINE_OK_NOWORK" in text
    assert "Data_Analytics\\threatconnect" in text


def test_write_job_and_cli_custom(tmp_path: Path):
    written = write_job(JOBS["noi"], tmp_path)
    names = {path.name for path in written}
    assert names == {"run_noi.bat", "run_noi_hidden.vbs"}
    rc = main(
        [
            "--new-name",
            "run_custom",
            "--python-args",
            "-m htoc_ml.custom",
            "--out",
            str(tmp_path),
            "--no-marker",
        ]
    )
    assert rc == 0
    bat = (tmp_path / "run_custom.bat").read_text(encoding="utf-8")
    assert "-m htoc_ml.custom" in bat
    assert "no PIPELINE_OK required" in bat
