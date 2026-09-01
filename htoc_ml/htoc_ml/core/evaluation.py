"""Classification and regression evaluation with task/metric guards.

Shared helpers for any model that emits predictions. Call ``evaluate`` (or the
task-specific helpers) with either an explicit ``task=`` or a fitted ``model=``
so the wrong metric family is rejected early.

Example::

    from htoc_ml.core.evaluation import evaluate

    report = evaluate(y_true, y_pred, model=fitted_clf, output_path="metrics.csv")
    print(report.metrics)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin, RegressorMixin
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from htoc_ml.core.pipeline import PipelineError

TaskType = Literal["classification", "regression"]

CLASSIFICATION_METRICS = frozenset(
    {
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "average_precision",
        "log_loss",
        "confusion_matrix",
    }
)
REGRESSION_METRICS = frozenset(
    {
        "mae",
        "mse",
        "rmse",
        "r2",
        "mape",
    }
)
DEFAULT_CLASSIFICATION_METRICS = (
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
)
DEFAULT_REGRESSION_METRICS = ("mae", "mse", "rmse", "r2")

_PROBABILITY_METRICS = frozenset({"roc_auc", "average_precision", "log_loss"})


@dataclass(frozen=True)
class EvaluationReport:
    """Computed metrics plus metadata. Use ``write`` to persist for a model run."""

    task: TaskType
    metrics: dict[str, Any]
    n_samples: int
    metric_names: tuple[str, ...] = ()
    extras: dict[str, Any] = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        """One-row flat table (scalar metrics only; matrices stay in ``metrics``)."""
        row: dict[str, Any] = {
            "task": self.task,
            "n_samples": self.n_samples,
        }
        for key, value in self.metrics.items():
            if isinstance(value, (list, dict)):
                continue
            row[key] = value
        for key, value in self.extras.items():
            if key not in row:
                row[key] = value
        return pd.DataFrame([row])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: str | Path) -> Path:
        """Write report to ``.csv``, ``.json``, or ``.xlsx`` based on suffix."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        suffix = out.suffix.lower()
        try:
            if suffix == ".csv":
                self.to_frame().to_csv(out, index=False)
            elif suffix == ".json":
                out.write_text(json.dumps(self.to_dict(), indent=2, default=_json_default), encoding="utf-8")
            elif suffix in {".xlsx", ".xlsm"}:
                frame = self.to_frame()
                with pd.ExcelWriter(out, engine="openpyxl") as writer:
                    frame.to_excel(writer, index=False, sheet_name="metrics")
                    cm = self.metrics.get("confusion_matrix")
                    if cm is not None:
                        pd.DataFrame(cm).to_excel(writer, index=False, sheet_name="confusion_matrix")
            else:
                raise PipelineError(
                    f"Unsupported evaluation output type {suffix!r}; use .csv, .json, or .xlsx"
                )
        except PipelineError:
            raise
        except OSError as exc:
            raise PipelineError(f"Failed to write evaluation report: {exc}", exit_code=4) from exc
        if not out.is_file():
            raise PipelineError(f"Expected evaluation output missing after write: {out}", exit_code=4)
        return out


def _json_default(value: Any):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def infer_task_from_model(model: Any) -> TaskType:
    """Infer ``classification`` vs ``regression`` from a fitted/unfitted estimator."""
    if model is None:
        raise PipelineError("infer_task_from_model requires a model instance")
    if isinstance(model, ClassifierMixin) and not isinstance(model, RegressorMixin):
        return "classification"
    if isinstance(model, RegressorMixin) and not isinstance(model, ClassifierMixin):
        return "regression"
    # CalibratedClassifierCV and some wrappers only expose predict_proba
    if hasattr(model, "predict_proba") and callable(getattr(model, "predict_proba")):
        return "classification"
    if hasattr(model, "_estimator_type"):
        est_type = str(getattr(model, "_estimator_type"))
        if est_type == "classifier":
            return "classification"
        if est_type == "regressor":
            return "regression"
    raise PipelineError(
        f"Cannot infer evaluation task from model type {type(model).__name__}; "
        "pass task='classification' or task='regression' explicitly"
    )


def assert_model_matches_task(model: Any, task: TaskType) -> None:
    """Raise if ``model`` is clearly the wrong family for ``task``."""
    if model is None:
        return
    inferred = infer_task_from_model(model)
    if inferred != task:
        raise PipelineError(
            f"Model {type(model).__name__} looks like {inferred}, but evaluation "
            f"task is {task!r}. Use matching metrics or pass the correct task."
        )


