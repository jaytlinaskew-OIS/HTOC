"""Split full horizontal TQL into multiple queries, each <= MAX_LEN characters."""
from __future__ import annotations

import re
from pathlib import Path

MAX_LEN = 4000
SRC = Path(__file__).with_name("_tql_horizontal.txt")
OUT = Path(__file__).with_name("_tql_chunks.txt")

PREFIX = 'typeName in ("Address") and summary in ("'
SUFFIX = '") and dateAdded >= "2025-04-01" and NOT hasTag(summary in ("SOAR Indicator PB")) and ownerName in ("HTOC Org")'


def main() -> None:
    line = SRC.read_text(encoding="utf-8").strip()
    m = re.search(
        r'typeName in \("Address"\) and summary in \("(.+)"\) and dateAdded',
        line,
    )
    if not m:
        raise SystemExit("Could not parse summary list from _tql_horizontal.txt")
    ips = m.group(1).split('","')
    chunks: list[list[str]] = []
    cur: list[str] = []

    def joined(parts: list[str]) -> str:
        return '","'.join(parts)

    for ip in ips:
        trial = PREFIX + joined(cur + [ip]) + SUFFIX
        if len(trial) <= MAX_LEN:
            cur.append(ip)
            continue
        if not cur:
            raise SystemExit(f"Single IP too long for limit: {ip!r} len={len(trial)}")
        chunks.append(cur)
        cur = [ip]
        if len(PREFIX + ip + SUFFIX) > MAX_LEN:
            raise SystemExit(f"Single IP exceeds limit: {ip!r}")
    if cur:
        chunks.append(cur)

    lines: list[str] = []
    for i, part in enumerate(chunks, start=1):
        q = PREFIX + joined(part) + SUFFIX
        assert len(q) <= MAX_LEN, (i, len(q))
        lines.append(f"--- TQL {i}/{len(chunks)} ({len(q)} chars) ---")
        lines.append(q)
        lines.append("")

    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(chunks)} queries; lengths:", [len(PREFIX + joined(c) + SUFFIX) for c in chunks])


if __name__ == "__main__":
    main()
