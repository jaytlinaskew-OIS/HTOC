# ML Engineering Efficiency — Reference

## Clean code & Big-O checklist

Before shipping or reviewing ML/data code:

- [ ] No `iterrows` / row-wise `apply` on large n without justification
- [ ] Nested loops document expected I, J, K and total iterations
- [ ] Lookups use dict/set, not repeated `df[df.col == x]` scans
- [ ] Dtypes tightened (`category`, `bool`, `float32`) if memory matters
- [ ] One `concat` at end, not `concat` inside a loop
- [ ] Expensive work cached (see `feat_cache`, `_noi_lookup` in `partner_relationships.py`)
- [ ] Public functions have type hints; config is a dataclass
- [ ] Unit test covers core transform on small fixture
- [ ] **Promotion only:** reusable cleaning/features live in `htoc.core`; not extracted from notebooks mid-exploration

## Promote to core (checklist)

When cutting a notebook over to `htoc_ml/src/htoc/` or `htoc.datapipelines/`:

1. Identify transforms used in more than one place (or likely to be) → `htoc.core`
2. Keep model-specific features in the model subpackage (`htoc.noi.features`, etc.)
3. Datapipeline module imports core; no copy-paste of cleaning logic
4. Add pytest on small fixture; export from `htoc.core.__init__` if public API
5. Notebook/analysis copy deleted or reduced to thin demo

## Refactor triggers

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Notebook cell > ~30s | Python loops over rows/indicators | `groupby`, merge, numpy |
| RAM spike after pivot | Wide dense float64 matrix | `float32`, sparse, filter indicators |
| Quadratic blow-up | Pairwise loops over active set | Filter to top-k; aggregate first |
| Repeated disk reads | Load inside loop | Preload once (`preload_noi_forecasts`) |

## Example: spread pairs (bad → better)

**O(I × S × T)** — loop every indicator, every source, every target:

```python
for indicator, row in active_mat.iterrows():
    for source in sources:
        for target in partners:
            ...
```

**Better** — melt active edges once, merge prob_mat long form → **O(edges × partners)** with vectorized merge:

```python
active_long = active_mat.stack().loc[lambda s: s].reset_index()
# merge to prob_mat long on (Indicator, Partner), filter source != target
```

Use the simpler loop only when prototyping on small samples.

---

## Adoption tiers

### Tier 0 — Always (any ML task in this repo)

- Python package + pytest for production logic
- Typed config (`dataclass` / Pydantic)
- Stamped outputs (`RUN_DATE`, slugged paths)
- Step 2 validation before step 3
- Big-O comment on any non-obvious loop

### Tier 1 — When training or batch eval exists (Track B class)

- **MLflow** — params, metrics, artifacts, compare runs
- **Pandera** — schema on ingest and event tables
- **sklearn Pipeline** — preprocess + model in one serialized object
- Thin **CLI** (`python -m htoc...`) wrapping the analysis module

### Tier 2 — When automating beyond manual runs

- **Optuna** — hyperparameter search (only after baseline logged in MLflow)
- **Prefect** or **Dagster** — schedule: validate → preprocess → train → eval → publish
- **Evidently** — drift report (spread rate, partner mix, feature distributions)
- **Polars** — if pandas profiling shows groupby/pivot > ~30s

### Tier 3 — Only with explicit product need

| Trigger | Tool |
|---------|------|
| Online real-time scoring API | FastAPI + container; K8s if ops requires HA |
| Multi-team shared features across models | Feature store |
| TB-scale data | Spark / Ray |
| Deep learning (vision, NLP, embeddings) | PyTorch / TF + experiment platform |

## NOR project sketch (example, not mandatory)

| Step | Likely choice |
|------|----------------|
| 1 | Partner CSVs + `RUN_DATE`; later DVC |
| 2 | Pandera on NOI columns + partner count |
| 3 | Vectorized pivot; promote spread logic out of triple loops |
| 4 | sklearn + MLflow (Track B); N/A EDA for Track A |
| 5 | MLflow metrics; SHAP optional |
| 6 | MLflow registry or `joblib` + `run_meta.json` |
| 7 | CLI + Task Scheduler |
| 8 | Compare CSVs; Evidently when automated |

## Anti-patterns

- Training in production notebook without tests
- Adding K8s before a CLI exists
- TensorFlow for tabular spread classification
- Skipping validation to save time (fails cost more later)
- Writing to production share folders from experiments
- `combinations(active_inds, 2)` on full universe without partner-level filtering
- Correlation on thousands of columns without pre-filter