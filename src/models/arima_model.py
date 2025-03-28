import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults
from sklearn.metrics import mean_squared_error
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose

def check_stationarity(data):
    from statsmodels.tsa.stattools import adfuller
    result = adfuller(data)
    return result[1] < 0.05

def visualize_stationarity(data):
    plt.figure(figsize=(10, 6))
    plt.plot(data)
    plt.title("Time Series Data")
    plt.show()

def check_seasonality(data):
    result = seasonal_decompose(data, model='additive', period=12)
    return result.seasonal is not None

def visualize_seasonality(data):
    result = seasonal_decompose(data, model='additive', period=12)
    plt.figure(figsize=(10, 6))
    plt.plot(result.seasonal)
    plt.title("Seasonal Component")
    plt.show()

def check_autocorrelation(data):
    plot_acf(data)
    plt.title("Autocorrelation Plot")
    plt.show()

def check_partial_autocorrelation(data):
    plot_pacf(data)
    plt.title("Partial Autocorrelation Plot")
    plt.show()

def build_arima_model(train_data, order):
    model = ARIMA(train_data, order=order)
    return model

def fit_arima_model(model):
    model_fit = model.fit()
    return model_fit

def make_arima_forecast(model_fit, start, end):
    forecast = model_fit.predict(start=start, end=end)
    return forecast

def evaluate_arima_model(test_data, forecast):
    rmse = np.sqrt(mean_squared_error(test_data, forecast))
    return rmse

def generate_arima_report(train_data, test_data, forecast, model_fit, title="ARIMA Model Report"):
    """
    Generate a report for the ARIMA model, including metrics, plots, and diagnostics.

    Args:
        train_data (pd.Series): The training data.
        test_data (pd.Series): The test data.
        forecast (pd.Series): The forecasted values.
        model_fit: The fitted ARIMA model.
        title (str): The title of the report.

    Returns:
        None
    """
    # Create a figure for the report
    plt.figure(figsize=(15, 10))
    plt.suptitle(title, fontsize=16)

    # Plot the training data, test data, and forecast
    plt.subplot(2, 2, 1)
    plt.plot(train_data, label="Train Data", color="skyblue")
    plt.plot(test_data, label="Test Data", color="green")
    plt.plot(forecast, label="Forecast", color="red")
    plt.title("ARIMA Forecast")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()

    # Plot residuals
    residuals = model_fit.resid
    plt.subplot(2, 2, 2)
    plt.plot(residuals, label="Residuals", color="orange")
    plt.axhline(y=0, color="black", linestyle="--", linewidth=1)
    plt.title("Residuals")
    plt.xlabel("Time")
    plt.ylabel("Residuals")
    plt.legend()

    # Plot autocorrelation of residuals
    plt.subplot(2, 2, 3)
    plot_acf(residuals, ax=plt.gca())
    plt.title("Autocorrelation of Residuals")

    # Plot partial autocorrelation of residuals
    plt.subplot(2, 2, 4)
    plot_pacf(residuals, ax=plt.gca())
    plt.title("Partial Autocorrelation of Residuals")

    # Show the report
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

    # Print model summary
    print("\nModel Summary:")
    print(model_fit.summary())

    # Print evaluation metrics
    rmse = evaluate_arima_model(test_data, forecast)
    print(f"\nEvaluation Metrics:")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")