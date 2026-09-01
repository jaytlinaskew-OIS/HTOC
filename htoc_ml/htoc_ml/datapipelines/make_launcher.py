"""Write standardized Task Scheduler .bat + hidden .vbs launchers."""
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

LAUNCHERS_DIR = Path(__file__).resolve().parents[2] / "launchers"

PRODUCTION_SNAPSHOTS: tuple[tuple[str, str], ...] = (
    ("notebooks/ensure_htoc_data_share.bat", "notebooks_root/ensure_htoc_data_share.bat"),
    ("notebooks/run_loggedoff_share_probe.bat", "notebooks_root/run_loggedoff_share_probe.bat"),
    (
        "notebooks/observationEventForecasting/NextObservedIndicatorV4/run_NextObservedIndicatorV4.bat",
        "NextObservedIndicatorV4/run_NextObservedIndicatorV4.bat",
    ),
    (
        "notebooks/observationEventForecasting/NextObservedIndicatorV4/run_NextObservedIndicatorV4_hidden.vbs",
        "NextObservedIndicatorV4/run_NextObservedIndicatorV4_hidden.vbs",
    ),
    (
        "notebooks/observationEventForecasting/NextObservedIndicatorV4/run_NextObservedDailyReportsV4.bat",
        "NextObservedIndicatorV4/run_NextObservedDailyReportsV4.bat",
    ),
    (
        "notebooks/observationEventForecasting/NextObservedIndicatorV4/run_NextObservedDailyReportsV4_hidden.vbs",
        "NextObservedIndicatorV4/run_NextObservedDailyReportsV4_hidden.vbs",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatAssessScoringV5/run_ThreatAssessScoringV5.bat",
        "ThreatAssessScoringV5/run_ThreatAssessScoringV5.bat",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatAssessScoringV5/run_ThreatAssessScoringV5_hidden.vbs",
        "ThreatAssessScoringV5/run_ThreatAssessScoringV5_hidden.vbs",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatAssessScoringV5Daily/run_ThreatAssessScoringV5Daily.bat",
        "ThreatAssessScoringV5Daily/run_ThreatAssessScoringV5Daily.bat",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatAssessScoringV5Daily/run_ThreatAssessScoringV5Daily_hidden.vbs",
        "ThreatAssessScoringV5Daily/run_ThreatAssessScoringV5Daily_hidden.vbs",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatScoreIW/run_ThreatScoreIW.bat",
        "ThreatScoreIW/run_ThreatScoreIW.bat",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatScoreIW/run_ThreatScoreIW_hidden.vbs",
        "ThreatScoreIW/run_ThreatScoreIW_hidden.vbs",
    ),
    (
        "notebooks/ThreatAssessment Scoring/ThreatScoreIW/run_skip_wheelhouse.bat",
        "ThreatScoreIW/run_skip_wheelhouse.bat",
    ),
    (
        "notebooks/I&W Reporting/Batch/I&W Generator/run_iw_generator.bat",
        "IW_Batch/run_iw_generator.bat",
    ),
    (
        "notebooks/I&W Reporting/Batch/I&W Spreadsheet/run_iw_spreadsheet.bat",
        "IW_Batch/run_iw_spreadsheet.bat",
    ),
    (
        "notebooks/I&W Reporting/Batch/I&W Spreadsheet/run_iw_spreadsheet_Test.bat",
        "IW_Batch/run_iw_spreadsheet_Test.bat",
    ),
    (
        "notebooks/I&W Reporting/Batch/I&W Expanded/run_iw_expanded_spreadsheet.bat",
        "IW_Batch/run_iw_expanded_spreadsheet.bat",
    ),
    (
        "notebooks/I&W Reporting/Batch/I&W Expanded/run_iw_expanded_generator.bat",
        "IW_Batch/run_iw_expanded_generator.bat",
    ),
    ("scripts/batch-processing-script/Tipper/run_tipper.bat", "Tipper/run_tipper.bat"),
    (
        "scripts/batch-processing-script/NextObserved/NextObserved.bat",
        "NextObserved_legacy/NextObserved.bat",
    ),
    (
        "scripts/batch-processing-script/Next_Obs_Daily/next_observed_daily_reports.bat",
        "NextObserved_legacy/next_observed_daily_reports.bat",
    ),
)


