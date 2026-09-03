"""Enrich PRISM Address indicators with ip-api.com infrastructure context."""
from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from htoc.datapipelines.paths import env_path, share_root

BATCH_SIZE = 100
RATE_LIMIT_WAIT = 1.5
REQUEST_TIMEOUT = 15
HEADERS = {"User-Agent": "HTOC-ThreatIntel-Triage/1.0"}
IP_API_FIELDS = "status,message,country,countryCode,regionName,city,isp,org,as,hosting,proxy,mobile,query"

BULLETPROOF_KEYWORDS = {
    "unmanaged", "flokinet", "frantech", "buyvm", "combahton",
    "serverius", "quasi", "lir.net", "leaseweb", "serverstack",
    "m247", "choopa", "vultr", "pptechnology", "dmzhost",
    "offshore", "sharktech", "psychz",
}
BENIGN_HOSTING_KEYWORDS = {
    "amazon", "google", "microsoft", "cloudflare", "akamai",
    "fastly", "digitalocean", "linode", "hetzner", "ovh",
    "level3", "comcast", "att ", "verizon", "spectrum",
}
HIGH_RISK_COUNTRIES = {"China", "Russia", "North Korea", "Iran", "Belarus"}


def default_scores_path() -> Path:
    return env_path(
        "TRIAGE_SCORES_XLSX",
        share_root() / "Data_Analytics" / "Data" / "Threat Assessment Scores" / "Threat_Assessment_Scores.xlsx",
    )


def default_output_path() -> Path:
    return env_path(
        "TRIAGE_OUTPUT",
        share_root() / "JA" / "PrismTest" / "indicator_triage_results.csv",
    )


def default_checkpoint_path() -> Path:
    return env_path(
        "TRIAGE_CHECKPOINT",
        share_root() / "JA" / "PrismTest" / "indicator_triage_checkpoint.txt",
    )


def classify_indicator(ip_api: dict, sans: dict, indicator_type: str) -> dict:
    if indicator_type not in ("Address",):
        return {
            "behavior": "non_ip",
            "flags": "",
            "score_recommendation": "manual_review",
            "triage_notes": f"Non-IP type ({indicator_type}). No automated triage available.",
        }
    isp = str(ip_api.get("isp", "") or "").lower()
    org = str(ip_api.get("org", "") or "").lower()
    asn_name = str(sans.get("sans_asname", "") or "").lower()
    is_proxy = bool(ip_api.get("proxy", False))
    is_hosting = bool(ip_api.get("hosting", False))
    country = str(ip_api.get("country", "") or "")
    asn_str = str(ip_api.get("as", "") or "")
    combined = f"{isp} {org} {asn_name}"
    is_bulletproof = any(kw in combined for kw in BULLETPROOF_KEYWORDS)
    is_benign_cloud = any(kw in combined for kw in BENIGN_HOSTING_KEYWORDS)
    flags: list[str] = []
    behavior = "unknown"
    recommendation = "no_change"
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
    if country in HIGH_RISK_COUNTRIES:
        flags.append(f"high_risk_country_{country.replace(' ', '_')}")
        if recommendation == "no_change":
            recommendation = "analyst_review"
    if not flags:
        behavior = "insufficient_data"
        recommendation = "no_change"
    notes = (
        f"ISP: {ip_api.get('isp', 'unknown')}. "
        f"Org: {ip_api.get('org', 'unknown')}. "
        f"Country: {ip_api.get('country', 'unknown')}. "
        f"ASN: {asn_str}. "
        f"Proxy: {is_proxy}. "
        f"Hosting: {is_hosting}. "
        f"Behavior: {behavior}. "
        f"Recommendation: {recommendation}."
    )
    return {
        "behavior": behavior,
        "flags": "; ".join(flags),
        "score_recommendation": recommendation,
        "triage_notes": notes,
    }


