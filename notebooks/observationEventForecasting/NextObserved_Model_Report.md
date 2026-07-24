# Next Observed Indicator — Performance & Outlook
**Reporting period:** June 16, 2025 – July 23, 2026 · **Prepared:** July 24, 2026

---

## What this model does (in one paragraph)

Every day, for each threat indicator we track (an IP address or domain), the model estimates the **chance we'll see that indicator again** within the next 1, 7, 14, 30, and 45 days — and attaches a **confidence level** (Highly likely / Possibly active / Low confidence). It's an early read on which known indicators are still "live" so analysts can prioritize. It forecasts the *continuation of known activity*; it is not a detector of brand‑new threats.

---

## Executive summary

- Over the past year the model made **~4.1 million daily predictions** across **9,299 indicators** and **10 divisions**.
- When it said **"Highly likely," it was right about 83% of the time** — strong, but that reliability slipped at the longer time ranges and the label wasn't consistent.
- We rebuilt the model (**V3 → V4**). In head‑to‑head testing on the same predictions, the **"Highly likely" reliability rose from ~82% to ~96%**, and — importantly — it's now **consistent across every time range**.
- The **percentages are now trustworthy**: when V4 says "70% chance," it happens about 70% of the time. Before, the longer‑range percentages could be off by ~13 points.
- A confusing quirk is gone: labels can **no longer contradict their own number** (e.g., "Low confidence — 72%").
- **Next year, if activity patterns hold, we expect ~96% reliability on "Highly likely" calls and ~96% on "Low confidence" calls, consistently across all time ranges.**

---

## Part 1 — How the model did over the past year (current model)

The model was active all year and its daily predictions were saved, so we can check each one against what actually happened afterward.

**Scale of what it produced**
- ~4.1 million predictions · 9,299 indicators · 10 divisions · every day for ~13 months.

**How well the confidence levels held up**

| When the model said… | What actually happened |
|---|---|
| **Highly likely** | Correct **~83%** of the time overall |
| **Low confidence** | The indicator correctly stayed quiet **~90%+** of the time |
| **Possibly active** | Roughly a coin flip (**~30–48%**) — genuinely uncertain |

**Where it was strong**
- Very reliable for **near‑term** calls: at the 7‑day range, "Highly likely" was right **~91%** of the time.
- Good at ruling things *out*: "Low confidence" indicators almost always stayed quiet.

**Where it fell short (what motivated the update)**
- **The "Highly likely" label meant different things at different ranges** — about 91% reliable at 7 days but only ~78% at 30–45 days. Same words, different trustworthiness.
- **No short‑term high‑confidence calls existed.** A rule quirk made it impossible for the model to ever mark a 1‑day forecast "Highly likely," so that useful signal was missing entirely.
- **Confusing labels.** Because the confidence level was set using a side rule rather than the percentage itself, you could see contradictions like *"Low confidence — 72%."*
- **The percentages didn't fully mean what they said**, especially at 30–45 days.

**Bottom line for the year:** a genuinely useful model — strong at short‑range and at ruling indicators out — but with inconsistent confidence labels and reliability that faded at the longer ranges.

---

## Part 2 — What improved from V3 to V4

We rebuilt the model and tested the new version (V4) against the current one (V3) **on the exact same predictions**, graded the same way. The numbers below are from that fair, side‑by‑side test.

| Measure (plain English) | V3 (current) | V4 (new) |
|---|:---:|:---:|
| **"Highly likely" — how often it's right** (overall) | ~82% | **~96%** |
| **"Highly likely" reliability at the *longer* ranges (30–45 days)** | ~78% | **~96%** |
| **Consistent meaning across all time ranges?** | No (91% → 78%) | **Yes (~96% everywhere)** |
| **Do the percentages mean what they say?** (30‑day) | Off by ~13 points | **Off by ~1 point** |
| **Short‑term (1‑day) high‑confidence calls** | None possible | **Now works (~92% right)** |
| **"Low confidence" — how often it's correct** | ~91% | **~96%** |
| **Label can contradict its own number?** | Yes ("Low conf — 72%") | **No — never** |
| **False "Highly likely" alerts** | More (over‑flagged) | **Fewer, and far more reliable** |

**In plain terms:**
- The alerts analysts act on — **"Highly likely"** — went from right ~82% of the time to **~96%**, and now hold that reliability **at every time range**, not just short‑term.
- The model raises **fewer** high‑confidence alerts but each one is much more trustworthy, so less time is spent chasing false alarms.
- The **percentages are now dependable**, and the **confidence label always matches the number** shown.

---

## Part 3 — What to expect next year with the updated model

Based on the fair test above (new model trained on older data, checked against newer, real outcomes), here's what to expect going forward if activity stays broadly similar to the past year:

- **"Highly likely" ≈ 96% right, consistently** across 1‑, 7‑, 14‑, 30‑, and 45‑day ranges. A "Highly likely" call means the same thing regardless of the time window.
- **"Low confidence" ≈ 96% correct** — these indicators can be safely de‑prioritized.
- **"Possibly active" ≈ a true 50/50** — an honest watch list of genuinely uncertain indicators, not hidden among the confident calls.
- **Trustworthy numbers and labels** — a stated percentage will roughly match reality, and you'll never see a low‑confidence label on a high percentage again.
- **Earliest reliable forecast: the very next day** for indicators that are currently active.

**Roughly how the daily volume will split** (typical): about **30% Highly likely, ~18% Possibly active, ~52% Low confidence.**

**Honest limitations (unchanged, and not fixable by modeling alone):**
- **Brand‑new indicators** (never seen before) can't be forecast — there's no history to learn from.
- **Long‑dormant indicators** that suddenly reactivate are near‑impossible to time.
- These gaps need **outside information** (threat‑intel feeds, indicator reputation/attributes), not a better algorithm. That's the recommended next investment.
- One division (**CDC**) is inherently the noisiest and will remain the hardest to forecast.

---

## How to read the confidence levels (quick reference)

| Label | Plain meaning | Suggested action |
|---|---|---|
| **Highly likely** | ~96% chance we'll see it again in the window | Prioritize |
| **Possibly active** | Genuinely uncertain (~50/50) | Watch list |
| **Low confidence** | ~96% chance it stays quiet | De‑prioritize |

*Figures in Parts 2–3 come from a controlled backtest on 91,810 matured predictions (new model trained on earlier data, scored on later, unseen outcomes). Part 1 figures come from the full year of live predictions checked against what actually occurred.*
