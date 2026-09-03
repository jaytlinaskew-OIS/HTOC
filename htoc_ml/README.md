# htoc_ml

Production models and datapipelines live in `htoc_ml/src/htoc/`. Exploratory
Jupyter notebooks live in `htoc_ml/analysis/`. Live scheduled scripts under
repo-root `notebooks/` are unchanged until cutover.

## Run PRISM (Threat Assessment)

Does **not** touch the live V5 / V5Daily Excel. Default output is
`%HTOC_SHARE_ROOT%\JA\PrismTest\Threat_Assessment_Scores.xlsx`.

```
cd htoc_ml
set PRISM_MODE=daily
py -3.13 -m htoc.prism
```

`PRISM_MODE=weekly` is the 7-day `lastObserved` intake (V5). Daily is first-seen-today (V5Daily). Both call the same `score_frame` engine.

| Variable | Role |
|---|---|
| `PRISM_MODE` | `daily` or `weekly` |
| `HTOC_SHARE_ROOT` | UNC root |
| `PRISM_SAVE_DIR` | Workbook directory (default `JA\PrismTest`) |
| `PRISM_CONFIG_PATH` | ThreatConnect `config.json` |
| `PRISM_TC_PROJECT` | Folder with `utils/config.json` (default `%HTOC_SHARE_ROOT%\Data_Analytics\ThrearConnect-api-pull`) |

Cut over later by pointing `run_ThreatAssessScoringV5Daily.bat` at `py -3.13 -m htoc.prism` and `run_ThreatAssessScoringV5.bat` at the same with `PRISM_MODE=weekly`. Set `PRISM_SAVE_DIR` to the production Threat Assessment Scores folder only after you have compared a test workbook.

## Run ThreatScoreIW

Downstream I&W candidate workbook from recent ThreatConnect observations + PRISM scores + OpDiv multi-partner hits. Default output is `%HTOC_SHARE_ROOT%\JA\ThreatScoreIwTest\ThreatAssessI_W_YYYYMMDD.xlsx` (does **not** write the live `ThreatAssessI_W` folder until you set `THREAT_SCORE_IW_SAVE_DIR`).

```
cd htoc_ml
py -3.13 -m htoc.datapipelines.threat_score_iw
```

| Variable | Role |
|---|---|
| `HTOC_SHARE_ROOT` | UNC root |
| `THREAT_SCORE_IW_SAVE_DIR` | Output directory (default `JA\ThreatScoreIwTest`) |
| `THREAT_SCORE_IW_SCORES_XLSX` | PRISM scores workbook input |
| `THREAT_SCORE_IW_LOOKBACK_HOURS` | Rolling UTC lookback (default `48`) |
| `PRISM_CONFIG_PATH` | ThreatConnect `config.json` (shared with PRISM) |

## Datapipelines CLIs

