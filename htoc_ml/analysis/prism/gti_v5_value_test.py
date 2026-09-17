"""Compare Google TI enrichment against today's ThreatAssessScoringV5 scores.

Reads the live PRISM workbook, looks up a stratified sample in GTI, and writes
coverage / score-delta tables under analysis/_outputs/gti-v5-value/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np
import pandas as pd

from htoc.core.bootstrap import ensure_htoc_on_path

ensure_htoc_on_path()

from htoc.core.gti import (  # noqa: E402
    attach_gti_enrichment,
    classify_ioc,
)
from htoc.core.paths import threat_assessment_scores_xlsx  # noqa: E402
from htoc.prism.engine import MALICIOUS_EXPONENT, VT_EFFECTIVE_MAX, WEIGHTS, _base_cap  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "_outputs" / "gti-v5-value"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("GTI_CACHE_PATH", str(OUT / "gti_cache.json"))

SAMPLE_N = 220
RANDOM_STATE = 16
MALICIOUS_WEIGHT = WEIGHTS["MALICIOUS_WEIGHT"]
RAW_CAP = float(_base_cap())
PRISM_SCALE = 1000.0 * 1.40 / RAW_CAP
TYPE_TO_GTI = {
    "Address": "Address",
    "IPv4": "IPv4",
    "IPv6": "IPv6",
    "Host": "Host",
    "Domain": "Domain",
    "URL": "URL",
    "File": "File",
    "SHA1": "SHA1",
    "SHA256": "SHA256",
    "MD5": "MD5",
}


def _severity(score: float) -> str:
    if score < 200:
        return "low"
    if score < 500:
        return "medium"
    if score < 800:
        return "high"
    return "critical"


def parse_vt(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    missing = text.str.lower().isin({"", "nan", "none", "no vt score"})
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.where(~missing, np.nan)
    return numeric


def vt_raw(count: pd.Series) -> pd.Series:
    clipped = count.fillna(0).clip(0, VT_EFFECTIVE_MAX)
    return np.power(clipped, MALICIOUS_EXPONENT) * MALICIOUS_WEIGHT


def map_gti_type(row: pd.Series) -> str:
    raw_type = str(row.get("Indicator Type") or "").strip()
    mapped = TYPE_TO_GTI.get(raw_type)
    if mapped:
        return mapped
    kind = classify_ioc(str(row.get("Indicator") or ""))
    return {"ip": "Address", "domain": "Host", "url": "URL", "file": "File"}[kind]


def vt_bucket(count: float, present: bool) -> str:
    if not present:
        return "missing"
    if count <= 3:
        return "0-3"
    if count <= 12:
        return "4-12"
    return "13+"


def load_prism() -> pd.DataFrame:
    path = threat_assessment_scores_xlsx()
    print(f"Loading PRISM scores from {path}")
    frame = pd.read_excel(path, sheet_name="PRISM Scores")
    frame["vt_tc"] = parse_vt(frame["VirusTotal Malicious Score"])
    frame["vt_tc_present"] = frame["vt_tc"].notna()
    frame["prism"] = pd.to_numeric(frame["PRISM Score"], errors="coerce")
    frame["severity"] = frame["Severity"].astype(str).str.lower()
    frame["pb_lower"] = (
        frame["Explanation"].astype(str).str.contains("PB lower-start rule applied", case=False, na=False)
        if "Explanation" in frame.columns
        else False
    )
    expl = frame["Explanation"].astype(str) if "Explanation" in frame.columns else pd.Series("", index=frame.index)
    frame["scored_today"] = expl.str.contains("[2026-09-16]", regex=False)
    print(f"PRISM rows: {len(frame):,} | scored today: {int(frame['scored_today'].sum()):,}")
    print("Types:\n", frame["Indicator Type"].value_counts(dropna=False).to_string())
    print("VT present:", int(frame["vt_tc_present"].sum()), "/", len(frame))
    print("VT missing by type:\n", frame.loc[~frame["vt_tc_present"], "Indicator Type"].value_counts().to_string())
    print("Severity:\n", frame["severity"].value_counts().to_string())
    return frame


def stratified_sample(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    work = frame.copy()
    work["_bucket"] = [
        f"{typ}|{vt_bucket(vt, present)}"
        for typ, vt, present in zip(work["Indicator Type"], work["vt_tc"].fillna(0), work["vt_tc_present"])
    ]
    # Prefer today's rows, then fill from the rest so rare types still appear.
    today = work[work["scored_today"]].copy()
    rest = work[~work["scored_today"]].copy()
    parts: list[pd.DataFrame] = []
    remaining = n
    for source in (today, rest):
        if remaining <= 0 or source.empty:
            continue
        groups = list(source.groupby("_bucket", sort=False))
        per = max(1, remaining // max(len(groups), 1))
        taken = 0
        for _, group in groups:
            size = min(len(group), per)
            if size <= 0:
                continue
            parts.append(group.sample(n=size, random_state=RANDOM_STATE))
            taken += size
        remaining = n - sum(len(p) for p in parts)
    sample = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["Indicator"])
    if len(sample) < n:
        extra = work[~work["Indicator"].isin(sample["Indicator"])]
        need = min(n - len(sample), len(extra))
        if need:
            sample = pd.concat([sample, extra.sample(n=need, random_state=RANDOM_STATE)], ignore_index=True)
    sample = sample.drop(columns=["_bucket"], errors="ignore")
    print(f"Sample size: {len(sample)} | today: {int(sample['scored_today'].sum())}")
    print("Sample types:\n", sample["Indicator Type"].value_counts().to_string())
    print("Sample VT present:", int(sample["vt_tc_present"].sum()), "/", len(sample))
    return sample


def apply_vt_gates(score: pd.Series, vt: pd.Series, present: pd.Series, pb_lower: pd.Series) -> pd.Series:
    out = score.astype(float).copy()
    low = present & (vt.fillna(0) <= 3)
    high = present & (vt.fillna(0) >= 13) & ~pb_lower.fillna(False)
    out = out.mask(low, out.clip(upper=499))
    out = out.mask(high, out.clip(lower=500))
    return out.clip(0, 1000)


def compare(sample: pd.DataFrame, gti: pd.DataFrame) -> pd.DataFrame:
    merged = sample.merge(gti, on="Indicator", how="left")
    merged["vt_gti"] = pd.to_numeric(merged["enrich_vtMaliciousCount"], errors="coerce")
    merged["vt_gti_present"] = merged["vt_gti"].notna()
    merged["gti_threat_score"] = pd.to_numeric(merged["enrich_gti_threat_score"], errors="coerce")
    merged["gti_verdict"] = merged["enrich_gti_verdict"]
    merged["gti_severity"] = merged["enrich_gti_severity"]
    merged["gti_mandiant"] = merged["enrich_gti_mandiant"].fillna(False).astype(bool)
    merged["gti_actors"] = merged["enrich_gti_threat_actors"].fillna("").astype(str)
    merged["gti_families"] = merged["enrich_gti_malware_families"].fillna("").astype(str)
    merged["gti_description"] = merged["enrich_gti_description"].fillna("").astype(str)

    old_raw = vt_raw(merged["vt_tc"])
    new_raw = vt_raw(merged["vt_gti"])
    # Missing GTI keeps the TC VT contribution so we isolate API swap, not lookup misses.
    new_raw = new_raw.where(merged["vt_gti_present"], old_raw)
    delta_raw = new_raw - old_raw
    merged["vt_count_delta"] = merged["vt_gti"] - merged["vt_tc"]
    merged["prism_delta_est"] = (delta_raw * PRISM_SCALE).round(1)
    estimated = merged["prism"] + merged["prism_delta_est"]
    merged["prism_gti_est"] = apply_vt_gates(
        estimated, merged["vt_gti"].fillna(merged["vt_tc"]), merged["vt_gti_present"] | merged["vt_tc_present"], merged["pb_lower"]
    ).round()
    merged["severity_gti_est"] = merged["prism_gti_est"].map(_severity)
    merged["severity_change"] = merged["severity"] != merged["severity_gti_est"]

    def gate(count: pd.Series, present: pd.Series) -> pd.Series:
        return np.select(
            [~present, present & (count.fillna(0) <= 3), present & (count.fillna(0) >= 13)],
            ["none", "low_cap", "high_floor"],
            default="mid",
        )

    merged["gate_tc"] = gate(merged["vt_tc"], merged["vt_tc_present"])
    merged["gate_gti"] = gate(merged["vt_gti"], merged["vt_gti_present"])
    merged["gate_flip"] = merged["gate_tc"] != merged["gate_gti"]
    merged["coverage_gain"] = (~merged["vt_tc_present"]) & merged["vt_gti_present"]
    merged["coverage_loss"] = merged["vt_tc_present"] & (~merged["vt_gti_present"])
    tc_actor = merged["Threat Actor"].astype(str).str.strip().str.lower()
    merged["new_gti_actor"] = merged["gti_actors"].str.len().gt(0) & tc_actor.isin({"", "nan", "none", "nat"})
    merged["new_gti_family"] = merged["gti_families"].str.len().gt(0)
    merged["abs_prism_delta"] = merged["prism_gti_est"] - merged["prism"]
    return merged


def summarize(frame: pd.DataFrame, merged: pd.DataFrame) -> dict:
    both = merged["vt_tc_present"] & merged["vt_gti_present"]
    vt_delta = (merged.loc[both, "vt_gti"] - merged.loc[both, "vt_tc"]).abs()
    prism_delta = merged["abs_prism_delta"].abs()
    corr_vt_threat = None
    if merged["vt_gti_present"].sum() >= 8:
        corr_vt_threat = float(
            pd.to_numeric(merged["vt_gti"], errors="coerce").corr(merged["gti_threat_score"])
        )
    summary = {
        "prism_universe": int(len(frame)),
        "scored_today": int(frame["scored_today"].sum()),
        "sample_n": int(len(merged)),
        "raw_cap": RAW_CAP,
        "prism_points_per_vt_raw": PRISM_SCALE,
        "tc_vt_present_universe": int(frame["vt_tc_present"].sum()),
        "tc_vt_missing_universe": int((~frame["vt_tc_present"]).sum()),
        "gti_hit": int(merged["vt_gti_present"].sum()),
        "gti_miss": int((~merged["vt_gti_present"]).sum()),
        "coverage_gain": int(merged["coverage_gain"].sum()),
        "coverage_loss": int(merged["coverage_loss"].sum()),
        "both_present": int(both.sum()),
        "vt_count_exact_match": int((merged.loc[both, "vt_gti"] == merged.loc[both, "vt_tc"]).sum()),
        "vt_count_abs_mean": float(vt_delta.mean()) if len(vt_delta) else None,
        "vt_count_abs_p50": float(vt_delta.median()) if len(vt_delta) else None,
        "vt_count_abs_p90": float(vt_delta.quantile(0.9)) if len(vt_delta) else None,
        "vt_count_abs_max": float(vt_delta.max()) if len(vt_delta) else None,
        "prism_abs_mean": float(prism_delta.mean()) if len(prism_delta) else None,
        "prism_abs_p50": float(prism_delta.median()) if len(prism_delta) else None,
        "prism_abs_p90": float(prism_delta.quantile(0.9)) if len(prism_delta) else None,
        "prism_abs_max": float(prism_delta.max()) if len(prism_delta) else None,
        "prism_delta_ge_50": int((prism_delta >= 50).sum()),
        "prism_delta_ge_100": int((prism_delta >= 100).sum()),
        "severity_changes": int(merged["severity_change"].sum()),
        "gate_flips": int(merged["gate_flip"].sum()),
        "gti_verdict_counts": merged["gti_verdict"].fillna("missing").value_counts().to_dict(),
        "gti_severity_counts": merged["gti_severity"].fillna("missing").value_counts().to_dict(),
        "mandiant_true": int(merged["gti_mandiant"].sum()),
        "new_gti_actor": int(merged["new_gti_actor"].sum()),
        "malware_family_hits": int(merged["new_gti_family"].sum()),
        "description_hits": int(merged["gti_description"].str.len().gt(0).sum()),
        "corr_gti_vt_vs_threat_score": corr_vt_threat,
        "type_coverage": (
            merged.groupby("Indicator Type")
            .agg(
                n=("Indicator", "size"),
                tc_vt=("vt_tc_present", "sum"),
                gti_vt=("vt_gti_present", "sum"),
                coverage_gain=("coverage_gain", "sum"),
            )
            .reset_index()
            .to_dict(orient="records")
        ),
        "severity_crosstab": (
            pd.crosstab(merged["severity"], merged["severity_gti_est"], dropna=False)
            .rename_axis(index="current", columns="gti_est")
            .reset_index()
            .to_dict(orient="records")
        ),
    }
    return summary


def main() -> None:
    frame = load_prism()
    sample = stratified_sample(frame, SAMPLE_N)
    lookup = sample[["Indicator", "Indicator Type"]].copy()
    lookup["type"] = sample.apply(map_gti_type, axis=1)
    lookup = lookup.rename(columns={"Indicator": "indicator"})
    print("GTI type mapping:\n", lookup["type"].value_counts().to_string())
    print(f"Calling Google TI for {len(lookup)} indicators...")
    enriched = attach_gti_enrichment(lookup, key_col="indicator", type_col="type", max_workers=4)
    gti_cols = ["indicator"] + [c for c in enriched.columns if str(c).startswith("enrich_")]
    gti = enriched[gti_cols].rename(columns={"indicator": "Indicator"})
    print("GTI columns:", list(gti.columns))
    print("GTI hits:", int(pd.to_numeric(gti.get("enrich_vtMaliciousCount"), errors="coerce").notna().sum()))

    merged = compare(sample, gti)
    summary = summarize(frame, merged)
    keep = [
        "Indicator",
        "Indicator Type",
        "scored_today",
        "Severity",
        "severity_gti_est",
        "prism",
        "prism_gti_est",
        "abs_prism_delta",
        "vt_tc",
        "vt_gti",
        "vt_count_delta",
        "gate_tc",
        "gate_gti",
        "gate_flip",
        "coverage_gain",
        "coverage_loss",
        "gti_verdict",
        "gti_severity",
        "gti_threat_score",
        "gti_mandiant",
        "gti_actors",
        "gti_families",
        "Threat Actor",
        "new_gti_actor",
        "gti_description",
        "pb_lower",
        "Tagging Boost",
    ]
    keep = [c for c in keep if c in merged.columns]
    merged[keep].to_csv(OUT / "sample_comparison.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    flips = merged.loc[merged["gate_flip"] | merged["severity_change"] | (merged["abs_prism_delta"].abs() >= 50)]
    flips[keep].to_csv(OUT / "material_changes.csv", index=False)
    gains = merged.loc[merged["coverage_gain"] | merged["new_gti_actor"] | merged["gti_mandiant"]]
    gains[keep].to_csv(OUT / "added_context.csv", index=False)
    print(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
