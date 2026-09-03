"""Load forecasts, score horizons, write growing performance workbooks."""
from __future__ import annotations

import os
import re
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from htoc.core.eval.alerts import MetricAlertRule, collect_alerts
from htoc.core.eval.metrics import SENTINELS
from htoc.core.eval.workbook import upsert_history, write_grouped_workbook
from htoc.noi.bands import BAND_HIGH_P_OPDIV
from htoc.noi.eval.config import (
    BACKFILL_MARKER_NAME,
    DATE_FMT,
    EXCLUDE_FOLDERS,
    HORIZON_FILE_LABELS,
    PERF_COLUMNS,
    PERF_OPDIV_COLUMNS,
    PROVISIONAL_NOTE,
    EvalConfig,
)
from htoc.noi.eval.scoring import (
    nothing_scorable_row,
    score_banded_forecast,
)
from htoc.noi.feed_health import EARLY_SETTLE, EARLY_SETTLE_MIN_AGE, FeedHealth, SETTLE_DAYS

V4_NAME = re.compile(r"^.+_output_(\d{8})\.csv$", re.IGNORECASE)
LEGACY_NAME = re.compile(r"^(\d{8})\.csv$", re.IGNORECASE)


class PerformanceEval:
    def __init__(self, config: EvalConfig, health: FeedHealth | None = None) -> None:
        self.config = config
        self._health = health
        self._backfill_cache: set[str] | None = None

    def feed_health(self) -> FeedHealth:
        if self._health is None or self._health.obs_template != self.config.obs_template:
            self._health = FeedHealth.from_files(self.config.obs_template)
        return self._health

    def log(self, message: str, level: str = "INFO") -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[PERF {ts}] {level}: {message}"
        print(line, flush=True)
        try:
            self.config.logs_dir.mkdir(parents=True, exist_ok=True)
            log_fp = self.config.logs_dir / f"perf_eval_{datetime.today().strftime('%Y%m%d')}.log"
            with log_fp.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            print(f"[PERF {ts}] WARNING: could not write perf log: {exc}", flush=True)

    def log_error(self, context: str, exc: BaseException | None = None) -> None:
        if exc is None:
            tb = traceback.format_exc().strip()
            summary = context
        else:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
            summary = f"{context}: {exc}"
        self.log(summary, level="ERROR")
        if tb and tb != "NoneType: None":
            for tb_line in tb.splitlines():
                self.log(tb_line, level="ERROR")

    def forecast_report_path(self, day) -> Path:
        return self.config.daily_report_dir / f"full_daily_report_{day.strftime(DATE_FMT)}.csv"

    def horizon_workbook_path(self, horizon_days: int) -> Path:
        label = HORIZON_FILE_LABELS.get(horizon_days, f"{horizon_days}day")
        return self.config.performance_dir / f"performance_{label}.xlsx"

    def backfilled_dates(self) -> set[str]:
        if self._backfill_cache is not None:
            return self._backfill_cache
        dates: set[str] = set()
        marker = Path(self.config.save_root) / BACKFILL_MARKER_NAME
        try:
            if marker.exists():
                dates = {ln.strip() for ln in marker.read_text(encoding="utf-8").splitlines() if ln.strip()}
        except OSError as exc:
            self.log(f"could not read backfill marker {marker}: {exc}", level="WARNING")
        self._backfill_cache = dates
        return dates

    def load_observations(self, obs_date_str: str) -> pd.DataFrame:
        empty = pd.DataFrame(columns=["Indicator", "Partner", "Observed"])
        obs_fp = self.config.obs_template.format(date=obs_date_str)
        if not os.path.exists(obs_fp):
            self.log(f"observation file missing for {obs_date_str}: {obs_fp}", level="WARNING")
            return empty
        obs_frame = pd.read_csv(obs_fp, usecols=["indicator", "obs_date", "OpDiv"])
        obs_frame["Indicator"] = obs_frame["indicator"].astype(str).str.strip()
        obs_frame["Partner"] = obs_frame["OpDiv"].astype(str).str.strip()
        obs_frame["date"] = pd.to_datetime(obs_frame["obs_date"], errors="coerce").dt.normalize()
        obs_frame = obs_frame[
            obs_frame["Indicator"].ne("")
            & obs_frame["Indicator"].ne("nan")
            & obs_frame["Partner"].ne("")
            & obs_frame["Partner"].ne("nan")
        ]
        if obs_frame.empty:
            return empty
        eval_date = pd.to_datetime(obs_date_str, format=DATE_FMT, errors="coerce")
        if pd.notna(eval_date):
            obs_frame = obs_frame[obs_frame["date"] == eval_date]
        if obs_frame.empty:
            return empty
        out = obs_frame.drop_duplicates(["Indicator", "Partner"])[["Indicator", "Partner"]]
        out["Observed"] = 1
        return out

    def observed_union(self, start_exclusive, end_inclusive) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        cur = start_exclusive + timedelta(days=1)
        while cur <= end_inclusive:
            obs = self.load_observations(cur.strftime(DATE_FMT))
            if not obs.empty:
                frames.append(obs[["Indicator", "Partner"]])
            cur += timedelta(days=1)
        if not frames:
            return pd.DataFrame(columns=["Indicator", "Partner", "Observed"])
        out = pd.concat(frames, ignore_index=True).drop_duplicates(["Indicator", "Partner"])
        out["Observed"] = 1
        return out

    def load_forecasts(self, file_date: str) -> pd.DataFrame:
        root = Path(self.config.save_root)
        frames: list[pd.DataFrame] = []
        if not root.is_dir():
            self.log(f"data root does not exist: {root}", level="WARNING")
            return pd.DataFrame()
        for dirpath, _, filenames in os.walk(root):
            parts = set(Path(dirpath).parts)
            if parts & EXCLUDE_FOLDERS:
                continue
            partner = os.path.basename(dirpath)
            for fname in filenames:
                match = V4_NAME.match(fname) or LEGACY_NAME.match(fname)
                if not match or match.group(1) != file_date:
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    frame = pd.read_csv(fpath)
                    frame["Partner"] = partner
                    frame["FileDate"] = file_date
                    frames.append(frame)
                    print(f"loaded {fpath} ({len(frame)} rows)")
                except Exception as exc:
                    self.log(f"Skipping {fpath}: {exc}", level="WARNING")
        if not frames:
            print("No CSV files found for today.")
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def consolidate_daily_report(self, date_str: str | None = None) -> str | None:
        date_str = date_str or datetime.today().strftime(DATE_FMT)
        daily = self.load_forecasts(date_str)
        if daily.empty:
            self.log(f"no OpDiv forecast files found for {date_str}; skip consolidate.", level="WARNING")
            return None
        try:
            self.config.daily_report_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.config.daily_report_dir / f"full_daily_report_{date_str}.csv"
            daily.to_csv(output_path, index=False)
            print(f"Saved to {output_path} ({len(daily)} rows)")
            return str(output_path)
        except Exception as exc:
            self.log_error(f"consolidation failed for {date_str}", exc)
            return None

    def evaluate_horizon(self, horizon_days: int, eval_date) -> dict | None:
        forecast_date = eval_date - timedelta(days=horizon_days)
        forecast_date_str = forecast_date.strftime(DATE_FMT)
        eval_date_str = eval_date.strftime(DATE_FMT)
        forecast_fp = self.forecast_report_path(forecast_date)
        if not forecast_fp.exists():
            self.log(f"forecast daily report missing: {forecast_fp}", level="WARNING")
            return None
        predicted = pd.read_csv(forecast_fp)
        conf_col = f"Confidence: {horizon_days}-Day"
        missing = {"Indicator", "Partner", conf_col} - set(predicted.columns)
        if missing:
            raise RuntimeError(f"PERF: missing columns in {forecast_fp}: {sorted(missing)}")
        observed = self.observed_union(forecast_date, eval_date)
        if observed.empty:
            self.log(
                "no observation ground-truth in window "
                f"({forecast_date_str}, {eval_date_str}] for H={horizon_days}; skipping eval.",
                level="WARNING",
            )
            return None
        predicted["Indicator"] = predicted["Indicator"].astype(str).str.strip()
        predicted["Partner"] = predicted["Partner"].astype(str).str.strip()
        healthy, mask_info = self.feed_health().healthy_opdivs(
            candidate_opdivs=predicted["Partner"].unique(),
            start_exclusive=forecast_date,
            end_inclusive=eval_date,
        )
        excluded_info = mask_info["excluded"]
        provisional_info = mask_info.get("provisional", {})
        if excluded_info:
            for opdiv in sorted(excluded_info):
                self.log(
                    f"H={horizon_days} eval={eval_date_str}: excluding {opdiv} -- "
                    f"incomplete label window ({'; '.join(excluded_info[opdiv][:4])})",
                    level="WARNING",
                )
        if provisional_info:
            self.log(
                f"H={horizon_days} eval={eval_date_str}: scoring "
                f"{', '.join(sorted(provisional_info))} on days that have delivered but "
                f"not formally settled; rows are marked provisional with their "
                f"completeness and will be rewritten once those days settle"
            )
        excluded_mask = predicted["Partner"].isin(excluded_info.keys())
        excluded_pairs = int(excluded_mask.sum())
        excluded_pop = (
            predicted[excluded_mask]
            .groupby("Partner")
            .agg(pairs=("Indicator", "size"), uniq=("Indicator", "nunique"))
            .to_dict("index")
        )
        backfilled = forecast_date_str in self.backfilled_dates()
        predicted = predicted[predicted["Partner"].isin(healthy)]
        if predicted.empty:
            self.log(
                f"H={horizon_days} eval={eval_date_str}: every OpDiv has an incomplete "
                f"label window over ({forecast_date_str}, {eval_date_str}]; nothing scorable. "
                f"unsettled={len(mask_info['unsettled_days'])} missing={len(mask_info['missing_days'])}",
                level="WARNING",
            )
            return nothing_scorable_row(
                eval_date_str=eval_date_str,
                forecast_date_str=forecast_date_str,
                horizon_days=horizon_days,
                excluded_info=excluded_info,
                excluded_pairs=excluded_pairs,
                excluded_pop=excluded_pop,
                backfilled=backfilled,
            )
        return score_banded_forecast(
            predicted,
            observed,
            horizon_days=horizon_days,
            eval_date_str=eval_date_str,
            forecast_date_str=forecast_date_str,
            excluded_info=excluded_info,
            provisional_info=provisional_info,
            excluded_pairs=excluded_pairs,
            excluded_pop=excluded_pop,
            backfilled=backfilled,
        )

    def alert_rules(self, *, opdiv: str | None, horizon_days: int) -> list[MetricAlertRule]:
        cfg = self.config
        recall_floor = cfg.recall_all_opdiv_abs_min if opdiv else cfg.recall_all_abs_min
        rules = [
            MetricAlertRule(
                raw_column="_raw_recall_all",
                n_column="Decided (High + Low)",
                min_n=cfg.min_decided_count,
                abs_min=recall_floor,
                require_actual_positives=True,
                floor_template=(
                    "PERFORMANCE_ALERT ({tag}): Recall vs all positives dropped to "
                    "{value} (target minimum: {floor}, positives={positives})"
                ),
            ),
            MetricAlertRule(
                raw_column="_raw_recall_all",
                n_column="Decided (High + Low)",
                min_n=cfg.min_decided_count,
                drop_pp=cfg.recall_all_drop_pp_rolling,
                rolling_days=cfg.rolling_baseline_days,
                require_actual_positives=True,
                overall_only=True,
                drop_template=(
                    "PERFORMANCE_ALERT ({tag}): Recall vs all {value} fell below "
                    "{rolling_days}-day rolling average {rolling} "
                    "by more than {drop_pp}pp (positives={positives})"
                ),
            ),
            MetricAlertRule(
                raw_column="_raw_neg_prec",
                n_column="Predicted Low Count",
                min_n=cfg.min_decided_count,
                abs_min=cfg.low_neg_prec_abs_min,
                drop_pp=cfg.low_neg_prec_drop_pp_rolling,
                rolling_days=cfg.rolling_baseline_days,
                floor_template=(
                    "PERFORMANCE_ALERT ({tag}): Low-band negative precision dropped to "
                    "{value} (minimum standard: {floor}, n={n})"
                ),
                drop_template=(
                    "PERFORMANCE_ALERT ({tag}): Low-band negative precision {value} "
                    "fell below {rolling_days}-day rolling average {rolling} "
                    "by more than {drop_pp}pp (n={n})"
                ),
            ),
        ]
        watch_precision = opdiv is None or int(horizon_days) in BAND_HIGH_P_OPDIV.get(
            str(opdiv).strip().upper(), {}
        )
        if watch_precision:
            rules.insert(
                0,
                MetricAlertRule(
                    raw_column="_raw_precision",
                    n_column="Decided (High + Low)",
                    min_n=cfg.min_decided_count,
                    abs_min=cfg.high_prec_abs_min,
                    drop_pp=cfg.high_prec_drop_pp_rolling,
                    rolling_days=cfg.rolling_baseline_days,
                    drop_only_when_below_floor=True,
                    floor_template=(
                        "PERFORMANCE_ALERT ({tag}): Precision dropped to {value} "
                        "(floor: {floor}, n={n})"
                    ),
                    drop_template=(
                        "PERFORMANCE_ALERT ({tag}): Precision {value} fell below "
                        "{rolling_days}-day rolling average {rolling} "
                        "by more than {drop_pp}pp while under the floor (n={n})"
                    ),
                ),
            )
        return rules

    def maybe_alert(self, history: pd.DataFrame, row: dict, opdiv: str | None = None) -> list[str]:
        status = str(row.get("Data Status", ""))
        if status.startswith("Not scored") or PROVISIONAL_NOTE in status:
            return []
        horizon_days = int(row["Horizon (Days)"])
        tag = f"{horizon_days}-Day" if not opdiv else f"{horizon_days}-Day {opdiv}"
        return collect_alerts(
            history,
            row,
            self.alert_rules(opdiv=opdiv, horizon_days=horizon_days),
            tag=tag,
            slice_id=opdiv,
        )

    def check_forecast_coverage(self, today=None) -> list[str]:
        today = today or datetime.today().date()
        lookback = self.config.coverage_lookback_days
        missing = [
            today - timedelta(days=k)
            for k in range(lookback + 1)
            if not self.forecast_report_path(today - timedelta(days=k)).exists()
        ]
        expected = lookback + 1
        if not missing:
            self.log(f"forecast coverage: all {expected} of the last {expected} days present")
            return []
        missing_str = ", ".join(day.strftime(DATE_FMT) for day in sorted(missing))
        self.log(
            f"forecast coverage: {expected - len(missing)}/{expected} days present; "
            f"missing {missing_str}",
            level="WARNING",
        )
        recent = [day for day in missing if (today - day).days < self.config.coverage_alert_days]
        if not recent:
            return []
        return [
            f"PIPELINE_ALERT: no forecast written for "
            f"{', '.join(day.strftime(DATE_FMT) for day in sorted(recent))} "
            f"(checked {self.config.daily_report_dir}). The forecast job did not produce output -- "
            f"check its run log for a FATAL exit. Days older than {self.config.coverage_alert_days} "
            f"are reported in the performance log but not alerted; total gap over the last "
            f"{expected} days: {missing_str}"
        ]

    def run_eval_loop(self, eval_date, all_alerts: list[str]) -> int:
        error_count = 0
        for horizon_days in self.config.horizons:
            try:
                row = self.evaluate_horizon(horizon_days=horizon_days, eval_date=eval_date)
                if row is None:
                    continue
                wb_path = self.horizon_workbook_path(horizon_days)
                overall_hist, opdiv_hist = self._read_horizon_history(wb_path)
                overall_new = upsert_history(
                    overall_hist,
                    [row],
                    keys=["Evaluation Date", "Forecast Date", "Horizon (Days)"],
                    columns=PERF_COLUMNS,
                    sort_by=["Evaluation Date"],
                )
                _print_summary(row)
                alerts = self.maybe_alert(overall_hist, row)
                if alerts:
                    for line in alerts:
                        print(line)
                    all_alerts.extend(alerts)
                opdiv_rows = row.get("_opdiv_rows", [])
                for opdiv_row in opdiv_rows:
                    opd = str(opdiv_row.get("OpDiv", "")).strip()
                    if not opd:
                        continue
                    hist = (
                        opdiv_hist[opdiv_hist["OpDiv"].astype(str).str.strip() == opd]
                        if (not opdiv_hist.empty and "OpDiv" in opdiv_hist.columns)
                        else pd.DataFrame()
                    )
                    opdiv_alerts = self.maybe_alert(hist, opdiv_row, opdiv=opd)
                    if opdiv_alerts:
                        for line in opdiv_alerts:
                            print(line)
                        all_alerts.extend(opdiv_alerts)
                opdiv_new = opdiv_hist
                if opdiv_rows:
                    opdiv_new = upsert_history(
                        opdiv_hist,
                        opdiv_rows,
                        keys=["Evaluation Date", "Forecast Date", "Horizon (Days)", "OpDiv"],
                        columns=PERF_OPDIV_COLUMNS,
                        sort_by=["OpDiv", "Evaluation Date"],
                    )
                write_grouped_workbook(
                    wb_path,
                    overall_new,
                    opdiv_new if isinstance(opdiv_new, pd.DataFrame) else pd.DataFrame(),
                    group_col="OpDiv",
                    legend=self.config.legend(),
                )
            except Exception as exc:
                self.log_error(
                    f"{horizon_days}-day horizon failed for eval_date={eval_date.strftime(DATE_FMT)}",
                    exc,
                )
                error_count += 1
        return error_count

    def run(self, eval_date=None) -> bool:
        total_errors = 0
        try:
            self.config.performance_dir.mkdir(parents=True, exist_ok=True)
            self.config.alerts_dir.mkdir(parents=True, exist_ok=True)
            self.config.logs_dir.mkdir(parents=True, exist_ok=True)
            self.log("starting performance evaluation")
            if self.config.backfill_start and self.config.backfill_end:
                start_date = datetime.strptime(self.config.backfill_start, DATE_FMT).date()
                end_date = datetime.strptime(self.config.backfill_end, DATE_FMT).date()
                if end_date < start_date:
                    raise RuntimeError("NOI_V4_PERF_BACKFILL_END must be >= NOI_V4_PERF_BACKFILL_START")
                cur = start_date
                while cur <= end_date:
                    day_alerts: list[str] = []
                    try:
                        total_errors += self.run_eval_loop(eval_date=cur, all_alerts=day_alerts)
                        self._write_alerts(day_alerts, cur)
                    except Exception as exc:
                        self.log_error(f"backfill day {cur.strftime(DATE_FMT)} failed", exc)
                        total_errors += 1
                    cur += timedelta(days=1)
            else:
                if eval_date is None:
                    settled = datetime.today().date() - timedelta(days=SETTLE_DAYS)
                    newest = datetime.today().date() - timedelta(days=max(EARLY_SETTLE_MIN_AGE, 1))
                    eval_dates = (
                        [settled + timedelta(days=k) for k in range((newest - settled).days + 1)]
                        if EARLY_SETTLE
                        else [settled]
                    )
                    self.log(
                        f"scoring {eval_dates[0].strftime(DATE_FMT)} (settled) plus "
                        f"{len(eval_dates) - 1} provisional date(s) up to "
                        f"{eval_dates[-1].strftime(DATE_FMT)}"
                    )
                else:
                    settled = eval_date
                    eval_dates = [eval_date]
                for day in eval_dates:
                    day_alerts = []
                    total_errors += self.run_eval_loop(eval_date=day, all_alerts=day_alerts)
                    if day_alerts and day == settled:
                        self._write_alerts(day_alerts, day)
                coverage_alerts = self.check_forecast_coverage()
                if coverage_alerts:
                    today_str = datetime.today().strftime(DATE_FMT)
                    cov_fp = self.config.alerts_dir / f"alert_pipeline_{today_str}.txt"
                    cov_fp.write_text("\n".join(coverage_alerts) + "\n", encoding="utf-8")
                    self.log(f"wrote pipeline alerts to {cov_fp}", level="WARNING")
            if total_errors:
                self.log(f"evaluation finished with {total_errors} error(s)", level="WARNING")
                return False
            self.log("evaluation finished successfully")
            return True
        except Exception as exc:
            self.log_error("performance evaluation aborted", exc)
            return False

    def _write_alerts(self, alerts: list[str], day: date) -> None:
        if not alerts:
            return
        alert_fp = self.config.alerts_dir / f"alert_{day.strftime(DATE_FMT)}.txt"
        alert_fp.write_text("\n".join(alerts) + "\n", encoding="utf-8")
        self.log(f"wrote metric alerts to {alert_fp}")

    def _read_horizon_history(self, path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
        if not path.exists():
            return pd.DataFrame(), pd.DataFrame()
        try:
            with pd.ExcelFile(path) as xf:
                overall = (
                    _normalize_perf_history(pd.read_excel(xf, sheet_name="overall"))
                    if "overall" in xf.sheet_names
                    else pd.DataFrame()
                )
                opdiv_frames = []
                for sheet in xf.sheet_names:
                    if sheet in {"overall", "Legend"}:
                        continue
                    frame = _normalize_perf_history(pd.read_excel(xf, sheet_name=sheet))
                    if "OpDiv" not in frame.columns:
                        frame["OpDiv"] = sheet
                    opdiv_frames.append(frame)
            opdiv = pd.concat(opdiv_frames, ignore_index=True) if opdiv_frames else pd.DataFrame()
            return overall, opdiv
        except Exception as exc:
            self.log_error(f"could not read existing workbook {path}; starting fresh", exc)
            return pd.DataFrame(), pd.DataFrame()

    def run_after_forecast(self, stamp: str, consolidate_only: bool = False) -> bool:
        try:
            self.log(f"starting post-forecast evaluation (stamp={stamp})")
            out = self.consolidate_daily_report(stamp)
            if out is None:
                self.log(f"consolidation produced no report for stamp={stamp}", level="WARNING")
            else:
                self.log(f"consolidated daily report: {out}")
            if consolidate_only:
                self.log(f"consolidate-only mode (stamp={stamp}); skipping scoring pass")
                return out is not None
            return self.run()
        except Exception as exc:
            self.log_error("post-forecast evaluation failed (non-fatal)", exc)
            return False


def _print_summary(row: dict) -> None:
    def fmt(key: str) -> str:
        value = row.get(key)
        return str(value) if value in SENTINELS else f"{value}%"

    horizon = row["Horizon (Days)"]
    print(
        f"PERF SUMMARY  Horizon={horizon}-Day  "
        f"Eval={row['Evaluation Date']}  Forecast={row['Forecast Date']}  "
        f"UniqueIndicators={row['Unique Indicators Scored']}  "
        f"Pairs={row['Scored Pairs (Indicator-OpDiv)']}  "
        f"Decided={row['Decided (High + Low)']}  "
        f"Coverage={fmt('Coverage (%)')}"
    )
    print(
        f"  TARGET Recall vs all positives={fmt('Recall - High vs All Positives (%)')}  "
        f"Precision floor={fmt('Precision - High (%)')}  "
        f"AccuracyHigh={fmt('Accuracy - High (%)')}  "
        f"Recall(decided)={fmt('Recall - High (%)')}"
    )
    if int(row["Horizon (Days)"]) == 1:
        print(
            f"  SKIP-DAY 7-Day High vs 1-Day pos="
            f"{fmt('Recall - 7-Day High vs 1-Day Positives (%)')}  "
            f"1-Day or 7-Day High="
            f"{fmt('Recall - 1-Day or 7-Day High vs All Positives (%)')}  "
            f"PA observed already 7-Day High="
            f"{row.get('Possibly Active Observed already 7-Day High')}"
        )
    print(
        f"  Accuracy={fmt('Accuracy (%)')}  "
        f"(do not use for High-band health)  "
        f"F1={fmt('F1 Score - High (%)')}"
    )
    print(
        f"  Specificity={fmt('Specificity - True Negative Rate (%)')}  "
        f"BalancedAcc={fmt('Balanced Accuracy (%)')}"
    )
    print(
        f"  HIGH band: TP={row['True Positives (High)']}/{row['Predicted High Count']}  "
        f"FP={row['False Positives (High)']}  FN={row['False Negatives (High)']}"
    )
    print(
        f"  LOW  band: TN={row['True Negatives (Low)']}/{row['Predicted Low Count']}  "
        f"FP={row['False Positives (Low)']}  "
        f"Neg Precision={fmt('Negative Precision - Low (%)')}"
    )
    print(
        f"  POSS band: n={row['Possibly Active Count']}  "
        f"EndedHigh={row['Possibly Active Ended High (Observed)']}  "
        f"EndedLow={row['Possibly Active Ended Low (Not Observed)']}  "
        f"EndedHighRate={fmt('Possibly Active Ended High Rate (%)')}  "
        f"AvgProb={fmt('Avg Prob - Possibly Active (%)')}  "
        f"(EndedHighAvg={fmt('Avg Prob - Possibly Active Ended High (%)')}, "
        f"EndedLowAvg={fmt('Avg Prob - Possibly Active Ended Low (%)')})"
    )


def _normalize_perf_history(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    if "Total Indicators Scored" in frame.columns:
        if "Scored Pairs (Indicator-OpDiv)" not in frame.columns:
            frame = frame.rename(columns={"Total Indicators Scored": "Scored Pairs (Indicator-OpDiv)"})
        else:
            frame = frame.drop(columns=["Total Indicators Scored"])
        if "Unique Indicators Scored" not in frame.columns:
            frame["Unique Indicators Scored"] = pd.NA
    if "False Negatives (Low)" in frame.columns and "False Negatives (High)" not in frame.columns:
        frame = frame.rename(columns={"False Negatives (Low)": "False Negatives (High)"})
    if "F1 Score (%)" in frame.columns and "F1 Score - High (%)" not in frame.columns:
        frame = frame.rename(columns={"F1 Score (%)": "F1 Score - High (%)"})
    return _backfill_balanced_accuracy(_backfill_accuracy_high(frame))


def _backfill_accuracy_high(frame: pd.DataFrame) -> pd.DataFrame:
    from htoc.core.eval.metrics import NOT_APPLICABLE

    need = ["True Positives (High)", "False Positives (High)", "False Negatives (High)"]
    if any(col not in frame.columns for col in need):
        return frame
    tp, fp, fn = (pd.to_numeric(frame[col], errors="coerce") for col in need)
    union = tp + fp + fn
    acc_h = (tp / union).where(union > 0) * 100
    col = "Accuracy - High (%)"
    rounded = acc_h.round(2)
    if col not in frame.columns:
        frame[col] = rounded
    else:
        existing = pd.to_numeric(frame[col], errors="coerce")
        frame[col] = frame[col].where(existing.notna(), rounded)
    frame[col] = frame[col].where(frame[col].notna(), NOT_APPLICABLE)
    if "_raw_accuracy_high" in frame.columns:
        raw = pd.to_numeric(frame["_raw_accuracy_high"], errors="coerce")
        frame["_raw_accuracy_high"] = raw.where(raw.notna(), acc_h / 100)
    else:
        frame["_raw_accuracy_high"] = acc_h / 100
    return frame


def _backfill_balanced_accuracy(frame: pd.DataFrame) -> pd.DataFrame:
    from htoc.core.eval.metrics import NOT_APPLICABLE

    need = [
        "True Negatives (Low)",
        "False Positives (High)",
        "True Positives (High)",
        "False Positives (Low)",
    ]
    if any(col not in frame.columns for col in need):
        return frame
    tn, fp, tp, fn = (pd.to_numeric(frame[col], errors="coerce") for col in need)
    neg, pos = tn + fp, tp + fn
    spec = (tn / neg).where(neg > 0) * 100
    rec = (tp / pos).where(pos > 0) * 100
    bal = (spec + rec) / 2
    for col, vals in (
        ("Specificity - True Negative Rate (%)", spec),
        ("Balanced Accuracy (%)", bal),
    ):
        rounded = vals.round(2)
        if col not in frame.columns:
            frame[col] = rounded
        else:
            existing = pd.to_numeric(frame[col], errors="coerce")
            frame[col] = frame[col].where(existing.notna(), rounded)
        frame[col] = frame[col].where(frame[col].notna(), NOT_APPLICABLE)
    if "_raw_balanced_acc" in frame.columns:
        raw = pd.to_numeric(frame["_raw_balanced_acc"], errors="coerce")
        frame["_raw_balanced_acc"] = raw.where(raw.notna(), bal / 100)
    else:
        frame["_raw_balanced_acc"] = bal / 100
    return frame


def run_eval_after_forecast(
    stamp: str,
    save_dir: str,
    htoc_share_root: str | None = None,
    consolidate_only: bool = False,
) -> bool:
    config = EvalConfig.from_paths(save_dir, htoc_share_root or "")
    return PerformanceEval(config).run_after_forecast(stamp, consolidate_only=consolidate_only)
