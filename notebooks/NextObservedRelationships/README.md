# Cross-Partner Threat Spread Analysis

**Product goal:** Each day, rebuild a **forecast graph** of same-IOC cross-partner spread risks from the daily observation pull, score every eligible edge with a calibrated hybrid policy — **NOI + historical pathways when NOI exists; pathways alone when it does not** — then **rank** what matters most for each partner (Top 10). Graph first; rankings are a view of it.

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

- **Question:** If indicator X is active at other partner(s) and Partner B has no hit in the current open source-activity opportunity as of T, what is **P(B sees X in the horizon)**?
- **Framing:** **Predictive forecast** — not a ticket/case system and not IOC→IOC relatedness. Build a **probability graph**, then **rank** per partner.
- **Edge meaning:** eligible **(X → B)** = same IOC, cross-partner only (A ≠ B). One X can have high P toward **many** partners.
- **Two eligible cohorts:** **warm / NOI-covered** edges may have older B history but no hit in the current opportunity; **cold / NOI-uncovered** edges have no usable B prediction. Both predict the same next B observation outcome.
- **Edge P (v1):** calibrated probability from historical cross-partner pathway features, plus the target partner’s NOI when it is available.
- **Missing NOI:** never removes an eligible edge. Use the calibrated pathway-only score for cold / uncovered indicators.
- **Combination rule:** learn and validate NOI’s contribution; do not use an arbitrary fixed-weight blend.
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
- **Data (production only):** see **§1b Data sources and flow** — daily observations, historical pathways, NOI as-of T when available, PRISM medium+
- **Ranking rule:** per partner, **Top 10 = top eligible edges by calibrated edge P**; show PRISM and score provenance on the row
- **Thresholds:** no fixed P cut (e.g. not 75%) — operating points from data / tests
- **Defaults for publish:** per-partner Top 10 on **1–7**; graph on demand; thin leadership roll-up (counts / # high-P opens) — not a full matrix dump every day

**Success criteria**

- Daily **forecast graph** + per-partner **Top 10** covering all eligible edges
- Pathway-only baseline checked for ranking quality and calibration
- Where NOI exists, the learned NOI + pathway model must show out-of-time lift over both NOI-only and pathway-only
- Both scoring routes must predict the same outcome / horizon and be calibrated to a comparable probability scale

**Exclusions**

- Low-severity PRISM
- Candidates without current cross-partner source activity
- New feeds or operational changes for this study
- IOC→IOC “related indicator” probabilities as the primary product

### 1b. Breakdown of the process

**Data sources (production only)**

| Source | Role | Path (via `htoc.core.paths`) |
|--------|------|------------------------------|
| **OpDiv observations** | Eligibility + labels + leakage-safe historical pathway features | `OpDiv_Observations/htoc_opdiv_obs_d{YYYYMMDD}.csv` |
| **NOI forecasts** | Optional target-partner feature when a prediction exists | `JA/NextObserveV4Test/{Partner}/{Partner}_output_{YYYYMMDD}.csv` (`Probability: 7-Day` / `14-Day`) |
| **PRISM** | Medium+ filter; severity on ranked rows | `JA/PrismTest` threat-assessment scores |

**Data flow (daily)**

```text
Daily observation pull          Daily NOI CSVs (as-of T)         PRISM scores
        |                              |                              |
        v                              v                              v
 eligibility + labels          optional NOI feature             medium+ filter
 + historical pathways                |                              |
        +--------------+---------------+---------------+--------------+
                       v
              Eligible edges (X -> B)
              X active elsewhere, no B hit in current opportunity, medium+
                       |
           +-----------+-----------+
           |                       |
      NOI available          NOI unavailable
      NOI + pathways         pathways only
           +-----------+-----------+
                       |
                       v
              Calibrated forecast graph
                       |
           +-----------+-----------+
           v                       v
     Explore graph           Per-partner Top 10
     (1 IOC -> many partners) (rank inbound edges by P)
```

- Observations define the **graph skeleton, labels, and pathway history**; NOI enriches covered edges; PRISM **filters/annotates**; Top 10 is a **cut of the graph**
- Rebuild each day from that day’s pulls; drop `(X -> B)` when B observes X; demote when source sightings go quiet
- A later source-activity episode may reopen `(X -> B)`; prior B history then makes it a warm edge rather than a cold edge
- Keep missing-NOI edges and score them from pathways; record whether NOI contributed to every score

**Pipeline**

- **Business Understanding (this phase):** lock question, graph-first products, hybrid scoring policy, users — **done**
- **Data Understanding:** join observations + NOI + PRISM; QC; EDA positive rates / imbalance (1–7, 8–14 by partner); test pathway-only, NOI-only, and combined coverage / ranking; document as-of-T joins
- **Data Preparation:** eligible-edge table; leakage-safe pathway features; optional NOI + availability flag; labels for days 1–7 and 8–14; as-of-T only
- **Modeling:** simple pathway-only baseline; learned/calibrated hybrid with NOI where available
- **Evaluation:** out-of-time graph + Top 10 ranking and calibration; compare pathway-only, NOI-only, and combined models on matching cohorts
- **Deployment / Acceptance:** findings write-up; go/no-go

**Product outputs (graph first, then rankings)**

- **Forecast graph (primary):** indicators + partners; edges = eligible same-IOC spreads scored by the calibrated hybrid policy
- **Top 10 (derived):** per partner, rank at-risk edges by that P — a **view of the graph**, not a separate model
- **Supporting stats:** empirical spread rate (eval), n, PRISM, ΔP / Δrank vs prior day
- **Edge caps (later):** from EDA volume for readability

**Operating objective:** Daily — build the **probability graph** for all eligible edges using **NOI + pathways when covered and pathways alone otherwise**; publish **per-partner rankings** of highest-P at-risk IOCs. Drop edges when the target has seen the IOC; decay/refresh with daily source activity; keep history for learning / calibration so rankings do not freeze on flat “high chance soon” for weeks.

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

- Calibration / reliability of both score routes on the same target and horizon
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
- **No combined lift:** NOI may add no out-of-time value beyond pathways; retain it only if testing supports it
- **Route mismatch:** NOI-covered and missing-NOI scores may not be comparable unless calibrated and monitored together

**First EDA checks**

- Eligible-edge counts by partner / day
- Warm / NOI-covered vs cold / NOI-uncovered cohort sizes and outcome rates
- Pathway-only vs NOI-only vs combined ranking on matching eligible-edge cohorts
- Missing-NOI rate on eligible edges
- Days 8–14 positive rate
- NOI as-of-T join audit (forecast stamp == T)

### 1c. Users

- **HTOC analysts** — graph for structure; Top 10 (by P) for triage
- **Partner CTI / OpDiv** — earlier awareness when another partner already saw a medium+ IOC; partner-scoped graph + ranking
- **Leadership** — whether the hybrid cross-partner graph/rankings are worth promoting; Phase 2 go/no-go

**Actionability:** graph and Top 10 interpretable without a data scientist; alert cuts from data + tests only.

### 1d. Modeling

**Locked hybrid policy**

- **NOI available:** use historical pathway features plus NOI in a learned, calibrated cross-partner model.
- **NOI unavailable / cold indicator:** use the calibrated pathway-only prediction; do not drop or zero the edge.
- Prefer one simple model with NOI value + an NOI-available flag first. Test separate calibrated routes only if they improve out-of-time ranking or calibration.
- Both routes predict the same cross-partner arrival outcome and horizon, so their probabilities can share one graph and Top 10.

**Simple baseline**

- Regularized logistic regression on leakage-safe pathway features.
- This is the full-coverage benchmark and the production fallback when NOI is absent.

**Improved options, selected from evidence**

- Regularized logistic with pathway features + NOI + NOI-available flag
- Calibrated gradient boosting if it improves out-of-time ranking and probability quality
- Separate pathway-only and NOI + pathway models only if pooled calibration is inadequate

**Required comparisons:** cold edges = pathway-only; NOI-covered edges = pathway-only vs NOI-only vs combined. No fixed-weight NOI/pathway blend.

**Selection rule:** use research and chronological holdout results; promote complexity only for reliable lift, calibration, and manageable daily runtime.


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

### Pass 1 — preliminary warm / NOI-covered test

The initial event builder excluded targets observed **on cutoff T**, but allowed
targets that had observed the IOC earlier. It therefore sampled the warm / target
re-observation cohort. Its 75% Top-10 hit rate is preliminary and enriched; rerun
it with explicit source-activity episodes, pathway features, and chronological
holdout before treating it as evidence for the hybrid product.

### Pass 2 — cold / first-arrival pathway retest

Pass 2 isolates the cold cohort and loads a bounded **180-day** raw window so
every evaluated cutoff has up to 90 days of pathway history. The target has not
observed the IOC in the loaded history; multiple active source partners are
collapsed into one (IOC → target partner) edge.

| Check | Corrected result |
|-------|------------------|
| Source-level events | 290,455 |
| Cold-target source edges | 194,730 |
| Collapsed graph edges (common eval slice) | **51,103** |
| Indicators / target partners | 1,038 / 10 |
| Actual spread in days 1–7 | **0.69%** |
| Actual spread in days 8–14 | **0.53%** |
| NOI coverage on true cold edges | **0%** |
| Pathways 30d | AUC 0.69; AP 0.015; Top-10 hit 3.40% |
| Pathways 60d | AUC 0.72; AP 0.019; Top-10 hit **3.90%** |
| Pathways 90d | AUC **0.74**; AP **0.024**; Top-10 hit 3.48% |
| Mean Top-10 comparison base rate | **0.78%** |

**Interpretation**

- NOI cannot be the primary edge score for true first-arrival edges in this sample; it has no coverage.
- Historical partner pathways provide full coverage and meaningful ranking lift:
  the 60-day Top 10 is about **5×** the comparison base rate.
- Raw pathway probabilities are not calibrated: mean 60-day score is ~5.0% vs
  an actual 0.69% rate. Treat them as ranking features, not final probabilities.
- **Hybrid policy:** add NOI to pathway features where it is available; otherwise
  produce the edge probability from pathways alone. Missing NOI never removes an edge.
- The corrected cold-edge sample cannot measure NOI’s incremental value because
  NOI coverage is 0%; that comparison requires a separate NOI-covered cohort.
- 90 days ranks best overall (AUC/AP); 60 days performs best for the Top-10
  product. Do not choose the window until chronological validation is expanded.
- “Cold” currently means unseen in the bounded loaded history. Production should
  maintain a compact seen-before registry so old sightings do not require loading
  years of raw observations.

**Next checks:** time-split calibration; cold pathway-only evaluation; matched
NOI-covered comparison (NOI-only vs pathways-only vs combined); pooled score
comparability; per-partner Top-10 stability; 8–14 pathway features;
source-combination features; compact seen-before registry; 30/60/90
runtime-memory comparison.

## 3. Data Preparation

_Build episode-aware eligible graph edges for warm and cold cohorts; leakage-safe
rolling pathway features; labels for **days 1–7** and **days 8–14**; optional NOI
as-of-T plus an availability flag._

## 4. Modeling

Historical pathways are the simple full-coverage baseline. The improved model
uses pathways + NOI when NOI exists and pathways alone when it does not. Compare
both routes on chronological holdout and calibrate them to the same probability
meaning before producing a shared graph and Top 10.

## 5. Evaluation

_Evaluate pathway/model probabilities, per-partner Top 10 lift and stability,
calibration, horizon performance, and bounded-window efficiency._

## 6. Deployment / Acceptance

_Findings write-up and go/no-go recommendation for stakeholders._
