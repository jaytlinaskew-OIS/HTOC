---
description: >-
  FAANG-aligned ML efficiency: clean code, Big-O and data-structure choices,
  pipeline-step tools, package-first workflow. Use when implementing ML/data
  code, reviewing performance, planning projects, or refactoring hot paths.
---

# ML Engineering Efficiency

Guide **clean code**, **algorithmic efficiency**, and **tool choices** for ML/data work. Not every project needs every tool — recommend the **smallest stack that fits**.

Pair with [ml-pipeline-notebook](../ml-pipeline-notebook/SKILL.md) for the eight-step planning outline.

## Core principles (apply by default)

1. **Notebooks explore; packages ship** — prod logic in `htoc/` with pytest; **do not** pull cleaning/features into `htoc.core` until promotion
2. **Fail early** — validate data before preprocess (step 2 before 3)
3. **Version what matters** — data snapshot id, config, model artifact, run metadata
4. **One command = one reproducible run** — CLI or orchestrated job in prod
5. **Right-size infra and algorithms** — no K8s/Spark/deep learning unless needed; no O(n²) loops when vectorization works

## Clean code (ML / data)

- **Small functions** — load, validate, transform, aggregate, save; test each in isolation
- **Typed boundaries** — `dataclass` config; type hints on public functions; Pandera/sklearn at edges
- **Immutable by default** — prefer functional transforms; one explicit `.copy()` when branching
- **Domain names** — `active_mat`, `spread_7d`, `noi_prob_7`; avoid `df`, `temp`, `data2`
- **Match repo style** — read surrounding `htoc` code before adding abstractions
- **Comments** — only non-obvious business logic or complexity tradeoffs (include Big-O if loop is intentional)

## Promote cleaning & features to `htoc.core`

**Trigger:** only when moving a notebook into `htoc_ml/src/htoc/` (model package) or `htoc.datapipelines/` — not during exploratory work in `notebooks/` or `htoc_ml/analysis/`.

| Phase | Where code lives |
|-------|------------------|
| Explore | Notebook cells — inline cleaning, pivots, features OK |
| Promote to package | Extract reusable transforms → **`htoc.core`** + pytest |
| Model-specific | Orchestration, config, model-only features → `htoc.{noi,prism,...}` (e.g. `noi/features.py`) |
| Datapipeline CLI | Thin wiring in `htoc.datapipelines.*` — import from core/model; no duplicated transforms |

**Core vs model:** if two or more pipelines/models would reuse a transform (date normalization, observation cleaning, indicator tables, shared pivots), it belongs in `htoc.core`. If only one model uses it, keep it in that model's subpackage.

Existing core examples: `observations.py`, `day.py`, `paths.py`, `bootstrap.py`.

## Big-O and data structures

**Before writing nested loops**, estimate sizes and state complexity in a comment or PR note.

### Preferred structures

| Need | Structure | Lookup / scan |
|------|-----------|---------------|
| Key → value (partner, indicator) | `dict` | O(1) avg |
| Membership / dedupe | `set` | O(1) avg |
| Sorted dates per entity | `numpy` int array + `searchsorted` | O(log n) per query |
| Tabular aggregate | `groupby` / `pivot_table` | O(n) typical |
| Feature matrix (dense) | `numpy` / pandas numeric | Vectorized O(n) |
| Mostly empty indicator×partner | sparse matrix (`scipy.sparse`) | O(nnz) |

### Common ML/data patterns

| Pattern | Complexity | When OK | Prefer instead |
|---------|------------|---------|----------------|
| Row-wise `apply` / `iterrows` | O(n) × Python overhead | n < ~5k prototype | Vectorized ops, `groupby` |
| `pivot_table` / merge on keys | O(n) | Default for aggregates | — |
| Correlation matrix (d columns) | O(d² × n) | d ≤ ~100 | Filter columns first |
| All pairs in group size k | O(k²) per group | k small | Filter group; sample; approximate |
| Triple loop I × S × T | O(I·S·T) | **Rarely** | Pre-index by source; `groupby` + merge |
| Full DataFrame copy in loop | O(n) × iterations | **Avoid** | Build list of frames → one `concat` |

### NOR-scale reference (~5k indicators, ~10 partners)

- `pivot_table` → **fine** (O(rows))
- Partner `corr` on ~10 columns → **fine**
- Indicator–indicator corr on top 40 → **fine**
- Per-indicator triple loop for spread → **watch I×S×T**; use grouped operations or sparse active index
- Co-occurrence `combinations(present, 2)` per partner → **watch** when many IOCs active at one partner

### When to escalate

- **Polars** — pandas groupby/pivot becomes bottleneck on 10M+ rows
- **NumPy broadcasting** — element-wise ops across matrices without Python loops
- **Joblib / multiprocessing** — embarrassingly parallel per-partner loads (I/O bound: `ThreadPoolExecutor`)
- **Sparse / categorical** — memory-bound indicator×partner matrices

## Eight pipeline steps → tool menu

| Step | Prefer | When scaling |
|------|--------|--------------|
| 1 Ingestion & versioning | `RUN_DATE` + manifest; `htoc.core.paths` | DVC, lake tables |
| 2 Validation | **Pandera** | Great Expectations |
| 3 Preprocessing | Package code; sklearn **Pipeline** | Polars, sparse dtypes |
| 4 Training & tuning | **sklearn** + **MLflow** | Optuna |
| 5 Analysis | MLflow metrics | SHAP |
| 6 Model versioning | MLflow / `joblib` + `run_meta.json` | Registry stages |
| 7 Deployment | **CLI** + scheduler | Prefect/Dagster |
| 8 Feedback loops | Run diff | Evidently |

## Defer unless explicitly needed

TensorFlow/PyTorch (tabular), Kubernetes (no always-on API), Spark/Ray (single-machine scale), feature stores (single model family), Kafka (batch CSVs).

## HTOC defaults

- `ensure_htoc_on_path()` / editable `htoc_ml`
- Outputs: `htoc_ml/analysis/_outputs/{slug}/` only
- Paths: `htoc.core.paths.share_root()`
- Reuse patterns from `partner_relationships.py`: `_noi_lookup` dict, `feat_cache`, `numpy` date arrays

## Agent behavior

1. Eight-step README; fill **one step at a time** when asked
2. Suggest **at most 1–2 tools** per step; note deferrals
3. On new loops or large merges, **call out Big-O** and a vectorized alternative
4. **Notebook phase:** keep transforms in the notebook; import existing `htoc.core` APIs where they already exist
5. **Promotion phase:** extract reusable cleaning/features to `htoc.core` with tests; wire model/datapipeline modules to import them — do not extract early
6. Do not add MLflow/K8s/DVC unless user confirms scope

## Additional detail

Tiers, NOR sketch, refactor checklist: [reference.md](reference.md)