def assert_metrics_for_task(task: TaskType, metrics: Sequence[str]) -> tuple[str, ...]:
    """Validate metric names against the allowed set for ``task``."""
    names = tuple(str(m).strip().lower() for m in metrics if str(m).strip())
    if not names:
        raise PipelineError("At least one evaluation metric is required")
    allowed = CLASSIFICATION_METRICS if task == "classification" else REGRESSION_METRICS
    invalid = [m for m in names if m not in allowed]
    if invalid:
        other = "regression" if task == "classification" else "classification"
        other_set = REGRESSION_METRICS if task == "classification" else CLASSIFICATION_METRICS
        wrong_family = [m for m in invalid if m in other_set]
        unknown = [m for m in invalid if m not in other_set]
        parts = []
        if wrong_family:
            parts.append(
                f"{wrong_family} are {other} metrics and cannot be used for {task} evaluation"
            )
        if unknown:
            parts.append(f"unknown metrics {unknown}; allowed for {task}: {sorted(allowed)}")
        raise PipelineError("; ".join(parts))
    return names


def resolve_task(*, task: TaskType | None = None, model: Any = None) -> TaskType:
    if task is not None:
        if task not in {"classification", "regression"}:
            raise PipelineError(f"task must be 'classification' or 'regression', got {task!r}")
        assert_model_matches_task(model, task)
        return task
    if model is not None:
        return infer_task_from_model(model)
    raise PipelineError("Pass task='classification'|'regression' or model= to select evaluation metrics")


def _as_1d(values) -> np.ndarray:
    arr = np.asarray(values)
    if arr.ndim > 1 and arr.shape[-1] == 1:
        arr = arr.reshape(-1)
    if arr.ndim != 1:
        raise PipelineError(f"Expected 1-d labels/predictions, got shape {arr.shape}")
    return arr


