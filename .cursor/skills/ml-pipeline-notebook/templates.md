# ML Pipeline — Templates

## Planning outline (initial scaffold)

```markdown
# {Project Title}

**Product goal:** _TBD_

Planning doc for the ML pipeline ([Ameisen](https://learning.oreilly.com/library/view/building-machine-learning/9781492053187/)). Work through one step at a time.

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

---

## 1. Data ingestion and data versioning

## 2. Data validation

## 3. Data preprocessing

## 4. Model training and tuning

## 5. Model analysis

## 6. Model versioning

## 7. Model deployment

## 8. Feedback loops
```

When filling a step, add content directly under its heading.

---

## Notebook (optional)

Markdown headers: `## {N}. {Step name}` — one pair per step when implementing code.

Setup cell:

```python
from pathlib import Path
from datetime import date
from htoc.core.bootstrap import ensure_htoc_on_path

ensure_htoc_on_path()

RUN_DATE = date.today().strftime("%Y%m%d")
OUT = Path("htoc_ml/analysis/_outputs") / "{project_slug}"
OUT.mkdir(parents=True, exist_ok=True)
```