def lookup_ip_api_bulk(ip_list: list[str]) -> dict:
    try:
        import requests
    except ImportError as exc:
        raise SystemExit("requests is not installed. py -m pip install requests") from exc
    payload = [{"query": ip, "fields": IP_API_FIELDS} for ip in ip_list]
    results: dict = {}
    try:
        resp = requests.post(
            "http://ip-api.com/batch", json=payload, headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            for entry in resp.json():
                results[entry.get("query", "")] = entry
        else:
            for ip in ip_list:
                results[ip] = {"error": f"HTTP {resp.status_code}"}
    except Exception as exc:
        for ip in ip_list:
            results[ip] = {"error": str(exc)[:100]}
    return results


def _row_record(indicator: str, indicator_type: str, ip_data: dict, classification: dict) -> dict:
    sans = {
        "sans_asname": ip_data.get("as"),
        "sans_ascountry": ip_data.get("countryCode"),
        "sans_network": None,
        "sans_abuse_contact": None,
    }
    return {
        "Indicator": indicator,
        "Indicator Type": indicator_type,
        "triage_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "ipapi_country": ip_data.get("country"),
        "ipapi_isp": ip_data.get("isp"),
        "ipapi_org": ip_data.get("org"),
        "ipapi_asn": ip_data.get("as"),
        "ipapi_proxy": ip_data.get("proxy"),
        "ipapi_hosting": ip_data.get("hosting"),
        "sans_asname": sans.get("sans_asname"),
        "sans_ascountry": sans.get("sans_ascountry"),
        "sans_network": sans.get("sans_network"),
        "sans_abuse_contact": sans.get("sans_abuse_contact"),
        **classification,
    }


def _append_results(rows: list[dict], output_path: Path, write_header: bool) -> bool:
    if not rows:
        return write_header
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, mode="a", index=False, header=write_header)
    return False


def _append_checkpoint(rows: list[dict], checkpoint_path: Path) -> None:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint_path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(str(row["Indicator"]) + "\n")


def run_triage(
    *,
    scores_path: Path,
    output_path: Path,
    checkpoint_path: Path,
    sheet_name: str = "PRISM Scores",
    lookup_fn=lookup_ip_api_bulk,
    pause_s: float = RATE_LIMIT_WAIT,
) -> Path:
    print(f"HTOC Indicator Triage — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    frame = pd.read_excel(scores_path, sheet_name=sheet_name)
    print(f"  Total indicators: {len(frame)}")
    completed: set[str] = set()
    if checkpoint_path.exists():
        completed = {line.strip() for line in checkpoint_path.read_text(encoding="utf-8").splitlines() if line.strip()}
        print(f"  Resuming — {len(completed)} already completed.")
    remaining = frame[~frame["Indicator"].astype(str).isin(completed)].copy()
    ips = remaining[remaining["Indicator Type"] == "Address"]
    others = remaining[remaining["Indicator Type"] != "Address"]
    print(f"  IPs to triage: {len(ips)}")
    print(f"  Other types: {len(others)}")
    write_header = not output_path.exists()
    other_rows = []
    for _, row in others.iterrows():
        itype = str(row.get("Indicator Type", ""))
        other_rows.append(
            _row_record(str(row["Indicator"]), itype, {}, classify_indicator({}, {}, itype))
        )
    write_header = _append_results(other_rows, output_path, write_header)
    _append_checkpoint(other_rows, checkpoint_path)

    ip_list = ips["Indicator"].astype(str).tolist()
    total_batches = max(1, (len(ip_list) + BATCH_SIZE - 1) // BATCH_SIZE) if ip_list else 0
    type_by_ip = dict(zip(ips["Indicator"].astype(str), ips["Indicator Type"].astype(str)))
    for batch_num, start in enumerate(range(0, len(ip_list), BATCH_SIZE), start=1):
        batch = ip_list[start : start + BATCH_SIZE]
        ip_api_results = lookup_fn(batch)
        batch_rows = []
        for ip in batch:
            itype = type_by_ip.get(ip, "Address")
            ip_data = ip_api_results.get(ip, {})
            sans = {"sans_asname": ip_data.get("as")}
            batch_rows.append(_row_record(ip, itype, ip_data, classify_indicator(ip_data, sans, itype)))
        write_header = _append_results(batch_rows, output_path, write_header)
        _append_checkpoint(batch_rows, checkpoint_path)
        pct = round(batch_num / total_batches * 100, 1)
        print(f"  Batch {batch_num}/{total_batches} ({pct}%) — saved {len(batch)} indicators.")
        if pause_s:
            time.sleep(pause_s)
    print(f"DONE. Results saved to {output_path}")
    if output_path.exists():
        results = pd.read_csv(output_path)
        print("Behavior Summary:")
        print(results["behavior"].value_counts().to_string())
        print("Score Recommendations:")
        print(results["score_recommendation"].value_counts().to_string())
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Triage PRISM Address indicators via ip-api.com.")
    parser.add_argument("--scores", default=str(default_scores_path()))
    parser.add_argument("--output", default=str(default_output_path()))
    parser.add_argument("--checkpoint", default=str(default_checkpoint_path()))
    parser.add_argument("--sheet", default="PRISM Scores")
    parser.add_argument("--no-pause", action="store_true", help="Skip the inter-batch sleep (tests).")
    args = parser.parse_args(argv)
    run_triage(
        scores_path=Path(args.scores),
        output_path=Path(args.output),
        checkpoint_path=Path(args.checkpoint),
        sheet_name=args.sheet,
        pause_s=0.0 if args.no_pause else RATE_LIMIT_WAIT,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