def evaluate_classification(
    y_true,
    y_pred,
    *,
    metrics: Sequence[str] = DEFAULT_CLASSIFICATION_METRICS,
    y_score=None,
    average: str = "binary",
    model: Any = None,
    extras: Mapping[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> EvaluationReport:
    """Score hard labels (and optional probabilities) with classification metrics."""
    assert_model_matches_task(model, "classification")
    names = assert_metrics_for_task("classification", metrics)
    y_t = _as_1d(y_true)
    y_p = _as_1d(y_pred)
    if len(y_t) != len(y_p):
        raise PipelineError(f"y_true length {len(y_t)} != y_pred length {len(y_p)}")
    if len(y_t) == 0:
        raise PipelineError("Cannot evaluate classification metrics on empty arrays")

    need_scores = [m for m in names if m in _PROBABILITY_METRICS]
    scores = None
    if need_scores:
        if y_score is None and model is not None and hasattr(model, "predict_proba"):
            # Caller must pass the same X used for y_pred; without X we require y_score.
            raise PipelineError(
                f"Metrics {need_scores} need probability/decision scores; pass y_score= "
                "(predict_proba[:, 1] for binary, or full matrix for multiclass log_loss)"
            )
        if y_score is None:
            raise PipelineError(f"Metrics {need_scores} require y_score=")
        scores = np.asarray(y_score)

    computed: dict[str, Any] = {}
    zero_div = 0.0
    for name in names:
        if name == "accuracy":
            computed[name] = float(accuracy_score(y_t, y_p))
        elif name == "balanced_accuracy":
            computed[name] = float(balanced_accuracy_score(y_t, y_p))
        elif name == "precision":
            computed[name] = float(precision_score(y_t, y_p, average=average, zero_division=zero_div))
        elif name == "recall":
            computed[name] = float(recall_score(y_t, y_p, average=average, zero_division=zero_div))
        elif name == "f1":
            computed[name] = float(f1_score(y_t, y_p, average=average, zero_division=zero_div))
        elif name == "roc_auc":
            computed[name] = float(_roc_auc(y_t, scores))
        elif name == "average_precision":
            computed[name] = float(_average_precision(y_t, scores))
        elif name == "log_loss":
            computed[name] = float(log_loss(y_t, scores))
        elif name == "confusion_matrix":
            computed[name] = confusion_matrix(y_t, y_p).tolist()

    report = EvaluationReport(
        task="classification",
        metrics=computed,
        n_samples=int(len(y_t)),
        metric_names=names,
        extras=dict(extras or {}),
    )
    if output_path is not None:
        report.write(output_path)
    return report


def _binary_positive_scores(y_true: np.ndarray, y_score: np.ndarray) -> np.ndarray:
    score = np.asarray(y_score)
    if score.ndim == 2 and score.shape[1] == 2:
        return score[:, 1]
    if score.ndim == 1:
        return score
    raise PipelineError(
        f"Binary probability metrics need 1-d scores or shape (n, 2); got {score.shape}"
    )


def _roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    classes = np.unique(y_true)
    if len(classes) < 2:
        raise PipelineError("roc_auc requires at least two classes in y_true")
    if len(classes) == 2:
        return float(roc_auc_score(y_true, _binary_positive_scores(y_true, y_score)))
    return float(roc_auc_score(y_true, y_score, multi_class="ovr", average="weighted"))


def _average_precision(y_true: np.ndarray, y_score: np.ndarray) -> float:
    classes = np.unique(y_true)
    if len(classes) != 2:
        raise PipelineError("average_precision currently supports binary labels only")
    return float(average_precision_score(y_true, _binary_positive_scores(y_true, y_score)))


def evaluate_regression(
    y_true,
    y_pred,
    *,
    metrics: Sequence[str] = DEFAULT_REGRESSION_METRICS,
    model: Any = None,
    extras: Mapping[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> EvaluationReport:
    """Score continuous predictions with regression metrics."""
    assert_model_matches_task(model, "regression")
    names = assert_metrics_for_task("regression", metrics)
    y_t = _as_1d(y_true).astype(float)
    y_p = _as_1d(y_pred).astype(float)
    if len(y_t) != len(y_p):
        raise PipelineError(f"y_true length {len(y_t)} != y_pred length {len(y_p)}")
    if len(y_t) == 0:
        raise PipelineError("Cannot evaluate regression metrics on empty arrays")

    computed: dict[str, Any] = {}
    for name in names:
        if name == "mae":
            computed[name] = float(mean_absolute_error(y_t, y_p))
        elif name == "mse":
            computed[name] = float(mean_squared_error(y_t, y_p))
        elif name == "rmse":
            computed[name] = float(np.sqrt(mean_squared_error(y_t, y_p)))
        elif name == "r2":
            computed[name] = float(r2_score(y_t, y_p))
        elif name == "mape":
            computed[name] = float(mean_absolute_percentage_error(y_t, y_p))

    report = EvaluationReport(
        task="regression",
        metrics=computed,
        n_samples=int(len(y_t)),
        metric_names=names,
        extras=dict(extras or {}),
    )
    if output_path is not None:
        report.write(output_path)
    return report


def evaluate(
    y_true,
    y_pred,
    *,
    task: TaskType | None = None,
    model: Any = None,
    metrics: Sequence[str] | None = None,
    y_score=None,
    average: str = "binary",
    extras: Mapping[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> EvaluationReport:
    """Evaluate predictions; ``task`` or ``model`` selects classification vs regression.

    Raises ``PipelineError`` when metrics do not belong to the resolved task, or when
    ``model`` and ``task`` disagree.
    """
    resolved = resolve_task(task=task, model=model)
    if resolved == "classification":
        chosen = metrics if metrics is not None else DEFAULT_CLASSIFICATION_METRICS
        return evaluate_classification(
            y_true,
            y_pred,
            metrics=chosen,
            y_score=y_score,
            average=average,
            model=model,
            extras=extras,
            output_path=output_path,
        )
    chosen = metrics if metrics is not None else DEFAULT_REGRESSION_METRICS
    if y_score is not None:
        raise PipelineError("y_score is only valid for classification evaluation")
    return evaluate_regression(
        y_true,
        y_pred,
        metrics=chosen,
        model=model,
        extras=extras,
        output_path=output_path,
    )


def evaluate_model(
    model: Any,
    X,
    y_true,
    *,
    metrics: Sequence[str] | None = None,
    task: TaskType | None = None,
    extras: Mapping[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> EvaluationReport:
    """Predict with ``model`` on ``X`` and evaluate against ``y_true``.

    Classification models that need probability metrics will use ``predict_proba``
    when those metrics are requested.
    """
    resolved = resolve_task(task=task, model=model)
    if not hasattr(model, "predict"):
        raise PipelineError(f"Model {type(model).__name__} has no predict()")
    try:
        y_pred = model.predict(X)
    except Exception as exc:
        raise PipelineError(f"model.predict failed during evaluation: {exc}") from exc

    y_score = None
    chosen = metrics
    if resolved == "classification":
        names = assert_metrics_for_task(
            "classification",
            chosen if chosen is not None else DEFAULT_CLASSIFICATION_METRICS,
        )
        if any(m in _PROBABILITY_METRICS for m in names):
            if not hasattr(model, "predict_proba"):
                raise PipelineError(
                    f"Requested {sorted(set(names) & _PROBABILITY_METRICS)} but "
                    f"{type(model).__name__} has no predict_proba()"
                )
            try:
                y_score = model.predict_proba(X)
            except Exception as exc:
                raise PipelineError(f"model.predict_proba failed during evaluation: {exc}") from exc

    return evaluate(
        y_true,
        y_pred,
        task=resolved,
        model=model,
        metrics=chosen,
        y_score=y_score,
        extras=extras,
        output_path=output_path,
    )
