# Analysis notebooks

Exploratory work for NOI, PRISM, ThreatConnect, and datapipelines.

Production code lives in `htoc_ml/src/htoc/`. This folder is Jupyter-only.

## Rules

1. **Import from `htoc`.** Notebooks call package APIs; reusable logic goes into
   `htoc_ml/src/htoc/` with tests.
2. **Write outputs to `_outputs/`** (or `%TEMP%`). Never write to live share folders
   or cutover test dirs (`JA\NextObserveV4`, `JA\NextObserveV4Test`, etc.).
3. **Name notebooks** `YYYYMMDD_<topic>.ipynb` so they sort by date.
4. **Promote, don't copy.** When analysis stabilizes, extract functions into the
   package and delete duplicated notebook code.

## Folders

| Folder | Use for |
|---|---|
| `noi/` | Forecast features, eval deep-dives, feed-health experiments — see also [Next Observed Relationships plan](../../notebooks/NextObservedRelationships/README.md) |
| `prism/` | Score distributions, ThreatConnect intake checks |
| `threatconnect/` | TC API probes, tag/playbook experiments |
| `datapipelines/` | ThreatScoreIW, search-tags, triage, iw-listing exploration |
| `adhoc/` | One-off questions that don't fit a domain |

## Starter pattern

Run notebooks with working directory `htoc_ml/` (or adjust `OUT` below).

```python
from pathlib import Path

from htoc.core.bootstrap import ensure_htoc_on_path
from htoc.core.observations import ObservationData
from htoc.noi.config import ForecastConfig

ensure_htoc_on_path()  # no-op when htoc is installed / on PYTHONPATH

OUT = Path("analysis/_outputs")
OUT.mkdir(parents=True, exist_ok=True)

config = ForecastConfig(
    save_dir=str(OUT / "noi_run"),
    htoc_share_root=r"\\cscso1fsappv01\data\HTOC",
    run_eval=False,
)
observations = ObservationData.load(
    obs_template=config.obs_template,
    train_days=config.train_days,
)
observations.describe()
```

Install the package editable once: `uv pip install -e ./htoc_ml` (from repo root).
Point your Jupyter kernel at the root workspace env (`pyproject.toml` at repo root).

Repo-root `notebooks/` still holds live scheduled runners until Task Scheduler cutover.
New analysis belongs here, not there.
