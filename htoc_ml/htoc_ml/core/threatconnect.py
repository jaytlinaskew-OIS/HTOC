"""ThreatConnect API session, indicator queries, and enrichment.

Connection and query knobs are set at the call site so any model can reuse this.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

import pandas as pd
import pytz
import urllib3

from htoc_ml.core.pipeline import PipelineError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_INDICATOR_FIELDS = ("tags", "observations", "associatedGroups", "falsePositives", "threatAssess")


def load_api_config(config_path: str | Path) -> tuple[str, str, str, str]:
    """Load api_secret_key, api_access_id, api_base_url, api_default_org from config.json."""
    path = Path(config_path)
    if not path.is_file():
        raise PipelineError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        config = json.load(fh)
    secret = config.get("api_secret_key")
    access_id = config.get("api_access_id")
    base_url = config.get("api_base_url")
    org = config.get("api_default_org")
    if not all([secret, access_id, base_url, org]):
        raise PipelineError("config.json is missing one or more required ThreatConnect keys")
    return secret, access_id, base_url, org


def _quoted(values: Sequence[str]) -> str:
    return ", ".join(f'"{v}"' for v in values)


def build_indicator_tql(*, owner_names: Sequence[str] | None = None, indicator_types: Sequence[str] | None = None, summaries: Sequence[str] | None = None, last_observed_on_or_after: str | None = None, extra_clauses: Sequence[str] | None = None) -> str:
    """Build a TQL string from named filters. Pass only the clauses you need."""
    clauses: list[str] = []
    if owner_names:
        clauses.append(f"ownerName IN ({_quoted(owner_names)})")
    if indicator_types:
        clauses.append(f"typeName IN ({_quoted(indicator_types)})")
    if summaries:
        clauses.append(f"summary IN ({_quoted(summaries)})")
    if last_observed_on_or_after:
        clauses.append(f'lastObserved >= "{last_observed_on_or_after}"')
    if extra_clauses:
        clauses.extend(str(c).strip() for c in extra_clauses if str(c).strip())
    if not clauses:
        raise PipelineError("build_indicator_tql requires at least one filter clause")
    return " AND ".join(clauses)


def _fields_query_value(fields: Sequence[str] | str) -> str:
    if isinstance(fields, str):
        return fields
    return ",".join(fields)


class ThreatConnectClient:
    """Reusable ThreatConnect API client. Pass connection paths/params into ``__init__``."""

    def __init__(self, *, config_path: str | Path, tc_sdk_path: str | Path, tc_project_root: str | Path, result_page_size: int = 500) -> None:
        self.result_page_size = int(result_page_size)
        sdk = str(tc_sdk_path)
        project = str(tc_project_root)
        if sdk not in sys.path:
            sys.path.insert(0, sdk)
        if project not in sys.path:
            sys.path.insert(0, project)
        from ThreatConnect import ThreatConnect
        from RequestObject import RequestObject

        self._RequestObject = RequestObject
        secret, access_id, base_url, org = load_api_config(config_path)
        self.session = ThreatConnect(access_id, secret, org, base_url)

    def paginate_indicators(self, tql: str, *, fields: Sequence[str] | str = DEFAULT_INDICATOR_FIELDS, page_size: int | None = None, result_start: int = 0, sorting: str | None = None) -> list[dict]:
        """GET /v3/indicators pages. Set ``tql``, ``fields``, ``page_size``, ``result_start``, ``sorting`` at call site."""
        encoded_tql = urllib.parse.quote(tql)
        field_param = urllib.parse.quote(_fields_query_value(fields), safe=",")
        request = self._RequestObject()
        request.set_http_method("GET")
        pages: list[dict] = []
        start = int(result_start)
        limit = self.result_page_size if page_size is None else int(page_size)
        while True:
            uri = (
                f"/v3/indicators?tql={encoded_tql}"
                f"&fields={field_param}"
                f"&resultStart={start}&resultLimit={limit}"
            )
            if sorting:
                uri += f"&sorting={urllib.parse.quote(sorting)}"
            request.set_request_uri(uri)
            try:
                response = self.session.api_request(request)
            except Exception as exc:
                raise PipelineError(f"Failed to query indicators (start={start}): {exc}") from exc
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise PipelineError(f"Non-JSON response ({content_type}): {response.content[:200]}")
            payload = response.json()
            items = payload.get("data", []) or []
            if not items:
                break
            pages.append(payload)
            start += limit
        return pages

    def query_indicators(self, *, tql: str | None = None, owner_names: Sequence[str] | None = None, indicator_types: Sequence[str] | None = None, summaries: Sequence[str] | None = None, last_observed_on_or_after: str | None = None, extra_tql_clauses: Sequence[str] | None = None, fields: Sequence[str] | str = DEFAULT_INDICATOR_FIELDS, page_size: int | None = None, result_start: int = 0, sorting: str | None = None) -> pd.DataFrame:
        """Query indicators with either a raw ``tql`` string or named TQL filter params."""
        query = tql or build_indicator_tql(
            owner_names=owner_names,
            indicator_types=indicator_types,
            summaries=summaries,
            last_observed_on_or_after=last_observed_on_or_after,
            extra_clauses=extra_tql_clauses,
        )
        return self.normalize_indicator_pages(
            self.paginate_indicators(query, fields=fields, page_size=page_size, result_start=result_start, sorting=sorting)
        )

    def normalize_indicator_pages(self, pages: list[dict]) -> pd.DataFrame:
        rows = []
        for page in pages:
            for item in page.get("data", []) or []:
                if isinstance(item, dict) and "summary" in item:
                    rows.append(item)
        if not rows:
            return pd.DataFrame()
        frame = pd.json_normalize(rows)
        frame["indicator"] = frame["summary"].astype(str).str.split().str[0].str.strip()
        sources = (
            frame.groupby("indicator")["ownerName"]
            .apply(lambda x: ", ".join(sorted(set(x))))
            .reset_index()
            .rename(columns={"ownerName": "sources"})
        )
        return frame.merge(sources, on="indicator", how="left")

    def query_indicators_by_last_observed(self, *, owner_names: Sequence[str], indicator_types: Sequence[str], lookback_days: int = 7, prefer_owner: str = "HTOC Org", fields: Sequence[str] | str = DEFAULT_INDICATOR_FIELDS, page_size: int | None = None, extra_tql_clauses: Sequence[str] | None = None, sorting: str | None = None) -> pd.DataFrame:
        """Indicators lastObserved within ``lookback_days``, optionally filtered to ``prefer_owner``."""
        start_date = (datetime.now(pytz.UTC) - timedelta(days=lookback_days)).date()
        start = f"{start_date}T00:00:00Z"
        frame = self.query_indicators(
            owner_names=owner_names,
            indicator_types=indicator_types,
            last_observed_on_or_after=start,
            extra_tql_clauses=extra_tql_clauses,
            fields=fields,
            page_size=page_size,
            sorting=sorting,
        )
        if frame.empty:
            return frame
        frame["lastObserved"] = pd.to_datetime(frame["lastObserved"], utc=True, errors="coerce")
        frame = frame[frame["lastObserved"] >= pd.to_datetime(start, utc=True)]
        if prefer_owner:
            frame = frame[frame["ownerName"] == prefer_owner]
        return frame.copy()

    def query_indicators_by_summaries(self, *, summaries: Sequence[str], owner_names: Sequence[str], indicator_types: Sequence[str], prefer_owner: str = "HTOC Org", fields: Sequence[str] | str = DEFAULT_INDICATOR_FIELDS, page_size: int | None = None, extra_tql_clauses: Sequence[str] | None = None, sorting: str | None = None) -> pd.DataFrame:
        """Indicators matching ``summaries``, one row per indicator (prefer_owner first when present)."""
        if not summaries:
            return pd.DataFrame()
        frame = self.query_indicators(
            owner_names=owner_names,
            indicator_types=indicator_types,
            summaries=summaries,
            extra_tql_clauses=extra_tql_clauses,
            fields=fields,
            page_size=page_size,
            sorting=sorting,
        )
        if frame.empty:
            return frame
        if prefer_owner:
            frame["_prefer"] = (frame["ownerName"] == prefer_owner).astype(int)
            frame = frame.sort_values(["indicator", "_prefer"], ascending=[True, False])
            frame = frame.drop(columns=["_prefer"])
        frame = frame.groupby("indicator", as_index=False).first()
        if prefer_owner:
            frame = frame[frame["ownerName"] == prefer_owner]
        return frame.copy()

    def enrich_indicators(self, agg_df: pd.DataFrame, *, max_workers: int = 8) -> pd.DataFrame:
        """POST enrichment (VirusTotal / Shodan by type) and merge results onto ``agg_df``."""
        key_col = "indicator" if "indicator" in agg_df.columns else "summary"
        vt_types = {"Address", "IPv4", "IPv6", "Host", "Domain", "URL", "File", "SHA1", "SHA256", "MD5"}
        shodan_types = {"Address", "IPv4", "IPv6"}
        cols = [key_col, "type"] + (["id"] if "id" in agg_df.columns else [])
        candidates = (
            agg_df[cols].dropna(subset=[key_col]).astype({key_col: str}).drop_duplicates(subset=[key_col])
        )
        candidates = candidates[candidates["type"].astype(str).str.strip().isin(vt_types | shodan_types)].copy()
        if candidates.empty:
            return agg_df.copy()

        def _one(row_series):
            value = row_series[key_col]
            typ = str(row_series.get("type", "") or "")
            row_id = row_series.get("id")
            use_id = pd.notna(row_id) and str(row_id).strip().isdigit()
            try:
                iid = str(int(float(row_id))) if use_id else urllib.parse.quote(value, safe="")
                providers = []
                if typ in vt_types:
                    providers.append("VirusTotalV3")
                if typ in shodan_types:
                    providers.append("Shodan")
                if not providers:
                    providers.append("VirusTotalV3")
                query = urllib.parse.urlencode({"type": providers}, doseq=True)
                request = self._RequestObject()
                request.set_http_method("POST")
                request.set_request_uri(f"/v3/indicators/{iid}/enrich?{query}")
                request.set_body({})
                resp = self.session.api_request(request)
                try:
                    data = resp.json()
                except (ValueError, TypeError):
                    data = {"status": getattr(resp, "status_code", "n/a"), "raw": getattr(resp, "text", None)}
                data[key_col] = value
                return data, None
            except Exception as exc:
                return None, {key_col: value, "type": typ, "error": str(exc)}

        enriched, failed = [], []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_one, row): row for _, row in candidates.iterrows()}
            for future in as_completed(futures):
                result, err = future.result()
                if result is not None:
                    enriched.append(result)
                else:
                    failed.append(err)
        if failed:
            print(f"WARN: {len(failed)} indicators failed enrichment (showing up to 10)")
            print(pd.DataFrame(failed).head(10).to_string())
        if not enriched:
            return agg_df.copy()
        df_enriched = pd.json_normalize(enriched).drop_duplicates(subset=[key_col], keep="last")
        recent = agg_df.merge(df_enriched, on=key_col, how="left")
        col_path = "data.enrichment.data"
        if col_path not in recent.columns:
            return recent
        exploded = recent[[key_col, col_path]].explode(col_path).dropna(subset=[col_path])
        enrich_flat = pd.json_normalize(exploded[col_path]).add_prefix("enrich_")
        enrich_flat[key_col] = exploded[key_col].values

        def _agg_obj(series):
            vals = [v for v in series.dropna()]
            if not vals:
                return None
            flat = []
            for v in vals:
                if isinstance(v, list):
                    flat.extend(v)
                else:
                    flat.append(v)
            if all(not isinstance(v, (list, dict)) for v in flat):
                return list(pd.Series(flat).unique())
            return flat

        obj_cols = enrich_flat.select_dtypes("object").columns.difference([key_col])
        num_cols = enrich_flat.columns.difference(obj_cols.union({key_col}))
        agg_dict = {c: _agg_obj for c in obj_cols}
        agg_dict.update({c: "max" for c in num_cols})
        enrich_wide = enrich_flat.groupby(key_col, as_index=False).agg(agg_dict)
        return (
            recent.drop(columns=[col_path], errors="ignore")
            .drop_duplicates(subset=[key_col])
            .merge(enrich_wide, on=key_col, how="left")
        )
