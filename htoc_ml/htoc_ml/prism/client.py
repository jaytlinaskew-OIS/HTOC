"""ThreatConnect session, indicator query, and enrichment."""
from __future__ import annotations

import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytz
import urllib3

from htoc_ml.core.pipeline import PipelineError
from htoc_ml.prism.config import PrismConfig

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_api_config(config_path: str) -> tuple[str, str, str, str]:
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


class ThreatConnectClient:
    def __init__(self, config: PrismConfig) -> None:
        self.config = config
        sdk = config.tc_sdk_path
        if sdk not in sys.path:
            sys.path.insert(0, sdk)
        project = config.tc_project_root
        if project not in sys.path:
            sys.path.insert(0, project)
        from ThreatConnect import ThreatConnect
        from RequestObject import RequestObject

        self._RequestObject = RequestObject
        secret, access_id, base_url, org = load_api_config(config.config_path)
        print(f"Loaded config — Base URL: {base_url} | Access ID: {access_id}")
        self.session = ThreatConnect(access_id, secret, org, base_url)
        print("ThreatConnect initialized.")

    def _paginate(self, tql_raw: str) -> list[dict]:
        encoded = urllib.parse.quote(tql_raw)
        request = self._RequestObject()
        request.set_http_method("GET")
        pages = []
        start = 0
        page_size = self.config.result_page_size
        while True:
            request.set_request_uri(
                f"/v3/indicators?tql={encoded}"
                f"&fields=tags,observations,associatedGroups,falsePositives,threatAssess"
                f"&resultStart={start}&resultLimit={page_size}"
            )
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
            start += page_size
        return pages

    def query_weekly(self) -> pd.DataFrame:
        start_date = (datetime.now(pytz.UTC) - timedelta(days=self.config.query_lookback_days)).date()
        start = f"{start_date}T00:00:00Z"
        tql = (
            f'ownerName IN ({_quoted(self.config.owner_names)}) AND '
            f'typeName IN ({_quoted(self.config.indicator_types)}) AND '
            f'lastObserved >= "{start}"'
        )
        frame = self._normalize(self._paginate(tql))
        if frame.empty:
            return frame
        frame["lastObserved"] = pd.to_datetime(frame["lastObserved"], utc=True, errors="coerce")
        frame = frame[frame["lastObserved"] >= pd.to_datetime(start, utc=True)]
        return frame[frame["ownerName"] == "HTOC Org"].copy()

    def query_summaries(self, summaries: list[str]) -> pd.DataFrame:
        tql = (
            f'ownerName IN ({_quoted(self.config.owner_names)}) AND '
            f'typeName IN ({_quoted(self.config.indicator_types)}) AND '
            f'summary IN ({_quoted(summaries)})'
        )
        frame = self._normalize(self._paginate(tql))
        if frame.empty:
            return frame
        frame["_htoc_first"] = (frame["ownerName"] == "HTOC Org").astype(int)
        frame = frame.sort_values(["indicator", "_htoc_first"], ascending=[True, False])
        frame = frame.drop(columns=["_htoc_first"])
        frame = frame.groupby("indicator", as_index=False).first()
        return frame[frame["ownerName"] == "HTOC Org"].copy()

    def _normalize(self, pages: list[dict]) -> pd.DataFrame:
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

    def enrich(self, agg_df: pd.DataFrame) -> pd.DataFrame:
        key_col = "indicator" if "indicator" in agg_df.columns else "summary"
        vt_types = {"Address", "IPv4", "IPv6", "Host", "Domain", "URL", "File", "SHA1", "SHA256", "MD5"}
        shodan_types = {"Address", "IPv4", "IPv6"}
        cols = [key_col, "type"] + (["id"] if "id" in agg_df.columns else [])
        candidates = (
            agg_df[cols].dropna(subset=[key_col]).astype({key_col: str}).drop_duplicates(subset=[key_col])
        )
        candidates = candidates[candidates["type"].astype(str).str.strip().isin(vt_types | shodan_types)].copy()
        print(f"Enriching {len(candidates)} indicators (VT; Shodan for IP types only)...")
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
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(_one, row): row for _, row in candidates.iterrows()}
            for future in as_completed(futures):
                result, err = future.result()
                if result is not None:
                    enriched.append(result)
                else:
                    failed.append(err)
        if failed:
            print(f"{len(failed)} indicators failed enrichment (showing up to 10):")
            print(pd.DataFrame(failed).head(10).to_string())
        if not enriched:
            print("No enrichment data retrieved.")
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
        recent = (
            recent.drop(columns=[col_path], errors="ignore")
            .drop_duplicates(subset=[key_col])
            .merge(enrich_wide, on=key_col, how="left")
        )
        print(f"Enrichment complete for {recent[key_col].notna().sum()} indicators.")
        return recent


def _quoted(values) -> str:
    return ", ".join(f'"{v}"' for v in values)
