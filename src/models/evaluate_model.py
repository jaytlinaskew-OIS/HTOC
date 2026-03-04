
#=========== Generalized ================
def evaluate_model(model_type, y_true, y_pred):
    """
    Generalized function to evaluate a model based on its type.

    Args:
        model_type (str): The type of model ("classification", "regression", "time_series").
        y_true (array-like): True values.
        y_pred (array-like): Predicted values.

    Returns:
        dict: A dictionary containing evaluation metrics.
    """
    if model_type == "classification":
        return evaluate_classification_model(y_true, y_pred)
    elif model_type == "regression":
        return evaluate_regression_model(y_true, y_pred)
    elif model_type == "time_series":
        return evaluate_time_series_model(y_true, y_pred)
    else:
        raise ValueError("Invalid model type. Choose from 'classification', 'regression', or 'time_series'.")
#=========== Classification ================
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def evaluate_classification_model(y_true, y_pred):
    """
    Evaluate a classification model using common metrics.

    Args:
        y_true (array-like): True labels.
        y_pred (array-like): Predicted labels.

    Returns:
        dict: A dictionary containing evaluation metrics.
    """
    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, average="weighted"),
        "Recall": recall_score(y_true, y_pred, average="weighted"),
        "F1 Score": f1_score(y_true, y_pred, average="weighted"),
        "Confusion Matrix": confusion_matrix(y_true, y_pred).tolist()  # Convert to list for JSON compatibility
    }
    return metrics

#=========== Regression =================
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

def evaluate_regression_model(y_true, y_pred):
    """
    Evaluate a regression model using common metrics.

    Args:
        y_true (array-like): True values.
        y_pred (array-like): Predicted values.

    Returns:
        dict: A dictionary containing evaluation metrics.
    """
    metrics = {
        "Mean Absolute Error (MAE)": mean_absolute_error(y_true, y_pred),
        "Mean Squared Error (MSE)": mean_squared_error(y_true, y_pred),
        "Root Mean Squared Error (RMSE)": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2 Score": r2_score(y_true, y_pred)
    }
    return metrics

#=========== Time series =================
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

def evaluate_time_series_model(y_true, y_pred):
    """
    Evaluate a time series model using common metrics.

    Args:
        y_true (array-like): True values.
        y_pred (array-like): Predicted values.

    Returns:
        dict: A dictionary containing evaluation metrics.
    """
    metrics = {
        "Mean Absolute Error (MAE)": mean_absolute_error(y_true, y_pred),
        "Mean Squared Error (MSE)": mean_squared_error(y_true, y_pred),
        "Root Mean Squared Error (RMSE)": np.sqrt(mean_squared_error(y_true, y_pred)),
        "Mean Absolute Percentage Error (MAPE)": np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    }
    return metrics

import matplotlib.pyplot as plt

def plot_residuals(y_true, y_pred):
    """
    Plot residuals for a time series model.

    Args:
        y_true (array-like): True values.
        y_pred (array-like): Predicted values.

    Returns:
        None
    """
    residuals = y_true - y_pred
    plt.figure(figsize=(12, 6))
    plt.plot(residuals, label="Residuals", color="orange")
    plt.axhline(y=0, color="black", linestyle="--", linewidth=1)
    plt.title("Residuals of the Model")
    plt.xlabel("Time")
    plt.ylabel("Residuals")
    plt.legend()
    plt.grid(True)
    plt.show()