"""Data Understanding pass 2: historical partner-pathway retest.

Exploratory only. Compares target NOI, leakage-safe historical pathway
probabilities, and a simple blend on cold-target graph edges.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htoc_ml" / "src"))

from htoc.core.bootstrap import ensure_htoc_on_path

ensure_htoc_on_path()

from htoc.core.observations import ObservationData
from htoc.noi.config import ForecastConfig
from htoc.noi.feed_health import FeedHealth

sys.path.insert(0, str(REPO / "htoc_ml" / "analysis" / "noi"))
import partner_relationships as nor  # noqa: E402

OUT = REPO / "htoc_ml" / "analysis" / "_outputs" / "next_observed_relationships" / "data_understanding"
OUT.mkdir(parents=True, exist_ok=True)

LOAD_DAYS = 180
PATH_WINDOWS = (30, 60, 90)
PRIOR_STRENGTH = 20.0


def first_seen_table(observations: ObservationData) -> pd.DataFrame:
    """One row per indicator/partner, using first observed day."""
    return (
        observations.frame.groupby(["indicator", "opdiv"], as_index=False)["d"]
        .min()
        .rename(columns={"d": "first_day"})
    )


def transition_rows(first_seen: pd.DataFrame, partners: list[str]) -> pd.DataFrame:
    """Build unique A->B opportunities from historical first-seen order.

    O(I * P^2), with P about 10. Repeated sightings do not duplicate movement.
    """
    wide = first_seen.pivot(index="indicator", columns="opdiv", values="first_day")
    rows: list[pd.DataFrame] = []
    for source in partners:
        if source not in wide.columns:
            continue
        source_day = wide[source]
        for target in partners:
            if source == target:
                continue
            target_day = (
                wide[target]
                if target in wide.columns
                else pd.Series(np.nan, index=wide.index)
            )
            opportunity = source_day.notna() & (
                target_day.isna() | target_day.gt(source_day)
            )
            if not opportunity.any():
                continue
            lag = target_day.loc[opportunity] - source_day.loc[opportunity]
            rows.append(
                pd.DataFrame(
                    {
                        "indicator": wide.index[opportunity],
                        "source_partner": source,
                        "target_partner": target,
                        "source_first_day": source_day.loc[opportunity]
                        .astype(int)
                        .to_numpy(),
                        "lag_days": lag.to_numpy(),
                        "spread_7d": lag.between(1, 7, inclusive="both")
                        .fillna(False)
                        .astype(int)
                        .to_numpy(),
                        "spread_8_14": lag.between(8, 14, inclusive="both")
                        .fillna(False)
                        .astype(int)
                        .to_numpy(),
                    }
                )
            )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def cold_target_edges(
    events: pd.DataFrame, first_seen: pd.DataFrame
) -> pd.DataFrame:
    """Keep X->B only when B had never observed X through cutoff T."""
    target_first = first_seen.rename(
        columns={"opdiv": "target_partner", "first_day": "target_first_day"}
    )
    edges = events.merge(
        target_first,
        on=["indicator", "target_partner"],
        how="left",
        validate="many_to_one",
    )
    return edges[
        edges["target_first_day"].isna()
        | edges["target_first_day"].gt(edges["cutoff_day"])
    ].copy()


def add_pathway_features(
    edges: pd.DataFrame,
    transitions: pd.DataFrame,
    *,
    window_days: int,
) -> pd.DataFrame:
    """Attach smoothed A->B rates using outcomes resolved before cutoff T."""
    rows: list[pd.DataFrame] = []
    priors: dict[int, float] = {}
    for cutoff in sorted(edges["cutoff_day"].unique()):
        history = transitions[
            transitions["source_first_day"].between(
                int(cutoff) - window_days,
                int(cutoff) - 7,
                inclusive="both",
            )
        ]
        global_rate = float(history["spread_7d"].mean()) if len(history) else 0.0
        priors[int(cutoff)] = global_rate
        pair = (
            history.groupby(["source_partner", "target_partner"])["spread_7d"]
            .agg(["size", "sum"])
            .reset_index()
            .rename(
                columns={
                    "size": f"path_support_{window_days}",
                    "sum": f"path_success_{window_days}",
                }
            )
        )
        pair["cutoff_day"] = int(cutoff)
        pair[f"path_prob_{window_days}"] = (
            pair[f"path_success_{window_days}"] + PRIOR_STRENGTH * global_rate
        ) / (pair[f"path_support_{window_days}"] + PRIOR_STRENGTH)
        rows.append(pair)

    stats = pd.concat(rows, ignore_index=True)
    result = edges.merge(
        stats,
        on=["cutoff_day", "source_partner", "target_partner"],
        how="left",
        validate="many_to_one",
    )
    result[f"path_support_{window_days}"] = result[
        f"path_support_{window_days}"
    ].fillna(0)
    result[f"path_prob_{window_days}"] = result[
        f"path_prob_{window_days}"
    ].fillna(result["cutoff_day"].map(priors))
    return result


def collapse_sources(
    source_edges: pd.DataFrame, score_cols: list[str]
) -> pd.DataFrame:
    """Create one graph edge per cutoff/indicator/target.

    Max pathway probability is an interpretable initial combiner for multiple
    active source partners; a learned combiner belongs in Modeling.
    """
    aggregations: dict[str, object] = {
        "spread_7d": "max",
        "noi_prob_7": "max",
        "severity": "first",
        "prism_score": "max",
        "source_partner": lambda values: ",".join(sorted(set(values))),
    }
    for column in score_cols:
        aggregations[column] = "max"
    return (
        source_edges.groupby(
            ["cutoff_day", "cutoff_date", "indicator", "target_partner"],
            as_index=False,
        )
        .agg(aggregations)
        .rename(columns={"source_partner": "source_partners"})
    )


def score_metrics(
    frame: pd.DataFrame, score: str, *, name: str
) -> dict[str, float | int | str]:
    scored = frame.dropna(subset=[score])
    result: dict[str, float | int | str] = {
        "score": name,
        "n": len(scored),
        "coverage": len(scored) / len(frame) if len(frame) else np.nan,
        "positive_rate": float(scored["spread_7d"].mean())
        if len(scored)
        else np.nan,
    }
    if scored["spread_7d"].nunique() == 2:
        actual = scored["spread_7d"].astype(int)
        probability = scored[score].clip(0, 1).astype(float)
        result.update(
            {
                "roc_auc": float(roc_auc_score(actual, probability)),
                "avg_precision": float(
                    average_precision_score(actual, probability)
                ),
                "brier": float(brier_score_loss(actual, probability)),
            }
        )

    top_rows: list[dict[str, float]] = []
    for (_cutoff, _partner), group in scored.groupby(
        ["cutoff_day", "target_partner"]
    ):
        top = group.nlargest(min(10, len(group)), score)
        top_rows.append(
            {
                "top10_hit": float(top["spread_7d"].mean()),
                "base_rate": float(group["spread_7d"].mean()),
            }
        )
    if top_rows:
        top_metrics = pd.DataFrame(top_rows)
        result["top10_hit_rate"] = float(top_metrics["top10_hit"].mean())
        result["top10_base_rate"] = float(top_metrics["base_rate"].mean())
    return result


def add_spread_8_14(
    graph_edges: pd.DataFrame, observations: ObservationData
) -> pd.DataFrame:
    """Add non-overlapping day 8-14 outcome to collapsed graph edges."""
    labels = observations.labels.as_dict()
    empty = np.array([], dtype=int)
    later: list[int] = []
    for row in graph_edges.itertuples(index=False):
        dates = labels.get((row.target_partner, row.indicator), empty)
        seen_by_14 = observations.labels.seen_next(
            dates, int(row.cutoff_day), 14
        )
        later.append(int(seen_by_14 == 1 and int(row.spread_7d) == 0))
    result = graph_edges.copy()
    result["spread_8_14"] = later
    return result


def main() -> None:
    config = nor.AnalysisConfig.production(REPO)
    forecast = ForecastConfig(
        htoc_share_root=config.htoc_share_root,
        save_dir=str(config.noi_save_dir),
        train_days=LOAD_DAYS,
        lookback_days=config.lookback_days,
        run_eval=False,
    )
    print("load observations", LOAD_DAYS, "days")
    observations = ObservationData.load(
        obs_template=forecast.obs_template,
        train_days=LOAD_DAYS,
    )
    health = FeedHealth.from_data(
        observations.frame, today=observations.end_date
    )
    prism = nor.load_prism_scores(config.prism_xlsx)

    print("build source-level events")
    events = nor.build_event_table(
        observations,
        prism,
        health,
        forecast,
        noi_save_dir=config.noi_save_dir,
        medium_plus_only=True,
    )
    first_seen = first_seen_table(observations)
    cold = cold_target_edges(events, first_seen)
    medium_plus = set(
        prism.loc[prism["severity"].isin(nor.SEVERITY_KEEP), "indicator"]
    )
    transitions = transition_rows(
        first_seen[first_seen["indicator"].isin(medium_plus)],
        observations.labels.opdivs(),
    )
    print(
        "all source edges",
        len(events),
        "cold-target source edges",
        len(cold),
        "historical opportunities",
        len(transitions),
    )

    for window in PATH_WINDOWS:
        cold = add_pathway_features(cold, transitions, window_days=window)

    path_cols = [f"path_prob_{window}" for window in PATH_WINDOWS]
    support_cols = [f"path_support_{window}" for window in PATH_WINDOWS]
    graph_edges = collapse_sources(cold, path_cols + support_cols)
    graph_edges = add_spread_8_14(graph_edges, observations)

    # Fair window comparison: all methods use cutoffs with 90 days of history.
    common = graph_edges[
        graph_edges["cutoff_day"].ge(observations.day_min + 90 + 7)
    ].copy()
    common["combined_prob_60"] = np.where(
        common["noi_prob_7"].notna(),
        0.5 * common["noi_prob_7"] + 0.5 * common["path_prob_60"],
        common["path_prob_60"],
    )

    metrics = [score_metrics(common, "noi_prob_7", name="NOI only")]
    for window in PATH_WINDOWS:
        metrics.append(
            score_metrics(
                common,
                f"path_prob_{window}",
                name=f"Pathways {window}d",
            )
        )
    metrics.append(
        score_metrics(
            common,
            "combined_prob_60",
            name="NOI + pathways 60d",
        )
    )
    metrics_frame = pd.DataFrame(metrics)
    horizon_rates = pd.DataFrame(
        [
            {
                "n_edges": len(common),
                "spread_1_7_rate": float(common["spread_7d"].mean()),
                "spread_8_14_rate": float(common["spread_8_14"].mean()),
            }
        ]
    )

    common.to_csv(OUT / "pass2_pathway_graph_edges.csv", index=False)
    transitions.to_csv(
        OUT / "pass2_historical_transitions.csv", index=False
    )
    metrics_frame.to_csv(OUT / "pass2_pathway_metrics.csv", index=False)
    horizon_rates.to_csv(OUT / "pass2_horizon_rates.csv", index=False)
    (
        common.groupby("target_partner")
        .agg(
            n_edges=("indicator", "size"),
            positive_rate=("spread_7d", "mean"),
            noi_coverage=("noi_prob_7", lambda values: values.notna().mean()),
            mean_path_support_60=("path_support_60", "mean"),
        )
        .to_csv(OUT / "pass2_edges_by_target_partner.csv")
    )
    print(metrics_frame.to_string(index=False))
    print(horizon_rates.to_string(index=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
