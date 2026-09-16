"""Google Threat Intelligence (VirusTotal v3) IOC lookup and enrich columns.

Production scoring still uses ``enrich_vtMaliciousCount`` (GTI last_analysis_stats.malicious).
GTI verdict / score / Mandiant flags are extra columns, not formula inputs.
"""
from __future__ import annotations

import base64
import ipaddress
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests

from htoc.core.bootstrap import find_htoc_src, htoc_src_dir
from htoc.core.paths import gti_cache_path
from htoc.core.pipeline import PipelineError

GTI_BASE = "https://www.virustotal.com/api/v3"
X_TOOL = "htoc.VirusTotalApi.v0.1"
RELATIONSHIPS = "related_threat_actors,malware_families,campaigns"
_HEX_HASH = re.compile(r"^[0-9a-fA-F]{32}$|^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$")
_PLACEHOLDER_KEY = "PASTE_YOUR_GOOGLE_THREAT_INTEL_API_KEY_HERE"
CACHE_TTL_DAYS = 7
CACHE_FLUSH_EVERY = 25
GTI_IOC_TYPES = {
    "Address", "IPv4", "IPv6", "Host", "Domain", "URL", "File", "SHA1", "SHA256", "MD5",
}
_TYPE_TO_KIND = {
    "Address": "ip",
    "IPv4": "ip",
    "IPv6": "ip",
    "Host": "domain",
    "Domain": "domain",
    "URL": "url",
    "File": "file",
    "SHA1": "file",
    "SHA256": "file",
    "MD5": "file",
}
ENRICH_COLUMNS = (
    "enrich_vtMaliciousCount",
    "enrich_gti_verdict",
    "enrich_gti_severity",
    "enrich_gti_threat_score",
    "enrich_gti_description",
    "enrich_gti_mandiant",
    "enrich_gti_threat_actors",
    "enrich_gti_malware_families",
)


def repo_root(start: Path | str | None = None) -> Path:
    src = find_htoc_src(start=start) or htoc_src_dir()
    return src.parent.parent


def gti_config_path(start: Path | str | None = None) -> Path:
    return repo_root(start) / "notebooks" / "GoogleThreatIntel" / "config.json"


def _apply_dotenv(start: Path | str | None = None) -> None:
    path = repo_root(start) / ".env"
    if not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_gti_api_key(*, start: Path | str | None = None) -> str:
    """API key from env, repo ``.env``, or GoogleThreatIntel ``config.json``."""
    _apply_dotenv(start)
    for name in ("GTI_API_KEY", "VT_API_KEY", "VT_APIKEY"):
        raw = os.environ.get(name, "").strip()
        if raw and raw != _PLACEHOLDER_KEY:
            return raw
    path = gti_config_path(start)
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raw = str(payload.get("api_key") or "").strip()
            if raw and raw != _PLACEHOLDER_KEY:
                return raw
    raise PipelineError(
        "Google TI API key missing. Set GTI_API_KEY or VT_API_KEY, "
        f"or put api_key in {path}."
    )


def _headers(api_key: str | None = None) -> dict[str, str]:
    key = api_key if api_key is not None else load_gti_api_key()
    return {
        "Accept": "application/json",
        "x-apikey": key,
        "x-tool": X_TOOL,
    }


def classify_ioc(value: str) -> str:
    text = str(value).strip()
    if _HEX_HASH.fullmatch(text):
        return "file"
    if text.lower().startswith(("http://", "https://")):
        return "url"
    try:
        ipaddress.ip_address(text)
        return "ip"
    except ValueError:
        return "domain"


