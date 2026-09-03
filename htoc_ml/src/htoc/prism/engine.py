"""PRISM score for an enriched indicator frame. Port of ThreatAssessScoringV5Daily step 9."""
from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd

from htoc.prism.tags import (
    convert_to_list,
    count_partners,
    count_sources,
    evaluate_tagging_boost_reason,
    extract_pb_lower_tags_from_val,
    has_incident_event,
    has_pb_lower_tag,
    has_scanner_tag,
    has_threat_actor,
    has_tor_activity,
    is_botnet,
)

WEIGHTS = {
    "MALICIOUS_WEIGHT": 7.50,
    "OBSERVATION_COUNT_WEIGHT": 0.02,
    "CONTINUITY_WEIGHT": 0.90,
    "TC_RATING": 0.01,
    "TC_CONFIDENCE": 0.025,
    "TOR_ACTIVITY_WEIGHT": 9.00,
    "CAL_SCORE_WEIGHT": 2.75,
    "TC_THREAT_SCORE_WEIGHT": 0.75,
    "INCIDENTS_EVENTS_WEIGHT": 8.00,
    "PARTNER_WEIGHT": 2.10,
    "SOURCES_WEIGHT": 2.80,
    "THREAT_ACTOR_WEIGHT": 10.00,
    "FIRST_OBS_WEIGHT": 2.00,
}

SCORING_BINS = [0, 200, 500, 800, 1001]
SEVERITY_LABELS = ["low", "medium", "high", "critical"]
VT_COL = "enrich_vtMaliciousCount"
VT_EFFECTIVE_MAX = 40
MAX_OBS_REALISTIC = 365
MAX_RATING = 5
MAX_CONFIDENCE = 100
FALSE_POSITIVE_WEIGHT = 0.9
BOTNET_MULTIPLIER = 0.4
SCANNER_PENALTY_MULTIPLIER = 0.80
DATA_QUALITY_FLOOR = 0.85
PB_BASE_SCORE_MULTIPLIER = 0.45
THREAT_TAG_MIN_FLOOR = 560
FIRST_OBS_MAX_DAYS = 14
MALICIOUS_EXPONENT = 0.75
FILE_TYPES = {"SHA1", "SHA256", "MD5", "file", "File"}
MASS_SCANNER_TIER1_MULTIPLIER = 0.40
MASS_SCANNER_TIER2_MULTIPLIER = 0.05
OBS_MIN_MULTIPLIER = 0.50
MAX_SOURCES_REALISTIC = 8
MAX_PARTNERS_REALISTIC = 10
FILE_BASELINE_RAW = 900.0
MAX_STACKED_CONTEXT_BONUS = 25.0
INCIDENTS_EVENTS_COL = "incidents/events"
TC_THREAT_COL = "threatAssessScore"

_NAME_MAP = {
    "malicious_raw_score": "VT malicious (log-scaled)",
    "continuity_raw_score": "Continuity (indicator type)",
    "tc_raw_rating": "TC rating",
    "tc_raw_confidence": "TC confidence",
    "tor_activity_score": "TOR activity",
    "incidents_events_score": "Incident/Event association",
    "sources_raw_score": "Multi-source validation",
    "partner_raw_score": "Partner coverage bonus",
    "threat_actor_score": "Threat actor association",
    "cal_raw_score": "CAL score",
    "tc_threat_raw_score": "TC threat assessment",
    "first_obs_raw_score": "Recent first-seen activity",
    "stacked_context_bonus": "Reinforcing context bonus",
}

