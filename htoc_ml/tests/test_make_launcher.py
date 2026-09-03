from pathlib import Path

from htoc.datapipelines.make_launcher import (
    DATAPIPELINES_BATS_DIR,
    JOBS,
    LAUNCHERS_DIR,
    default_out_dir,
    main,
    ml_root_bat_expr,
    package_root,
    render_bat,
    render_vbs,
    write_job,
)


def test_vbs_is_relative_not_unc():
    text = render_vbs("run_noi.bat")
    assert "GetParentFolderName(WScript.ScriptFullName)" in text
    assert "cscso1fsappv01" not in text
    assert "run_noi.bat" in text


def test_noi_bat_contract():
    text = render_bat(JOBS["noi"])
    assert "py -3.13" in text
    assert "-m htoc.noi" in text
    assert "ensure_htoc_data_share.bat" in text
    assert r"PYTHONUSERBASE=%USERPROFILE%\AppData\Roaming\Python" in text
    assert r"PYTHONPATH=%HTOC_ML_ROOT%\src" in text
    assert 'set "HTOC_ML_ROOT=%~dp0.."' in text
    assert "PIPELINE_OK" in text
    assert "C:\\Users\\jaskew" not in text
    assert "exit /b 3" in text


def test_prism_daily_allows_nowork():
    text = render_bat(JOBS["prism-daily"])
    assert 'set "PRISM_MODE=daily"' in text
    assert "PIPELINE_OK_NOWORK" in text
    assert "Data_Analytics\\threatconnect" in text
    assert r"%HTOC_ML_ROOT%\src" in text
    assert "-m htoc.prism" in text


def test_threat_score_iw_bat_allows_nowork():
    text = render_bat(JOBS["threat-score-iw"])
    assert "-m htoc.datapipelines.threat_score_iw" in text
    assert "PIPELINE_OK_NOWORK" in text
    assert "Data_Analytics\\threatconnect" in text
    assert r"%~dp0..\..\..\.." in text
    assert default_out_dir(JOBS["threat-score-iw"]) == DATAPIPELINES_BATS_DIR


def test_ml_root_climb_for_datapipelines_bats():
    assert ml_root_bat_expr(DATAPIPELINES_BATS_DIR) == r"%~dp0..\..\..\.."
    assert ml_root_bat_expr(LAUNCHERS_DIR) == r"%~dp0.."


def test_package_root_finds_htoc_ml():
    root = package_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "htoc").is_dir()
    assert LAUNCHERS_DIR == root / "launchers"
    assert DATAPIPELINES_BATS_DIR == root / "src" / "htoc" / "datapipelines" / "bats"


def test_write_job_and_cli_custom(tmp_path: Path):
    written = write_job(JOBS["noi"], tmp_path)
    names = {path.name for path in written}
    assert names == {"run_noi.bat", "run_noi_hidden.vbs"}
    rc = main(
        [
            "--new-name",
            "run_custom",
            "--python-args",
            "-m htoc.datapipelines.custom",
            "--out",
            str(tmp_path),
            "--no-marker",
        ]
    )
    assert rc == 0
    bat = (tmp_path / "run_custom.bat").read_text(encoding="utf-8")
    assert "-m htoc.datapipelines.custom" in bat
    assert "no PIPELINE_OK required" in bat
    assert r"%HTOC_ML_ROOT%\src" in bat
