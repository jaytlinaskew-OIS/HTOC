# -*- coding: utf-8 -*-
"""Minimal ThreatConnect client (GET-only) + get_tc_data(days) helper."""

import base64
import hashlib
import hmac
import logging
import re
import socket
import time
from datetime import datetime, date
from pathlib import Path

from requests import exceptions, packages, Request, Session
packages.urllib3.disable_warnings()


def _tc_logger():
    """Create a quiet base logger; enable elsewhere if needed."""
    tcl = logging.getLogger('threatconnect')
    tcl.setLevel(logging.CRITICAL)
    return tcl


class ThreatConnect:
    """Lightweight ThreatConnect client with GET-only requests."""

    def __init__(
        self,
        api_aid=None,
        api_sec=None,
        api_org=None,
        api_url=None,
        api_token=None,
        api_token_expires=None,
    ):
        # logger
        self.tcl = _tc_logger()
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(funcName)s:%(lineno)d)'
        )

        # credentials
        self._api_aid = api_aid
        self._api_sec = api_sec
        self._api_token = api_token
        self._api_token_expires = api_token_expires

        # user defined
        self._api_org = api_org
        self._api_url = api_url

        # defaults
        self._activity_log = False
        self._api_request_timeout = 30
        self._api_retries = 5
        self._api_sleep = 59
        self._proxies = {'https': None}
        self._verify_ssl = False

        # requests session
        self._session = Session()

        # hard-lock to GET only
        self.read_only = True

    # ----------- Public configuration (kept minimal) -----------

    def set_verify_ssl(self, verify_bool):
        """Explicit SSL verify toggle to match caller behavior."""
        if isinstance(verify_bool, bool):
            self._verify_ssl = verify_bool

    # ------------------- Internal helpers ----------------------

    def _renew_token(self):
        """Refresh app token if expired (server may require POST in some setups)."""
        url = f'{self._api_url}/appAuth'
        payload = {'expiredToken': self._api_token}
        token_response = self._session.get(
            url, params=payload, verify=self._verify_ssl,
            timeout=self._api_request_timeout, proxies=self._proxies, stream=False
        )
        if token_response.status_code == 401:
            ctype = (token_response.headers.get('content-type') or '').lower()
            err_data = token_response.json().get('message') if 'application/json' in ctype else token_response.text
            raise RuntimeError(f'Could not refresh ThreatConnect Token ({err_data}).')

        token_data = token_response.json()
        self._api_token = token_data['apiToken']
        self._api_token_expires = int(token_data['apiTokenExpires'])

    def _api_request_headers(self, ro):
        """Attach required headers for either token or HMAC auth."""
        timestamp = int(time.time())
        if self._api_token is not None and self._api_token_expires is not None:
            # renew if close/expired
            window_padding = 15
            current_time = int(time.time()) - window_padding
            if int(self._api_token_expires) < current_time:
                self._renew_token()
            authorization = f'TC-Token {self._api_token}'
        elif self._api_aid is not None and self._api_sec is not None:
            signature = f"{ro.path_url}:{ro.http_method}:{timestamp}"
            hmac_signature = hmac.new(
                self._api_sec.encode(), signature.encode(), digestmod=hashlib.sha256
            ).digest()
            authorization = f'TC {self._api_aid}:{base64.b64encode(hmac_signature).decode()}'
        else:
            authorization = ''

        ro.add_header('Timestamp', str(timestamp))  # ensure header value is a string
        ro.add_header('Authorization', authorization)

    # ---------------------- Core request -----------------------

    def api_request(self, ro, log=True):
        """Perform a single HTTP request (GET-only enforced)."""
        method = (ro.http_method or '').upper()
        if self.read_only and method != 'GET':
            raise PermissionError(f"Read-only client: '{method}' requests are blocked.")

        api_response = None
        start = datetime.now()

        if self._activity_log:
            ro.enable_activity_log()

        url = f'{self._api_url}{ro.request_uri}'
        api_request = Request(ro.http_method, url, data=ro.body, params=ro.payload)
        request_prepped = api_request.prepare()

        ro.set_path_url(request_prepped.path_url)
        self._api_request_headers(ro)
        request_prepped.prepare_headers(ro.headers)

        if log:
            self.tcl.debug('request_object: %s', ro)
            self.tcl.debug('url: %s', url)
            self.tcl.debug('path url: %s', request_prepped.path_url)

        for i in range(1, self._api_retries + 1):
            try:
                api_response = self._session.send(
                    request_prepped,
                    verify=self._verify_ssl,
                    timeout=self._api_request_timeout,
                    proxies=self._proxies,
                    stream=ro.stream,
                )
                break
            except exceptions.ReadTimeout as e:
                self.tcl.error('ReadTimeout: %s', e)
                time.sleep(self._api_sleep)
                if i == self._api_retries:
                    raise RuntimeError(e)
            except exceptions.ConnectionError as e:
                self.tcl.error('ConnectionError: %s', e)
                time.sleep(self._api_sleep)
                if i == self._api_retries:
                    raise RuntimeError(e)
            except socket.error as e:
                raise RuntimeError(e)

        # Basic error handling
        if api_response.status_code not in [200, 201, 202]:
            non_critical_errors = [
                b'The MD5 for this File is invalid, a File with this MD5 already exists',
                b'The SHA-1 for this File is invalid, a File with this SHA-1 already exists',
                b'The SHA-256 for this File is invalid, a File with this SHA-256 already exists',
                b'The requested resource was not found',
                b'Could not find resource for relative',
                b'The requested Security Label was not removed - access was denied',
            ]
            content = api_response.content or b''
            if not any(re.findall(nce, content) for nce in non_critical_errors):
                raise RuntimeError(content)

        if api_response.encoding is None:
            api_response.encoding = 'utf-8'

        if log:
            c_len = api_response.headers.get('content-length')
            c_type = api_response.headers.get('content-type')
            self.tcl.debug('url: %s', api_response.url)
            self.tcl.debug('status_code: %s', api_response.status_code)
            self.tcl.debug('content-length: %s', c_len)
            self.tcl.debug('content-type: %s', c_type)
            self.tcl.debug('Request Time: %s', datetime.now() - start)

        return api_response