@dataclass(frozen=True)
class LauncherJob:
    key: str
    name: str
    title: str
    log_prefix: str
    python_args: str
    extra_env: tuple[tuple[str, str], ...] = ()
    packages: str = ""
    allow_nowork: bool = False
    need_threatconnect_path: bool = False
    require_success_marker: bool = True
    hidden: bool = True


JOBS: dict[str, LauncherJob] = {
    "noi": LauncherJob(
        key="noi",
        name="run_noi",
        title="NextObservedIndicator V4 (htoc_ml)",
        log_prefix="noi_v4",
        python_args="-m htoc_ml.noi",
        packages="pandas numpy scikit-learn openpyxl",
    ),
    "prism-daily": LauncherJob(
        key="prism-daily",
        name="run_prism_daily",
        title="PRISM daily first-seen (htoc_ml)",
        log_prefix="prism_daily",
        python_args="-m htoc_ml.prism",
        extra_env=(("PRISM_MODE", "daily"),),
        packages="pandas openpyxl pytz",
        allow_nowork=True,
        need_threatconnect_path=True,
    ),
    "prism-weekly": LauncherJob(
        key="prism-weekly",
        name="run_prism_weekly",
        title="PRISM weekly lastObserved (htoc_ml)",
        log_prefix="prism_weekly",
        python_args="-m htoc_ml.prism",
        extra_env=(("PRISM_MODE", "weekly"),),
        packages="pandas openpyxl pytz",
        need_threatconnect_path=True,
    ),
    "threat-score-iw": LauncherJob(
        key="threat-score-iw",
        name="run_threat_score_iw",
        title="ThreatScoreIW multi-partner I&W workbook (htoc_ml)",
        log_prefix="threat_score_iw",
        python_args="-m htoc_ml.datapipelines.threat_score_iw",
        packages="pandas openpyxl pytz xlsxwriter",
        allow_nowork=True,
        need_threatconnect_path=True,
    ),
    "search-tags": LauncherJob(
        key="search-tags",
        name="run_search_tags",
        title="Search indicators by tags",
        log_prefix="search_tags",
        python_args="-m htoc_ml.datapipelines search-tags --interactive",
        packages="pandas openpyxl tabulate",
        require_success_marker=False,
        hidden=False,
    ),
    "triage": LauncherJob(
        key="triage",
        name="run_triage",
        title="PRISM indicator triage",
        log_prefix="triage",
        python_args="-m htoc_ml.datapipelines triage",
        packages="pandas openpyxl requests",
        require_success_marker=False,
    ),
    "iw-listing": LauncherJob(
        key="iw-listing",
        name="run_iw_listing",
        title="I&W master listing from PDFs",
        log_prefix="iw_listing",
        python_args="-m htoc_ml.datapipelines iw-listing",
        packages="pandas openpyxl pdfplumber",
        require_success_marker=False,
    ),
}


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "notebooks" / "ensure_htoc_data_share.bat").exists():
            return parent
    raise FileNotFoundError("cannot find HTOC repo root (notebooks/ensure_htoc_data_share.bat)")


def _extra_env_block(job: LauncherJob) -> str:
    if not job.extra_env:
        return ""
    lines = [f'set "{key}={value}"' for key, value in job.extra_env]
    return "\n" + "\n".join(lines) + "\n"


