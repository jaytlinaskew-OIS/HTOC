# htoc_ml

Object-oriented package for HTOC production models. Live scheduled scripts
under `notebooks/` are unchanged. Cut over a `.bat` only after you have compared
outputs.

## Run PRISM (Threat Assessment)

Does **not** touch the live V5 / V5Daily Excel. Default output is
`%HTOC_SHARE_ROOT%\JA\PrismTest\Threat_Assessment_Scores.xlsx`.

```
cd htoc_ml
set PRISM_MODE=daily
py -3.13 -m htoc_ml.prism
```

`PRISM_MODE=weekly` is the 7-day `lastObserved` intake (V5). Daily is first-seen-today (V5Daily). Both call the same `score_frame` engine.

| Variable | Role |
|---|---|
| `PRISM_MODE` | `daily` or `weekly` |
| `HTOC_SHARE_ROOT` | UNC root |
| `PRISM_SAVE_DIR` | Workbook directory (default `JA\PrismTest`) |
| `PRISM_CONFIG_PATH` | ThreatConnect `config.json` |
| `PRISM_TC_PROJECT` | Folder that contains `utils/config.json` |

Cut over later by pointing `run_ThreatAssessScoringV5Daily.bat` at `py -3.13 -m htoc_ml.prism` and `run_ThreatAssessScoringV5.bat` at the same with `PRISM_MODE=weekly`. Set `PRISM_SAVE_DIR` to the production Threat Assessment Scores folder only after you have compared a test workbook.

I&W (`ThreatScoreIW`) is a downstream report, not part of this drop.

## Run the forecast

From the `htoc_ml/` directory (or after `uv pip install -e ./htoc_ml`):

