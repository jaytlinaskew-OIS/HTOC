---
name: ml-pipeline-notebook
description: >-
  Start ML analysis projects with an eight-step planning outline (Ameisen):
  data ingestion, validation, preprocessing, training, analysis, versioning,
  deployment, feedback loops. Use when starting a new ML project, planning an
  analysis, or when the user asks to work through pipeline steps one at a time.
---

# ML Pipeline Planning

Start with **only the 8 pipeline steps visible**. Fill in each step when the user works on it — do not pre-populate the whole plan upfront.

## When to apply

- New ML / analysis project
- User wants pipeline structure before implementation
- User says: "plan step 1", "fill in ingestion", "work through the pipeline"

## Initial scaffold (do this first)

Create `README.md` using [templates.md](templates.md) § Planning outline.

**Include only:**

- Project title (if known)
- One-line product goal (if user gave it; else `_TBD_`)
- Progress tracker table (8 steps, all `[ ]`)
- Eight `##` headings — body empty or `_TBD_` under each

**Do not** on first scaffold: notebook code, guessed content, implementation files.

## The 8 steps (fixed order)

1. Data ingestion and data versioning
2. Data validation
3. Data preprocessing
4. Model training and tuning
5. Model analysis
6. Model versioning
7. Model deployment
8. Feedback loops

## Incremental fill-in workflow

When the user picks a step:

1. Read current README and existing code for that step only
2. Write planning notes **under that step's heading** (prose and bullets — no fixed subsections)
3. Mark `[x]` in the progress tracker
4. Stop — do not auto-fill later steps

## When to add a notebook

After steps 1–3 are planned, or when user asks for code:

- `{ProjectName}.ipynb` with `## {N}. {Step name}` markdown headers
- HTOC: `ensure_htoc_on_path()`, outputs under `htoc_ml/analysis/_outputs/{slug}/`

See [templates.md](templates.md) § Notebook (optional).

## HTOC conventions (when implementing)

- `from htoc.core.bootstrap import ensure_htoc_on_path`
- `htoc.core.paths.share_root()` — no hardcoded share paths
- Write to `_outputs/` only

**Example:** [notebooks/NextObservedRelationships/README.md](../../notebooks/NextObservedRelationships/README.md)

## Progress tracker (top of README)

```markdown
| Step | Name | Status |
|------|------|--------|
| 1 | Data ingestion & versioning | [ ] |
| 2 | Data validation | [ ] |
| 3 | Data preprocessing | [ ] |
| 4 | Model training & tuning | [ ] |
| 5 | Model analysis | [ ] |
| 6 | Model versioning | [ ] |
| 7 | Model deployment | [ ] |
| 8 | Feedback loops | [ ] |
```
