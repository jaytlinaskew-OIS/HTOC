"""Tag token helpers shared by scoring and partner extraction."""
from __future__ import annotations

import ast
import re

import pandas as pd

PB_START_LOWER_TAGS = {
    "soar indicator pb",
    "scanning cdn pb",
    "known scanning pb",
    "web scanner",
    "active scanning",
}
BOTNET_ACTIONS = {
    "scanning", "ddos", "spam", "phishing", "cryptojacking",
    "credential stuffing", "ransomware",
}
TOR_ACTIVITY = {"tor", "tor activity"}
CVE_PATTERN = re.compile(r"^cve-\d{1,4}-\d{1,7}$", re.IGNORECASE)
PAIRED_COUNTRY_TAGS = {
    "iran": ["MOIS", "IRGC", "IRGC CEC", "IRGC EWCD", "IRGC QF", "*Sandstorm", "*Kitten"],
    "russia": ["SVR", "FSB", "GRU", "*Blizzard", "*Bear"],
    "china": [
        "MSS", "ShSSB", "TSSB", "GSSB", "JSSB", "SSSB", "HuSSB", "HaSSB", "SiSSB",
        "PLA", "PLA CSF", "PLA SSF", "PLAN", "*Panda", "*Typhoon",
    ],
    "north korea": ["RGB", "*Chollima", "*Sleet"],
    "palestine": ["Hamas"],
    "lebanon": ["Lebanese Hizballah"],
}
STANDALONE_BOOST_TAGS = {
    "vietnam", "belarus", "palestine", "pakistan", "india",
    "teampcp", "compromised trivy", "operational relay box",
    "command and control", "command and control (c2)", "c2", "data exfiltration",
    "wiper", "destructive wiper", "data wiper",
    "dropper", "loader", "loader/dropper", "loader / dropper",
    "backdoor", "rat", "backdoor/rat", "backdoor / rat", "ransomware",
    "remote code execution", "remote code execution (rce)", "rce",
    "cisco", "fortigate", "fortinet", "sap netweaver",
    "apt & targeted attack", "spacehop orb", "superjumper",
}


def convert_to_list(val) -> list:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if isinstance(val, (list, set, tuple)):
        return list(val)
    if isinstance(val, str):
        text = val.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, (list, tuple)):
                    return list(parsed)
            except (ValueError, SyntaxError):
                pass
        return [x.strip() for x in val.split(",") if x.strip()]
    return [val] if val else []


def extract_pb_lower_tags_from_val(val) -> list[str]:
    return [str(x).strip() for x in convert_to_list(val) if str(x).strip().lower() in PB_START_LOWER_TAGS]


def has_pb_lower_tag(val) -> bool:
    return len(extract_pb_lower_tags_from_val(val)) > 0


def normalize_token(val) -> str:
    text = str(val).strip().lower().replace("_", " ")
    text = re.sub(r"[()]", lambda m: f" {m.group(0)} ", text)
    text = re.sub(r"\s*/\s*", " / ", text)
    return " ".join(text.split())


def flatten_tag_tokens(val) -> list[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    values = val if isinstance(val, (list, set, tuple)) else [val]
    out = []
    for item in values:
        if item is None or (isinstance(item, float) and pd.isna(item)):
            continue
        if isinstance(item, dict):
            tag_name = item.get("name")
            if tag_name is not None:
                out.append(normalize_token(tag_name))
            continue
        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            parsed = convert_to_list(text)
            if isinstance(parsed, list) and len(parsed) > 1:
                out.extend(normalize_token(x) for x in parsed if str(x).strip())
            else:
                out.extend(normalize_token(x) for x in text.split(",") if str(x).strip())
            continue
        out.append(normalize_token(item))
    return [t for t in out if t not in {"", "none", "nan"}]


def token_matches_pattern(token: str, pattern: str) -> bool:
    normalized = normalize_token(pattern)
    return token.endswith(normalized[1:]) if normalized.startswith("*") else token == normalized


def has_threat_actor(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    if isinstance(val, str):
        text = val.strip()
        return not (text == "" or text.lower() in {"none", "nan"})
    if isinstance(val, (list, set, tuple)):
        return len(val) > 0
    return False


def has_incident_event(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    if isinstance(val, (list, set, tuple)):
        return len(val) > 0
    text = str(val).strip()
    return not (text == "" or text.lower() in {"none", "nan"})


def count_sources(val) -> int:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0
    if isinstance(val, str):
        return len({s.strip() for s in val.split(",") if s.strip()})
    if isinstance(val, (list, set, tuple)):
        return len({str(s).strip() for s in val if str(s).strip()})
    return 0


def count_partners(val) -> int:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0
    if isinstance(val, (list, set, tuple)):
        return len({str(x).strip() for x in val if str(x).strip()})
    text = str(val).strip()
    if text == "" or text.lower() in {"none", "nan"}:
        return 0
    return len({str(x).strip() for x in convert_to_list(text) if str(x).strip()})


def has_tor_activity(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    if isinstance(val, (list, set, tuple)):
        text = " ".join(map(str, val)).lower()
    elif isinstance(val, str):
        if not val.strip():
            return False
        text = " ".join(x.strip() for x in val.split(",")).lower()
    else:
        text = str(val).lower()
        if text in ["nan", "none", ""]:
            return False
    return any(keyword in text for keyword in TOR_ACTIVITY)


def is_botnet(val) -> int:
    text = " ".join(map(str, val)).lower() if isinstance(val, (list, set, tuple)) else str(val).lower()
    return int(any(action in text for action in BOTNET_ACTIONS))


def has_scanner_tag(val) -> bool:
    scanners = {
        "scanner", "masscan", "zmap", "shodan", "censys",
        "active scanning: scanning ip blocks", "web scanner", "active scanning",
    }
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    text = " ".join(map(str, val)).lower() if isinstance(val, (list, set, tuple)) else str(val).lower() if val else ""
    if text in ["nan", "none", ""]:
        return False
    return any(s in text for s in scanners)


def evaluate_tagging_boost_reason(row, extra_standalone: frozenset[str] | None = None) -> str | None:
    standalone = STANDALONE_BOOST_TAGS | set(extra_standalone or ())
    token_fields = [
        "adversary", "threat_actor", "threat_actor_orig_tag", "threat_actor_category",
        "threat_nation_state", "threat_security_org", "threat_malware_class", "threat_cve_nbr",
        "tag_name", "enrich_tags", "tags.data",
    ]
    tokens = []
    for col in token_fields:
        if col in row.index:
            tokens.extend(flatten_tag_tokens(row.get(col)))
    token_set = set(tokens)
    for country, pair_tags in PAIRED_COUNTRY_TAGS.items():
        pair_hits = sorted({
            tok for tok in token_set for patt in pair_tags if token_matches_pattern(tok, patt)
        })
        if country in token_set and pair_hits:
            return f"pair:{country}+{pair_hits[0]}"
    standalone_hits = sorted(tok for tok in token_set if tok in standalone)
    if standalone_hits:
        return f"standalone:{standalone_hits[0]}"
    cve_hits = sorted(tok for tok in token_set if CVE_PATTERN.match(tok))
    if cve_hits:
        return f"cve:{cve_hits[0]}"
    return None
