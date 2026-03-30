"""Tag icon library: tags are grouped under categories (e.g. all phishing under one category with one icon)."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import pandas as pd

TAGGING_DIR = Path(__file__).resolve().parent
ICONS_JSON = TAGGING_DIR / "tag_icons_library.json"
LUCIDE_POOL_FILE = TAGGING_DIR / "lucide_icon_pool.txt"

_FALLBACK_LUCIDE_POOL: tuple[str, ...] = (
    "tags",
    "shield",
    "bug",
    "lock",
    "key-round",
    "eye",
    "globe",
    "network",
    "server",
    "cpu",
    "database",
    "mail",
    "flag",
    "radar",
    "radio",
    "wifi",
    "alert-triangle",
    "skull",
    "virus",
    "terminal",
    "fingerprint",
    "crosshair",
)

# Category id, display label, Lucide icon, substring matchers (longer strings should appear first in list).
DEFAULT_CATEGORIES: list[dict[str, object]] = [
    {
        "id": "phishing",
        "label": "Phishing",
        "icon": "mail-warning",
        "includes": [
            "spear phishing",
            "callback phish",
            "phishing for information",
            "phishing",
            "phish",
        ],
    },
    {
        "id": "ransomware",
        "label": "Ransomware & extortion",
        "icon": "skull",
        "includes": ["ransomware", "ransom", "blackcat", "black suit", "blacksuit"],
    },
    {
        "id": "malware",
        "label": "Malware",
        "icon": "bug",
        "includes": ["malware", "trojan", "worm", "botnet", "dropper", "stealer", "loader"],
    },
    {"id": "virus", "label": "Virus & cryptojacking", "icon": "virus", "includes": ["virus", "cryptojack"]},
    {
        "id": "threat_actor",
        "label": "Threat actors & groups",
        "icon": "users",
        "includes": ["threat actor", "apt", "nation-state", "nation state", "svr", "gang"],
    },
    {
        "id": "intel_api",
        "label": "Intel / API / Splunk",
        "icon": "server",
        "includes": ["splunk", " api", "api "],
    },
    {"id": "ddos", "label": "DDoS / DoS", "icon": "zap", "includes": ["ddos", "dos attack", "denial of service"]},
    {
        "id": "scanning",
        "label": "Scanning",
        "icon": "scan-search",
        "includes": ["scanning", " active scan", "scan "],
    },
    {
        "id": "credentials",
        "label": "Credentials & access",
        "icon": "key-round",
        "includes": ["credential", "stuffing", "password", "brute force"],
    },
    {
        "id": "web_attack",
        "label": "Web attacks",
        "icon": "code-xml",
        "includes": ["sql injection", "xss", "cross site", "cross-site"],
    },
    {
        "id": "exfiltration",
        "label": "Exfiltration",
        "icon": "cloud-upload",
        "includes": ["exfil", "exfiltration", "data theft"],
    },
    {
        "id": "reconnaissance",
        "label": "Reconnaissance",
        "icon": "binoculars",
        "includes": ["reconnaissance", "recon ", " recon"],
    },
    {
        "id": "exploitation",
        "label": "Exploitation",
        "icon": "shield-alert",
        "includes": ["exploit", "zero-day", "0-day"],
    },
    {"id": "wipers", "label": "Wipers & destruction", "icon": "flame", "includes": ["wiper", "destruct"]},
    {
        "id": "c2",
        "label": "C2 & beacons",
        "icon": "radio",
        "includes": ["c2", "command and control", "beacon"],
    },
    {"id": "spam_malware", "label": "Spam & malspam", "icon": "mail", "includes": ["malspam", "spam"]},
    {
        "id": "mobile",
        "label": "Mobile",
        "icon": "monitor-smartphone",
        "includes": ["mobile", "android", "ios malware"],
    },
    {"id": "dns_domains", "label": "DNS & domains", "icon": "globe", "includes": ["dns", "domain"]},
    {"id": "other", "label": "Other / uncategorized", "icon": "tags", "includes": []},
]

_LUCIDE_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
_ICONS_PARAM_RE = re.compile(r"(?:^|[?&])icons=([^&]+)")


def _load_lucide_pool() -> tuple[str, ...]:
    if LUCIDE_POOL_FILE.is_file():
        lines = [ln.strip() for ln in LUCIDE_POOL_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            return tuple(dict.fromkeys(lines))
    return _FALLBACK_LUCIDE_POOL


LUCIDE_ICON_POOL: tuple[str, ...] = _load_lucide_pool()


def canonical_tag_key(tag: str | None) -> str:
    return (tag or "").strip()


def _is_lucide_icon_name(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    return bool(_LUCIDE_NAME_RE.fullmatch(s.strip()))


def stable_icon_for_tag(tag: str, default: str = "tags") -> str:
    key = canonical_tag_key(tag)
    if not key:
        return default
    h = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)
    return LUCIDE_ICON_POOL[h % len(LUCIDE_ICON_POOL)]


def icon_svg_url(icon_name: str, library: dict | None = None) -> str:
    lib = library if library is not None else load_icon_library()
    tmpl = lib.get("icon_url_template", "https://api.iconify.design/lucide/{icon}.svg")
    return tmpl.format(icon=icon_name.strip())


def parse_icon_id_from_url(url: str) -> str | None:
    if not url:
        return None
    m = re.search(r"/lucide/([^/?.]+)\.svg(?:\?|$)", url)
    if m:
        s = m.group(1)
        return s if _is_lucide_icon_name(s) else None
    m = _ICONS_PARAM_RE.search(url)
    if not m:
        return None
    first = unquote(m.group(1)).split(",")[0].strip()
    return first if _is_lucide_icon_name(first) else None


def _ensure_icon_overrides(lib: dict) -> None:
    if "icon_overrides" not in lib or lib["icon_overrides"] is None:
        lib["icon_overrides"] = {}


def _default_categories_dict() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for spec in DEFAULT_CATEGORIES:
        cid = str(spec["id"])
        out[cid] = {
            "label": spec["label"],
            "icon": spec["icon"],
            "includes": list(spec.get("includes", [])),
            "tags": [],
        }
    return out


def _ensure_categories(lib: dict) -> None:
    if lib.get("categories") and isinstance(lib["categories"], dict) and len(lib["categories"]) > 0:
        for cid, c in lib["categories"].items():
            c.setdefault("label", cid)
            c.setdefault("icon", "tags")
            c.setdefault("includes", [])
            c.setdefault("tags", [])
        if "other" not in lib["categories"]:
            lib["categories"]["other"] = {
                "label": "Other / uncategorized",
                "icon": "tags",
                "includes": [],
                "tags": [],
            }
        return
    lib["categories"] = _default_categories_dict()
    if lib.get("families"):
        for fam in lib["families"]:
            icon = fam.get("icon")
            if not icon:
                continue
            cid = next((k for k, v in lib["categories"].items() if v.get("icon") == icon), None)
            if cid:
                inc = lib["categories"][cid].setdefault("includes", [])
                for x in fam.get("includes", []) or []:
                    if x not in inc:
                        inc.append(x)


def _match_includes(tag: str, needles: list) -> bool:
    t = tag.casefold()
    for needle in sorted((needles or []), key=lambda x: len(str(x)), reverse=True):
        if str(needle).casefold() in t:
            return True
    return False


def match_family_icon(tag: str, families: list[dict]) -> str | None:
    """Legacy: return Lucide id from flat families list."""
    t = tag.casefold()
    for fam in families:
        icon = fam.get("icon")
        if not icon or not _is_lucide_icon_name(str(icon)):
            continue
        icon = str(icon).strip()
        for ex in fam.get("exact", []) or []:
            if str(ex).casefold().strip() == t:
                return icon
        needles = sorted((fam.get("includes", []) or []), key=lambda x: len(str(x)), reverse=True)
        for needle in needles:
            if str(needle).casefold() in t:
                return icon
    return None


def assign_category_id_for_tag(tag: str, lib: dict) -> str:
    """
    Pick a category id: explicit membership first, then includes order (DEFAULT_CATEGORIES order),
    then legacy families, then other.
    """
    _ensure_categories(lib)
    key = canonical_tag_key(tag)
    cats = lib["categories"]

    for cid, c in cats.items():
        if key in (c.get("tags") or []):
            return cid

    for spec in DEFAULT_CATEGORIES:
        cid = spec["id"]
        if cid not in cats:
            continue
        c = cats[cid]
        if cid == "other":
            continue
        for ex in c.get("exact", []) or []:
            if str(ex).casefold().strip() == key.casefold():
                return cid
        if _match_includes(key, c.get("includes", [])):
            return cid

    fam = match_family_icon(key, lib.get("families", []) or [])
    if fam:
        for cid, c in cats.items():
            if c.get("icon") == fam:
                return cid

    return "other"


def _entries_are_nested(entries: dict) -> bool:
    """True when entries[category_id][tag_name] = {icon_url}; False for legacy flat entries[tag]."""
    if not entries:
        return True
    for v in entries.values():
        if not isinstance(v, dict):
            continue
        if "icon_url" in v or "category" in v:
            return False
    return True


def migrate_entries_flat_to_nested(lib: dict) -> None:
    """Legacy flat entries[tag] = {icon_url, category} -> entries[cid][tag] = {icon_url}."""
    raw = lib.get("entries", {})
    if not raw:
        return
    first = next(iter(raw.values()), None)
    if not isinstance(first, dict) or "category" not in first:
        return
    nested: dict[str, dict[str, dict[str, str]]] = {}
    for tag, e in raw.items():
        if not isinstance(e, dict):
            continue
        cid = str(e.get("category", "other"))
        nested.setdefault(cid, {})[tag] = {"icon_url": str(e["icon_url"]).strip()}
    lib["entries"] = nested


def get_entry_for_tag(tag: str, lib: dict) -> dict | None:
    """Resolve entries[category][tag] or legacy entries[tag]."""
    key = canonical_tag_key(tag)
    ent = lib.get("entries", {})
    if not ent:
        return None
    if _entries_are_nested(ent):
        for bucket in ent.values():
            if isinstance(bucket, dict) and key in bucket:
                return bucket[key]
        return None
    e = ent.get(key)
    return e if isinstance(e, dict) else None


def iter_all_tags_in_entries(entries: dict) -> list[str]:
    if not entries:
        return []
    if _entries_are_nested(entries):
        out: list[str] = []
        for bucket in entries.values():
            if isinstance(bucket, dict):
                out.extend(bucket.keys())
        return out
    return [k for k in entries.keys() if canonical_tag_key(str(k))]


def find_category_id_for_tag(tag: str, lib: dict) -> str | None:
    """Category from categories.tags, nested entries, or assignment rules."""
    key = canonical_tag_key(tag)
    _ensure_categories(lib)
    for cid, c in lib["categories"].items():
        if key in (c.get("tags") or []):
            return cid
    ent = lib.get("entries", {})
    if _entries_are_nested(ent):
        for cid, bucket in ent.items():
            if isinstance(bucket, dict) and key in bucket:
                return cid
    elif isinstance(ent.get(key), dict) and "category" in ent[key]:
        return ent[key].get("category")
    return assign_category_id_for_tag(tag, lib)


def resolved_icon_url_for_tag(tag_key: str, lib: dict, raw_entry: dict | None) -> str:
    _ensure_categories(lib)
    _ensure_icon_overrides(lib)
    key = canonical_tag_key(tag_key)
    default_id = lib.get("default_icon", "tags")

    over = lib.get("icon_overrides", {}).get(key)
    if over and _is_lucide_icon_name(str(over)):
        return icon_svg_url(str(over).strip(), lib)

    cid = find_category_id_for_tag(key, lib)
    if cid and cid in lib["categories"]:
        c = lib["categories"][cid]
        if c.get("icon_url"):
            return str(c["icon_url"]).strip()
        icon = c.get("icon", default_id)
        if cid == "other":
            return icon_svg_url(stable_icon_for_tag(key, default_id), lib)
        if _is_lucide_icon_name(str(icon)):
            return icon_svg_url(str(icon).strip(), lib)

    if raw_entry and isinstance(raw_entry, dict) and raw_entry.get("icon_url"):
        url = str(raw_entry["icon_url"]).strip()
        pid = parse_icon_id_from_url(url)
        if pid:
            return icon_svg_url(pid, lib)
        if url.startswith("http"):
            return url

    return icon_svg_url(stable_icon_for_tag(key, default_id), lib)


def rebuild_categories_and_entries(lib: dict, all_tags: list[str]) -> None:
    """Sort each tag into a category and rebuild flat `entries` with icon_url + category."""
    _ensure_categories(lib)
    _ensure_icon_overrides(lib)
    cats = lib["categories"]

    prev_membership: dict[str, str] = {}
    for cid, c in cats.items():
        for t in c.get("tags") or []:
            prev_membership[canonical_tag_key(t)] = cid

    for c in cats.values():
        c["tags"] = []

    seen = sorted(set(canonical_tag_key(t) for t in all_tags if canonical_tag_key(t)))
    tag_to_cat: dict[str, str] = {}
    for tag in seen:
        cid = prev_membership.get(tag)
        if not cid or cid not in cats:
            cid = assign_category_id_for_tag(tag, lib)
        cats.setdefault(cid, {"label": cid, "icon": "tags", "includes": [], "tags": []})
        tag_to_cat[tag] = cid
        cats[cid]["tags"].append(tag)

    for cid in cats:
        cats[cid]["tags"] = sorted(set(cats[cid]["tags"]))

    lib["entries"] = {}
    cat_ids = sorted(set(tag_to_cat.values()), key=lambda x: (x == "other", x))
    for cid in cat_ids:
        lib["entries"][cid] = {}
    for tag in seen:
        cid = tag_to_cat[tag]
        url = resolved_icon_url_for_tag(tag, lib, get_entry_for_tag(tag, lib))
        lib["entries"].setdefault(cid, {})[tag] = {"icon_url": url}


def normalize_library(lib: dict) -> dict:
    lib.pop("defaults_by_threat_category", None)
    lib["icon_url_template"] = "https://api.iconify.design/lucide/{icon}.svg"
    lib["icon_cdn"] = "iconify"
    lib["default_icon"] = lib.get("default_icon", "tags")
    _ensure_categories(lib)
    _ensure_icon_overrides(lib)
    migrate_entries_flat_to_nested(lib)

    raw_entries = lib.get("entries", {})
    tags_from_entries = iter_all_tags_in_entries(raw_entries)
    if tags_from_entries:
        rebuild_categories_and_entries(lib, tags_from_entries)

    lib["schema_version"] = 8
    lib["icon_format"] = "svg_url"
    if lib.get("categories"):
        lib.pop("families", None)
    lib["description"] = (
        "categories: label, icon, includes, tags. entries: nested by category id — entries.phishing[\"Tag Name\"] = {icon_url}. "
        "Sync preserves grouping; migrate converts legacy flat entries[tag].category."
    )
    return lib


def load_icon_library(path: Path | None = None) -> dict:
    p = path or ICONS_JSON
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_icon_library(data: dict, path: Path | None = None) -> None:
    p = path or ICONS_JSON
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def sync_icon_entries_from_dataframe(
    tags_df: pd.DataFrame,
    library: dict | None = None,
    *,
    tag_col: str = "tag",
) -> tuple[dict, dict]:
    lib = normalize_library(library if library is not None else load_icon_library())

    if tag_col not in tags_df.columns:
        raise KeyError(f"Missing column {tag_col!r}")

    tdf = tags_df.dropna(subset=[tag_col]).copy()
    tdf[tag_col] = tdf[tag_col].astype(str).map(canonical_tag_key)
    tdf = tdf[tdf[tag_col] != ""]

    unique_tags = sorted(set(tdf[tag_col].tolist()))
    rebuild_categories_and_entries(lib, unique_tags)

    by_cat: dict[str, int] = {}
    ent = lib.get("entries", {})
    if _entries_are_nested(ent):
        for cid, bucket in ent.items():
            if isinstance(bucket, dict):
                by_cat[cid] = len(bucket)
    else:
        for t, e in ent.items():
            cid = (e or {}).get("category", "other")
            by_cat[cid] = by_cat.get(cid, 0) + 1

    n_tags = sum(by_cat.values()) if by_cat else 0
    stats = {
        "distinct_tag_names": len(unique_tags),
        "entries_in_library": n_tags,
        "tags_per_category": by_cat,
    }
    return lib, stats


def icon_id_for_tag(tag: str | float | None, library: dict | None = None) -> str:
    lib = library if library is not None else load_icon_library()
    default_id = lib.get("default_icon", "tags")
    if tag is None or (isinstance(tag, float) and pd.isna(tag)):
        return default_id
    key = canonical_tag_key(str(tag))
    if not key:
        return default_id
    ent = get_entry_for_tag(key, lib)
    if ent and ent.get("icon_url"):
        pid = parse_icon_id_from_url(str(ent["icon_url"]))
        if pid:
            return pid
    over = lib.get("icon_overrides", {}).get(key)
    if over and _is_lucide_icon_name(str(over)):
        return str(over).strip()
    cid = find_category_id_for_tag(key, lib)
    c = lib.get("categories", {}).get(cid or "", {})
    icon = c.get("icon", default_id)
    if (cid or "") == "other":
        return stable_icon_for_tag(key, default_id)
    return str(icon).strip() if _is_lucide_icon_name(str(icon)) else stable_icon_for_tag(key, default_id)


def icon_url_for_tag(tag: str | float | None, library: dict | None = None) -> str:
    lib = library if library is not None else load_icon_library()
    default_id = lib.get("default_icon", "tags")
    if tag is None or (isinstance(tag, float) and pd.isna(tag)):
        return icon_svg_url(default_id, lib)
    key = canonical_tag_key(str(tag))
    if not key:
        return icon_svg_url(default_id, lib)
    ent = get_entry_for_tag(key, lib)
    if ent and ent.get("icon_url"):
        return str(ent["icon_url"]).strip()
    return resolved_icon_url_for_tag(key, lib, ent)


def icon_for_tag(tag: str | float | None, library: dict | None = None) -> str:
    return icon_url_for_tag(tag, library)


def decorate_tags_column(
    tags_df: pd.DataFrame,
    *,
    tag_col: str = "tag",
    library: dict | None = None,
) -> pd.Series:
    return tags_df[tag_col].map(
        lambda t: str(t).strip() if pd.notna(t) and canonical_tag_key(str(t)) else ""
    )


def decorate_tags_column_html(
    tags_df: pd.DataFrame,
    *,
    tag_col: str = "tag",
    library: dict | None = None,
    icon_size: int = 16,
) -> pd.Series:
    lib = library if library is not None else load_icon_library()
    return tags_df[tag_col].map(lambda t: tag_html_span(t, lib, size=icon_size))


def tag_html_span(
    tag: str | float | None,
    library: dict | None = None,
    *,
    size: int = 16,
) -> str:
    lib = library if library is not None else load_icon_library()
    if tag is None or (isinstance(tag, float) and pd.isna(tag)):
        return ""
    text = canonical_tag_key(str(tag))
    if not text:
        return ""
    url = icon_url_for_tag(text, lib)
    esc_text = html.escape(text)
    esc_url = html.escape(url)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;">'
        f'<img src="{esc_url}" width="{size}" height="{size}" alt="" '
        f'style="vertical-align:middle;opacity:.92"/>'
        f"<span>{esc_text}</span>"
        f"</span>"
    )


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"Z:\HTOC\Data_Analytics\Data\Observed_Tags\htoc_observed_indicator_tags.csv"
    )
    if not csv_path.is_file():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        print("Usage: python tag_icons.py <path_to_htoc_observed_indicator_tags.csv>", file=sys.stderr)
        sys.exit(1)
    tags_df = pd.read_csv(csv_path)
    lib = load_icon_library()
    lib, stats = sync_icon_entries_from_dataframe(tags_df, lib)
    save_icon_library(lib)
    print(f"Saved {ICONS_JSON}")
    print(stats)


if __name__ == "__main__":
    main()