```
py -3.13 -m htoc_ml.noi
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

Install editable (optional): `uv pip install -e ./htoc_ml`

Unit tests (no share mount): `py -3.13 -m pytest htoc_ml/tests`

## Map to the old script

| Old | New |
|---|---|
| `L`, `HORIZONS`, `TRAIN_DAYS`, … | `ForecastConfig` |
| `_to_int` / `_to_ts` | `htoc_ml.core.day` |
| `load_panel` + `lookup` | `ObservationPanel` + `IndicatorIndex` |
| `LOOKUP_FEAT` vs `lookup` | `panel.features` vs `panel.labels` |
| `featurize` | `FeatureBuilder.featurize` (name-keyed dict) |
| `train_cutoffs` | `CutoffSchedule` |
| `build_rows` / `stack` | `TrainingSet` |
| `new_model` + isotonic fit | `HorizonModel` |
| `noi_v4_bands.band` | `BandPolicy` |
| `to_production` | `ProductionReport` |
| top-level script + `PIPELINE_OK` | `ForecastRunner` (`Pipeline` subclass) |
| `noi_v4_feed_health` / `noi_v4_outage_impute` | copied into `htoc_ml.noi` (see below) |
| `noi_v4_performance_eval` | `htoc_ml.core.eval` (metrics/alerts/workbook) + `htoc_ml.noi.eval` (forecast join, bands, horizons) |

## Cut over the scheduled job

1. Capture goldens: `py -3.13 htoc_ml/tools/capture_golden.py`
2. Run the package into `htoc_ml/golden/new/{YYYYMMDD}` with `NOI_V4_AS_OF` and `NOI_V4_SAVE_DIR`
3. `py -3.13 htoc_ml/tools/compare_golden.py --as-of 20260822 20260826 20260828`
4. Point `run_NextObservedIndicatorV4.bat` at `py -3.13 -m htoc_ml.noi` (keep the share mount, log capture, and `PIPELINE_OK` grep)
5. Delete the copies under the old folder once the bat is cut over:
   - `noi_v4_feed_health.py`
   - `noi_v4_outage_impute.py`
   - `noi_v4_bands.py` (policy now lives in `htoc_ml.noi.bands`)
   - `noi_v4_performance_eval.py` (eval now lives in `htoc_ml.core.eval` + `htoc_ml.noi.eval`)
   - `NextObservedIndicatorV4.0.py` if nothing else imports it

Until step 5, the copies in this package are **intentional duplication**.

## Adding a model

Reusable as-is:

- `ObservationPanel` — every HTOC model reads `htoc_opdiv_obs_d{date}.csv`
- `htoc_ml.core.day` — epoch-integer days
- `Pipeline` — execute, check files, print `PIPELINE_OK`, map `PipelineError` to exit codes 2/3/4
- `htoc_ml.core.eval` — banded binary metrics, rolling alerts, traffic-light workbooks

Checklist:

1. Subclass `Pipeline`, implement `execute()`, return paths from `expected_outputs()`.
2. Put model-specific code in its own subpackage (`htoc_ml.prism`, …). Do not inherit `FeatureBuilder` or `BandPolicy` unless the new model actually uses those features.
3. Add a `tests/conftest.py` fixture that does not need the share.
4. Use `ForecastConfig`-style frozen dataclasses for tunables, with validation in `__post_init__`.
5. If the model is a classifier with a later binary label, call `count_bands` / `rates_from_counts` and pass your own `BandSpec`, `MetricAlertRule` list, and `LegendSpec`. Do not import `htoc_ml.noi.eval` for that.

`noi/` is the forecasting reference. `prism/` is the scoring reference (shared engine, two intake modes). `noi.eval` is the delayed-label eval reference (forecast CSVs joined to observation files).

### Changing NOI features

`FeatureBuilder.featurize` returns a dict. Column order is `FEATURE_NAMES`. Constraints are `MONOTONIC_CONSTRAINTS`. A test fails if those three disagree. To add a feature: compute it in `featurize`, add the name, add its constraint — all in `features.py`.

## Design decisions

**`early_stopping=False`.** sklearn turns early stopping on above 10k rows and holds out a random 10%. `stack()` emits each row once per horizon and cutoffs are only a few days apart, so a row's near-duplicates leak into that split. Capacity is bounded by `max_iter` / `max_depth` / `l2` instead, which also keeps the tree count reproducible.

**`cutoff_step` must be coprime with 7.** A multiple of 7 pins every training cutoff to one weekday and aliases `last_seen` / gap structure.

**AS-OF replay.** `NOI_V4_AS_OF` truncates the panel, so `day_max` and the label windows stop at that morning. Replay still reads today's settled files, so the last few days are slightly cleaner than they were live. Replayed days are recorded in `backfilled_forecasts.txt`.

**Masked labels are withheld, not counted as negatives.** `seen_next` cannot tell "this indicator went quiet" from "the feed was down". Those windows become NaN and `stack()` drops them per horizon.

**Feature list.** Held-out permutation (31 Aug 2026): `last_seen` is most of the AUC drop; horizon, `avg_gap`, `overdue`, `freq_100`, burstiness, and the 7/14/30 windows pay rent. Dropped as dead or redundant: `freq_1`, `freq_45`, `active_frac`, `dow`, `mom`, `tenure`.

**`Observed Today` vs `Frequency (1d)`.** `Observed Today` reads the raw panel. `Frequency (1d)` is `last_seen == 0` on (possibly imputed) features. A report line is a statement of fact; features may rest on a fill.

**Two indicator indexes.** Features may include imputed outage days. Labels never do. Mixing them poisons training.

**Banded eval is shared; NOI wiring is not.** `core.eval` scores a positive / negative / abstain call against a 0/1 label: confusion counts, rates, empty-denominator sentinels, rolling-floor alerts, traffic-light Excel. NOI's `eval` package is the adapter that loads `*_output_YYYYMMDD.csv`, joins observation files through `FeedHealth`, maps Highly likely / Low confidence / Possibly active, and adds the 7-day skip-day coverage columns. A future classifier should copy that adapter pattern, not the NOI column names.

**Three sentinels, not one blank.** `Missing Data to compute` is an absent feed. `Not settled yet` will rewrite itself. `Not applicable` is a scored day with an empty denominator (no High calls, or no actual positives). Printing 100% in that last case looks like a perfect day that never tested the model.

**Recall vs all positives includes abstain.** Decided-only recall hides Possibly Active misses. The mission metric's denominator is every actual positive.

**Performance eval used to live only in the live folder** (`noi_v4_performance_eval.py`). The scheduled runner now calls the package. Leave the live file until the `.bat` is cut over.
