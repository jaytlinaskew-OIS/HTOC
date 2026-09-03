"""Next Observed Indicator forecast process.

Walkthrough (start at run_next_observed_indicator_forecast):
  1. load_observation_data
  2. report_feed_health
  3. fill_outage_gaps
  4. fit_model_on_history
  5. score_indicators
  6. write_opdiv_csv
  7. write_opdiv_eval
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from htoc.core.day import to_day_index, to_timestamp
from htoc.core.observations import ObservationData
from htoc.core.pipeline import PipelineError
from htoc.noi.bands import BandPolicy
from htoc.noi.config import DATE_FMT, ForecastConfig
from htoc.noi.dataset import TrainingSet
from htoc.noi.features import featurize_window
from htoc.noi.feed_health import FeedHealth
from htoc.noi.model import HorizonModel
from htoc.noi.outage import (
    OutageContext,
    build_imputed_feature_lookup,
    format_findings,
    imputed_indicator_pairs,
    prepare_outage_context,
    verify_outage_recovery,
)
from htoc.noi.report import ProductionReport
from htoc.noi.schedule import CutoffSchedule


def run_next_observed_indicator_forecast(config: ForecastConfig | None = None) -> list[Path]:
    """Build the forecast and write OpDiv CSVs. Returns paths written."""
    config = config or ForecastConfig.from_env()
    observations = load_observation_data(config)
    health = report_feed_health(observations, config)
    outage_context = fill_outage_gaps(observations, health)
    model, training, as_of_day = fit_model_on_history(observations, health, config)
    scored = score_indicators(observations, training, model, outage_context, as_of_day, config)
    written = write_opdiv_csv(scored, as_of_day, config)
    write_opdiv_eval(as_of_day, config)
    return written


def load_observation_data(config: ForecastConfig) -> ObservationData:
    return ObservationData.load(
        obs_template=config.obs_template,
        train_days=config.train_days,
        end_date=config.as_of,
        min_file_coverage=config.min_file_coverage,
        max_lag_days=config.max_lag_days,
    )


def report_feed_health(observations: ObservationData, config: ForecastConfig) -> FeedHealth:
    return FeedHealth.from_data(observations.frame, today=config.as_of)


def fill_outage_gaps(observations: ObservationData, health: FeedHealth) -> OutageContext:
    context = prepare_outage_context(observations.frame, health)
    feature_lookup, _impute_report = build_imputed_feature_lookup(
        context, observations.labels.as_dict()
    )
    observations.set_features(feature_lookup)
    findings = verify_outage_recovery(context)
    if findings:
        print("WARNING: feed composition changed across an outage")
        for line in format_findings(findings):
            print(line)
    return context


def fit_model_on_history(observations: ObservationData, health: FeedHealth, config: ForecastConfig) -> tuple[HorizonModel, TrainingSet, int]:
    training = TrainingSet(
        config=config,
        labels=observations.labels,
        features=observations.features,
        health=health,
    )
    schedule = CutoffSchedule.build(observations.day_min, observations.day_max, config)
    train_df = training.build_rows(schedule.cutoffs, need_label=True)
    if train_df.empty:
        raise PipelineError("Training frame is empty after feature build.")

    model = HorizonModel(config, training).fit(train_df, schedule)

    if config.as_of is None:
        as_of_day = observations.day_max
    else:
        as_of_day = int(to_day_index(np.datetime64(pd.Timestamp(config.as_of).date())))
    return model, training, as_of_day


def score_indicators(observations: ObservationData, training: TrainingSet, model: HorizonModel, outage_context: OutageContext, as_of_day: int, config: ForecastConfig) -> pd.DataFrame:
    infer_df = training.build_rows([as_of_day], need_label=False)
    if infer_df.empty:
        raise PipelineError(
            f"No candidate indicators to score as-of {to_timestamp(as_of_day).date()}.",
            exit_code=3,
        )

    probabilities = model.predict(infer_df)
    bands = BandPolicy()
    out = infer_df[["opdiv", "indicator", "last_seen", "freq_7", "freq_30"]].copy()
    for j, horizon_days in enumerate(config.horizons):
        out[f"prob_{horizon_days}"] = probabilities[:, j]
        out[f"band_{horizon_days}"] = [
            bands.label(p, horizon_days, opdiv)
            for p, opdiv in zip(probabilities[:, j], out["opdiv"])
        ]

    imputed_pairs = imputed_indicator_pairs(
        outage_context, observations.labels.as_dict(), upto_day_index=as_of_day
    )
    out["observed_today"] = [
        observations.labels.really_seen(opdiv, indicator, as_of_day)
        for opdiv, indicator in zip(out["opdiv"], out["indicator"])
    ]
    out["basis"] = [
        "est" if (opdiv, indicator) in imputed_pairs else ""
        for opdiv, indicator in zip(out["opdiv"], out["indicator"])
    ]
    return out


def write_opdiv_csv(scored: pd.DataFrame, as_of_day: int, config: ForecastConfig) -> list[Path]:
    report = ProductionReport(config.horizons)
    opdiv_outputs = {
        opdiv: report.format_opdiv(group).reset_index(drop=True)
        for opdiv, group in scored.groupby("opdiv")
    }

    if not config.save_output:
        raise PipelineError("SAVE_OUTPUT is False")
    if not opdiv_outputs:
        raise PipelineError("no OpDiv outputs produced", exit_code=3)

    stamp = to_timestamp(as_of_day).strftime(DATE_FMT)
    written = report.write(opdiv_outputs, config.save_dir, stamp)
    record_as_of_replay_marker(stamp, config)
    return written


def write_opdiv_eval(as_of_day: int, config: ForecastConfig) -> None:
    """Run post-forecast eval. Failures are non-fatal: forecast CSVs already written."""
    if not config.run_eval:
        return
    from htoc.noi.eval import run_eval_after_forecast

    stamp = to_timestamp(as_of_day).strftime(DATE_FMT)
    if not run_eval_after_forecast(
        stamp,
        config.save_dir,
        config.htoc_share_root,
        consolidate_only=bool(config.as_of),
    ):
        print("WARN: PERF evaluation completed with errors (forecast outputs were still written)")


def record_as_of_replay_marker(stamp: str, config: ForecastConfig) -> None:
    if not config.as_of:
        return
    marker = Path(config.save_dir) / "backfilled_forecasts.txt"
    try:
        seen: set[str] = set()
        if marker.exists():
            seen = {ln.strip() for ln in marker.read_text(encoding="utf-8").splitlines() if ln.strip()}
        if stamp not in seen:
            with marker.open("a", encoding="utf-8") as fh:
                fh.write(f"{stamp}\n")
    except OSError as exc:
        print(f"WARN: could not record backfill marker: {exc}")
