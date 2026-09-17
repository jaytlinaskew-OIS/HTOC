# Cross-Partner Threat Spread Analysis

**Product goal:** Each day, rebuild a **forecast graph** of same-IOC cross-partner spread risks from the daily observation pull, score eligible edges with **existing Next Observed (NOI) probabilities** for the target partner (new model only if we need lift), then **rank** what matters most for each partner (Top 10). Graph first; rankings are a view of it.

Planning follows **CRISP-DM**. Work through one phase at a time.

| Phase | Name | Window (weekdays) | Status |
|------|------|--------|--------|
| 1 | Business Understanding | Sep 17 – Sep 18 | [x] locked |
| 2 | Data Understanding | Sep 22 – Oct 2 | [x] in progress |
| 3 | Data Preparation | Oct 6 – Oct 16 | [ ] |
| 4 | Modeling | Oct 20 – Nov 6 | [ ] |
| 5 | Evaluation | Nov 10 – Nov 13 | [ ] |
| 6 | Deployment / Acceptance | Nov 16 – Nov 17 | [ ] |

**Window:** Sep 17 – Nov 17, 2026 (2 months, Mon–Fri only)  
**Board:** [Cross-Partner Threat Spread Analysis](https://github.com/users/jaytlinaskew-OIS/projects/1)  
**Schedule PDF:** [Cross_Partner_Threat_Spread_Schedule.pdf](Cross_Partner_Threat_Spread_Schedule.pdf)  
**Artifacts:** [NextObservedRelationships.ipynb](NextObservedRelationships.ipynb) · [partner_relationships.py](../../htoc_ml/analysis/noi/partner_relationships.py)

---

## 1. Business Understanding

Locked scope for now: **question**, **process** (incl. data sources & flow, risks), **users**, **modeling**. Revisit as Data Understanding / build teaches us more. Full detail below; board card mirrors this.

### 1a. Question solving

What problem are we solving, and what counts as a valid answer?

- **Question:** If indicator X has been observed at other partner(s) and not yet at Partner B, what is **P(B sees X in the horizon)** from as-of date T?
- **Framing:** **Predictive forecast** — not a ticket/case system and not IOC→IOC relatedness. Build a **probability graph**, then **rank** per partner.
- **Edge meaning:** eligible **(X → B)** = same IOC, cross-partner only (A ≠ B). One X can have high P toward **many** partners.
- **Edge P (v1):** **target partner’s NOI** for X (`Probability: 7-Day` / `14-Day` from daily NOI CSVs), gated to eligible edges. Matches analysis **M0** in `partner_relationships.py`.
- **Optional later model:** only if holdout shows **lift over NOI** on the same eligible edges.
- **Horizons (non-overlapping from T):**
  - **Days 1–7** — primary ranking horizon (NOI 7-day)
  - **Days 8–14** — later window (not cumulative); keep if EDA shows enough signal (NOI 14-day)
- **Grain:** by partner (rankings + evaluation partner-scoped)
- **Severity:** PRISM medium / high / critical only
- **Daily cadence:**
  - Pull **observations daily**; rebuild graph + rankings each day
  - Eligible: X seen at ≥1 other partner in daily feeds; B has **not** observed X yet
  - Edges **persist** across days while eligible (not “today’s file only”)
  - **Drop (X → B)** when B observes X; keep history for eval / learning
  - Soft-drop / demote from Top 10 if source sightings go stale (provisional: no source sighting in **7 daily pulls**; tune in EDA)
  - Refresh when X appears again in a later daily pull at a source partner
- **Data (production only):** see **§1b Data sources and flow** — daily observations, NOI as-of T, PRISM medium+
- **Ranking rule:** per partner, **Top 10 = top eligible edges by edge P** (default = target NOI); show PRISM on the row
- **Thresholds:** no fixed P cut (e.g. not 75%) — operating points from data / tests
- **Defaults for publish:** per-partner Top 10 on **1–7**; graph on demand; thin leadership roll-up (counts / # high-P opens) — not a full matrix dump every day

**Success criteria**

- Daily **forecast graph** + per-partner **Top 10** from **NOI-alone** on eligible edges
- NOI checked for **ranking quality / calibration** on those edges (does high NOI actually spread?)
- Optional: measurable **lift** if a new model is tried; Phase 2 promote-or-not on whether graph+rankings (and any new model) are worth ops use

**Exclusions**

- Low-severity PRISM
- Same-partner reappearance (NOI already covers that)
- New feeds or operational changes for this study
- IOC→IOC “related indicator” probabilities as the primary product

### 1b. Breakdown of the process

**Data sources (production only)**

| Source | Role | Path (via `htoc.core.paths`) |
|--------|------|------------------------------|
| **OpDiv observations** | Who saw which IOC when — eligibility + labels | `OpDiv_Observations/htoc_opdiv_obs_d{YYYYMMDD}.csv` |
| **NOI forecasts** | Edge **P** = target partner’s score for that IOC | `JA/NextObserveV4Test/{Partner}/{Partner}_output_{YYYYMMDD}.csv` (`Probability: 7-Day` / `14-Day`) |
| **PRISM** | Medium+ filter; severity on ranked rows | `JA/PrismTest` threat-assessment scores |

**Data flow (daily)**

```text
Daily observation pull          Daily NOI CSVs (as-of T)         PRISM scores
        |                              |                              |
        v                              v                              v
  Who has seen X?              B's P(see X in 7/14d)           medium+ filter
        |                              |                              |
        +--------------+---------------+---------------+--------------+
                       v
              Eligible edges (X -> B)
              X seen elsewhere, not at B, medium+
                       |
                       v
              Forecast graph
              edge weight = target NOI P
                       |
           +-----------+-----------+
           v                       v
     Explore graph           Per-partner Top 10
     (1 IOC -> many partners) (rank inbound edges by P)
```

- Observations define the **graph skeleton**; NOI paints **probabilities**; PRISM **filters/annotates**; Top 10 is a **cut of the graph**
- Rebuild each day from that day’s pulls; drop `(X -> B)` when B observes X; demote when source sightings go quiet
- Optional later: new model only if it **beats NOI** on the same edges

**Pipeline**

- **Business Understanding (this phase):** lock question, graph-first products, NOI-as-P, users — **done**
- **Data Understanding:** join observations + NOI + PRISM; QC; EDA positive rates / imbalance (1–7, 8–14 by partner); test whether target NOI ranks/calibrates on eligible edges; document as-of-T NOI joins
- **Data Preparation:** eligible-edge table; attach target NOI as edge P; labels for days 1–7 and 8–14; as-of-T only
- **Modeling:** **NOI-alone first**; optional cross-partner model only if lift vs NOI
- **Evaluation:** graph + Top 10 by P; calibration on eligible edges; Phase 2 / lift if new model tried
- **Deployment / Acceptance:** findings write-up; go/no-go

**Product outputs (graph first, then rankings)**

- **Forecast graph (primary):** indicators + partners; edges = eligible same-IOC spreads scored by **target NOI P**
- **Top 10 (derived):** per partner, rank at-risk edges by that P — a **view of the graph**, not a separate model
- **Supporting stats:** empirical spread rate (eval), n, PRISM, ΔP / Δrank vs prior day
- **Edge caps (later):** from EDA volume for readability

**Operating objective:** Daily — build the **probability graph** (eligible edges × **NOI scores**); publish **per-partner rankings** of highest-P at-risk IOCs. Drop edges when the target has seen the IOC; decay/refresh with daily source activity; keep history for learning / calibration so rankings do not freeze on flat “high chance soon” for weeks.

**Graph → ranking freshness**

- Eligible edges only; drop **(X → B)** when B observes X
- Rank by P; show **New / ↑ / ↓ / same** vs yesterday
- Stale source activity → demote; provisional soft-drop after **7** days with no source sighting (tune in EDA)
- No artificial churn — if the graph is stable, deltas say so

**When B observes X**

- Remove **(X → B)** from the live graph and B’s Top 10
- Keep outcome in history for train/eval
- Edges to other partners for X can stay / update

**Controls**

- Calibration / reliability of edge P (NOI, then any new model) on eligible edges
- Class imbalance EDA before any new model
- Thresholds from data/tests — no predefined P≥x%
- **NOI as-of T only** — no future forecast leakage into features or labels

**Potential risks** (discover in Data Understanding / build)

- **NOI ≠ movement:** target NOI is same-partner reappearance; it may not rank true A→B spreads on eligible edges
- **Cold / missing NOI:** B may have no (or weak) NOI for X never seen there → sparse or biased edge scores
- **Eligibility volume:** “seen elsewhere, not at B” may flood some partners or starve others
- **Stale edges:** persist-across-days + weak demotion can leave high-P edges that no longer move
- **Horizon sparsity:** days 8–14 positives may be too rare to rank or evaluate
- **As-of / leakage joins:** wrong NOI file date vs T quietly breaks calibration and lift tests
- **Label noise:** delayed or uneven partner reporting caps how well any score (NOI or model) can look
- **Flat rankings:** honest stable P can still feel stale without clear Δrank / demotion rules
- **No lift:** optional cross-partner model may not beat NOI — value then is graph/UX productization only

**First EDA checks**

- Eligible-edge counts by partner / day
- NOI vs actual spread (top-10 hit rate / AUC on eligible edges)
- Missing-NOI rate on eligible edges
- Days 8–14 positive rate
- NOI as-of-T join audit (forecast stamp == T)

### 1c. Users

- **HTOC analysts** — graph for structure; Top 10 (by P) for triage
- **Partner CTI / OpDiv** — earlier awareness when another partner already saw a medium+ IOC; partner-scoped graph + ranking
- **Leadership** — whether productizing NOI into cross-partner graph/rankings (and any lift model) is worth promoting; Phase 2 go/no-go

**Actionability:** graph and Top 10 interpretable without a data scientist; alert cuts from data + tests only.

### 1d. Modeling

**Default probability source = Next Observed (NOI)** (= analysis **M0**).

- NOI = **P(this partner sees this IOC again in H days)** from that partner’s history (production horizons 1/7/14/30/45)
- NOI does **not** natively output P(B | A saw). Cross-partner meaning = **eligibility + graph**: score only edges where X was seen elsewhere and not yet at B, using **B’s NOI for X**
- Files: `{Partner}_output_{YYYYMMDD}.csv` — `Probability: 7-Day`, `Probability: 14-Day`, etc.

**Baseline product (no new model required)**

- Edge P = target NOI (primary 7-day; optional 14-day)
- Graph + Top 10 from that
- Done when: daily graph + rankings exist and NOI is evaluated on eligible edges

**Improved options (only if NOI-alone is not enough)**

Compare lift vs NOI-alone on observation-labeled spread outcomes:

- Regularized logistic
- Gradient boosting (calibrated; promote only if beats NOI and logistic)
- Random forest + calibration

**Selection rule:** promote a new model only if it beats NOI-alone; otherwise this project is **graph + ranking productization** of existing NOI forecasts.


---

## 2. Data Understanding

**Status:** in progress · notebook: [DataUnderstanding.ipynb](DataUnderstanding.ipynb)  
**Outputs:** `htoc_ml/analysis/_outputs/next_observed_relationships/data_understanding/`

Explore/join observations + NOI + PRISM; QC coverage. Run first EDA checks from §1b:

1. Eligible-edge counts by partner / day
2. NOI vs actual spread (top-10 hit rate / AUC)
3. Missing-NOI rate on eligible edges
4. Days 8–14 positive rate
5. NOI as-of-T join audit

First pass uses a **90-day** observation window for speed; widen later if needed.

### Pass 1 findings (2026-06-19 → 2026-09-17)

| Check | Result |
|-------|--------|
| Inventory | 362k obs rows; 10 OpDivs; ~2,018 medium+ PRISM |
| NOI as-of-T | **6/16** cutoffs had NOI files |
| Eligible edges | **127,128** |
| Missing NOI on edges | **90.5%** |
| NOI vs spread (where present) | AUC **0.87**; Top-10 hit **75%** vs base **32%** |
| spread_7d overall | **8.7%** |
| spread_8_14 (sample) | **2.7%** |

**Open:** how to rank edges with missing NOI; align cutoffs to NOI file dates; missing = cold B vs file gap.

## 3. Data Preparation

_Build eligible-edge table (X seen elsewhere, not at B); attach target NOI as edge P; labels for **days 1–7** and **days 8–14**; as-of-T NOI joins only._

## 4. Modeling

Execute **§1d**: **NOI-alone graph + rankings first**; optional cross-partner model only if holdout lift beats NOI.

## 5. Evaluation

_**Graph** scored by NOI (then optional model) + per-partner **Top 10 by P**; calibration on eligible edges; Phase 2 / lift vs NOI if a new model is tried._

## 6. Deployment / Acceptance

_Findings write-up and go/no-go recommendation for stakeholders._
