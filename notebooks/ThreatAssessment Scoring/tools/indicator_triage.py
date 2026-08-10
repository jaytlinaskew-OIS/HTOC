"""
Indicator Triage Script — No API Keys Required
-----------------------------------------------
Sources:
  - ip-api.com (bulk, HTTP, 100 IPs/call) — infrastructure type, ASN, proxy/hosting flags
  - SANS ISC    (HTTPS, per IP)            — ASN details, abuse contact, network block

Outputs a CSV with behavioral context for every indicator in the PRISM scores file.
Runs incrementally — safe to stop and resume.
"""

import pandas as pd
import requests
import time
import os
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")  # suppress SSL warnings from corporate proxy

# ─── CONFIG ───────────────────────────────────────────────────────────────────
EXCEL_PATH      = r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\Threat_Assessment_Scores.xlsx"
OUTPUT_PATH     = r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\indicator_triage_results.csv"
CHECKPOINT_PATH = r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\indicator_triage_checkpoint.txt"

BATCH_SIZE      = 100    # ip-api.com max per bulk call
RATE_LIMIT_WAIT = 1.5    # seconds between batches (stay under 45 req/min)
REQUEST_TIMEOUT = 15

HEADERS = {"User-Agent": "HTOC-ThreatIntel-Triage/1.0"}

# ─── KNOWN BULLETPROOF / HIGH-RISK HOSTING PROVIDERS ─────────────────────────
# These ASNs/orgs are well-known for ignoring abuse complaints or hosting criminal infra
BULLETPROOF_KEYWORDS = {
    "unmanaged", "flokinet", "frantech", "buyvm", "combahton",
    "serverius", "quasi", "lir.net", "leaseweb", "serverstack",
    "m247", "choopa", "vultr", "pptechnology", "dmzhost",
    "offshore", "sharktech", "psychz",
}

# Known legitimate hosting/cloud that should NOT be flagged as bulletproof
BENIGN_HOSTING_KEYWORDS = {
    "amazon", "google", "microsoft", "cloudflare", "akamai",
    "fastly", "digitalocean", "linode", "hetzner", "ovh",
    "level3", "comcast", "att ", "verizon", "spectrum",
}

# ─── IP-API.COM BULK LOOKUP ───────────────────────────────────────────────────
IP_API_FIELDS = "status,message,country,countryCode,regionName,city,isp,org,as,hosting,proxy,mobile,query"