COLUMN_RENAME = {
    "indicator": "Indicator",
    "type": "Indicator Type",
    "lastObserved": "Last Observed",
    "vt_display": "VT Display",
    "obs_count": "Observation Yearly Count",
    "rating": "ThreatConnect Rating",
    "obs_penalty_multiplier": "Observation Penalty Multiplier",
    "botnet_flag": "Botnet Flag",
    "falsePositives": "False Positives",
    "partners": "Partners",
    "partners_count": "Partner Count",
    "sources_count": "Source Count",
    "adversary": "Adversary",
    "threat_actor": "Threat Actor",
    "threat_nation_state": "Threat Nation State",
    "threat_security_org": "Threat Security Org",
    "threat_cve_nbr": "Threat CVE",
    "Tagging_Boost": "Tagging Boost",
    "Tagging_Boost_Reason": "Tagging Boost Reason",
    "pb_lower_flag": "PB Lower Flag",
    "pb_lower_tags": "PB Lower Tags",
    "pb_lower_reason": "PB Lower Reason",
    "pb_base_multiplier": "PB Base Multiplier",
    "vt_high_floor_bypassed": "VT High Floor Bypassed",
    "calScore": "CAL Score",
    "threatAssessScore": "ThreatConnect Score",
    "PRISM_Score": "PRISM Score",
    "PRISM_Score_Final": "PRISM Score (Final)",
    "Severity": "Severity",
    "Severity_Final": "Severity (Final)",
    "Explanation": "Explanation",
}

EXPORT_COLUMNS = [
    "Indicator", "Last Observed", "Indicator Type", "VirusTotal Malicious Score",
    "Observation Yearly Count", "ThreatConnect Rating", "Observation Penalty Multiplier",
    "Botnet Flag", "False Positives", "Partners", "incidents/events", "Threat Actor",
    "Threat Nation State", "Threat Security Org", "Threat CVE", "Tagging Boost", "Tagging Boost Reason",
    "CAL Score", "ThreatConnect Score", "PRISM Score", "Severity", "Explanation",
]


def _base_cap() -> float:
    return (
        np.power(VT_EFFECTIVE_MAX, MALICIOUS_EXPONENT) * WEIGHTS["MALICIOUS_WEIGHT"]
        + 3 * WEIGHTS["CONTINUITY_WEIGHT"]
        + (MAX_RATING * WEIGHTS["TC_RATING"])
        + (np.sqrt(MAX_CONFIDENCE) * WEIGHTS["TC_CONFIDENCE"])
        + (WEIGHTS["TOR_ACTIVITY_WEIGHT"] * 2)
        + WEIGHTS["INCIDENTS_EVENTS_WEIGHT"]
        + (np.log1p(MAX_SOURCES_REALISTIC - 1) * WEIGHTS["SOURCES_WEIGHT"])
        + (np.log1p(MAX_PARTNERS_REALISTIC - 1) * WEIGHTS["PARTNER_WEIGHT"])
        + WEIGHTS["THREAT_ACTOR_WEIGHT"]
        + WEIGHTS["CAL_SCORE_WEIGHT"]
        + WEIGHTS["TC_THREAT_SCORE_WEIGHT"]
        + WEIGHTS["FIRST_OBS_WEIGHT"]
        + MAX_STACKED_CONTEXT_BONUS
    )


