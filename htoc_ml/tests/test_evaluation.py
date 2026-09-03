"""Unit tests for shared classification/regression evaluation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression

from htoc.core.evaluation import (
    CLASSIFICATION_METRICS,
    REGRESSION_METRICS,
    assert_metrics_for_task,
    evaluate,
    evaluate_model,
    infer_task_from_model,
)
from htoc.core.pipeline import PipelineError


def test_infer_task_from_sklearn_estimators():
    assert infer_task_from_model(LogisticRegression()) == "classification"
    assert infer_task_from_model(LinearRegression()) == "regression"


def test_wrong_family_metrics_rejected():
    try:
        assert_metrics_for_task("classification", ["mae", "accuracy"])
    except PipelineError as exc:
        assert "regression metrics" in str(exc)
        assert "mae" in str(exc)
    else:
        raise AssertionError("expected PipelineError")

    try:
        assert_metrics_for_task("regression", ["f1", "rmse"])
    except PipelineError as exc:
        assert "classification metrics" in str(exc)
        assert "f1" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_model_task_mismatch_rejected():
    model = LinearRegression().fit([[0.0], [1.0], [2.0]], [0.0, 1.0, 2.0])
    try:
        evaluate([0, 1], [0, 1], task="classification", model=model)
    except PipelineError as exc:
        assert "regression" in str(exc)
        assert "classification" in str(exc)
    else:
        raise AssertionError("expected PipelineError")


def test_evaluate_classification_and_write(tmp_path):
    y_true = [0, 1, 1, 0, 1]
    y_pred = [0, 1, 0, 0, 1]
    y_score = [0.1, 0.8, 0.4, 0.2, 0.9]
    out = tmp_path / "clf_metrics.csv"
    report = evaluate(
        y_true,
        y_pred,
        task="classification",
        metrics=["accuracy", "precision", "recall", "f1", "roc_auc"],
        y_score=y_score,
        extras={"model": "unit-test"},
        output_path=out,
    )
    assert report.task == "classification"
    assert report.n_samples == 5
    assert 0.0 <= report.metrics["accuracy"] <= 1.0
    assert out.is_file()
    frame = pd.read_csv(out)
    assert "accuracy" in frame.columns
    assert frame.loc[0, "model"] == "unit-test"


def test_evaluate_regression_and_json(tmp_path):
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 1.9, 3.2, 3.8])
    out = tmp_path / "reg_metrics.json"
    report = evaluate(
        y_true,
        y_pred,
        task="regression",
        metrics=list(REGRESSION_METRICS),
        output_path=out,
    )
    assert report.task == "regression"
    assert report.metrics["mae"] >= 0
    assert report.metrics["rmse"] >= 0
    assert out.is_file()


def test_evaluate_model_classifier_with_proba(tmp_path):
    rng = np.random.default_rng(0)
    X = rng.normal(size=(40, 2))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    model = LogisticRegression(max_iter=500).fit(X, y)
    out = tmp_path / "model_eval.xlsx"
    report = evaluate_model(
        model,
        X,
        y,
        metrics=["accuracy", "f1", "roc_auc", "confusion_matrix"],
        extras={"split": "train"},
        output_path=out,
    )
    assert report.task == "classification"
    assert "roc_auc" in report.metrics
    assert isinstance(report.metrics["confusion_matrix"], list)
    assert out.is_file()
    assert set(CLASSIFICATION_METRICS)  # sanity that catalog is non-empty