def _pip_block(job: LauncherJob) -> str:
    if not job.packages.strip():
        return "call :log CHECK   No extra pip packages declared\n"
    return f"""set "PKGS={job.packages.strip()}"
set "PIP_FLAGS=--user --disable-pip-version-check --no-warn-script-location --no-cache-dir --timeout 120 --retries 10"
set "PIP_TRUST=--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org"
set "PIP_OK=0"
set "WHEELHOUSE=%HTOC_SHARE_ROOT%\\JA\\wheelhouse"
call :log RUN     Installing packages...
if exist "%WHEELHOUSE%" (
    "%PYTHON_EXE%" -m pip install --user --no-index --find-links="%WHEELHOUSE%" %PKGS% > "%TEMP_OUT%" 2>&1
    if "!ERRORLEVEL!"=="0" set "PIP_OK=1"
)
if "!PIP_OK!"=="0" (
    "%PYTHON_EXE%" -m pip install %PIP_FLAGS% %PIP_TRUST% %PKGS% > "%TEMP_OUT%" 2>&1
    if "!ERRORLEVEL!"=="0" set "PIP_OK=1"
)
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
if not "!PIP_OK!"=="1" (
    call :log ERROR   Package install failed
    popd >nul
    exit /b 1
)
call :log CHECK   Packages OK
"""


def _nowork_block(job: LauncherJob) -> str:
    if not job.allow_nowork:
        return ""
    return """
findstr /C:"PIPELINE_OK_NOWORK" "%TEMP_OUT%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    call :log SUCCESS No-work success ^(PIPELINE_OK_NOWORK^)
    set "FINAL_EXIT=0"
    goto :finish
)
"""


def _pythonpath_block(job: LauncherJob) -> str:
    if job.need_threatconnect_path:
        return (
            'set "PYTHONPATH=%HTOC_SHARE_ROOT%\\Data_Analytics\\threatconnect;'
            '%HTOC_ML_ROOT%;%PYTHONPATH%"\n'
        )
    return 'set "PYTHONPATH=%HTOC_ML_ROOT%;%PYTHONPATH%"\n'


def _success_block(job: LauncherJob) -> str:
    if not job.require_success_marker:
        return """call :log SUCCESS Completed successfully (exit 0; no PIPELINE_OK required)
set "FINAL_EXIT=0"
"""
    return """findstr /C:"%SUCCESS_MARKER%" "%TEMP_OUT%" >nul 2>&1
if not "!ERRORLEVEL!"=="0" (
    call :log ERROR   Missing success marker %SUCCESS_MARKER%
    goto :finish
)

call :log SUCCESS Completed successfully
set "FINAL_EXIT=0"
"""


def _regenerate_hint(job: LauncherJob) -> str:
    if job.key:
        return f"py -3.13 -m htoc_ml.datapipelines make-launcher --name {job.key}"
    return f'py -3.13 -m htoc_ml.datapipelines make-launcher --new-name {job.name} --python-args "{job.python_args}"'


