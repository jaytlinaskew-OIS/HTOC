"""PRISM scores vs Google TI for every Stripped URL in the V5 workbook."""
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

from htoc.core.gti import attach_gti_enrichment, classify_ioc  # noqa: E402
from htoc.core.paths import threat_assessment_scores_xlsx  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "_outputs" / "gti-v5-value"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("GTI_CACHE_PATH", str(OUT / "gti_cache.json"))


def parse_vt(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    missing = text.str.lower().isin({"", "nan", "none", "no vt score"})
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.where(~missing, np.nan)


def gti_kind_for_stripped(value: str) -> str:
    kind = classify_ioc(str(value).strip())
    return {"ip": "Address", "domain": "Host", "url": "URL", "file": "File"}[kind]


def main() -> None:
    path = threat_assessment_scores_xlsx()
    frame = pd.read_excel(path, sheet_name="PRISM Scores")
    stripped = frame[frame["Indicator Type"].astype(str).str.strip().eq("Stripped URL")].copy()
    stripped["vt_tc"] = parse_vt(stripped["VirusTotal Malicious Score"])
    stripped["prism"] = pd.to_numeric(stripped["PRISM Score"], errors="coerce")
    stripped["severity"] = stripped["Severity"].astype(str).str.lower()
    expl = stripped["Explanation"].astype(str) if "Explanation" in stripped.columns else pd.Series("", index=stripped.index)
    stripped["scored_today"] = expl.str.contains("[2026-09-16]", regex=False)
    stripped["pb_lower"] = expl.str.contains("PB lower-start rule applied", case=False, na=False)

    print(f"Stripped URLs: {len(stripped)}")
    print("Severity:\n", stripped["severity"].value_counts().to_string())
    print("PRISM describe:\n", stripped["prism"].describe().to_string())
    print("TC VT present:", int(stripped["vt_tc"].notna().sum()), "/", len(stripped))

    lookup = pd.DataFrame({
        "indicator": stripped["Indicator"].astype(str),
        "type": stripped["Indicator"].map(gti_kind_for_stripped),
    })
    print("GTI kind mapping:\n", lookup["type"].value_counts().to_string())
    enriched = attach_gti_enrichment(lookup, key_col="indicator", type_col="type", max_workers=4)
    gti_cols = ["indicator"] + [c for c in enriched.columns if str(c).startswith("enrich_")]
    gti = enriched[gti_cols].rename(columns={"indicator": "Indicator"})

    merged = stripped.merge(gti, on="Indicator", how="left")
    merged["vt_gti"] = pd.to_numeric(merged["enrich_vtMaliciousCount"], errors="coerce")
    merged["gti_verdict"] = merged["enrich_gti_verdict"].fillna("missing")
    merged["gti_severity"] = merged["enrich_gti_severity"].fillna("missing")
    merged["gti_threat_score"] = pd.to_numeric(merged["enrich_gti_threat_score"], errors="coerce")
    merged["gti_mandiant"] = merged["enrich_gti_mandiant"].fillna(False).astype(bool)
    merged["gti_description"] = merged["enrich_gti_description"].fillna("").astype(str)
    merged["gti_hit"] = merged["vt_gti"].notna() | merged["gti_verdict"].ne("missing")

    keep = [
        "Indicator",
        "scored_today",
        "severity",
        "prism",
        "vt_tc",
        "vt_gti",
        "gti_verdict",
        "gti_severity",
        "gti_threat_score",
        "gti_mandiant",
        "gti_description",
        "Threat Actor",
        "Tagging Boost",
        "pb_lower",
        "Partners",
        "Last Observed",
    ]
    keep = [c for c in keep if c in merged.columns]
    out = merged[keep].sort_values(["prism", "gti_threat_score"], ascending=[False, False])
    out.to_csv(OUT / "stripped_urls_comparison.csv", index=False)

    both = merged["vt_tc"].notna() & merged["vt_gti"].notna()
    summary = {
        "n": int(len(merged)),
        "scored_today": int(merged["scored_today"].sum()),
        "prism": {
            "min": float(merged["prism"].min()),
            "p50": float(merged["prism"].median()),
            "mean": float(merged["prism"].mean()),
            "p90": float(merged["prism"].quantile(0.9)),
            "max": float(merged["prism"].max()),
        },
        "severity": merged["severity"].value_counts().to_dict(),
        "tc_vt_present": int(merged["vt_tc"].notna().sum()),
        "gti_hit": int(merged["gti_hit"].sum()),
        "gti_miss": int((~merged["gti_hit"]).sum()),
        "coverage_gain": int((merged["vt_tc"].isna() & merged["vt_gti"].notna()).sum()),
        "gti_vt_gt0": int(merged["vt_gti"].fillna(0).gt(0).sum()),
        "both_present": int(both.sum()),
        "vt_exact": int((merged.loc[both, "vt_gti"] == merged.loc[both, "vt_tc"]).sum()) if both.any() else 0,
        "verdict": merged["gti_verdict"].value_counts().to_dict(),
        "gti_severity": merged["gti_severity"].value_counts().to_dict(),
        "prism_by_verdict": (
            merged.groupby("gti_verdict")["prism"]
            .agg(["count", "median", "mean", "min", "max"])
            .round(1)
            .reset_index()
            .to_dict(orient="records")
        ),
        "severity_by_verdict": (
            pd.crosstab(merged["severity"], merged["gti_verdict"])
            .reset_index()
            .to_dict(orient="records")
        ),
        "high_or_medium": int(merged["severity"].isin(["medium", "high", "critical"]).sum()),
        "gti_malicious_or_suspicious": int(
            merged["gti_verdict"].isin(["VERDICT_MALICIOUS", "VERDICT_SUSPICIOUS"]).sum()
        ),
        "disagreement_we_low_gti_bad": int(
            (
                merged["severity"].eq("low")
                & merged["gti_verdict"].isin(["VERDICT_MALICIOUS", "VERDICT_SUSPICIOUS"])
            ).sum()
        ),
        "disagreement_we_elevated_gti_clean": int(
            (
                merged["severity"].isin(["medium", "high", "critical"])
                & merged["gti_verdict"].isin(["VERDICT_UNDETECTED", "VERDICT_BENIGN"])
            ).sum()
        ),
    }
    (OUT / "stripped_urls_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT / 'stripped_urls_comparison.csv'}")


if __name__ == "__main__":
    main()
