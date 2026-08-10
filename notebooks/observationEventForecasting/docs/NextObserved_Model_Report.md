# Next Observed Indicator — Performance & Outlook

**Reporting period:** June 16, 2025 – July 23, 2026 · **Prepared:** July 24, 2026

---

## What this model does (in one paragraph)

Every day, for each threat indicator we track (an IP address or domain), the model estimates the **chance we'll see that indicator again** within the next 1, 7, 14, 30, and 45 days — and attaches a **confidence level** (Highly likely / Possibly active / Low confidence).

---

## Executive summary

- Over the past year the model made **~4.1 million daily predictions** .
- When it said **"Highly likely," it was right about 83.4% of the time** — strong.
- We rebuilt the model (**V3 → V4**). In head‑to‑head testing on the same predictions, the **"Highly likely" reliability rose from ~83.4% to ~96%**.
- **Next year, if activity patterns hold, we expect ~96% reliability on "Highly likely" calls and ~96% on "Low confidence" calls, consistently across all time ranges.**

---



## Part 1 — How the model did over the past year (current model)

The model was active all year and its daily predictions were saved, so we can check each one against what actually happened afterward.

**Scale of what it produced**

- ~4.1 million predictions · 10 Partners · every day for ~13 months.

**How well the confidence levels held up**


| When the model said… | What actually happened                                     |
| -------------------- | ---------------------------------------------------------- |
| **Highly likely**    | Correct **~83%** of the time overall                       |
| **Low confidence**   | The indicator correctly stayed quiet **~90%+** of the time |
| **Possibly active**  | Roughly a coin flip (**~30–48%**) — genuinely uncertain    |


**Where it was strong**

- Very reliable for **near‑term** calls: at the 7‑day range, "Highly likely" was right **~91%** of the time.
- Good at ruling things *out*: "Low confidence" indicators almost always stayed quiet.

**Where it fell short (what motivated the update)**

- **The "Highly likely" label meant different things at different ranges** — about 91% reliable at 7 and 14 days but only ~78% at 30–45 days.
**Bottom line for the year:** a genuinely useful model — strong at short‑range and at ruling indicators out — but reliability lowered at the longer ranges.

---



## Part 2 — What improved from V3 to V4

We rebuilt the model and tested the new version (V4) against the current one (V3) **on the exact same predictions**, graded the same way. The numbers below are from that fair, side‑by‑side test.


| Measure (plain English)                                             | V3 (current) | V4 (new) |
| ------------------------------------------------------------------- | ------------ | -------- |
| **"Highly likely" — how often it's right** (overall)                | ~82%         | **~96%** |
| **"Highly likely" reliability at the *longer* ranges (30–45 days)** | ~78%         | **~96%** |
| **"Low confidence" — how often it's correct**                       | ~91%         | **~96%** |


**In plain terms:**

- The alerts analysts act on — **"Highly likely"** — went from right ~~82% of the time to **~~96%**, and now hold that reliability **at every time range**.

---



## Part 3 — What to expect next year with the updated model

Based on the fair test above (new model trained on older data, checked against newer, real outcomes), here's what to expect going forward if activity stays broadly similar to the past year:

- **"Highly likely" ≈ 96% right, consistently** across 1‑, 7‑, 14‑, 30‑, and 45‑day ranges. A "Highly likely" call means the same thing regardless of the time window.
- **"Low confidence" ≈ 96% correct** — these indicators can be safely de‑prioritized.
- **"Possibly active" ≈ a true 50/50** — Less probable indicators and more decisive predictions.
- **Earliest reliable forecast: the very next day** for indicators that are currently active.

**Roughly how the daily volume will split** (typical): about **30% Highly likely, ~18% Possibly active, ~52% Low confidence.**

**Honest limitations (unchanged, and not fixable by modeling alone):**

- **Brand‑new indicators** (never seen before) can't be forecast — there's no history to learn from.

---



## Part 4 — A closer look: what we learned digging into this year's data

Beyond measuring the model, we examined the underlying data itself. A few findings stand out and are worth sharing plainly.

### A sudden wave of brand‑new indicators

Starting around **April 2026**, a large wave of **brand‑new indicators** — ones we had never observed before — entered our tracking. This arrived abruptly rather than building up gradually, which points to **new data sources or feeds coming online** rather than a real surge in threat activity. The mix of divisions also shifted: some (for example **HRSA** and **NIH**) grew sharply while others (**DHA**, **CMS**) quieted down.

### The current model struggled with those new indicators

Brand‑new indicators are the hardest thing to forecast, because there's no past behavior to learn from. When we checked how the **current model** did specifically on these new arrivals, it was **noticeably less reliable than on established indicators — roughly 5 to 15 percentage points lower — and the gap widened at the longer time ranges.** It also tended to **wrongly label some new indicators as "unlikely to return" when they were in fact still active.** The updated model is specifically designed to reduce this problem.

### The biggest limitation is new indicators, not dormant ones

It's natural to worry about old indicators going quiet and then suddenly reactivating. In practice that's **rare — only about 1 in 100 reappearances.** The real gap is **brand‑new indicators with no track record.** At the longer time ranges, **up to roughly half of all reappearances involve indicators that were simply too new to forecast** when the prediction was made. No modeling change can close this gap — it needs **outside information**.

### Some divisions had stretches with no data

Our data feed was complete every single day overall, but **individual divisions had periods where they sent no data at all:**

- **HRSA:** no data for about **two months in summer 2025**, and again for about **two weeks in December 2025**.
- **CDC:** a **two‑week gap in May 2026** (on top of being our lowest‑volume, noisiest division).
- Smaller gaps for a few others; **DHA and CMS** saw large, lasting **drops in volume** during 2026.

### No weekly or seasonal patterns

We also checked for day‑of‑week or seasonal effects (for example, weekends being quieter). There essentially **aren't any** — activity is steady across the week.

---



## How to read the confidence levels (quick reference)


| Label               | Plain meaning                                | Suggested action |
| ------------------- | -------------------------------------------- | ---------------- |
| **Highly likely**   | ~96% chance we'll see it again in the window | Prioritize       |
| **Possibly active** | Genuinely uncertain (~50/50)                 | Watch list       |
| **Low confidence**  | ~96% chance it stays quiet                   | De‑prioritize    |