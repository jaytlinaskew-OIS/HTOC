"""Cross-partner indicator spread analysis (Next Observed Relationships)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve

from htoc.core.day import to_date, to_timestamp
from htoc.core.eval.metrics import parse_probability_percent
from htoc.core.observations import ObservationData
from htoc.noi.config import ForecastConfig
from htoc.noi.dataset import TrainingSet
from htoc.noi.features import FEATURE_NAMES, featurize
from htoc.noi.feed_health import FeedHealth

HORIZON = 7
HORIZON_1 = 1
SOURCE_ACTIVE_DAYS = 7
SEVERITY_KEEP = frozenset({"medium", "high", "critical"})
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2}
MIN_PAIR_EVENTS = 30
EVAL_TAIL_DAYS = 30
CUTOFF_STEP = 5
NOI_PROB_COL = "Probability: 7-Day"
V4_NAME = re.compile(r"^.+_output_(\d{8})\.csv$", re.IGNORECASE)
EXCLUDE_DIRS = frozenset(
    {"automation scripts", "Logs", "LogsBackup", "Full Daily Reports", "Performance", "Possibly Active Review", "Alerts"}
)


@dataclass(frozen=True)
class AnalysisConfig:
    htoc_share_root: str
    noi_save_dir: Path
    prism_xlsx: Path
    out_dir: Path
    train_days: int = 220
    lookback_days: int = 100
    horizon: int = HORIZON
    eval_tail_days: int = EVAL_TAIL_DAYS
    min_pair_events: int = MIN_PAIR_EVENTS
    test_noi_save_dir: Path | None = None

    @classmethod
    def production(cls, repo_root: Path | None = None) -> "AnalysisConfig":
        from htoc.core import paths as htoc_paths

        share = htoc_paths.DEFAULT_SHARE_ROOT
        root = repo_root or Path(".")
        return cls(
            htoc_share_root=share,
            noi_save_dir=Path(share) / "JA" / "NextObserveV4Test",
            prism_xlsx=htoc_paths.threat_assessment_scores_xlsx(share),
            out_dir=root / "htoc_ml" / "analysis" / "_outputs" / "next_observed_relationships",
        )


def load_prism_scores(path: Path) -> pd.DataFrame:
    frame = pd.read_excel(path, sheet_name="PRISM Scores")
    frame = frame.rename(columns=str.strip)
    indicator_col = next((c for c in frame.columns if c.lower() == "indicator"), "Indicator")
    out = frame.copy()
    out["indicator"] = out[indicator_col].astype(str).str.strip()
    out["severity"] = out.get("Severity", pd.Series(dtype=str)).astype(str).str.strip().str.lower()
    out["prism_score"] = pd.to_numeric(out.get("PRISM Score", np.nan), errors="coerce")
    if "Partner Count" in out.columns:
        out["partner_count"] = pd.to_numeric(out["Partner Count"], errors="coerce").fillna(0)
    elif "Partners" in out.columns:
        out["partner_count"] = out["Partners"].astype(str).str.count(",") + 1
        out.loc[out["Partners"].astype(str).str.strip().eq(""), "partner_count"] = 0
    else:
        out["partner_count"] = 0
    if "Explanation" in out.columns:
        out["vt_score"] = pd.to_numeric(
            out["Explanation"].astype(str).str.extract(r"VT score:\s*(\d+)", expand=False),
            errors="coerce",
        )
    else:
        out["vt_score"] = np.nan
    out = out.drop_duplicates("indicator", keep="last")
    return out[["indicator", "severity", "prism_score", "partner_count", "vt_score"]]


def os_walk_partner_dirs(save_dir: Path):
    import os

    for dirpath, dirnames, filenames in os.walk(save_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        parts = set(Path(dirpath).parts)
        if parts & EXCLUDE_DIRS:
            continue
        yield dirpath, dirnames, filenames


def load_noi_for_date(save_dir: Path, file_date: str) -> pd.DataFrame:
    cached = preload_noi_forecasts(save_dir, {file_date})
    return cached.get(file_date, pd.DataFrame())


def preload_noi_forecasts(save_dir: Path, needed_dates: set[str]) -> dict[str, pd.DataFrame]:
    """Load all NOI CSVs for needed_dates in one filesystem walk."""
    buckets: dict[str, list[pd.DataFrame]] = {d: [] for d in needed_dates}
    if not save_dir.is_dir():
        return {d: pd.DataFrame() for d in needed_dates}
    for dirpath, _, filenames in os_walk_partner_dirs(save_dir):
        partner = Path(dirpath).name
        for fname in filenames:
            match = V4_NAME.match(fname)
            if not match:
                continue
            file_date = match.group(1)
            if file_date not in needed_dates:
                continue
            try:
                chunk = pd.read_csv(Path(dirpath) / fname)
                chunk["Partner"] = partner
                buckets[file_date].append(chunk)
            except OSError:
                continue
    out: dict[str, pd.DataFrame] = {}
    for file_date, frames in buckets.items():
        if not frames:
            out[file_date] = pd.DataFrame()
            continue
        merged = pd.concat(frames, ignore_index=True)
        merged["Indicator"] = merged["Indicator"].astype(str).str.strip()
        merged["Partner"] = merged["Partner"].astype(str).str.strip()
        if NOI_PROB_COL in merged.columns:
            merged["noi_prob_7"] = parse_probability_percent(merged[NOI_PROB_COL]) / 100.0
        else:
            merged["noi_prob_7"] = np.nan
        out[file_date] = merged
    return out


def _noi_lookup(noi_day: pd.DataFrame) -> dict[tuple[str, str], float]:
    if noi_day.empty:
        return {}
    return {
        (str(r.Partner), str(r.Indicator)): float(r.noi_prob_7) if pd.notna(r.noi_prob_7) else np.nan
        for r in noi_day.itertuples(index=False)
    }


def _indicator_index(labels: dict) -> dict[str, dict[str, np.ndarray]]:
    by_ind: dict[str, dict[str, np.ndarray]] = {}
    for (opdiv, indicator), dates in labels.items():
        by_ind.setdefault(indicator, {})[opdiv] = dates
    return by_ind


def _active_within(dates: np.ndarray | None, cutoff_day: int, within_days: int) -> bool:
    if dates is None or dates.size == 0:
        return False
    start = cutoff_day - within_days + 1
    lo = np.searchsorted(dates, start, side="left")
    hi = np.searchsorted(dates, cutoff_day, side="right")
    return hi > lo


def _seen_on_day(dates: np.ndarray | None, day: int) -> bool:
    if dates is None or dates.size == 0:
        return False
    i = np.searchsorted(dates, day, side="left")
    return i < dates.size and dates[i] == day


def cutoff_days(day_min: int, day_max: int, step: int = CUTOFF_STEP) -> list[int]:
    return list(range(day_min + step, day_max - HORIZON + 1, step))


def _active_indicators_by_source_cutoff(
    by_indicator: dict[str, dict[str, np.ndarray]],
    opdivs: list[str],
    cutoffs: list[int],
    eligible: set[str],
    within_days: int,
) -> dict[tuple[str, int], list[str]]:
    """For each (source, cutoff), indicators active within `within_days` at source."""
    result: dict[tuple[str, int], list[str]] = {}
    for indicator in eligible:
        opdiv_dates = by_indicator.get(indicator)
        if not opdiv_dates:
            continue
        for source in opdivs:
            dates = opdiv_dates.get(source)
            if dates is None:
                continue
            for cutoff_day in cutoffs:
                if _active_within(dates, cutoff_day, within_days):
                    result.setdefault((source, cutoff_day), []).append(indicator)
    return result


def build_event_table(
    observations: ObservationData,
    prism: pd.DataFrame,
    health: FeedHealth,
    forecast_config: ForecastConfig,
    *,
    noi_save_dir: Path,
    medium_plus_only: bool = True,
) -> pd.DataFrame:
    labels = observations.labels.as_dict()
    training = TrainingSet(
        config=forecast_config,
        labels=observations.labels,
        features=observations.features,
        health=health,
    )
    opdivs = observations.labels.opdivs()
    all_cutoffs = cutoff_days(observations.day_min, observations.day_max)
    label_mask = training.build_label_mask(all_cutoffs, opdivs)

    prism_map = prism.set_index("indicator")
    medium_plus = set(prism.loc[prism["severity"].isin(SEVERITY_KEEP), "indicator"])
    by_indicator = _indicator_index(labels)
    eligible_indicators = medium_plus & set(by_indicator.keys()) if medium_plus_only else set(by_indicator.keys())

    needed_dates = {to_timestamp(c).strftime("%Y%m%d") for c in all_cutoffs}
    noi_cache = preload_noi_forecasts(noi_save_dir, needed_dates)
    active_map = _active_indicators_by_source_cutoff(
        by_indicator, opdivs, all_cutoffs, eligible_indicators, SOURCE_ACTIVE_DAYS
    )

    feat_cache: dict[tuple[str, str, int], dict[str, float]] = {}
    empty_dates = np.array([], dtype=int)

    def get_feat(opdiv: str, indicator: str, cutoff_day: int) -> dict[str, float]:
        key = (opdiv, indicator, cutoff_day)
        if key not in feat_cache:
            dates = labels.get((opdiv, indicator), empty_dates)
            feat_cache[key] = featurize(forecast_config.lookback_days, dates, cutoff_day)
        return feat_cache[key]

    records: list[dict] = []

    for cutoff_day in all_cutoffs:
        cutoff_str = to_timestamp(cutoff_day).strftime("%Y%m%d")
        noi_lu = _noi_lookup(noi_cache.get(cutoff_str, pd.DataFrame()))

        for source in opdivs:
            for indicator in active_map.get((source, cutoff_day), []):
                opdiv_dates = by_indicator[indicator]
                prism_row = prism_map.loc[indicator]
                if isinstance(prism_row, pd.DataFrame):
                    prism_row = prism_row.iloc[-1]

                source_feat = get_feat(source, indicator, cutoff_day)
                for target in opdivs:
                    if source == target:
                        continue
                    target_dates = opdiv_dates.get(target, empty_dates)
                    if _seen_on_day(target_dates, cutoff_day):
                        continue
                    if not label_mask.get((target, cutoff_day, HORIZON), True):
                        continue

                    spread = observations.labels.seen_next(target_dates, cutoff_day, HORIZON)
                    spread_1 = observations.labels.seen_next(target_dates, cutoff_day, HORIZON_1)
                    target_feat = get_feat(target, indicator, cutoff_day)

                    records.append(
                        {
                            "cutoff_day": cutoff_day,
                            "cutoff_date": to_date(cutoff_day),
                            "indicator": indicator,
                            "source_partner": source,
                            "target_partner": target,
                            "spread_7d": int(spread),
                            "spread_1d": int(spread_1),
                            "noi_prob_7": noi_lu.get((target, indicator), np.nan),
                            "severity": str(prism_row["severity"]),
                            "prism_score": float(prism_row["prism_score"])
                            if pd.notna(prism_row["prism_score"])
                            else np.nan,
                            "partner_count": float(prism_row.get("partner_count", 0) or 0),
                            **{f"src_{k}": v for k, v in source_feat.items()},
                            **{f"tgt_{k}": v for k, v in target_feat.items()},
                        }
                    )

    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def temporal_split(events: pd.DataFrame, eval_tail_days: int = EVAL_TAIL_DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    max_day = int(events["cutoff_day"].max())
    min_eval = max_day - eval_tail_days
    train = events[events["cutoff_day"] < min_eval].copy()
    eval_df = events[events["cutoff_day"] >= min_eval].copy()
    return train, eval_df


def _feature_sets() -> dict[str, list[str]]:
    src = [f"src_{n}" for n in FEATURE_NAMES]
    tgt = [f"tgt_{n}" for n in FEATURE_NAMES]
    return {
        "M0": ["noi_prob_7"],
        "M1": src,
        "M2": src + tgt + ["noi_prob_7"],
        "M3": src + tgt + ["noi_prob_7", "prism_score", "partner_count", "severity_ord"],
    }


def _add_severity_ord(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["severity_ord"] = out["severity"].map(lambda s: SEVERITY_RANK.get(str(s).lower(), 3))
    return out


def train_models(train: pd.DataFrame) -> dict[str, HistGradientBoostingClassifier]:
    train = _add_severity_ord(train)
    models: dict[str, HistGradientBoostingClassifier] = {}
    y = train["spread_7d"].astype(int)
    for name, cols in _feature_sets().items():
        if name == "M0":
            continue
        X = train[cols].fillna(0.0).to_numpy(float)
        model = HistGradientBoostingClassifier(max_depth=4, max_iter=200, random_state=42)
        model.fit(X, y)
        models[name] = model
    return models


def score_events(events: pd.DataFrame, models: dict[str, HistGradientBoostingClassifier]) -> pd.DataFrame:
    out = _add_severity_ord(events.copy())
    out["spread_prob_m0"] = out["noi_prob_7"].fillna(0.0)
    for name, cols in _feature_sets().items():
        if name == "M0":
            continue
        X = out[cols].fillna(0.0).to_numpy(float)
        out[f"spread_prob_{name.lower()}"] = models[name].predict_proba(X)[:, 1]
    out["spread_probability"] = out["spread_prob_m2"]
    return out


def metrics_at_precision_threshold(
    y_true: np.ndarray, y_score: np.ndarray, target_precision: float = 0.20
) -> tuple[float, float]:
    if y_true.sum() == 0:
        return 0.0, 0.0
    prec, rec, _ = precision_recall_curve(y_true, y_score)
    mask = prec >= target_precision
    if not mask.any():
        return 0.0, 0.0
    idx = int(np.where(mask)[0][np.argmax(rec[mask])])
    return float(prec[idx]), float(rec[idx])


def pair_metrics(group: pd.DataFrame, prob_col: str = "spread_probability") -> dict:
    y = group["spread_7d"].to_numpy(int)
    scores = group[prob_col].fillna(0).to_numpy(float)
    n = len(group)
    spread_rate = float(y.mean()) if n else 0.0
    avg_prob = float(scores.mean()) if n else 0.0
    avg_prism = float(group["prism_score"].mean()) if n else 0.0
    prec20, rec20 = metrics_at_precision_threshold(y, scores, 0.20)
    auc_pr = average_precision_score(y, scores) if y.sum() > 0 and n > 1 else float("nan")
    pair_score = rec20 * (avg_prism / 1000.0 if avg_prism == avg_prism else 0.5) * np.log1p(n)
    return {
        "N_Events": n,
        "Spread_Rate_7d": round(spread_rate * 100, 2),
        "Avg_Spread_Prob": round(avg_prob, 4),
        "Avg_PRISM_Score": round(avg_prism, 1),
        "Precision_at_20pct": round(prec20 * 100, 2),
        "Recall_at_20pct": round(rec20 * 100, 2),
        "AUC_PR": round(auc_pr, 4) if auc_pr == auc_pr else np.nan,
        "pair_score": pair_score,
    }


def top_partner_pairs(eval_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    rows: list[dict] = []
    for (source, target), group in eval_df.groupby(["source_partner", "target_partner"]):
        if len(group) < MIN_PAIR_EVENTS:
            continue
        m = pair_metrics(group)
        rows.append({"Source": source, "Target": target, **m})
    if not rows:
        return pd.DataFrame()
    ranked = pd.DataFrame(rows).sort_values("pair_score", ascending=False).head(top_n)
    ranked.insert(0, "Rank", range(1, len(ranked) + 1))
    return ranked[
        [
            "Rank",
            "Source",
            "Target",
            "Spread_Rate_7d",
            "Avg_Spread_Prob",
            "Precision_at_20pct",
            "Recall_at_20pct",
            "N_Events",
            "Avg_PRISM_Score",
            "AUC_PR",
        ]
    ]


def plot_pair_heatmap(eval_df: pd.DataFrame, top_pairs: pd.DataFrame, out_path: Path) -> None:
    partners = sorted(set(eval_df["source_partner"]) | set(eval_df["target_partner"]))
    matrix = pd.DataFrame(0.0, index=partners, columns=partners)
    for (source, target), group in eval_df.groupby(["source_partner", "target_partner"]):
        if len(group) >= MIN_PAIR_EVENTS:
            matrix.loc[source, target] = group["spread_7d"].mean() * 100

    top_set = set(zip(top_pairs["Source"], top_pairs["Target"])) if not top_pairs.empty else set()

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(partners)))
    ax.set_yticks(range(len(partners)))
    ax.set_xticklabels(partners, rotation=45, ha="right")
    ax.set_yticklabels(partners)
    ax.set_xlabel("Target partner")
    ax.set_ylabel("Source partner")
    ax.set_title("Spread rate (%) — medium+ PRISM (eval window)")
    plt.colorbar(im, ax=ax, label="Spread rate %")
    for i, src in enumerate(partners):
        for j, tgt in enumerate(partners):
            if (src, tgt) in top_set:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor="blue", lw=2))
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _value_add_vs_noi(ind_group: pd.DataFrame) -> bool:
    """True if M2 prob ranks actual spread target above M0 for this indicator snapshot."""
    positives = ind_group[ind_group["spread_7d"] == 1]
    if positives.empty:
        return False
    best_spread = ind_group["spread_prob_m2"].max()
    best_noi = ind_group.loc[ind_group["spread_7d"] == 1, "noi_prob_7"].max()
    m2_rank = ind_group.sort_values("spread_prob_m2", ascending=False).iloc[0]
    m0_rank = ind_group.sort_values("noi_prob_7", ascending=False).iloc[0]
    return bool(m2_rank["spread_7d"] == 1 and (m0_rank["spread_7d"] != 1 or m2_rank["spread_prob_m2"] > m0_rank["noi_prob_7"]))


def top_indicator_groups(eval_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    rows: list[dict] = []
    for indicator, ind_group in eval_df.groupby("indicator"):
        prism_score = float(ind_group["prism_score"].iloc[0])
        severity = str(ind_group["severity"].iloc[0])
        if severity not in SEVERITY_KEEP:
            continue
        best = ind_group.sort_values("spread_probability", ascending=False).iloc[0]
        rows.append(
            {
                "Indicator": indicator,
                "Severity": severity,
                "PRISM_Score": prism_score,
                "Best_Source": best["source_partner"],
                "Best_Target": best["target_partner"],
                "Spread_Prob": round(float(best["spread_probability"]), 4),
                "Target_NOI_Prob": round(float(best["noi_prob_7"]) if pd.notna(best["noi_prob_7"]) else np.nan, 4),
                "Actual_Spread": int(best["spread_7d"]),
                "Value_Add_vs_NOI": _value_add_vs_noi(ind_group),
                "_sev_rank": SEVERITY_RANK.get(severity, 3),
            }
        )
    if not rows:
        return pd.DataFrame()
    ranked = pd.DataFrame(rows).sort_values(["_sev_rank", "PRISM_Score"], ascending=[True, False]).head(top_n)
    ranked.insert(0, "Rank", range(1, len(ranked) + 1))
    return ranked.drop(columns=["_sev_rank"])


def spread_rates_by_pair(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for (source, target), group in events.groupby(["source_partner", "target_partner"]):
        rows.append(
            {
                "Source": source,
                "Target": target,
                "N_Events": len(group),
                "Spread_Rate_7d_pct": round(group["spread_7d"].mean() * 100, 2),
                "Spread_Rate_1d_pct": round(group["spread_1d"].mean() * 100, 2),
            }
        )
    return pd.DataFrame(rows).sort_values("Spread_Rate_7d_pct", ascending=False)


def model_eval_summary(eval_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    y = eval_df["spread_7d"].to_numpy(int)
    for col, name in [
        ("spread_prob_m0", "M0_NOI_only"),
        ("spread_prob_m1", "M1_source"),
        ("spread_prob_m2", "M2_combined"),
        ("spread_prob_m3", "M3_prism"),
    ]:
        if col not in eval_df.columns:
            continue
        scores = eval_df[col].fillna(0).to_numpy(float)
        prec, rec = metrics_at_precision_threshold(y, scores, 0.20)
        auc = average_precision_score(y, scores) if y.sum() > 0 else float("nan")
        rows.append(
            {
                "Model": name,
                "AUC_PR": round(auc, 4),
                "Precision_at_20pct": round(prec * 100, 2),
                "Recall_at_20pct": round(rec * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def severity_filter_summary(events: pd.DataFrame, prism: pd.DataFrame) -> pd.DataFrame:
    all_inds = set(events["indicator"].unique()) if not events.empty else set()
    scored = prism[prism["indicator"].isin(all_inds)]
    counts = scored["severity"].value_counts().reindex(["critical", "high", "medium", "low", ""], fill_value=0)
    return pd.DataFrame(
        {
            "severity": counts.index,
            "indicator_count": counts.values,
            "included_in_analysis": [s in SEVERITY_KEEP for s in counts.index],
        }
    )


def compare_noi_sources(
    eval_df: pd.DataFrame,
    production_scored: pd.DataFrame,
    test_noi_dir: Path,
) -> pd.DataFrame:
    """Re-score eval events with test NOI dir and diff pair-level AUC-PR."""
    if not test_noi_dir.is_dir():
        return pd.DataFrame({"note": ["Test NOI directory not found — skip Phase 2"]})

    test_probs: dict[tuple[int, str, str, str], float] = {}
    for cutoff_day in eval_df["cutoff_day"].unique():
        cutoff_str = to_timestamp(int(cutoff_day)).strftime("%Y%m%d")
        noi = load_noi_for_date(test_noi_dir, cutoff_str)
        if noi.empty:
            continue
        for row in noi.itertuples(index=False):
            test_probs[(int(cutoff_day), str(row.Partner), str(row.Indicator))] = float(
                getattr(row, "noi_prob_7", np.nan)
            )

    test_eval = eval_df.copy()
    test_eval["noi_prob_7_test"] = test_eval.apply(
        lambda r: test_probs.get(
            (int(r["cutoff_day"]), str(r["target_partner"]), str(r["indicator"])), np.nan
        ),
        axis=1,
    )
    test_eval["spread_prob_m0_test"] = test_eval["noi_prob_7_test"].fillna(0.0)

    rows: list[dict] = []
    for (source, target), group in test_eval.groupby(["source_partner", "target_partner"]):
        if len(group) < MIN_PAIR_EVENTS:
            continue
        prod = pair_metrics(group, "spread_probability")
        base_prod = pair_metrics(group, "spread_prob_m0")
        base_test = pair_metrics(group.rename(columns={"spread_prob_m0_test": "spread_prob_m0"}), "spread_prob_m0")
        rows.append(
            {
                "Source": source,
                "Target": target,
                "Prod_M2_AUC_PR": prod["AUC_PR"],
                "Prod_M0_AUC_PR": base_prod["AUC_PR"],
                "Test_M0_AUC_PR": base_test["AUC_PR"],
                "N_Events": prod["N_Events"],
            }
        )
    return pd.DataFrame(rows)


def run_analysis(cfg: AnalysisConfig) -> dict[str, pd.DataFrame | Path]:
    cfg.out_dir.mkdir(parents=True, exist_ok=True)

    forecast_config = ForecastConfig(
        htoc_share_root=cfg.htoc_share_root,
        save_dir=str(cfg.noi_save_dir),
        train_days=cfg.train_days,
        lookback_days=cfg.lookback_days,
        run_eval=False,
    )
    observations = ObservationData.load(
        obs_template=forecast_config.obs_template,
        train_days=cfg.train_days,
    )
    health = FeedHealth.from_data(observations.frame, today=observations.end_date)
    prism = load_prism_scores(cfg.prism_xlsx)

    events = build_event_table(
        observations,
        prism,
        health,
        forecast_config,
        noi_save_dir=cfg.noi_save_dir,
    )
    if events.empty:
        raise RuntimeError("No events built — check share paths and PRISM join.")

    sev_summary = severity_filter_summary(events, prism)
    train, eval_df = temporal_split(events, cfg.eval_tail_days)
    models = train_models(train)
    scored = score_events(events, models)
    train_scored, eval_scored = temporal_split(scored, cfg.eval_tail_days)

    spread_eda = spread_rates_by_pair(eval_scored)
    model_eval = model_eval_summary(eval_scored)
    top_pairs = top_partner_pairs(eval_scored)
    top_indicators = top_indicator_groups(eval_scored)

    heatmap_path = cfg.out_dir / "partner_spread_heatmap.png"
    plot_pair_heatmap(eval_scored, top_pairs, heatmap_path)

    value_add_pct = (
        float(top_indicators["Value_Add_vs_NOI"].mean() * 100) if not top_indicators.empty else 0.0
    )
    summary = pd.DataFrame(
        [
            {"metric": "total_events", "value": len(events)},
            {"metric": "eval_events", "value": len(eval_scored)},
            {"metric": "eval_spread_rate_pct", "value": round(eval_scored["spread_7d"].mean() * 100, 2)},
            {"metric": "top10_value_add_pct", "value": round(value_add_pct, 1)},
        ]
    )

    sev_summary.to_csv(cfg.out_dir / "severity_filter_summary.csv", index=False)
    spread_eda.to_csv(cfg.out_dir / "eda_spread_rates_by_pair.csv", index=False)
    model_eval.to_csv(cfg.out_dir / "model_eval_summary.csv", index=False)
    events.to_csv(cfg.out_dir / "events_all.csv", index=False)
    eval_scored.to_csv(cfg.out_dir / "events_eval_scored.csv", index=False)
    top_pairs.to_csv(cfg.out_dir / "top10_partner_pairs.csv", index=False)
    top_indicators.to_csv(cfg.out_dir / "top10_indicator_groups.csv", index=False)
    summary.to_csv(cfg.out_dir / "run_summary.csv", index=False)

    phase2 = pd.DataFrame()
    if cfg.test_noi_save_dir:
        phase2 = compare_noi_sources(eval_scored, scored, cfg.test_noi_save_dir)
        phase2.to_csv(cfg.out_dir / "phase2_noi_comparison.csv", index=False)

    return {
        "observations_desc": observations.describe(),
        "severity_summary": sev_summary,
        "spread_eda": spread_eda,
        "model_eval": model_eval,
        "events": events,
        "eval_scored": eval_scored,
        "top_pairs": top_pairs,
        "top_indicators": top_indicators,
        "summary": summary,
        "heatmap_path": heatmap_path,
        "phase2": phase2,
    }