def lookup_ip_api_bulk(ip_list: list) -> dict:
    """
    Query ip-api.com for up to 100 IPs at once.
    Returns dict keyed by IP address.
    """
    payload = [{"query": ip, "fields": IP_API_FIELDS} for ip in ip_list]
    results = {}
    try:
        resp = requests.post(
            "http://ip-api.com/batch",
            json=payload,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            for entry in resp.json():
                ip = entry.get("query", "")
                results[ip] = entry
        else:
            for ip in ip_list:
                results[ip] = {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        for ip in ip_list:
            results[ip] = {"error": str(e)[:100]}
    return results


# ─── SANS ISC LOOKUP ──────────────────────────────────────────────────────────
def lookup_sans_isc(ip: str) -> dict:
    """
    Query SANS ISC for ASN info and abuse contact.
    """
    result = {
        "sans_asn": None,
        "sans_asname": None,
        "sans_ascountry": None,
        "sans_network": None,
        "sans_abuse_contact": None,
        "sans_attack_count": None,
        "sans_error": None,
    }
    try:
        resp = requests.get(
            f"https://isc.sans.edu/api/ip/{ip}?json",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            verify=False
        )
        if resp.status_code == 200:
            ip_data = resp.json().get("ip", {})
            result["sans_asn"]           = ip_data.get("as")
            result["sans_asname"]        = ip_data.get("asname")
            result["sans_ascountry"]     = ip_data.get("ascountry")
            result["sans_network"]       = ip_data.get("network")
            result["sans_abuse_contact"] = ip_data.get("asabusecontact")
            result["sans_attack_count"]  = ip_data.get("count")
        else:
            result["sans_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["sans_error"] = str(e)[:100]
    return result


# ─── BEHAVIORAL CLASSIFICATION ────────────────────────────────────────────────
def classify_indicator(ip_api: dict, sans: dict, indicator_type: str) -> dict:
    """
    Apply rule-based classification using infrastructure signals.
    Returns behavior label, flags, and score recommendation.
    """
    flags = []
    behavior = "unknown"
    recommendation = "no_change"

    # Skip non-IP types
    if indicator_type not in ("Address",):
        return {
            "behavior":           "non_ip",
            "flags":              "",
            "score_recommendation": "manual_review",
            "triage_notes": f"Non-IP type ({indicator_type}). No automated triage available."
        }

    isp      = str(ip_api.get("isp", "") or "").lower()
    org      = str(ip_api.get("org", "") or "").lower()
    asn_name = str(sans.get("sans_asname", "") or "").lower()
    is_proxy   = bool(ip_api.get("proxy", False))
    is_hosting = bool(ip_api.get("hosting", False))
    country    = str(ip_api.get("country", "") or "")
    asn_str    = str(ip_api.get("as", "") or "")

    # Bulletproof hosting detection
    combined = f"{isp} {org} {asn_name}"
    is_bulletproof = any(kw in combined for kw in BULLETPROOF_KEYWORDS)
    is_benign_cloud = any(kw in combined for kw in BENIGN_HOSTING_KEYWORDS)

    if is_bulletproof and not is_benign_cloud:
        flags.append("bulletproof_hosting")
        behavior = "malicious_infrastructure"
        recommendation = "elevate_score"

    if is_proxy:
        flags.append("proxy_anonymizer")
        if behavior == "unknown":
            behavior = "anonymized_traffic"
            recommendation = "elevate_score"

    if is_hosting and not is_bulletproof and is_benign_cloud:
        flags.append("legitimate_cloud_hosting")
        behavior = "cloud_hosted"
        recommendation = "reduce_score"

    if is_hosting and not is_bulletproof and not is_benign_cloud:
        flags.append("generic_hosting")
        if behavior == "unknown":
            behavior = "hosted_infrastructure"
            recommendation = "no_change"

    # High-risk countries (not definitive but contextual)
    HIGH_RISK_COUNTRIES = {"China", "Russia", "North Korea", "Iran", "Belarus"}
    if country in HIGH_RISK_COUNTRIES:
        flags.append(f"high_risk_country_{country.replace(' ', '_')}")
        if recommendation == "no_change":
            recommendation = "analyst_review"

    if not flags:
        behavior = "insufficient_data"
        recommendation = "no_change"

    isp_display  = ip_api.get("isp", "unknown")
    org_display  = ip_api.get("org", "unknown")
    country_disp = ip_api.get("country", "unknown")

    notes = (
        f"ISP: {isp_display}. "
        f"Org: {org_display}. "
        f"Country: {country_disp}. "
        f"ASN: {asn_str}. "
        f"Proxy: {is_proxy}. "
        f"Hosting: {is_hosting}. "
        f"Behavior: {behavior}. "
        f"Recommendation: {recommendation}."
    )

    return {
        "behavior":             behavior,
        "flags":                "; ".join(flags),
        "score_recommendation": recommendation,
        "triage_notes":         notes,
    }


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"HTOC Indicator Triage — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    # Load indicators
    print("Loading indicators from Excel...")
    df = pd.read_excel(EXCEL_PATH, sheet_name="PRISM Scores")
    print(f"  Total indicators: {len(df)}")
    print(f"  Types: {df['Indicator Type'].value_counts().to_dict()}\n")

    # Load checkpoint
    completed = set()
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH) as f:
            completed = set(line.strip() for line in f if line.strip())
        print(f"  Resuming — {len(completed)} already completed.\n")

    # Filter to Address types only for this run (bulk of the work)
    df_ips = df[
        (df["Indicator Type"] == "Address") &
        (~df["Indicator"].astype(str).isin(completed))
    ].copy()

    df_other = df[
        (df["Indicator Type"] != "Address") &
        (~df["Indicator"].astype(str).isin(completed))
    ].copy()

    print(f"  IPs to triage:   {len(df_ips)}")
    print(f"  Other types:     {len(df_other)} (Host, EmailAddress, File — flagged for manual review)\n")

    all_results = []
    write_header = not os.path.exists(OUTPUT_PATH)

    # ── Process non-IP types immediately ──────────────────────────────────────
    for _, row in df_other.iterrows():
        classification = classify_indicator({}, {}, str(row.get("Indicator Type", "")))
        all_results.append({
            "Indicator":            str(row["Indicator"]),
            "Indicator Type":       str(row.get("Indicator Type", "")),
            "triage_timestamp":     datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "ipapi_country":        None,
            "ipapi_isp":            None,
            "ipapi_org":            None,
            "ipapi_asn":            None,
            "ipapi_proxy":          None,
            "ipapi_hosting":        None,
            "sans_asname":          None,
            "sans_ascountry":       None,
            "sans_network":         None,
            "sans_abuse_contact":   None,
            **classification,
        })

    # ── Process IPs in batches of 100 ─────────────────────────────────────────
    ip_list = df_ips["Indicator"].astype(str).tolist()
    total_batches = (len(ip_list) + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"Processing {len(ip_list)} IPs in {total_batches} batches of {BATCH_SIZE}...\n")

    for batch_num, i in enumerate(range(0, len(ip_list), BATCH_SIZE), start=1):
        batch = ip_list[i : i + BATCH_SIZE]

        # Bulk ip-api.com call
        ip_api_results = lookup_ip_api_bulk(batch)

        for ip in batch:
            itype = df_ips.loc[df_ips["Indicator"] == ip, "Indicator Type"].values
            itype = itype[0] if len(itype) > 0 else "Address"

            ip_data = ip_api_results.get(ip, {})
            # Build a sans-compatible dict from ip-api.com data (avoids per-IP SANS calls)
            sans = {
                "sans_asname":        ip_data.get("as"),
                "sans_ascountry":     ip_data.get("countryCode"),
                "sans_network":       None,
                "sans_abuse_contact": None,
            }
            classification = classify_indicator(ip_data, sans, itype)

            all_results.append({
                "Indicator":            ip,
                "Indicator Type":       itype,
                "triage_timestamp":     datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "ipapi_country":        ip_data.get("country"),
                "ipapi_isp":            ip_data.get("isp"),
                "ipapi_org":            ip_data.get("org"),
                "ipapi_asn":            ip_data.get("as"),
                "ipapi_proxy":          ip_data.get("proxy"),
                "ipapi_hosting":        ip_data.get("hosting"),
                "sans_asname":          sans.get("sans_asname"),
                "sans_ascountry":       sans.get("sans_ascountry"),
                "sans_network":         sans.get("sans_network"),
                "sans_abuse_contact":   sans.get("sans_abuse_contact"),
                **classification,
            })

        # Save every batch
        out_df = pd.DataFrame(all_results)
        out_df.to_csv(OUTPUT_PATH, mode="a", index=False, header=write_header)
        write_header = False

        with open(CHECKPOINT_PATH, "a") as f:
            for r in all_results:
                f.write(r["Indicator"] + "\n")

        all_results = []

        pct = round(batch_num / total_batches * 100, 1)
        print(f"  Batch {batch_num}/{total_batches} ({pct}%) — saved {len(batch)} indicators.")

        time.sleep(RATE_LIMIT_WAIT)

    print(f"\n{'='*60}")
    print(f"DONE. Results saved to:")
    print(f"  {OUTPUT_PATH}")
    print(f"{'='*60}\n")

    # Summary
    results_df = pd.read_csv(OUTPUT_PATH)
    print("Behavior Summary:")
    print(results_df["behavior"].value_counts().to_string())
    print("\nScore Recommendations:")
    print(results_df["score_recommendation"].value_counts().to_string())


if __name__ == "__main__":
    main()