def render_bat(job: LauncherJob) -> str:
    return f"""@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM {job.title}
REM Generated by htoc_ml.datapipelines.make_launcher. Task Scheduler should call the
REM sibling _hidden.vbs, not this file directly.
REM Regenerate: {_regenerate_hint(job)}
REM ============================================================================

if not exist "C:\\Temp" mkdir "C:\\Temp" >nul 2>&1
echo [%date% %time%] bat started from: %~dp0 > "C:\\Temp\\{job.log_prefix}_debug.txt" 2>&1

if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\\\cscso1fsappv01\\data\\HTOC"
{_extra_env_block(job)}
if not defined PYTHON_EXE (
    py -3.13 --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        for /f "delims=" %%p in ('py -3.13 -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%p"
    ) else (
        set "PYTHON_EXE=%HTOC_SHARE_ROOT%\\JA\\Python313\\python.exe"
    )
)

set "HTOC_ML_ROOT=%~dp0.."
set "LOG_DIR=%~dp0logs\\{job.log_prefix}"
set "SUCCESS_MARKER=PIPELINE_OK"
{_pythonpath_block(job)}
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
forfiles /p "%LOG_DIR%" /m "*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
set "_TS_RAW=%TIME: =0%"
set "NOW_STR=%_TS_RAW:~0,2%%_TS_RAW:~3,2%%_TS_RAW:~6,2%"
set "TS=%TODAY_STR%_%NOW_STR%"
set "LOG_FILE=%LOG_DIR%\\{job.log_prefix}_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\\temp_output_%TS%.log"

call :log START   {job.title}
call :log CONFIG  Python: %PYTHON_EXE%
call :log CONFIG  Module: {job.python_args}
call :log CONFIG  Root:   %HTOC_ML_ROOT%
call :log CONFIG  Log:    %LOG_FILE%
call :log RUN     Connecting data share...
call "%~dp0ensure_htoc_data_share.bat" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log ERROR   Cannot reach HTOC data share %HTOC_SHARE_ROOT%
    exit /b 3
)
call :log CHECK   Data share OK (%HTOC_SHARE_ROOT%)

if not exist "%PYTHON_EXE%" (
    call :log ERROR   Python not found: %PYTHON_EXE%
    exit /b 1
)

set "PYTHONUSERBASE=%USERPROFILE%\\AppData\\Roaming\\Python"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "TMP=C:\\Temp"
set "TEMP=C:\\Temp"
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1

pushd "%HTOC_ML_ROOT%" >nul 2>&1
if errorlevel 1 (
    call :log ERROR   Failed to pushd HTOC_ML_ROOT
    exit /b 1
)

{_pip_block(job)}
call :log RUN     Launching {job.python_args}...
"%PYTHON_EXE%" -u {job.python_args} > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"
popd >nul 2>&1

if not defined SCRIPT_EXIT_CODE set "SCRIPT_EXIT_CODE=1"
call :log RUN     Script exited with code !SCRIPT_EXIT_CODE!

echo. >> "%LOG_FILE%"
echo ---- script output ---- >> "%LOG_FILE%"
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
echo ---- end output ---- >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

set "FINAL_EXIT=1"
if not "!SCRIPT_EXIT_CODE!"=="0" (
    call :log ERROR   Script failed with exit code !SCRIPT_EXIT_CODE!
    goto :finish
)
{_nowork_block(job)}
{_success_block(job)}
:finish
if exist "%TEMP_OUT%" del "%TEMP_OUT%" >nul 2>&1
call :log END     Batch complete with exit !FINAL_EXIT!
exit /b !FINAL_EXIT!

:log
set "_T=%TIME: =0%"
echo [%TODAY_STR% %_T:~0,8%] %*
echo [%TODAY_STR% %_T:~0,8%] %*>> "%LOG_FILE%" 2>nul
exit /b 0
"""


def render_vbs(bat_name: str) -> str:
    return (
        "' Hidden launcher for Task Scheduler — no console window.\n"
        "' Generated by htoc_ml.datapipelines.make_launcher. Path is relative to this .vbs.\n"
        "Option Explicit\n"
        "Dim sh, fso, folder, bat, rc, cmd\n"
        'Set sh = CreateObject("WScript.Shell")\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\n'
        "folder = fso.GetParentFolderName(WScript.ScriptFullName)\n"
        f'bat = folder & "\\{bat_name}"\n'
        'cmd = "cmd.exe /c call """ & bat & """"\n'
        "rc = sh.Run(cmd, 0, True)\n"
        "If rc < 0 Then\n"
        "  rc = 1\n"
        "End If\n"
        "WScript.Quit rc\n"
    )


