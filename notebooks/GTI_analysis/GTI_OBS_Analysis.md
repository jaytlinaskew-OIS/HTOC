# GTI NIH/HRSA Observed Indicator Analysis

Analysis data through **October 27, 2026**.

## Population

- Distinct GTI-owned indicators attributed to NIH and/or HRSA in the preceding 90 days: **3,355**.
- NIH/HRSA indicators that would pass all current GTI Playbook rules and create a new HTOC Org copy as of October 27, 2026: **44**.
- Last 30 days: **1,921**.

## Indicator characteristics

Indicator types:

- Address: **3,279 (97.7%)**.
- Host: **72 (2.1%)**.
- URL: **4 (0.1%)**.

Quality and context:

- Rating 4 through 5: **659**.
- Rating 3: **448 (13.4%)**.
- Rating 2: **2,285 (68.1%)**.
- Rating 1: **370 (11.0%)**.
- Rating 0: **0 (0.0%)**.
- Rating missing: **41 (1.2%)**.
- Rating at least 3 and confidence at least 50: **526 (15.7%)**.
- Description present: **3,355 (100.0%)**.
- At least two normalized tags on the GTI-owned copy and not limited to `hex`/`dga`: **808 (24.1%)**.
- At least one qualified Malware, Campaign, Intrusion Set, or Report association: **3,017 (89.9%)**.

## Partner distribution

| Partner | Indicators | Share of 3,355 |
| --- | ---: | ---: |
| HRSA | 2,684 | 80.0% |
| NIH | 952 | 28.4% |

## Partner date-added distribution

This section includes only observations within the last 90 days. It does **not** represent the month in which a partner observed the indicator. An indicator associated with multiple partners appears in multiple rows.

### Indicators added during 2026

| Partner | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | 2026 total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HRSA | 0 | 1,061 | 614 | 41 | 123 | 71 | 415 | 164 | 158 | 37 | 2,684 |
| NIH | 0 | 280 | 293 | 7 | 17 | 12 | 163 | 31 | 132 | 17 | 952 |

## What the partner analysis shows
- **HRSA only:** **2,403** indicators.
- **NIH only:** **671** indicators.
- **Observed by both HRSA and NIH:** **281** indicators.

- **HRSA:** **2,684 indicators (80.0%)**, consisting of 2,677 Addresses, 3 Hosts, and 4 URLs.
- **NIH:** **952 indicators (28.4%)**, consisting of 883 Addresses and 69 Hosts.

## Method and validation

- Upstream population TQL: `ownerName = "Google Threat Intelligence" AND observationCount > 0`.
- Analysis population: retain distinct indicators with a positive NIH or HRSA `trackedUsers` observation count and `lastObserved` within the preceding 90 days.
- Existing-destination exclusion applies only to Playbook transfer eligibility: do not create a new copy when an active or inactive HTOC Org source has the same indicator type and summary.
- Partner attribution: one ThreatConnect v3 indicator-detail request per indicator with `fields=trackedUsers,observations` as the authoritative partner source.
- A current partner is assigned only when its mapped ThreatConnect tracked-user account has an observation count greater than zero and `lastObserved` is within the preceding 90 days.
- Indicators can belong to multiple partner subsets. Counts are therefore non-exclusive.
- Tags and associated groups are used only to describe GTI indicator context and Playbook eligibility; they never determine partner membership.
- Bulk `trackedUsers` expansion is not used because validation showed values could leak between adjacent list records. Individual detail responses are used instead.
- All characteristics, partner distributions, date-added distributions, and Playbook results are calculated only for the NIH/HRSA union defined above.
