htoc_ml Task Scheduler launchers
================================

Task Scheduler still points at the live files under notebooks/ and scripts/.
Do not retarget those tasks here until you are ready to cut over.

What lives here
---------------
ensure_htoc_data_share.bat     SMB probe (same as notebooks/)
run_loggedoff_share_probe.bat  Session-0 share + ThreatConnect smoke test
run_*.bat / run_*_hidden.vbs   Generated wrappers for htoc_ml modules
production_copies/             Exact snapshots of the live launchers
logs/                          Timestamped run logs (14-day rotation)

Standard contract (generated .bat)
----------------------------------
1. Resolve py -3.13, else %HTOC_SHARE_ROOT%\JA\Python313\python.exe
2. Call ensure_htoc_data_share.bat; exit 3 if the share is down
3. PYTHONUTF8=1, TMP=C:\Temp, PYTHONUSERBASE=%USERPROFILE%\AppData\Roaming\Python
4. Optional wheelhouse then PyPI pip install
5. pushd to htoc_ml/ (the folder with pyproject.toml) and run python -m ...
6. Capture stdout; require PIPELINE_OK (or PIPELINE_OK_NOWORK when allowed)
7. Hidden .vbs uses a path relative to itself (no hardcoded UNC)

Generate / refresh
------------------
  cd htoc_ml
  py -3.13 -m htoc_ml.datapipelines make-launcher --all
  py -3.13 -m htoc_ml.datapipelines make-launcher --name noi
  py -3.13 -m htoc_ml.datapipelines make-launcher --snapshot

New job (example)
-----------------
  py -3.13 -m htoc_ml.datapipelines make-launcher ^
    --new-name run_myjob ^
    --title "My pipeline" ^
    --python-args "-m htoc_ml.mypkg" ^
    --log-prefix myjob ^
    --packages "pandas openpyxl" ^
    --need-tc ^
    --allow-nowork

Point Task Scheduler at run_myjob_hidden.vbs, not the .bat.
Run whether the user is logged on or not; wscript.exe; highest privileges
only if the live jobs already use that.

production_copies/
-----------------
Reference only. Those files still use SCRIPT_PATH=%~dp0 and hardcoded UNC
in the .vbs files. Running them from this folder will not find the Python
scripts they were written next to.