def url_id(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def kind_from_tc_type(tc_type: str | None, value: str) -> str:
    mapped = _TYPE_TO_KIND.get(str(tc_type or "").strip())
    return mapped or classify_ioc(value)


def gti_path(value: str, ioc_type: str | None = None) -> str:
    kind = ioc_type if ioc_type in {"ip", "domain", "file", "url"} else classify_ioc(value)
    if kind == "ip":
        return f"/ip_addresses/{quote(value, safe='')}"
    if kind == "domain":
        return f"/domains/{quote(value, safe='')}"
    if kind == "file":
        return f"/files/{quote(value, safe='')}"
    if kind == "url":
        return f"/urls/{url_id(value)}"
    raise ValueError(f"Unsupported IOC type: {kind}")


def gui_link(value: str, ioc_type: str | None = None) -> str:
    kind = ioc_type if ioc_type in {"ip", "domain", "file", "url"} else classify_ioc(value)
    if kind == "ip":
        return f"https://www.virustotal.com/gui/ip-address/{quote(value, safe='')}"
    if kind == "domain":
        return f"https://www.virustotal.com/gui/domain/{quote(value, safe='')}"
    if kind == "file":
        return f"https://www.virustotal.com/gui/file/{quote(value, safe='')}"
    return f"https://www.virustotal.com/gui/url/{url_id(value)}"


def _nested(obj: Any, *keys: str) -> Any:
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _rel_ids(relationships: dict[str, Any], name: str) -> list[str]:
    payload = relationships.get(name) if isinstance(relationships, dict) else None
    data = (payload or {}).get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ident = item.get("id") or item.get("name")
        if ident:
            out.append(str(ident))
    return out


def _truthy_mandiant_factor(key: str, val: Any) -> bool:
    if "mandiant" not in key.lower():
        return False
    if val in (None, False, 0, 0.0, "", [], {}):
        return False
    return True


def flatten_gti_report(payload: dict[str, Any], *, indicator: str) -> dict[str, Any]:
    """Map one GTI JSON report onto ``enrich_*`` columns used by PRISM / V5."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        data = {}
    attrs = data.get("attributes") if isinstance(data.get("attributes"), dict) else {}
    stats = attrs.get("last_analysis_stats") if isinstance(attrs.get("last_analysis_stats"), dict) else {}
    gti = attrs.get("gti_assessment") if isinstance(attrs.get("gti_assessment"), dict) else {}
    factors = gti.get("contributing_factors") if isinstance(gti.get("contributing_factors"), dict) else {}
    relationships = data.get("relationships") if isinstance(data.get("relationships"), dict) else {}
    actors = _rel_ids(relationships, "related_threat_actors")
    families = _rel_ids(relationships, "malware_families")
    campaigns = _rel_ids(relationships, "campaigns")
    mandiant = any(_truthy_mandiant_factor(k, v) for k, v in factors.items()) or bool(
        actors or families or campaigns
    )
    malicious = stats.get("malicious")
    try:
        malicious_n = int(malicious) if malicious is not None else None
    except (TypeError, ValueError):
        malicious_n = None
    return {
        "indicator": indicator,
        "enrich_vtMaliciousCount": malicious_n,
        "enrich_gti_verdict": _nested(gti, "verdict", "value"),
        "enrich_gti_severity": _nested(gti, "severity", "value"),
        "enrich_gti_threat_score": _nested(gti, "threat_score", "value"),
        "enrich_gti_description": gti.get("description"),
        "enrich_gti_mandiant": bool(mandiant),
        "enrich_gti_threat_actors": ", ".join(actors),
        "enrich_gti_malware_families": ", ".join(families),
    }


def gti_get(
    path: str,
    params: dict[str, Any] | None = None,
    *,
    session: requests.Session | None = None,
    timeout: int = 30,
    max_retries: int = 4,
    api_key: str | None = None,
) -> dict[str, Any]:
    url = f"{GTI_BASE}{path}"
    http = session or requests
    headers = _headers(api_key)
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        response = http.get(url, headers=headers, params=params, timeout=timeout)
        if response.status_code == 404:
            raise FileNotFoundError(f"Not found in Google TI: {path}")
        if response.status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
            retry_after = response.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else 15.0
            except (TypeError, ValueError):
                wait = 15.0
            time.sleep(max(wait, 1.0))
            last_error = RuntimeError(f"GTI {response.status_code} {url}")
            continue
        if not response.ok:
            raise RuntimeError(f"GTI {response.status_code} {url}: {response.text[:500]}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError(f"GTI non-object JSON for {url}")
        return payload
    raise RuntimeError(str(last_error) if last_error else f"GTI failed {url}")


def lookup_ioc(
    value: str,
    *,
    ioc_type: str | None = None,
    session: requests.Session | None = None,
    api_key: str | None = None,
    timeout: int = 30,
    max_retries: int = 4,
) -> dict[str, Any]:
    text = str(value).strip()
    if not text:
        raise ValueError("indicator is empty")
    kind = ioc_type if ioc_type in {"ip", "domain", "file", "url"} else classify_ioc(text)
    return gti_get(
        gti_path(text, kind),
        params={"relationships": RELATIONSHIPS},
        session=session,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
    )


_tls = threading.local()
_CACHE_LOCK = threading.Lock()


def _thread_session() -> requests.Session:
    sess = getattr(_tls, "session", None)
    if sess is None:
        sess = requests.Session()
        _tls.session = sess
    return sess


def _lookup_row(
    value: str,
    tc_type: str | None,
    *,
    session: requests.Session | None,
    api_key: str,
    timeout: int = 20,
    max_retries: int = 2,
) -> dict[str, Any]:
    kind = kind_from_tc_type(tc_type, value)
    report = lookup_ioc(
        value,
        ioc_type=kind,
        session=session,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
    )
    return flatten_gti_report(report, indicator=value)


def resolve_gti_cache_path(start: Path | str | None = None) -> Path | None:
    env = os.environ.get("GTI_CACHE_PATH", "").strip()
    if env:
        return Path(env)
    try:
        path = gti_cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        local = gti_config_path(start).parent / "gti_cache.json"
        try:
            local.parent.mkdir(parents=True, exist_ok=True)
            return local
        except OSError:
            return None


def _cache_fresh(entry: dict[str, Any], *, ttl_days: int = CACHE_TTL_DAYS) -> bool:
    fetched = entry.get("fetched_at")
    if not fetched:
        return False
    try:
        ts = datetime.fromisoformat(str(fetched).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return False
    return datetime.now(UTC) - ts < timedelta(days=ttl_days)


def _load_cache(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(cache), encoding="utf-8")
    tmp.replace(path)


def _row_from_cache(entry: dict[str, Any], *, col: str, value: str) -> dict[str, Any]:
    row = {name: entry.get(name) for name in ENRICH_COLUMNS}
    row[col] = value
    return row


def attach_gti_enrichment(
    agg_df: pd.DataFrame,
    *,
    key_col: str | None = None,
    type_col: str = "type",
    max_workers: int = 4,
    api_key: str | None = None,
    session: requests.Session | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Merge GTI ``enrich_*`` columns onto ``agg_df``. One GET per unique IOC.

    Missing key, cache I/O errors, and GTI outages are fail-open: the original
    frame is returned and scoring continues with missing VT counts (neutral 0).
    """
    if agg_df.empty:
        return agg_df.copy()
    col = key_col or ("indicator" if "indicator" in agg_df.columns else "summary")
    if col not in agg_df.columns:
        return agg_df.copy()

    try:
        key = api_key if api_key is not None else load_gti_api_key()
    except PipelineError as exc:
        print(f"WARN: {exc} Scoring continues without Google TI.")
        return agg_df.copy()

    cols = [col] + ([type_col] if type_col in agg_df.columns else [])
    candidates = (
        agg_df[cols].dropna(subset=[col]).astype({col: str}).drop_duplicates(subset=[col])
    )
    if type_col in candidates.columns:
        typed = candidates[type_col].astype(str).str.strip()
        mask = typed.isin(GTI_IOC_TYPES) | typed.eq("") | typed.eq("nan")
        candidates = candidates[mask].copy()
    if candidates.empty:
        return agg_df.copy()

    cache_path = resolve_gti_cache_path() if use_cache else None
    cache: dict[str, Any] = _load_cache(cache_path) if cache_path is not None else {}
    cache_dirty = 0
    rows: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []
    workers = max(1, int(max_workers))
    circuit_fails = 0
    circuit_open = False
    circuit_lock = threading.Lock()
    trip_after = 8

    def _store_cache(value: str, entry: dict[str, Any]) -> None:
        nonlocal cache_dirty
        if cache_path is None:
            return
        with _CACHE_LOCK:
            cache[value] = entry
            cache_dirty += 1
            if cache_dirty >= CACHE_FLUSH_EVERY:
                try:
                    _save_cache(cache_path, cache)
                    cache_dirty = 0
                except OSError as exc:
                    print(f"WARN: Google TI cache write failed ({exc})")

    def _one(row_series: pd.Series) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
        nonlocal circuit_fails, circuit_open
        value = str(row_series[col]).strip()
        typ = str(row_series[type_col]).strip() if type_col in row_series.index else ""
        if not value:
            return None, None
        with _CACHE_LOCK:
            cached = cache.get(value) if isinstance(cache.get(value), dict) else None
        if cached and _cache_fresh(cached):
            if cached.get("not_found"):
                return None, None
            return _row_from_cache(cached, col=col, value=value), None
        with circuit_lock:
            if circuit_open:
                return None, {col: value, "error": "gti circuit open"}
        http = session if (session is not None and workers == 1) else _thread_session()
        try:
            payload = _lookup_row(value, typ or None, session=http, api_key=key)
            payload[col] = value
            if col != "indicator":
                payload.pop("indicator", None)
            entry = {name: payload.get(name) for name in ENRICH_COLUMNS}
            entry["fetched_at"] = datetime.now(UTC).isoformat()
            _store_cache(value, entry)
            with circuit_lock:
                circuit_fails = 0
            return payload, None
        except FileNotFoundError:
            _store_cache(value, {"not_found": True, "fetched_at": datetime.now(UTC).isoformat()})
            return None, None
        except Exception as exc:
            with circuit_lock:
                circuit_fails += 1
                if circuit_fails >= trip_after and not circuit_open:
                    circuit_open = True
                    print(
                        "WARN: Google TI lookups failing repeatedly; "
                        "remaining IOCs skip GTI and scoring continues."
                    )
            return None, {col: value, "error": str(exc)}

    try:
        if workers == 1:
            for _, row in candidates.iterrows():
                result, err = _one(row)
                if result is not None:
                    rows.append(result)
                elif err is not None:
                    failed.append(err)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_one, row) for _, row in candidates.iterrows()]
                for future in as_completed(futures):
                    result, err = future.result()
                    if result is not None:
                        rows.append(result)
                    elif err is not None:
                        failed.append(err)
        if cache_path is not None and cache_dirty:
            try:
                _save_cache(cache_path, cache)
            except OSError as exc:
                print(f"WARN: Google TI cache write failed ({exc})")
    except Exception as exc:
        print(f"WARN: Google TI enrichment failed ({exc}). Scoring continues without GTI columns.")
        return agg_df.copy()

    skipped = sum(1 for item in failed if item.get("error") == "gti circuit open")
    shown = [item for item in failed if item.get("error") != "gti circuit open"]
    if shown:
        print(f"WARN: {len(failed)} Google TI lookups failed (showing up to 10)")
        print(pd.DataFrame(shown).head(10).to_string())
    elif skipped:
        print(f"WARN: {skipped} Google TI lookups skipped after repeated failures")
    if not rows:
        return agg_df.copy()

    extra = pd.DataFrame(rows).drop_duplicates(subset=[col], keep="last")
    overlap = [c for c in extra.columns if c != col and c in agg_df.columns]
    out = agg_df.drop(columns=overlap, errors="ignore")
    return out.merge(extra, on=col, how="left")