def write_job(job: LauncherJob, dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    bat_name = f"{job.name}.bat"
    written = [dest / bat_name]
    written[0].write_text(render_bat(job), encoding="utf-8", newline="\r\n")
    if job.hidden:
        vbs = dest / f"{job.name}_hidden.vbs"
        vbs.write_text(render_vbs(bat_name), encoding="utf-8", newline="\r\n")
        written.append(vbs)
    return written


def snapshot_production(dest: Path | None = None) -> list[Path]:
    """Copy live scheduled .bat/.vbs files for reference. Do not run them from here."""
    root = repo_root()
    out = dest if dest is not None else LAUNCHERS_DIR / "production_copies"
    written: list[Path] = []
    missing: list[str] = []
    for src_rel, dst_rel in PRODUCTION_SNAPSHOTS:
        src = root / src_rel
        if not src.exists():
            missing.append(src_rel)
            continue
        target = out / dst_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        written.append(target)
    copied = [f"  {src}  ->  {dst}" for src, dst in PRODUCTION_SNAPSHOTS if (root / src).exists()]
    skipped = [f"  {src}  (missing, skipped)" for src in missing]
    readme = out / "README.txt"
    readme.write_text(
        "\n".join(
            [
                "Snapshots of the live Task Scheduler launchers (as of copy time).",
                "",
                "Do not point Task Scheduler here. SCRIPT_PATH=%~dp0 in these files",
                "still expects the original notebooks/ or scripts/ folder, which is",
                "where the scheduled jobs still run.",
                "",
                "New jobs should be generated instead:",
                "  py -3.13 -m htoc_ml.datapipelines make-launcher --all",
                "",
                "Source -> copy:",
                *copied,
                *(["", "Skipped:"] + skipped if skipped else []),
                "",
            ]
        ),
        encoding="utf-8",
        newline="\r\n",
    )
    written.append(readme)
    return written


def install_share_helpers(dest: Path | None = None) -> list[Path]:
    """Copy share-probe bats next to generated launchers so %~dp0 works."""
    root = repo_root()
    out = dest if dest is not None else LAUNCHERS_DIR
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in ("ensure_htoc_data_share.bat", "run_loggedoff_share_probe.bat"):
        src = root / "notebooks" / name
        if not src.exists():
            raise FileNotFoundError(src)
        target = out / name
        shutil.copy2(src, target)
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write standardized .bat + hidden .vbs launchers under htoc_ml/launchers/."
    )
    parser.add_argument("--all", action="store_true", help="Write every built-in job.")
    parser.add_argument("--name", choices=sorted(JOBS), help="Write one built-in job.")
    parser.add_argument(
        "--out",
        default=str(LAUNCHERS_DIR),
        help="Destination directory (default: htoc_ml/launchers)",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Copy live production .bat/.vbs files into launchers/production_copies.",
    )
    parser.add_argument("--new-name", default="", help="Custom job file stem, e.g. run_myjob")
    parser.add_argument("--title", default="", help="Log title for a custom job")
    parser.add_argument("--python-args", default="", help='Arguments after python.exe, e.g. "-m htoc_ml.noi"')
    parser.add_argument("--log-prefix", default="", help="Log file prefix")
    parser.add_argument("--packages", default="", help="pip package list")
    parser.add_argument("--allow-nowork", action="store_true")
    parser.add_argument("--need-tc", action="store_true", help="Prepend ThreatConnect SDK on PYTHONPATH")
    parser.add_argument("--no-marker", action="store_true", help="Treat exit 0 as success (no PIPELINE_OK)")
    parser.add_argument("--no-hidden", action="store_true")
    args = parser.parse_args(argv)

    dest = Path(args.out)
    jobs: list[LauncherJob] = []
    if args.all:
        jobs.extend(JOBS.values())
    elif args.name:
        jobs.append(JOBS[args.name])
    elif args.new_name and args.python_args:
        stem = args.new_name if args.new_name.startswith("run_") else f"run_{args.new_name}"
        jobs.append(
            LauncherJob(
                key="",
                name=stem,
                title=args.title or stem,
                log_prefix=args.log_prefix or stem.removeprefix("run_"),
                python_args=args.python_args,
                packages=args.packages,
                allow_nowork=args.allow_nowork,
                need_threatconnect_path=args.need_tc,
                require_success_marker=not args.no_marker,
                hidden=not args.no_hidden,
            )
        )
    elif not args.snapshot:
        parser.error("Pass --all, --name <job>, --snapshot, or --new-name plus --python-args")

    written: list[Path] = []
    if jobs:
        written.extend(install_share_helpers(dest))
        (dest / "logs").mkdir(exist_ok=True)
        for job in jobs:
            written.extend(write_job(job, dest))
    if args.snapshot or args.all:
        snap_dest = dest / "production_copies" if dest == LAUNCHERS_DIR else dest / "production_copies"
        written.extend(snapshot_production(snap_dest))
    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