def build_explanation(row) -> str:
    parts = {k: float(row.get(k, 0) or 0) for k in _NAME_MAP}
    final = row.get("PRISM_Score_Final")
    score = float(final) if pd.notna(final) else float(row.get("PRISM_Score", 0) or 0)
    severity = str(row.get("Severity_Final", row.get("Severity", "nan")))
    current_date = datetime.now(UTC).strftime("%Y-%m-%d")
    vt_note = (
        f"VT score: {int(row.get('vt_numeric_for_scoring', 0))}."
        if bool(row.get("vt_present", False))
        else "VT score not available (neutral)."
    )
    contrib = sorted(parts.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
    drivers_text = "; ".join(_NAME_MAP.get(k, k) for k, v in contrib if v != 0) or "No significant drivers"
    pb_reason = row.get("pb_lower_reason")
    pb_flag = bool(row.get("pb_lower_flag", False))
    pb_mult = float(row.get("pb_base_multiplier", 1.0) or 1.0)
    pb_vt_bypass = bool(row.get("vt_high_floor_bypassed", False))
    pb_note = (
        f"PB lower-start rule applied{f' ({pb_reason})' if pd.notna(pb_reason) and str(pb_reason).strip() else ''}; "
        f"base score multiplier {pb_mult:.2f}; incident/event boost suppressed"
        f"{'; VT high floor bypassed' if pb_vt_bypass else ''}."
        if pb_flag
        else "No PB lower-start rule."
    )
    threat_actor_val = row.get("adversary")
    if pd.isna(threat_actor_val) or str(threat_actor_val).strip().lower() in {"none", "nan", ""}:
        threat_actor_val = row.get("threat_actor")
    actor_sentence = (
        f" Associated threat actor(s): {str(threat_actor_val).strip()}."
        if threat_actor_val is not None and str(threat_actor_val).strip().lower() not in {"none", "nan", ""}
        else ""
    )
    inc_flag = int(row.get("incidents_events_flag", 0) or 0)
    inc_events = str(row.get("incidents/events", "")).strip()
    if inc_flag == 1 and not pb_flag and inc_events and inc_events.lower() not in {"none", "nan", ""}:
        inc_note = f"Linked to incident/event: {inc_events}."
    elif inc_flag == 1 and pb_flag:
        inc_note = "Linked to incident/event, but incident/event boost suppressed by PB rule."
    else:
        inc_note = "No incident/event link."
    tagging_reason_val = row.get("Tagging_Boost_Reason")
    if pd.notna(tagging_reason_val) and str(tagging_reason_val).strip().lower() not in {"none", "nan", ""}:
        boost_reason_note = f"Tagging boost: {str(tagging_reason_val).strip()}."
    elif bool(row.get("Tagging_Boost", False)):
        boost_reason_note = "Tagging boost: criteria matched."
    else:
        boost_reason_note = ""
    return (
        f"[{current_date}] Severity: {severity}. {vt_note} Contextual Drivers: {drivers_text}. "
        f"Observed across {int(row.get('partners_count', 0) or 0)} partner(s). "
        f"Observed by {int(row.get('sources_count', 1) or 1)} sources. "
        f"{pb_note} "
        f"{'Botnet penalty applied.' if float(row.get('botnet_penalty_multiplier', 1.0)) < 1.0 else 'No botnet penalty.'} "
        f"{'Scanner penalty applied.' if float(row.get('scanner_penalty_multiplier', 1.0)) < 1.0 else 'No scanner penalty.'} "
        f"{'TOR activity detected.' if float(row.get('tor_activity_score', 0) or 0) > 0 else 'No TOR activity.'} "
        f"{inc_note}{actor_sentence} {boost_reason_note} Score: {score:.0f}/1000."
    )


def score_frame(frame: pd.DataFrame, extra_standalone_tags: frozenset[str] | None = None) -> pd.DataFrame:
    """Add PRISM_Score / Severity / Explanation. Input columns match the live Daily runner."""
    df_scored = frame.copy()
    if VT_COL in df_scored.columns:
        df_scored[VT_COL] = pd.to_numeric(df_scored[VT_COL], errors="coerce")
        df_scored["vt_present"] = df_scored[VT_COL].notna()
    else:
        df_scored[VT_COL] = np.nan
        df_scored["vt_present"] = False
    df_scored["vt_present"] = df_scored["vt_present"].astype(bool)
    df_scored["vt_display"] = np.where(df_scored["vt_present"], df_scored[VT_COL], "No VT Score")
    df_scored["vt_numeric_for_scoring"] = df_scored[VT_COL].fillna(0).clip(0, VT_EFFECTIVE_MAX)

    for col, cap in [
        ("obs_count", MAX_OBS_REALISTIC),
        ("rating", MAX_RATING),
        ("confidence", MAX_CONFIDENCE),
        ("calScore", 1000),
    ]:
        df_scored[col] = pd.to_numeric(
            df_scored[col] if col in df_scored.columns else pd.Series(0, index=df_scored.index),
            errors="coerce",
        ).fillna(0).clip(0, cap)

    df_scored["type"] = (
        df_scored["type"] if "type" in df_scored.columns else pd.Series("", index=df_scored.index)
    ).astype(str)

    if "pb_lower_flag" in df_scored.columns:
        df_scored["pb_lower_flag"] = df_scored["pb_lower_flag"].fillna(False).astype(bool)
    elif "tag_list" in df_scored.columns:
        df_scored["pb_lower_flag"] = df_scored["tag_list"].apply(has_pb_lower_tag).astype(bool)
    else:
        df_scored["pb_lower_flag"] = False

    if "pb_lower_tags" not in df_scored.columns:
        df_scored["pb_lower_tags"] = (
            df_scored["tag_list"].apply(extract_pb_lower_tags_from_val)
            if "tag_list" in df_scored.columns
            else [[] for _ in range(len(df_scored))]
        )
    if "pb_lower_reason" not in df_scored.columns:
        df_scored["pb_lower_reason"] = df_scored["pb_lower_tags"].apply(
            lambda tags: f"pb_tag:{str(tags[0]).strip()}" if isinstance(tags, list) and len(tags) > 0 else None
        )

    firstseen_dt = pd.to_datetime(
        df_scored.get("firstseen_date", pd.Series(pd.NaT, index=df_scored.index)),
        errors="coerce",
    )
    today_ts = pd.Timestamp.today().normalize()
    age_days = (today_ts - firstseen_dt).dt.days.clip(lower=0)
    freshness = ((FIRST_OBS_MAX_DAYS - age_days) / FIRST_OBS_MAX_DAYS).clip(lower=0.0, upper=1.0)
    freshness = freshness.where(firstseen_dt.notna(), 0.0)
    df_scored["first_obs_raw_score"] = freshness * WEIGHTS["FIRST_OBS_WEIGHT"]

    df_scored["w_malicious_eff"] = WEIGHTS["MALICIOUS_WEIGHT"]
    df_scored["w_tc_rating_eff"] = WEIGHTS["TC_RATING"]
    df_scored["malicious_scaled"] = np.power(df_scored["vt_numeric_for_scoring"], MALICIOUS_EXPONENT)
    df_scored["malicious_raw_score"] = df_scored["malicious_scaled"] * WEIGHTS["MALICIOUS_WEIGHT"]
    df_scored["is_file_type"] = df_scored["type"].isin(FILE_TYPES)
    df_scored["continuity_val"] = df_scored["type"].map({
        "Address": 1, "IPv4": 1, "IPv6": 1,
        "Domain": 2, "Host": 2, "URL": 2, "Stripped URL": 2, "EmailAddress": 2, "EmailSubject": 2,
        "SHA1": 3, "SHA256": 3, "MD5": 3, "file": 3, "File": 3,
    }).fillna(0)
    df_scored["continuity_raw_score"] = df_scored["continuity_val"] * WEIGHTS["CONTINUITY_WEIGHT"]
    df_scored.loc[df_scored["is_file_type"], "continuity_raw_score"] = 900
    df_scored["tc_raw_rating"] = df_scored["rating"] * df_scored["w_tc_rating_eff"]
    df_scored["tc_raw_confidence"] = np.sqrt(df_scored["confidence"]) * WEIGHTS["TC_CONFIDENCE"]
    df_scored["cal_raw_score"] = (df_scored["calScore"] / 1000.0) * WEIGHTS["CAL_SCORE_WEIGHT"]
    if TC_THREAT_COL in df_scored.columns:
        df_scored[TC_THREAT_COL] = pd.to_numeric(df_scored.get(TC_THREAT_COL, 0), errors="coerce").fillna(0).clip(0, 1000)
        df_scored["tc_threat_raw_score"] = (df_scored[TC_THREAT_COL] / 1000.0) * WEIGHTS["TC_THREAT_SCORE_WEIGHT"]
    else:
        df_scored["tc_threat_raw_score"] = 0.0

    df_scored["incidents_events_flag"] = (
        df_scored[INCIDENTS_EVENTS_COL].apply(has_incident_event).astype(int)
        if INCIDENTS_EVENTS_COL in df_scored.columns
        else 0
    )
    df_scored["incidents_events_score"] = np.where(
        df_scored["pb_lower_flag"], 0.0, df_scored["incidents_events_flag"] * WEIGHTS["INCIDENTS_EVENTS_WEIGHT"]
    )

    df_scored["sources_count"] = df_scored["sources"].apply(count_sources) if "sources" in df_scored.columns else 1
    df_scored["sources_count_safe"] = df_scored["sources_count"].clip(lower=1)
    df_scored["sources_raw_score"] = np.log1p(df_scored["sources_count_safe"] - 1) * WEIGHTS["SOURCES_WEIGHT"]
    df_scored["partners_count"] = df_scored["partners"].apply(count_partners) if "partners" in df_scored.columns else 0
    df_scored["partners_count_safe"] = df_scored["partners_count"].clip(lower=1)
    df_scored["partner_raw_score"] = np.log1p(df_scored["partners_count_safe"] - 1) * WEIGHTS["PARTNER_WEIGHT"]

    threat_actor_flag = pd.Series(False, index=df_scored.index)
    if "adversary" in df_scored.columns:
        threat_actor_flag = df_scored["adversary"].apply(has_threat_actor)
    elif "threat_actor" in df_scored.columns:
        threat_actor_flag = df_scored["threat_actor"].apply(has_threat_actor)
    df_scored["threat_actor_score"] = threat_actor_flag.astype(int) * WEIGHTS["THREAT_ACTOR_WEIGHT"]
    df_scored["Tagging_Boost_Reason"] = df_scored.apply(
        lambda row: evaluate_tagging_boost_reason(row, extra_standalone_tags), axis=1
    )
    df_scored["Tagging_Boost"] = df_scored["Tagging_Boost_Reason"].notna().astype(bool)

    tor_mask_enrich = (
        df_scored["enrich_tags"].apply(has_tor_activity)
        if "enrich_tags" in df_scored.columns
        else pd.Series(False, index=df_scored.index)
    )
    tor_mask_tag = (
        df_scored["tag_name"].apply(convert_to_list).apply(has_tor_activity)
        if "tag_name" in df_scored.columns
        else pd.Series(False, index=df_scored.index)
    )
    tor_flag = (tor_mask_enrich | tor_mask_tag).astype(int)
    df_scored["tor_activity_score"] = tor_flag * WEIGHTS["TOR_ACTIVITY_WEIGHT"]
    boost_mask = (
        df_scored["vt_present"]
        & (pd.to_numeric(df_scored["vt_numeric_for_scoring"], errors="coerce").fillna(0) >= 10)
        & tor_flag.astype(bool)
    )
    df_scored.loc[boost_mask, "tor_activity_score"] *= 2

    df_scored["stacked_context_count"] = (
        (df_scored["threat_actor_score"] > 0).astype(int)
        + (df_scored["tor_activity_score"] > 0).astype(int)
        + (df_scored["incidents_events_score"] > 0).astype(int)
        + (df_scored["sources_count"] >= 2).astype(int)
        + (df_scored["partners_count"] >= 2).astype(int)
    )
    df_scored["stacked_context_bonus"] = np.select(
        [
            df_scored["stacked_context_count"] >= 4,
            df_scored["stacked_context_count"] == 3,
            df_scored["stacked_context_count"] == 2,
        ],
        [25.0, 15.0, 7.0],
        default=0.0,
    )

    threat_boost_mask = df_scored["Tagging_Boost"].astype(bool)
    df_scored.loc[threat_boost_mask, ["malicious_raw_score", "tc_raw_rating", "tc_raw_confidence", "tc_threat_raw_score"]] = 0.0
    df_scored["raw_score"] = (
        df_scored["malicious_raw_score"]
        + df_scored["continuity_raw_score"]
        + df_scored["tc_raw_rating"]
        + df_scored["tc_raw_confidence"]
        + df_scored["tor_activity_score"]
        + df_scored["incidents_events_score"]
        + df_scored["sources_raw_score"]
        + df_scored["partner_raw_score"]
        + df_scored["threat_actor_score"]
        + df_scored["cal_raw_score"]
        + df_scored["tc_threat_raw_score"]
        + df_scored["first_obs_raw_score"]
        + df_scored["stacked_context_bonus"]
    )
    df_scored["pb_base_multiplier"] = np.where(df_scored["pb_lower_flag"], PB_BASE_SCORE_MULTIPLIER, 1.0)
    df_scored["raw_score"] *= df_scored["pb_base_multiplier"]

    obs_frac = df_scored["obs_count"] / MAX_OBS_REALISTIC
    df_scored["obs_penalty_multiplier"] = (1.0 - WEIGHTS["OBSERVATION_COUNT_WEIGHT"] * obs_frac).clip(OBS_MIN_MULTIPLIER, 1.0)
    df_scored["raw_score"] *= df_scored["obs_penalty_multiplier"]
    present_frac = df_scored[["type", "rating", "confidence"]].notna().sum(axis=1) / 3
    df_scored["data_quality_multiplier"] = present_frac.clip(DATA_QUALITY_FLOOR, 1.0)
    df_scored["raw_score"] *= df_scored["data_quality_multiplier"]

    df_scored["botnet_flag"] = (
        pd.Series(df_scored["Botnet"]).apply(is_botnet).astype(int) if "Botnet" in df_scored.columns else 0
    )
    botnet_penalty_mask = (df_scored["botnet_flag"] == 1) & (~df_scored["Tagging_Boost"]) & (~df_scored["is_file_type"])
    df_scored["botnet_penalty_multiplier"] = 1.0
    df_scored.loc[botnet_penalty_mask, "botnet_penalty_multiplier"] = BOTNET_MULTIPLIER
    df_scored["raw_score"] *= df_scored["botnet_penalty_multiplier"]

    if "falsePositives" in df_scored.columns:
        df_scored["falsePositives"] = pd.to_numeric(df_scored["falsePositives"], errors="coerce").fillna(0)
        mask_fp = df_scored["falsePositives"] > 0
        df_scored["false_positive_raw_score"] = df_scored["raw_score"] * FALSE_POSITIVE_WEIGHT
        df_scored.loc[mask_fp, "raw_score"] = df_scored.loc[mask_fp, "false_positive_raw_score"]
    else:
        df_scored["falsePositives"] = 0
        df_scored["false_positive_raw_score"] = df_scored["raw_score"]

    scanner_mask_enrich = (
        df_scored["enrich_tags"].apply(has_scanner_tag)
        if "enrich_tags" in df_scored.columns
        else pd.Series(False, index=df_scored.index)
    )
    scanner_mask_tag = (
        df_scored["tag_name"].apply(convert_to_list).apply(has_scanner_tag)
        if "tag_name" in df_scored.columns
        else pd.Series(False, index=df_scored.index)
    )
    scanner_mask = (scanner_mask_enrich | scanner_mask_tag) & ~df_scored["is_file_type"]
    df_scored["scanner_penalty_multiplier"] = np.where(scanner_mask, SCANNER_PENALTY_MULTIPLIER, 1.0)
    df_scored["raw_score"] *= df_scored["scanner_penalty_multiplier"]

    tier1_col = df_scored.get("mass_scanner_tier1", None)
    tier2_col = df_scored.get("mass_scanner_tier2", None)
    mass_scanner_tier1_mask = (
        tier1_col.astype(bool) & ~df_scored["is_file_type"] if tier1_col is not None else pd.Series(False, index=df_scored.index)
    )
    mass_scanner_tier2_mask = (
        tier2_col.astype(bool) & ~df_scored["is_file_type"] if tier2_col is not None else pd.Series(False, index=df_scored.index)
    )
    df_scored["mass_scanner_penalty_multiplier"] = np.select(
        [mass_scanner_tier2_mask, mass_scanner_tier1_mask],
        [MASS_SCANNER_TIER2_MULTIPLIER, MASS_SCANNER_TIER1_MULTIPLIER],
        default=1.0,
    )
    df_scored["raw_score"] *= df_scored["mass_scanner_penalty_multiplier"]

    base_cap = _base_cap()
    df_scored["raw_score_cap_row"] = np.where(df_scored["is_file_type"], base_cap + FILE_BASELINE_RAW, base_cap)
    df_scored["PRISM_Score"] = (
        np.minimum(1000 * (df_scored["raw_score"] / df_scored["raw_score_cap_row"]).clip(0, 1) * 1.40, 1000)
        .round()
        .fillna(0)
        .astype(int)
    )

    vt_present_mask = df_scored["vt_present"]
    vt_counts_present = df_scored["vt_numeric_for_scoring"]
    low_cap_mask = vt_present_mask & (vt_counts_present <= 3)
    high_floor_mask = vt_present_mask & (vt_counts_present >= 13)
    tor_present_mask = df_scored["tor_activity_score"] > 0
    threat_actor_present_mask = df_scored["threat_actor_score"] > 0
    low_cap_final_mask = low_cap_mask & ~(tor_present_mask | threat_actor_present_mask | threat_boost_mask)
    df_scored.loc[low_cap_final_mask, "PRISM_Score"] = df_scored.loc[low_cap_final_mask, "PRISM_Score"].clip(upper=499)
    high_floor_final_mask = high_floor_mask & ~df_scored["pb_lower_flag"]
    df_scored["vt_high_floor_bypassed"] = high_floor_mask & df_scored["pb_lower_flag"]
    df_scored.loc[high_floor_final_mask, "PRISM_Score"] = df_scored.loc[high_floor_final_mask, "PRISM_Score"].clip(lower=500)

    df_scored["Severity"] = pd.cut(df_scored["PRISM_Score"], bins=SCORING_BINS, labels=SEVERITY_LABELS, right=False)
    file_hash_mask = df_scored["is_file_type"]
    df_scored.loc[file_hash_mask, "PRISM_Score"] = df_scored.loc[file_hash_mask, "PRISM_Score"].clip(lower=SCORING_BINS[3])
    df_scored.loc[file_hash_mask, "Severity"] = "critical"

    below_floor_mask = threat_boost_mask & (df_scored["PRISM_Score"] < THREAT_TAG_MIN_FLOOR)
    if below_floor_mask.any():
        vals = df_scored.loc[below_floor_mask, "PRISM_Score"].astype(float)
        min_val = vals.min()
        max_val = vals.max()
        if max_val > min_val:
            norm = (vals - min_val) / (max_val - min_val)
            df_scored.loc[below_floor_mask, "PRISM_Score"] = THREAT_TAG_MIN_FLOOR + norm * 60
        else:
            df_scored.loc[below_floor_mask, "PRISM_Score"] = THREAT_TAG_MIN_FLOOR + 30.0

    df_scored["PRISM_Score"] = df_scored["PRISM_Score"].clip(upper=1000).round().astype(int)
    df_scored["Severity"] = pd.cut(df_scored["PRISM_Score"], bins=SCORING_BINS, labels=SEVERITY_LABELS, right=False)
    df_scored.loc[df_scored["is_file_type"], "Severity"] = "critical"
    df_scored["PRISM_Score_Final"] = df_scored["PRISM_Score"].astype(int)
    df_scored["Severity_Final"] = pd.cut(
        df_scored["PRISM_Score_Final"], bins=SCORING_BINS, labels=SEVERITY_LABELS, right=False
    )
    df_scored.loc[df_scored["is_file_type"], "Severity_Final"] = "critical"
    df_scored["AI_Adjustment"] = 0
    df_scored["Explanation"] = df_scored.apply(build_explanation, axis=1)
    if "indicator" in df_scored.columns:
        df_scored.drop_duplicates(subset="indicator", inplace=True)
    df_scored.rename(columns=COLUMN_RENAME, inplace=True)
    return df_scored
