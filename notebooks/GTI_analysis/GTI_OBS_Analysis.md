# GTI Observed Indicator Analysis

Analysis data through **October 21, 2026**.

## Population

- GTI-owner indicators in ThreatConnect: **12,791,708**.
- GTI-owner indicators with `observationCount > 0`: **9,352**.
- Observed share: **0.0731%**, approximately 1 in every 1,368 GTI indicators.
- Observed indicators that pass all current GTI Playbook rules as of October 21, 2026: **62**.
- Indicators whose latest visible partner observation occurred within the last 30 days: **1,889**.
- Indicators whose latest visible partner observation occurred within the last 90 days: **3,395**.

## Indicator characteristics

Indicator types:

- Address: **8,692 (92.9%)**.
- Host: **638 (6.8%)**.
- File: **15 (0.2%)**.
- URL: **7 (0.1%)**.

Quality and context:

- Rating 3 through 5: **1,068**.
- Rating 3: **797 (8.5%)**.
- Rating 2: **6,804 (72.8%)**.
- Rating 1: **1,349 (14.4%)**.
- Rating 0: **131 (1.4%)**.
- Rating at least 3 and confidence at least 50: **837 (8.9%)**.
- Description present: **9,337 (99.8%)**.
- At least two normalized tags on the GTI-owned copy and not limited to `hex`/`dga`: **1,969 (21.1%)**.
- At least one qualified Malware, Campaign, Intrusion Set, or Report association: **8,085 (86.5%)**.

## Partner distribution

Counts are non-exclusive: an indicator is counted for every partner with a positive observation count in its ThreatConnect `trackedUsers` record.

| Partner | Indicators | Share of 9,352 |
| --- | ---: | ---: |
| HRSA | 5,095 | 54.5% |
| NIH | 3,914 | 41.9% |
| HHS | 2,486 | 26.6% |
| VA | 1,756 | 18.8% |
| CMS | 1,336 | 14.3% |
| OS | 986 | 10.5% |
| CDC | 976 | 10.4% |
| FDA | 917 | 9.8% |
| IHS | 705 | 7.5% |
| DHA | 560 | 6.0% |

## Partner date-added distribution

This section uses the GTI indicator's ThreatConnect `dateAdded` month. It does **not** represent the month in which a partner observed the indicator. An indicator associated with multiple partners appears in multiple rows.

### Indicators added during 2026

| Partner | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct* | 2026 total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CDC | 0 | 471 | 38 | 4 | 7 | 5 | 317 | 29 | 104 | 1 | 976 |
| CMS | 0 | 842 | 72 | 7 | 15 | 5 | 221 | 41 | 127 | 6 | 1,336 |
| DHA | 0 | 245 | 30 | 3 | 2 | 6 | 144 | 22 | 106 | 2 | 560 |
| FDA | 0 | 466 | 59 | 6 | 15 | 7 | 192 | 41 | 126 | 5 | 917 |
| HHS | 0 | 1,558 | 108 | 7 | 15 | 9 | 544 | 97 | 124 | 24 | 2,486 |
| HRSA | 0 | 2,279 | 1,152 | 79 | 188 | 160 | 772 | 209 | 226 | 30 | 5,095 |
| IHS | 0 | 288 | 41 | 6 | 17 | 12 | 171 | 28 | 138 | 4 | 705 |
| NIH | 0 | 1,847 | 1,128 | 11 | 28 | 21 | 543 | 112 | 192 | 32 | 3,914 |
| OS | 0 | 505 | 49 | 7 | 16 | 10 | 214 | 47 | 136 | 2 | 986 |
| VA | 0 | 959 | 101 | 13 | 17 | 8 | 468 | 58 | 128 | 4 | 1,756 |

`*` October is through October 21. A zero means none of the partner-associated GTI indicators in this population were added to ThreatConnect during that month; it does not mean the partner had no observations that month.

ThreatConnect `trackedUsers` provides a cumulative observation count and the latest observation timestamp for each user, not the full observation-event history. A true monthly observation-activity table cannot be reconstructed from this field alone.

## What the partner analysis shows

The tags and groups below are context on the GTI-owned indicator. They are not tags or groups supplied by the observing partner.

- **HRSA:** Largest subset at 5,095 indicators, including 5,014 Addresses. Its leading GTI tags are phishing (1,444), pwn (1,228), malware (1,181), and Tor (570). Its leading qualified groups are APT44 (630), Unknown malware (475), MIRAI (432), UNC6395 (380), and Cobalt Strike (362).
- **NIH:** Second-largest subset at 3,914 indicators. It contains 217 Hosts and 11 Files—the second-highest Host count and highest File count among the partner subsets. Cobalt Strike is its leading qualified group at 603 indicators; its leading tags are pwn (831), phishing (762), and malware (705).
- **HHS:** Contains 2,453 Addresses and 33 Hosts. Its leading tags are pwn (927), phishing (733), malware (362), and Tor (315); APT44 is its leading qualified group at 398 indicators.
- **VA:** Contains the largest Host count at 259, along with 1,497 Addresses. Its leading tags are pwn (641), phishing (505), malware (315), Tor (163), VPN (101), and suspicious UDP (101). Its leading qualified groups are APT44 (205), UNC6395 (157), Unknown malware (152), FIN12 (127), and BEACON (121).
- **CMS:** Contains 1,226 Addresses and 110 Hosts. Its leading tags are pwn (674), phishing (570), Tor (301), malware (214), and suspicious UDP (161); APT44 is its leading qualified group at 387 indicators.
- **OS:** Contains 975 Addresses and 11 Hosts. Its leading tags are pwn (444), phishing (421), Tor (188), malware (151), and suspicious UDP (118); APT44 is its leading qualified group at 221 indicators.
- **CDC:** Contains 972 Addresses and four Files. Its leading tags are pwn (393), phishing (317), Tor (163), and malware (104); FIN11 is its leading qualified group at 255 indicators.
- **FDA:** Contains 904 Addresses and 13 Hosts. Its leading tags are phishing (402), pwn (390), Tor (167), and malware (152); its leading qualified groups are APT44 (206), UNC6395 (165), and Unknown malware (136).
- **IHS:** Contains 647 Addresses and 58 Hosts. Its leading tags are phishing (286), pwn (248), Tor (102), malware (94), and suspicious UDP (77); Unknown malware is its leading qualified group at 137 indicators.
- **DHA:** Smallest subset at 560 indicators, including 512 Addresses and 48 Hosts. Its leading tags are phishing (179), pwn (165), and VPN (76); its leading qualified groups are Unknown malware (119), UNC4899 (67), and UNC5537 (61).

The strongest defensible conclusion is about the kinds of GTI indicators appearing in each partner's observed subset. Shared GTI tags or groups do not by themselves prove a partner-specific threat focus, because the same indicator may be observed by several partners and the enrichment originates from GTI.

## Method and validation

- Population TQL: `ownerName = "Google Threat Intelligence" AND observationCount > 0`.
- Partner attribution: per-indicator ThreatConnect v3 detail request with `fields=trackedUsers,observations`.
