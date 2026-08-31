r"""
Observation-feed health model shared by the NextObservedIndicator V4 forecast
runner and its performance evaluation.

The problem this solves: when an OpDiv's observation feed breaks, its
indicators look unobserved. Nothing downstream can tell that apart from the
indicators genuinely going quiet, so a forward label seen_next(...) returns 0
for a window whose ground truth is simply absent. A missing label is not a
negative label -- counted as one it produces phantom false positives in the
metrics and, worse, teaches the model that those indicators stopped recurring.

A day is classified per OpDiv as one of:

  HEALTHY          normal volume; labels trustworthy
  STRUCTURAL_ZERO  zero observations, but this OpDiv routinely reports nothing
                   on this weekday -- a true zero, so labels ARE trustworthy
  OUTAGE           zero observations with no such pattern; labels unusable
  DEGRADED         non-zero but far below the trailing baseline (partial
                   delivery / decaying feed); labels unusable
  MISSING          no observation file at all; labels unusable
  UNSETTLED        too recent to trust -- the upstream job keeps rewriting each
                   day's file for two to three mornings, so late-arriving
                   observations would read as misses
  EARLY            inside that window, but this OpDiv has delivered, so its
                   labels can be used now; provisional, reported with how
                   complete the day was, and rewritten once it truly settles

HEALTHY, STRUCTURAL_ZERO and EARLY are usable. Two distinctions do the work
here. STRUCTURAL_ZERO versus OUTAGE is what makes the mask safe to apply to
training labels: excluding a genuine zero throws away a real negative, which
for a small OpDiv can be most of its signal. EARLY versus UNSETTLED is what
keeps the mask from being wasteful: settling is a property of a feed, not of a
calendar day, so judging it per day would let one slow feed withhold every
other feed that had already finished. A metric that can be computed is
computed; what protects the reader is that the row says how complete it was,
not that the cell was left blank.

Counts can come from observation files (lazily, with caching) or from an
already-loaded panel DataFrame, so the forecast runner does not pay to read
the same 220 files twice.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import pandas as pd

DATE_FMT = "%Y%m%d"

HEALTHY = "healthy"
STRUCTURAL_ZERO = "structural_zero"
OUTAGE = "outage"
DEGRADED = "degraded"
MISSING = "missing"
UNSETTLED = "unsettled"
EARLY = "early"


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


# Days a file must age before its contents are trusted.
SETTLE_DAYS = _env_int("NOI_V4_OBS_SETTLE_DAYS", 3)
# Trailing window for the volume baseline. Deliberately long: a short window
# follows a slowly decaying feed downward and never registers the decay.
BASELINE_DAYS = _env_int("NOI_V4_HEALTH_BASELINE_DAYS", 56)
# Non-zero counts below this fraction of the baseline median are DEGRADED.
MIN_RATIO = _env_float("NOI_V4_HEALTH_MIN_RATIO", 0.20)
# Only apply the ratio test when the OpDiv is normally big enough for it to
# mean something; small OpDivs swing too much for a ratio to be informative.
MIN_BASELINE = _env_int("NOI_V4_HEALTH_MIN_BASELINE", 20)
# Fraction of same-weekday occurrences that must also be zero before a zero is
# treated as the OpDiv's normal reporting pattern rather than a break.
STRUCTURAL_ZERO_FRAC = _env_float("NOI_V4_HEALTH_STRUCTURAL_ZERO_FRAC", 0.5)
# Minimum same-weekday samples required before that judgement is allowed.
STRUCTURAL_MIN_SAMPLES = _env_int("NOI_V4_HEALTH_STRUCTURAL_MIN_SAMPLES", 4)

# Early settlement: score inside the settle window when there is data to score.
#
# Age alone is a crude proxy for completeness, and applying it per day rather
# than per OpDiv means one feed that is still filling withholds every other feed
# that has already finished.
#
# The gate is deliberately just "did this OpDiv deliver anything". An earlier
# version required 85% of the trailing volume, which reads as prudent but fails
# in two ways. It withholds real, computable metrics -- a blank cell is not a
# safer answer than a labelled approximate one, it is just a less useful one.
# And the bar is unfair to any feed whose volume has shifted: DHA stepped down
# from roughly 350/day to 50/day, so against an eight-week median it scores
# about 0.5 on days it is perfectly healthy and would have been withheld
# indefinitely.
#
# What makes this safe is not the threshold, it is what happens to the row:
# every early-scored row is marked provisional with its completeness, is never
# alerted on, and is rewritten with final numbers once the day settles. Raise
# EARLY_SETTLE_RATIO above 0 to require a volume fraction as well.
EARLY_SETTLE = _env_int("NOI_V4_HEALTH_EARLY_SETTLE", 1) == 1
EARLY_SETTLE_RATIO = _env_float("NOI_V4_HEALTH_EARLY_SETTLE_RATIO", 0.0)
# Today's file is mid-write, so never judge one younger than this.
EARLY_SETTLE_MIN_AGE = _env_int("NOI_V4_HEALTH_EARLY_SETTLE_MIN_AGE", 1)

# Fraction of a normal day's volume at which a feed is treated as having
# delivered. Not a gate -- it decides whether the day as a whole clearly landed,
# which is what lets a zero inside the settle window be called dark rather than
# pending, and it is the number reported alongside a provisional row.
DELIVERED_RATIO = _env_float("NOI_V4_HEALTH_DELIVERED_RATIO", 0.85)
# How many OpDivs must have delivered before that judgement is allowed.
DELIVERED_QUORUM = _env_float("NOI_V4_HEALTH_DELIVERED_QUORUM", 0.66)

# Whether a DEGRADED day should block scoring/labelling, or only be reported.
#
# Default is report-only, and that is a deliberate call. A zero is unambiguous:
# there is no data, so any label derived from it is fabricated. A merely low
# count is ambiguous -- it can be partial delivery, or it can be the OpDiv's
# real volume after a permanent level shift. Validated against 221 days of
# history, enforcing DEGRADED would have stripped 30 consecutive DHA days that
# were simply a step down from roughly 350/day to roughly 50/day, plus 27 CMS
# days that are ordinary variance for a feed whose daily count legitimately
# ranges from about 10 to 740. Those are valid observations; dropping them
# would thin training signal far more than the partial deliveries it catches.
#
# So DEGRADED is surfaced in logs and summaries -- which is what makes a slow
# decay like DHA's visible at all -- without silently removing data. Set
# NOI_V4_HEALTH_DEGRADED_UNUSABLE=1 to enforce it instead.
DEGRADED_UNUSABLE = _env_int("NOI_V4_HEALTH_DEGRADED_UNUSABLE", 0) == 1

_USABLE_BASE = {HEALTHY, STRUCTURAL_ZERO, EARLY}
USABLE_STATUSES = frozenset(
    _USABLE_BASE if DEGRADED_UNUSABLE else _USABLE_BASE | {DEGRADED}
)
# Usable, but resting on a file that may still grow. Callers that publish
# numbers should label these rather than presenting them as final.
PROVISIONAL_STATUSES = frozenset({EARLY})


def statuses_in(problems) -> set[str]:
    """Status tokens out of the problem strings window_usable() produces.

    Lives next to the code that formats them so the two stay in step. Callers
    need this to tell "the feed was down" from "the file is still being
    rewritten" -- both block scoring, but only the second one fixes itself.
    """
    return {str(p).rsplit(" ", 1)[-1] for p in problems if str(p).strip()}


def _as_date(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.strptime(d.strip(), DATE_FMT).date()
    ts = pd.Timestamp(d)
    return ts.date()


class FeedHealth:
    """Per-OpDiv, per-day observation feed health with a trailing baseline."""

    def __init__(
        self,
        obs_template: str | None = None,
        counts_by_day: dict[date, dict[str, int]] | None = None,
        settle_days: int | None = None,
        baseline_days: int | None = None,
        min_ratio: float | None = None,
        min_baseline: int | None = None,
        structural_zero_frac: float | None = None,
        today: date | None = None,
        early_settle: bool | None = None,
        early_settle_ratio: float | None = None,
        early_settle_min_age: int | None = None,
    ) -> None:
        if obs_template is None and counts_by_day is None:
            raise ValueError("FeedHealth needs either obs_template or counts_by_day")
        self.obs_template = obs_template
        self.settle_days = SETTLE_DAYS if settle_days is None else settle_days
        self.baseline_days = BASELINE_DAYS if baseline_days is None else baseline_days
        self.min_ratio = MIN_RATIO if min_ratio is None else min_ratio
        self.min_baseline = MIN_BASELINE if min_baseline is None else min_baseline
        self.structural_zero_frac = (
            STRUCTURAL_ZERO_FRAC if structural_zero_frac is None else structural_zero_frac
        )
        self.early_settle = EARLY_SETTLE if early_settle is None else early_settle
        self.early_settle_ratio = (
            EARLY_SETTLE_RATIO if early_settle_ratio is None else early_settle_ratio
        )
        self.early_settle_min_age = (
            EARLY_SETTLE_MIN_AGE if early_settle_min_age is None else early_settle_min_age
        )
        self._today = today
        # None marks "file absent"; a dict marks "file read, these are the counts".
        self._counts: dict[date, dict[str, int] | None] = dict(counts_by_day or {})
        self._preloaded = counts_by_day is not None
        self._status_cache: dict[tuple[str, date], str] = {}

    # ---------- construction ----------

    @classmethod
    def from_panel(cls, panel: pd.DataFrame, **kwargs) -> "FeedHealth":
        """Build from an already-loaded panel of (indicator, opdiv, date) rows.

        Only days present in the panel are known; any other day reads as
        MISSING, which is the conservative answer.
        """
        need = {"opdiv", "date"}
        if not need.issubset(panel.columns):
            raise ValueError(f"panel must have columns {sorted(need)}")
        grp = panel.groupby([panel["date"].dt.date, "opdiv"]).size()
        counts: dict[date, dict[str, int]] = {}
        for (day, opdiv), n in grp.items():
            counts.setdefault(day, {})[str(opdiv).strip()] = int(n)
        return cls(counts_by_day=counts, **kwargs)

    @classmethod
    def from_files(cls, obs_template: str, **kwargs) -> "FeedHealth":
        return cls(obs_template=obs_template, **kwargs)

    # ---------- raw counts ----------

    def today(self) -> date:
        return self._today or datetime.today().date()

    def counts_for_day(self, day) -> dict[str, int] | None:
        """Unique (indicator, OpDiv) pair counts for one day, or None if absent."""
        day = _as_date(day)
        if day in self._counts:
            return self._counts[day]
        if self._preloaded or not self.obs_template:
            self._counts[day] = None
            return None

        fp = self.obs_template.format(date=day.strftime(DATE_FMT))
        result: dict[str, int] | None
        if not os.path.exists(fp):
            result = None
        else:
            try:
                p = pd.read_csv(fp, usecols=["indicator", "obs_date", "OpDiv"])
                p["ind"] = p["indicator"].astype(str).str.strip()
                p["op"] = p["OpDiv"].astype(str).str.strip()
                p["dt"] = pd.to_datetime(p["obs_date"], errors="coerce").dt.normalize()
                p = p[p["dt"] == pd.Timestamp(day)]
                p = p[p["ind"].ne("") & p["ind"].ne("nan")]
                p = p[p["op"].ne("") & p["op"].ne("nan")]
                p = p.drop_duplicates(["ind", "op"])
                result = p["op"].value_counts().to_dict()
            except Exception:
                result = None
        self._counts[day] = result
        return result

    def count(self, opdiv: str, day) -> int | None:
        counts = self.counts_for_day(day)
        if counts is None:
            return None
        return int(counts.get(str(opdiv).strip(), 0))

    # ---------- classification ----------

    def _baseline_median(self, opdiv: str, day: date) -> float | None:
        vals: list[int] = []
        for k in range(1, self.baseline_days + 1):
            c = self.count(opdiv, day - timedelta(days=k))
            if c is not None:
                vals.append(c)
        if not vals:
            return None
        return float(pd.Series(vals).median())

    def _same_weekday_median(self, opdiv: str, day: date) -> float | None:
        """Typical volume for this OpDiv on this weekday.

        Weekday matters here in a way it does not for the DEGRADED test: a
        Sunday compared against an all-days median reads as a shortfall for
        feeds that are quieter at weekends. Zeros are left out so that an
        outage in the trailing weeks cannot drag the bar down far enough for a
        half-delivered day to clear it.
        """
        vals: list[int] = []
        k = 7
        while k <= self.baseline_days:
            c = self.count(opdiv, day - timedelta(days=k))
            if c:
                vals.append(c)
            k += 7
        if len(vals) < STRUCTURAL_MIN_SAMPLES:
            return None
        return float(pd.Series(vals).median())

    def completeness(self, opdiv: str, day) -> float | None:
        """This day's volume as a fraction of a normal one, or None if unknown."""
        day = _as_date(day)
        c = self.count(opdiv, day)
        if c is None:
            return None
        base = self._same_weekday_median(opdiv, day)
        if base is None or base < self.min_baseline:
            return None
        return c / base

    def _early_settled(self, opdiv: str, day: date) -> bool:
        """Can this OpDiv be scored before its day formally settles?"""
        if not self.early_settle:
            return False
        if (self.today() - day).days < self.early_settle_min_age:
            return False
        if not self.count(opdiv, day):
            return False
        if self.early_settle_ratio > 0:
            frac = self.completeness(opdiv, day)
            if frac is not None and frac < self.early_settle_ratio:
                return False
        return True

    def day_delivered(self, day) -> bool:
        """Has this day's delivery clearly happened across the feeds generally?

        Inside the settle window a zero is otherwise ambiguous: a dead feed and
        one that simply has not arrived yet look identical. When most other
        OpDivs have reached their usual volume for the day, that ambiguity is
        resolved -- the delivery ran, and a feed still at zero is dark.
        """
        day = _as_date(day)
        counts = self.counts_for_day(day)
        if not counts:
            return False
        judged = delivered = 0
        for opdiv in counts:
            frac = self.completeness(opdiv, day)
            if frac is None:
                continue
            judged += 1
            if frac >= DELIVERED_RATIO:
                delivered += 1
        if judged < STRUCTURAL_MIN_SAMPLES:
            return False
        return (delivered / judged) >= DELIVERED_QUORUM

    def _same_weekday_zero_fraction(self, opdiv: str, day: date) -> tuple[int, int]:
        """(zeros, samples) across same-weekday days in the baseline window."""
        zeros = samples = 0
        k = 7
        while k <= self.baseline_days:
            c = self.count(opdiv, day - timedelta(days=k))
            if c is not None:
                samples += 1
                if c == 0:
                    zeros += 1
            k += 7
        return zeros, samples

    def status(self, opdiv: str, day) -> str:
        opdiv = str(opdiv).strip()
        day = _as_date(day)
        key = (opdiv, day)
        cached = self._status_cache.get(key)
        if cached is not None:
            return cached

        result = self._classify(opdiv, day)
        self._status_cache[key] = result
        return result

    def _classify(self, opdiv: str, day: date) -> str:
        if (self.today() - day).days < self.settle_days:
            if self._early_settled(opdiv, day):
                return EARLY
            # Nothing from this OpDiv. If the day's delivery clearly ran for
            # everyone else, fall through and name the real problem -- an
            # outage, or a weekday this OpDiv never reports -- rather than
            # blaming the clock for an empty feed.
            if not self.day_delivered(day):
                return UNSETTLED

        c = self.count(opdiv, day)
        if c is None:
            return MISSING

        baseline = self._baseline_median(opdiv, day)

        if c == 0:
            # No history to lose, or the OpDiv simply does not report here.
            if baseline is None or baseline == 0:
                return STRUCTURAL_ZERO
            zeros, samples = self._same_weekday_zero_fraction(opdiv, day)
            if samples >= STRUCTURAL_MIN_SAMPLES and (zeros / samples) >= self.structural_zero_frac:
                return STRUCTURAL_ZERO
            return OUTAGE

        if baseline is not None and baseline >= self.min_baseline:
            if c < baseline * self.min_ratio:
                return DEGRADED
        return HEALTHY

    def is_usable(self, opdiv: str, day) -> bool:
        return self.status(opdiv, day) in USABLE_STATUSES

    # ---------- windows ----------

    def window_usable(self, opdiv: str, start_exclusive, end_inclusive) -> tuple[bool, list[str]]:
        """Is every day in (start, end] usable for this OpDiv?"""
        start_exclusive = _as_date(start_exclusive)
        end_inclusive = _as_date(end_inclusive)
        problems: list[str] = []
        cur = start_exclusive + timedelta(days=1)
        while cur <= end_inclusive:
            st = self.status(opdiv, cur)
            if st not in USABLE_STATUSES:
                problems.append(f"{cur.strftime(DATE_FMT)} {st}")
            cur += timedelta(days=1)
        return (not problems), problems

    def window_provisional_days(self, opdiv: str, start_exclusive, end_inclusive) -> list[str]:
        """Days in (start, end] scored before they settled, with completeness.

        The completeness figure rides along because it is what tells a reader
        whether a provisional number is nearly final or a rough early read.
        """
        start_exclusive = _as_date(start_exclusive)
        end_inclusive = _as_date(end_inclusive)
        out: list[str] = []
        cur = start_exclusive + timedelta(days=1)
        while cur <= end_inclusive:
            if self.status(opdiv, cur) in PROVISIONAL_STATUSES:
                frac = self.completeness(opdiv, cur)
                pct = "volume unknown" if frac is None else f"{frac * 100:.0f}% of normal volume"
                out.append(f"{cur.strftime(DATE_FMT)} at {pct}")
            cur += timedelta(days=1)
        return out

    def healthy_opdivs(
        self, candidate_opdivs, start_exclusive, end_inclusive
    ) -> tuple[set[str], dict]:
        """Partition candidates into those with a fully usable label window."""
        candidates = {str(o).strip() for o in candidate_opdivs if str(o).strip()}
        healthy: set[str] = set()
        excluded: dict[str, list[str]] = {}
        provisional: dict[str, list[str]] = {}
        for o in candidates:
            ok, problems = self.window_usable(o, start_exclusive, end_inclusive)
            if ok:
                healthy.add(o)
                early = self.window_provisional_days(o, start_exclusive, end_inclusive)
                if early:
                    provisional[o] = early
            else:
                excluded[o] = problems

        start_d = _as_date(start_exclusive)
        end_d = _as_date(end_inclusive)
        unsettled_days, missing_days = [], []
        cur = start_d + timedelta(days=1)
        while cur <= end_d:
            if (self.today() - cur).days < self.settle_days:
                unsettled_days.append(cur.strftime(DATE_FMT))
            elif self.counts_for_day(cur) is None:
                missing_days.append(cur.strftime(DATE_FMT))
            cur += timedelta(days=1)

        return healthy, {
            "excluded": excluded,
            "provisional": provisional,
            "unsettled_days": unsettled_days,
            "missing_days": missing_days,
        }

    def usable_day_mask(self, opdiv: str, start_inclusive, end_inclusive) -> dict[date, bool]:
        start_inclusive = _as_date(start_inclusive)
        end_inclusive = _as_date(end_inclusive)
        out: dict[date, bool] = {}
        cur = start_inclusive
        while cur <= end_inclusive:
            out[cur] = self.is_usable(opdiv, cur)
            cur += timedelta(days=1)
        return out

    # ---------- reporting ----------

    def summarize(self, opdivs, start_inclusive, end_inclusive) -> pd.DataFrame:
        """Status counts per OpDiv over a date range -- for audits and logs."""
        start_inclusive = _as_date(start_inclusive)
        end_inclusive = _as_date(end_inclusive)
        rows = []
        for o in sorted({str(x).strip() for x in opdivs}):
            tally: dict[str, int] = {}
            bad_days: list[str] = []
            cur = start_inclusive
            while cur <= end_inclusive:
                st = self.status(o, cur)
                tally[st] = tally.get(st, 0) + 1
                if st not in USABLE_STATUSES:
                    bad_days.append(f"{cur.strftime(DATE_FMT)}:{st}")
                cur += timedelta(days=1)
            rows.append({
                "OpDiv": o,
                HEALTHY: tally.get(HEALTHY, 0),
                STRUCTURAL_ZERO: tally.get(STRUCTURAL_ZERO, 0),
                OUTAGE: tally.get(OUTAGE, 0),
                DEGRADED: tally.get(DEGRADED, 0),
                MISSING: tally.get(MISSING, 0),
                UNSETTLED: tally.get(UNSETTLED, 0),
                EARLY: tally.get(EARLY, 0),
                "unusable_days": "; ".join(bad_days[:12]),
            })
        return pd.DataFrame(rows)