# ---------------------------------------------------------------------
# High-level helper: get_tc_data(days)
# ---------------------------------------------------------------------

def get_v3_threatconnect_data(lastObserved_date: date, indicatorActive: bool):

    import urllib.parse
    import urllib3
    import pandas as pd

    # Local imports (within package)
    from HTOCThreatConnect.RequestObject import RequestObject
    from HTOCThreatConnect.utils.config_loader import load_config

    # --- Settings you wanted hardcoded ---
    OWNERS = ["HTOC Org"]
    VERIFY_SSL = False

    # Resolve config.json inside the installed package
    package_dir = Path(__file__).resolve().parent  # .../AlynThreatConnect
    config_path = package_dir / "utils" / "config.json"

    api_secret_key, api_access_id, api_base_url, api_default_org = load_config(str(config_path))

    # Init client
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    tc = ThreatConnect(
        api_aid=api_access_id,
        api_sec=api_secret_key,
        api_org=api_default_org,
        api_url=api_base_url,
    )
    tc.set_verify_ssl(VERIFY_SSL)

    # RequestObject
    ro = RequestObject()
    ro.set_http_method("GET")
    ro.set_owner_allowed(True)

    # Normalize lastObserved_date to a date and build ISO8601 start at 00:00:00Z
    if not lastObserved_date:
        lastObserved_date = "2023-01-01"

    if isinstance(lastObserved_date, datetime):
        _date = lastObserved_date.date()
    elif isinstance(lastObserved_date, date):
        _date = lastObserved_date
    elif isinstance(lastObserved_date, str):
        try:
            _date = datetime.strptime(lastObserved_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("lastObserved_date must be in YYYY-MM-DD format")
    else:
        # Fallback to safe default
        _date = datetime.strptime("2023-01-01", "%Y-%m-%d").date()

    start = f"{_date.isoformat()}T00:00:00Z"

    # Indicator types
    type_names = [
        "Address", "Email Address", "File", "Host", "URL", "ASN", "CIDR",
        "Email Subject", "Hashtag", "Mutex", "Registry Key",
        "Stripped URL", "User Agent",
    ]
    type_name_condition = ", ".join([f'"{t}"' for t in type_names])

    # Query indicators with pagination
    final_results = []
    for owner in OWNERS:
        try:
            tql_raw = (
                f'ownerName EQ "{owner}" AND '
                f'typeName IN ({type_name_condition}) AND '
                #f'lastObserved >= "{start}" AND '
                f"indicatorActive={indicatorActive} "
            )
            tql_encoded = urllib.parse.quote(tql_raw)

            result_start = 0
            page_size = 10000

            while True:
                ro.set_request_uri(
                    f"/v3/indicators?tql={tql_encoded}"
                    f"&fields=tags,associatedGroups"
                    f"&resultStart={result_start}&resultLimit={page_size}"
                )
                response = tc.api_request(ro)

                ctype = (response.headers.get("content-type") or "").lower()
                if "application/json" not in ctype:
                    break

                payload = response.json() or {}
                data = payload.get("data", [])
                if not data:
                    break

                final_results.append(payload)

                if len(data) < page_size:
                    break
                result_start += page_size

        except Exception as e:
            print(f"Failed to query indicators for {owner}: {e}")

    # Normalize -> DataFrame
    normalized_data = []
    for result in final_results:
        for item in result.get("data", []):
            if isinstance(item, dict) and "summary" in item:
                normalized_data.append(item)

    if not normalized_data:
        return pd.DataFrame()

    df = pd.json_normalize(normalized_data)

    # Choose a stable indicator column
    indicator_col = None
    for cand in ["indicator", "value", "name", "summary"]:
        if cand in df.columns:
            indicator_col = cand
            break

    if indicator_col == "summary" or indicator_col is None:
        df["indicator"] = df["summary"].astype(str).str.split().str[0].str.strip()
    else:
        df["indicator"] = df[indicator_col].astype(str).str.strip()

    df.drop_duplicates(subset="indicator", inplace=True)
    cols_to_drop = ["summary", "ip", "text", "sha256", "sha1", "url", "md5", "hostName"]
    existing_cols = [col for col in cols_to_drop if col in df.columns]
    if existing_cols:
        df.drop(columns=existing_cols, inplace=True)

    return df.reset_index(drop=True)

def get_v2_threatconnect_data():

    from pathlib import Path
    from datetime import datetime, timezone
    import urllib.parse
    import urllib3
    import pandas as pd

    # Local imports (within your package)
    from HTOCThreatConnect.RequestObject import RequestObject
    from HTOCThreatConnect.ThreatConnect import ThreatConnect
    from HTOCThreatConnect.utils.config_loader import load_config

    # --- Hardcoded settings ---
    OWNERS = ["HTOC Org"]
    VERIFY_SSL = False

    # ── Setup ────────────────────────────────────────────────────────────────
    package_dir = Path(__file__).resolve().parent
    config_path = package_dir / "utils" / "config.json"
    api_secret_key, api_access_id, api_base_url, api_default_org = load_config(str(config_path))

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    tc = ThreatConnect(
        api_aid=api_access_id,
        api_sec=api_secret_key,
        api_org=api_default_org,
        api_url=api_base_url,
    )
    tc.set_verify_ssl(VERIFY_SSL)

    today_str = datetime.now(timezone.utc).date().isoformat()  # 'YYYY-MM-DD'
    all_rows = []

    # ── Single call per owner (no pagination) ───────────────────────────────
    for owner in OWNERS:
        owner_q = urllib.parse.quote(owner)

        # One wide call: all observed indicators for today (server returns full set)
        uri = (
            f"/v2/indicators/observed"
            f"?owner={owner_q}"
            f"&dateObserved={today_str}"
        )

        ro = RequestObject()
        ro.set_http_method("GET")
        ro.set_owner_allowed(True)
        ro.set_request_uri(uri)

        resp = tc.api_request(ro)
        print(f"[DEBUG] status={resp.status_code}")
        if resp.status_code != 200:
            try:
                print(f"[DEBUG] error body: {resp.text[:500]}")
            except Exception:
                pass
            continue

        payload = resp.json() or {}
        data_obj = payload.get("data", {}) or {}
        items = data_obj.get("indicator", [])
        print(f"[DEBUG] Retrieved {len(items)} observed indicators for {owner} on {today_str}")
        all_rows.extend(items)

    # ── Normalize to DataFrame ───────────────────────────────────────────────
    if not all_rows:
        print("[DEBUG] No rows returned.")
        return pd.DataFrame()

    df = pd.json_normalize(all_rows)

    # Choose a stable indicator column
    indicator_col = None
    for cand in ("indicator", "value", "name", "summary"):
        if cand in df.columns:
            indicator_col = cand
            break

    if indicator_col is None:
        if "summary" in df.columns:
            df["indicator"] = df["summary"].astype(str).str.split().str[0].str.strip()
        else:
            df["indicator"] = None
    else:
        df["indicator"] = df[indicator_col].astype(str).str.strip()

    # Light cleanup (keep 'type' so you can filter client-side if needed)
    if "summary" in df.columns:
        df.drop(columns=["summary"], inplace=True)

    df.drop_duplicates(subset="indicator", inplace=True)

    return df.reset_index(drop=True)