Each datapipeline is one module under `src/htoc/datapipelines/` that wires shared
`htoc.core` (and model packages) — not a nested package tree. Live notebooks
under `notebooks/` are unchanged. Outputs default to `%HTOC_SHARE_ROOT%\JA\...Test\`
where a write could clobber a shared workbook.

```
cd htoc_ml
py -3.13 -m htoc.datapipelines search-tags --search phishing
py -3.13 -m htoc.datapipelines search-tags --ui
py -3.13 -m htoc.datapipelines triage
py -3.13 -m htoc.datapipelines iw-listing
py -3.13 -m htoc.datapipelines threat-score-iw
```

Optional extras: `uv pip install -e "./htoc_ml[datapipelines]"` (requests, tabulate, python-pptx, pdfplumber). Gradio UI: `uv pip install -e "./htoc_ml[datapipelines,datapipelines-ui]"`.

| Command | Replaces | Default write |
|---|---|---|
| `search-tags` | `notebooks/SearchIndicatorsByTags/` | reads live tags CSV + PRISM workbook; optional CSV under Saved Search Files |
| `triage` | `ThreatAssessment Scoring/tools/indicator_triage.py` | `JA\PrismTest\indicator_triage_results.csv` |
| `iw-listing` | `I&W Master Listing/frontEnd.ipynb` (PDFs) and the PPTX `src/` (`--from-pptx`) | `JA\IwListingTest\reported_iocs.xlsx` |
| `threat-score-iw` | `ThreatAssessment Scoring/ThreatScoreIW/` | `JA\ThreatScoreIwTest\ThreatAssessI_W_*.xlsx` |

The PowerPoint slide-template fill at the bottom of `frontEnd.ipynb` stays in the notebook.

## Launchers

Standard Task Scheduler wrappers live in `htoc_ml/launchers/`. Live jobs still
point at `notebooks/` — do not retarget them until cutover.

```
cd htoc_ml
py -3.13 -m htoc.datapipelines make-launcher --all
py -3.13 -m htoc.datapipelines make-launcher --name noi
py -3.13 -m htoc.datapipelines make-launcher --snapshot
```

`--all` writes `run_noi`, `run_prism_daily`, `run_prism_weekly`, `run_threat_score_iw`, plus analyst
CLI bats, copies `ensure_htoc_data_share.bat` next to them, and snapshots the
live `.bat`/`.vbs` files into `launchers/production_copies/` (reference only).

New job:

```
py -3.13 -m htoc.datapipelines make-launcher --new-name run_myjob --python-args "-m htoc.mypkg" --log-prefix myjob --packages "pandas openpyxl"
```

Point the scheduled task at `run_myjob_hidden.vbs`. The `.vbs` resolves the
sibling `.bat` from its own folder (no hardcoded UNC). Contract: share probe,
Python 3.13, log capture, `PIPELINE_OK` (optional `PIPELINE_OK_NOWORK`).
See `launchers/README.txt`.

## Run the forecast

From the `htoc_ml/` directory (or after `uv pip install -e ./htoc_ml`):

```
py -3.13 -m htoc.noi
```

Environment variables (same names as the live runner):

| Variable | Role |
|---|---|
| `HTOC_SHARE_ROOT` | UNC root, default `\\cscso1fsappv01\data\HTOC` |
| `HTOC_OBS_TEMPLATE` | Observation file pattern |
| `NOI_V4_SAVE_DIR` | Output directory |
| `NOI_V4_AS_OF` | `YYYYMMDD` replay date |
| `NOI_V4_MIN_FILE_COVERAGE` | Fail if fewer than this fraction of expected daily files are present (default `0`) |
| `NOI_V4_MAX_LAG_DAYS` | Warn if the newest observation is older than this (default `2`) |
| `NOI_V4_SKIP_EVAL` | `1` to skip the post-forecast performance eval (still imported from the live folder when unset) |

## Run daily reports (consolidate + performance eval)

Separate scheduled job from the forecast runner. Consolidates per-OpDiv
``{OpDiv}_output_YYYYMMDD.csv`` files into ``Full Daily Reports/full_daily_report_YYYYMMDD.csv``,
then runs day-to-day performance scoring.

```
py -3.13 -m htoc.noi.daily_reports
```

| Variable | Role |
|---|---|
| `NOI_V4_SAVE_DIR` | Same forecast output root as the main NOI job |
| `HTOC_SHARE_ROOT` / `HTOC_OBS_TEMPLATE` | Observation files for scoring |
| `NOI_V4_PERF_BACKFILL_START` / `NOI_V4_PERF_BACKFILL_END` | Optional `YYYYMMDD` range — eval-only backfill, skips consolidation |

Exit markers match the notebook script: `PIPELINE_OK`, `PIPELINE_OK_NOWORK`, or exit `3` if the consolidated report is missing. Performance eval errors are logged but non-fatal.

Install editable (optional): `uv pip install -e ./htoc_ml`

Unit tests (no share mount): `py -3.13 -m pytest htoc_ml/tests`

## Analysis notebooks

Exploratory work goes in `htoc_ml/analysis/` (by domain: `noi/`, `prism/`,
`threatconnect/`, `datapipelines/`, `adhoc/`). See `htoc_ml/analysis/README.md`.

- Install editable: `uv pip install -e ./htoc_ml`
- Notebooks import from `htoc`; reusable code moves into the package with tests
- Write CSVs/plots to `analysis/_outputs/` — not live or cutover share paths
- Name notebooks `YYYYMMDD_<topic>.ipynb`

Repo-root `notebooks/` remains the scheduled-job source until `.bat` cutover.

## Map to the old script

| Old | New |
|---|---|
| `L`, `HORIZONS`, `TRAIN_DAYS`, … | `ForecastConfig` |
| `_to_int` / `_to_ts` | `htoc.core.day` |
| `load_panel` + `lookup` | `ObservationData` + `IndicatorIndex` |
| `LOOKUP_FEAT` vs `lookup` | `observations.features` vs `observations.labels` |
| `featurize` | `featurize(lookback_days, dates, cutoff_day)` (name-keyed dict) |
| `train_cutoffs` | `CutoffSchedule` |
| `build_rows` / `stack` | `TrainingSet` |
| `new_model` + isotonic fit | `HorizonModel` |
| `noi_v4_bands.band` | `BandPolicy` |
| `to_production` | `ProductionReport` |
| top-level script + `PIPELINE_OK` | `run_*` function + `core.cli_exit.run_and_return_exit_code` |
| `next_observed_daily_reports_v4.py` | `htoc.noi.daily_reports` (`-m htoc.noi.daily_reports`) |
| `noi_v4_feed_health` / `noi_v4_outage_impute` | copied into `htoc.noi` (see below) |
| `noi_v4_performance_eval` | `htoc.core.eval` (metrics/alerts/workbook) + `htoc.noi.eval` (forecast join, bands, horizons) |

## Cut over the scheduled job

1. Run unit tests: `py -3.13 -m pytest htoc_ml/tests`
2. Compare a test run on the share (`NOI_V4_SAVE_DIR` → `JA\NextObserveV4Test`) against the live notebook for a few replay dates
3. Point `run_NextObservedIndicatorV4.bat` at `py -3.13 -m htoc.noi` (keep the share mount, log capture, and `PIPELINE_OK` grep)
4. Delete the copies under the old folder once the bat is cut over:
   - `noi_v4_feed_health.py`
   - `noi_v4_outage_impute.py`
   - `noi_v4_bands.py` (policy now lives in `htoc.noi.bands`)
   - `noi_v4_performance_eval.py` (eval now lives in `htoc.core.eval` + `htoc.noi.eval`)
   - `NextObservedIndicatorV4.0.py` if nothing else imports it

Until step 5, the copies in this package are **intentional duplication**.

## Adding a model

Reusable as-is:

- `ObservationData` — every HTOC model reads `htoc_opdiv_obs_d{date}.csv`
- `htoc.core.day` — epoch-integer days
- `run_and_return_exit_code()` — wrap a `run_*()` function that returns `list[Path]`; prints `PIPELINE_OK`, maps `PipelineError` to exit codes 2/3/4
- `core/threatconnect_presets.py` — shared TC owner/type lists for PRISM and ThreatScoreIW
- `htoc.core.eval` — **delayed-label** banded binary metrics, rolling alerts, traffic-light workbooks (`core/evaluation.py` is immediate sklearn metrics — different job)

Checklist:

1. Add a `run_<model>()` orchestrator with numbered step functions (see module docstring walkthrough).
2. Return `list[Path]` from the orchestrator; wire `__main__.py` through `run_and_return_exit_code`.
3. Put model-specific code in its own subpackage (`htoc.prism`, …). Do not reuse NOI feature or band helpers unless the new model actually uses them.
4. Add a `tests/conftest.py` fixture that does not need the share.
5. Use `ForecastConfig`-style frozen dataclasses for tunables, with validation in `__post_init__`.
6. If the model is a classifier with a later binary label, call `count_bands` / `rates_from_counts` and pass your own `BandSpec`, `MetricAlertRule` list, and `LegendSpec`. Do not import `htoc.noi.eval` for that.

`noi/` is the forecasting reference. `prism/` is the scoring reference (shared engine, two intake modes). `noi.eval` is the delayed-label eval reference (forecast CSVs joined to observation files).

### Changing NOI features

`featurize(lookback_days, dates, cutoff_day)` returns a dict. Column order is `FEATURE_NAMES`. Constraints are `MONOTONIC_CONSTRAINTS`. A test fails if those three disagree. To add a feature: compute it in `featurize`, add the name, add its constraint — all in `features.py`.

## Design decisions

**`early_stopping=False`.** sklearn turns early stopping on above 10k rows and holds out a random 10%. `stack()` emits each row once per horizon and cutoffs are only a few days apart, so a row's near-duplicates leak into that split. Capacity is bounded by `max_iter` / `max_depth` / `l2` instead, which also keeps the tree count reproducible.

**`cutoff_step` must be coprime with 7.** A multiple of 7 pins every training cutoff to one weekday and aliases `last_seen` / gap structure.

**AS-OF replay.** `NOI_V4_AS_OF` truncates the loaded observations, so `day_max` and the label windows stop at that morning. Replay still reads today's settled files, so the last few days are slightly cleaner than they were live. Replayed days are recorded in `backfilled_forecasts.txt`.

**Masked labels are withheld, not counted as negatives.** `seen_next` cannot tell "this indicator went quiet" from "the feed was down". Those windows become NaN and `stack()` drops them per horizon.

**Feature list.** Held-out permutation (31 Aug 2026): `last_seen` is most of the AUC drop; horizon, `avg_gap`, `overdue`, `freq_100`, burstiness, and the 7/14/30 windows pay rent. Dropped as dead or redundant: `freq_1`, `freq_45`, `active_frac`, `dow`, `mom`, `tenure`.

**`Observed Today` vs `Frequency (1d)`.** `Observed Today` reads the raw observation data. `Frequency (1d)` is `last_seen == 0` on (possibly imputed) features. A report line is a statement of fact; features may rest on a fill.

**Two indicator indexes.** Features may include imputed outage days. Labels never do. Mixing them poisons training.

**Banded eval is shared; NOI wiring is not.** `core.eval` scores a positive / negative / abstain call against a 0/1 label: confusion counts, rates, empty-denominator sentinels, rolling-floor alerts, traffic-light Excel. NOI's `eval` package is the adapter that loads `*_output_YYYYMMDD.csv`, joins observation files through `FeedHealth`, maps Highly likely / Low confidence / Possibly active, and adds the 7-day skip-day coverage columns. A future classifier should copy that adapter pattern, not the NOI column names.

**Three sentinels, not one blank.** `Missing Data to compute` is an absent feed. `Not settled yet` will rewrite itself. `Not applicable` is a scored day with an empty denominator (no High calls, or no actual positives). Printing 100% in that last case looks like a perfect day that never tested the model.

**Recall vs all positives includes abstain.** Decided-only recall hides Possibly Active misses. The mission metric's denominator is every actual positive.

**Performance eval used to live only in the live folder** (`noi_v4_performance_eval.py`). The scheduled runner now calls the package. Leave the live file until the `.bat` is cut over.
