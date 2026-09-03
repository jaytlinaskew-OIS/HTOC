"""python -m htoc.datapipelines <command>"""
from __future__ import annotations

import importlib
import sys

COMMANDS = {
    "search-tags": "search_tags",
    "triage": "triage",
    "iw-listing": "iw_listing",
    "make-launcher": "make_launcher",
    "threat-score-iw": "threat_score_iw",
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        names = " | ".join(COMMANDS)
        print(f"usage: py -3.13 -m htoc.datapipelines {{{names}}} [options]")
        return 0
    command = args[0]
    if command not in COMMANDS:
        print(f"unknown command {command!r}; choose from {', '.join(COMMANDS)}")
        return 2
    rest = args[1:]
    module = importlib.import_module(f"htoc.datapipelines.{COMMANDS[command]}")
    return int(module.main(rest) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
