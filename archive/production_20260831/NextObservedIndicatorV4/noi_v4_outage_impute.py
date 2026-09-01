r"""
Keep a forecast alive through a short observation-feed outage.

When an OpDiv's feed goes dark the observations vanish but the indicators do
not, and the features cannot tell the difference. `last_seen` grows, `freq_1`
is forced to zero for every indicator at once, and `mom` turns negative across
the board, so the model reads a dead feed as an OpDiv where nothing recurs any
more. The effect is not subtle: HHS emitted zero "Highly likely" indicators on
each of 22-24 Aug 2026 against ~340 the day before, and VA did the same on 26
Aug. Nothing marks those files as suspect -- they are a confident all-clear.

What this module does is narrow on purpose. It does not try to reconstruct the
missing day. It fills in only the indicators that are so reliably present that
asserting them states a near-certainty, and it leaves everything else alone.

Why the bar sits at 98%
-----------------------
Stratifying every indicator by its trailing 30-day observation rate and checking
it against a held-out healthy day gives a sharp cliff:

    trailing rate    indicator-days    actually seen
    98-100%                  34,627            98.8%
    95-98%                    5,819            93.5%
    90-95%                    9,429            88.8%
    80-90%                   12,183            84.7%
    under 40%               140,705            12.3%

At 98% the assertion is nearly free. One step down it is wrong six times in a
hundred, and by 90% one in nine. So the cut is 98% and it is not a dial worth
turning down.

What imputation does not fix
----------------------------
Two limits are worth stating because neither is a bug to be fixed later.

Coverage is uneven and it follows an OpDiv's cadence. VA has 464 regulars out of
1,815 active indicators and FDA 182 of 355, so for them this restores most of a
lost forecast. NIH has 21 out of 2,196 and CDC has 8. Those feeds have almost no
daily regulars, so an outage there cannot be papered over by this and the
forecast should be treated as absent rather than quiet.

More importantly, an outage is not always a neutral gap in an unchanged stream.
Across the six outage episodes in the panel with enough history to test, five
would have imputed near-perfectly -- FDA Apr 22-23, VA Feb 26 and HHS Jul 12 at
zero error, HRSA's two single days within four points. HHS 22-23 Aug did not:
its volume returned to 99% of normal while 32 of its 134 regulars, every one of
them observed on 100% of the preceding thirty days, never appeared again. That
outage was an upstream content change wearing an outage's clothes, and while it
was happening it looked exactly like FDA's clean one.

That case cannot be detected in advance, so it is detected afterwards instead.
`verify_recovery` re-reads the regulars once the feed is back and reports any
that did not return, which surfaced the HHS shortfall on the first day of
recovery. Imputation is worth doing -- weighted across those episodes it is
about 96% accurate, against a status quo that is 0% -- but it is an assertion
with a tail, and the alarm is what keeps the tail visible.

Labels
------
Imputed observations feed features only. They must never reach seen_next(), or
the pipeline starts manufacturing training labels out of its own assumptions --
the exact poisoning the feed-health mask exists to prevent, except self-inflicted
and invisible, because the mask keys on empty days and an imputed day is not
empty. The separation is structural rather than conventional: `build()` returns
a second lookup for features and leaves the original untouched for labels.
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import date, timedelta

import numpy as np
import pandas as pd

import noi_v4_feed_health as fh


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except Exception:
        return default


# Enable/disable the whole mechanism.
IMPUTE_ENABLED = _env_int("NOI_V4_IMPUTE_ENABLED", 1) == 1
# Share of trailing healthy days an indicator must appear on to be imputed.
# See the table above before lowering this.
REGULAR_RATE = _env_float("NOI_V4_IMPUTE_REGULAR_RATE", 0.98)
# Healthy days used to establish that share.
REGULAR_LOOKBACK = _env_int("NOI_V4_IMPUTE_LOOKBACK", 30)
# Longest outage that will be imputed. Past this the short-window features are
# built almost entirely from assertion and the compounding risk outweighs the
# recovered coverage.
MAX_OUTAGE_DAYS = _env_int("NOI_V4_IMPUTE_MAX_DAYS", 7)
# An indicator must have been seen this recently before the outage began. A 98%
# regular that happened to be missing on the last day or two was already going
# quiet, and assuming otherwise is the one case where the rate is misleading.
MAX_PRE_GAP = _env_int("NOI_V4_IMPUTE_MAX_PRE_GAP", 2)
# Fewest regulars worth bothering with; below this the OpDiv has no daily core
# and imputation would restore a token handful while implying the feed is fine.
MIN_REGULARS = _env_int("NOI_V4_IMPUTE_MIN_REGULARS", 10)
# Healthy days examined after an outage when checking whether regulars returned.
VERIFY_WINDOW = _env_int("NOI_V4_IMPUTE_VERIFY_WINDOW", 3)
# Shortfall against the pre-outage baseline that trips the composition alarm.
VERIFY_ALERT_PP = _env_float("NOI_V4_IMPUTE_VERIFY_ALERT_PP", 10.0)

_UNUSABLE = {fh.OUTAGE, fh.MISSING}


class OutageImputer:
    """Fills an OpDiv's reliably-present indicators across a short outage.

    Consumes the panel the runner has already loaded, so no observation file is
    read a second time.
    """

    def __init__(
        self,
        panel: pd.DataFrame,
        health: fh.FeedHealth,
        regular_rate: float | None = None,
        lookback: int | None = None,
        max_outage_days: int | None = None,
    ) -> None:
        self.health = health
        self.regular_rate = REGULAR_RATE if regular_rate is None else regular_rate
        self.lookback = REGULAR_LOOKBACK if lookback is None else lookback
        self.max_outage_days = (
            MAX_OUTAGE_DAYS if max_outage_days is None else max_outage_days
        )

        # The runner counts days from its own epoch, not the Unix one. Deriving
        # the offset from a row of the panel rather than restating the constant
        # keeps the two from drifting apart -- getting this wrong is silent, and
        # reads as every feed having been dark for the whole window.
        if "date" not in panel.columns:
            raise ValueError("panel needs a 'date' column to anchor its day integers")
        ref = panel.iloc[0]
        self._epoch = np.datetime64(pd.Timestamp(ref["date"]).date()) - np.timedelta64(
            int(ref["d"]), "D"
        )

        self._byday: dict[tuple[str, int], set[str]] = defaultdict(set)
        for opd, ind, di in zip(panel["opdiv"], panel["indicator"], panel["d"]):
            self._byday[(opd, int(di))].add(ind)

        self._day_min = int(panel["d"].min())
        self._day_max = int(panel["d"].max())
        self._opdivs = sorted(panel["opdiv"].unique())
        self._status: dict[tuple[str, int], str] = {}

        probe = panel.iloc[len(panel) // 2]
        if self.to_date(int(probe["d"])) != pd.Timestamp(probe["date"]).date():
            raise ValueError(
                "day-integer epoch does not round-trip against the panel's dates; "
                "every feed would read as dark"
            )

    # ------------------------------------------------------------------ days
    def to_date(self, di: int) -> date:
        return (self._epoch + np.timedelta64(int(di), "D")).astype(date)

    def _stat(self, opdiv: str, di: int) -> str:
        key = (opdiv, di)
        if key not in self._status:
            self._status[key] = self.health.status(opdiv, self.to_date(di))
        return self._status[key]

    def _healthy_before(self, opdiv: str, di: int, n: int) -> list[int]:
        """The n most recent days before `di` whose data can be believed."""
        out: list[int] = []
        d = di - 1
        while d >= self._day_min and len(out) < n:
            if self._stat(opdiv, d) not in _UNUSABLE and self._byday.get((opdiv, d)):
                out.append(d)
            d -= 1
        return sorted(out)

    def outage_runs(self, opdiv: str) -> list[list[int]]:
        """Contiguous dark stretches for an OpDiv, oldest first."""
        bad = [
            d
            for d in range(self._day_min, self._day_max + 1)
            if self._stat(opdiv, d) in _UNUSABLE
        ]
        if not bad:
            return []
        runs, cur = [], [bad[0]]
        for d in bad[1:]:
            if d == cur[-1] + 1:
                cur.append(d)
            else:
                runs.append(cur)
                cur = [d]
        runs.append(cur)
        return runs

    # -------------------------------------------------------------- regulars
    def regulars(self, opdiv: str, before_di: int) -> tuple[set[str], int]:
        """Indicators present on at least `regular_rate` of the trailing healthy days.

        Trailing-only by construction: nothing at or after `before_di` is read,
        so a regular list built during an outage could have been built live.
        """
        hd = self._healthy_before(opdiv, before_di, self.lookback)
        if len(hd) < max(10, self.lookback // 3):
            return set(), len(hd)
        counts: dict[str, int] = defaultdict(int)
        for d in hd:
            for ind in self._byday.get((opdiv, d), ()):
                counts[ind] += 1
        need = self.regular_rate * len(hd)
        recent = set()
        for d in hd[-MAX_PRE_GAP:]:
            recent |= self._byday.get((opdiv, d), set())
        return {i for i, n in counts.items() if n >= need and i in recent}, len(hd)

    # ----------------------------------------------------------------- build
    def build(self, lookup: dict) -> tuple[dict, list[dict]]:
        """Return a feature-only lookup with outage days filled, plus a report.

        The input mapping is not modified. Labels must keep using it.
        """
        report: list[dict] = []
        if not IMPUTE_ENABLED:
            return lookup, report

        add: dict[tuple[str, str], list[int]] = defaultdict(list)
        for opdiv in self._opdivs:
            for run in self.outage_runs(opdiv):
                fill = run[: self.max_outage_days]
                regs, n_hist = self.regulars(opdiv, run[0])
                entry = {
                    "opdiv": opdiv,
                    "start": self.to_date(run[0]),
                    "end": self.to_date(run[-1]),
                    "days": len(run),
                    "days_filled": len(fill) if len(regs) >= MIN_REGULARS else 0,
                    "regulars": len(regs),
                    "history_days": n_hist,
                    "truncated": len(run) > len(fill),
                }
                if len(regs) < MIN_REGULARS:
                    entry["skipped"] = (
                        f"only {len(regs)} regulars; this feed has no daily core"
                    )
                    report.append(entry)
                    continue
                for ind in regs:
                    if (opdiv, ind) in lookup:
                        add[(opdiv, ind)].extend(fill)
                report.append(entry)

        if not add:
            return lookup, report

        imputed = dict(lookup)
        for key, days in add.items():
            imputed[key] = np.unique(
                np.concatenate([lookup[key], np.asarray(days, dtype=lookup[key].dtype)])
            )
        return imputed, report

    def imputed_indicators(self, lookup: dict, upto_di: int | None = None) -> set[tuple[str, str]]:
        """Pairs whose features rest on a filled day, for flagging output rows.

        `upto_di` restricts to outages still affecting a cutoff -- an outage that
        ended months ago no longer colours today's forecast in any way worth
        marking.
        """
        out: set[tuple[str, str]] = set()
        if not IMPUTE_ENABLED:
            return out
        horizon = 0 if upto_di is None else upto_di
        for opdiv in self._opdivs:
            for run in self.outage_runs(opdiv):
                if upto_di is not None and run[-1] < horizon - self.max_outage_days:
                    continue
                regs, _ = self.regulars(opdiv, run[0])
                if len(regs) < MIN_REGULARS:
                    continue
                for ind in regs:
                    if (opdiv, ind) in lookup:
                        out.add((opdiv, ind))
        return out

    # ------------------------------------------------------------- verifying
    def verify_recovery(self) -> list[dict]:
        """Check whether each ended outage's regulars actually came back.

        This is the guard against the HHS case, where a feed returns at full
        volume having quietly dropped part of its content. It is retrospective
        by necessity -- during the outage there is nothing to compare against --
        but it fires on the first day of recovery, which is early enough to stop
        imputing into a feed that has changed underneath us.
        """
        findings: list[dict] = []
        if not IMPUTE_ENABLED:
            return findings

        for opdiv in self._opdivs:
            for run in self.outage_runs(opdiv):
                after = [
                    d
                    for d in range(run[-1] + 1, self._day_max + 1)
                    if self._stat(opdiv, d) not in _UNUSABLE
                    and self._byday.get((opdiv, d))
                ][:VERIFY_WINDOW]
                if len(after) < VERIFY_WINDOW:
                    continue  # still dark, or too soon to judge
                regs, _ = self.regulars(opdiv, run[0])
                if len(regs) < MIN_REGULARS:
                    continue

                back = {
                    i for i in regs if any(i in self._byday.get((opdiv, d), ()) for d in after)
                }
                returned = 100.0 * len(back) / len(regs)

                pre = self._healthy_before(opdiv, run[0], self.lookback)
                ratios = []
                for k in range(len(pre) - VERIFY_WINDOW):
                    w = pre[k : k + VERIFY_WINDOW]
                    hit = {i for i in regs if any(i in self._byday.get((opdiv, d), ()) for d in w)}
                    ratios.append(100.0 * len(hit) / len(regs))
                baseline = sum(ratios) / len(ratios) if ratios else 100.0

                shortfall = baseline - returned
                if shortfall < VERIFY_ALERT_PP:
                    continue
                findings.append(
                    {
                        "opdiv": opdiv,
                        "start": self.to_date(run[0]),
                        "end": self.to_date(run[-1]),
                        "regulars": len(regs),
                        "returned_pct": round(returned, 1),
                        "baseline_pct": round(baseline, 1),
                        "shortfall_pp": round(shortfall, 1),
                        "lost": len(regs) - len(back),
                    }
                )
        return findings


def format_report(report: list[dict]) -> list[str]:
    lines = []
    for r in report:
        if not r["days_filled"]:
            lines.append(
                f"  {r['opdiv']}: {r['start']}..{r['end']} ({r['days']}d) not imputed"
                f" -- {r.get('skipped', 'no regulars')}"
            )
            continue
        extra = ""
        if r["truncated"]:
            extra = (
                f"; outage runs {r['days']}d, only first {r['days_filled']} filled"
                f" (cap {MAX_OUTAGE_DAYS}d)"
            )
        lines.append(
            f"  {r['opdiv']}: {r['start']}..{r['end']} -- filled {r['regulars']} regulars"
            f" across {r['days_filled']}d{extra}"
        )
    return lines


def format_findings(findings: list[dict]) -> list[str]:
    lines = []
    for f in findings:
        lines.append(
            f"  {f['opdiv']} {f['start']}..{f['end']}: only {f['returned_pct']}% of "
            f"{f['regulars']} regulars returned vs {f['baseline_pct']}% normally "
            f"({f['lost']} lost, {f['shortfall_pp']}pp short). The feed came back "
            f"with different content -- forecasts imputed during this outage "
            f"overstated those indicators."
        )
    return lines
