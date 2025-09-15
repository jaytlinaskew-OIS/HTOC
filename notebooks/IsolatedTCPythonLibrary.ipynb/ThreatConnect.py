# tc_cli.py
# Simple, static CLI for ThreatConnect tasks (no coding required).

import argparse
import configparser
import os
import sys
from datetime import datetime

# ── your simplified SDK imports ──
# Assumes your refactored module is installed/importable.
from ThreatConnect import ThreatConnect  # your cleaned class
from Owners import Owners                # your Owners resource

# ─────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────
def load_config(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if path and os.path.exists(path):
        cfg.read(path)
    else:
        # allow running without a file (env-only)
        cfg.read_dict({"auth": {}, "defaults": {}})
    return cfg

def get_auth(cfg: configparser.ConfigParser):
    # precedence: ENV > ini
    aid = os.getenv("TC_ACCESS_ID", cfg.get("auth", "api_access_id", fallback=None))
    sec = os.getenv("TC_SECRET_KEY", cfg.get("auth", "api_secret_key", fallback=None))
    org = os.getenv("TC_DEFAULT_ORG", cfg.get("auth", "api_default_org", fallback=None))
    url = os.getenv("TC_API_URL", cfg.get("auth", "api_url", fallback="https://api.threatconnect.com"))
    token = os.getenv("TC_TOKEN", cfg.get("auth", "api_token", fallback=None))
    token_exp = os.getenv("TC_TOKEN_EXPIRES", cfg.get("auth", "api_token_expires", fallback=None))
    return aid, sec, org, url, token, int(token_exp) if token_exp else None

def die(msg: str, code: int = 2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def print_table(rows, headers):
    # simple text table w/out third-party deps
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    def line(parts): return " | ".join(str(p).ljust(w) for p, w in zip(parts, widths))
    sep = "-+-".join("-" * w for w in widths)
    print(line(headers))
    print(sep)
    for r in rows:
        print(line(r))

# ─────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────
def cmd_owners_list(tc: ThreatConnect, args):
    owners = Owners(tc)
    owners.retrieve_mine()
    rows = [(o.id, o.name, getattr(o, "type", "")) for o in owners._objects]
    if not rows:
        print("No owners found.")
        return
    print_table(rows, headers=["ID", "Name", "Type"])

def cmd_owners_members(tc: ThreatConnect, args):
    owners = Owners(tc)
    members = owners.retrieve_members()
    if not members:
        print("No members found.")
        return
    # best-effort attribute access; adapt to your parse_member fields
    rows = []
    for m in members:
        rows.append((
            getattr(m, "id", ""),
            getattr(m, "username", getattr(m, "name", "")),
            getattr(m, "role", ""),
            getattr(m, "email", "")
        ))
    print_table(rows, headers=["ID", "User", "Role", "Email"])

def cmd_owners_metrics(tc: ThreatConnect, args):
    owners = Owners(tc)
    metrics = owners.retrieve_metrics()
    if not metrics:
        print("No metrics found.")
        return
    rows = []
    for x in metrics:
        rows.append((
            getattr(x, "ownerId", getattr(x, "owner_id", "")),
            getattr(x, "ownerName", getattr(x, "owner_name", "")),
            getattr(x, "indicatorCount", getattr(x, "indicators", "")),
            getattr(x, "groupCount", getattr(x, "groups", "")),
        ))
    print_table(rows, headers=["Owner ID", "Owner", "Indicators", "Groups"])

# ─────────────────────────────────────────────────────────────
# Main CLI
# ─────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="tc",
        description="ThreatConnect CLI (static & simplified for non-coders)"
    )
    p.add_argument("--config", "-c", default="tc.ini", help="Path to tc.ini (optional)")
    p.add_argument("--timeout", type=int, default=None, help="API timeout seconds (optional)")
    p.add_argument("--retries", type=int, default=None, help="Retry attempts on transient errors (optional)")

    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("owners", help="Owner operations")
    s1_sub = s1.add_subparsers(dest="owners_cmd", required=True)
    s1_sub.add_parser("list", help="List available owners")
    s1_sub.add_parser("members", help="List members in your owners")
    s1_sub.add_parser("metrics", help="Show owner metrics")
    return p

def main():
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    aid, sec, org, url, token, token_exp = get_auth(cfg)

    if not ((aid and sec) or (token and token_exp)):
        die("Provide API credentials: either ACCESS_ID/SECRET_KEY or TOKEN + TOKEN_EXPIRES. "
            "Use tc.ini [auth] or env vars (TC_ACCESS_ID, TC_SECRET_KEY, TC_TOKEN, TC_TOKEN_EXPIRES).")

    tc = ThreatConnect(
        api_aid=aid, api_sec=sec,
        api_org=org, api_url=url,
        api_token=token, api_token_expires=token_exp
    )

    if args.timeout:
        tc.set_api_request_timeout(args.timeout)
    if args.retries:
        tc.set_api_retries(args.retries)

    # route
    if args.cmd == "owners":
        if args.owners_cmd == "list":
            cmd_owners_list(tc, args)
        elif args.owners_cmd == "members":
            cmd_owners_members(tc, args)
        elif args.owners_cmd == "metrics":
            cmd_owners_metrics(tc, args)
        else:
            die("Unknown owners subcommand")

if __name__ == "__main__":
    main()
