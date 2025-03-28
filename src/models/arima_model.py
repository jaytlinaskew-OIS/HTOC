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

def visualize_stationarity(data, rolling_window=7, title="Time Series Trends (Rolling Average)"):
    """
    Visualize the time series data with rolling mean for multiple columns using subplots.

    Args:
        data (pd.DataFrame): The time series data with multiple columns.
        rolling_window (int): The window size for calculating rolling statistics.
        title (str): The title of the entire plot.

    Returns:
        None
    """
    # Create subplots
    num_columns = len(data.columns)
    fig, axes = plt.subplots(nrows=num_columns, ncols=1, figsize=(12, 10), sharex=True)

    # Define colors for consistency
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown']  # Add more colors if needed

    # Plot each variable in a separate subplot
    for i, column in enumerate(data.columns):
        axes[i].plot(data.index, data[column].rolling(window=rolling_window).mean(), 
                     color=colors[i % len(colors)], label=column)
        axes[i].set_title(column, fontsize=10)
        axes[i].set_ylabel("Value")
        axes[i].legend()

    # Adjust layout
    plt.xlabel("Time")
    plt.suptitle(title, fontsize=14)
    plt.tight_layout()
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

def plot_residuals(residuals):
    """
    Plot the residuals to check for randomness.

    Args:
        residuals (pd.Series): The residuals (actual - predicted).

    Returns:
        None
    """
    plt.figure(figsize=(12, 6))
    plt.plot(residuals, label="Residuals", color="orange")
    plt.axhline(y=0, color="black", linestyle="--", linewidth=1)
    plt.title("Residuals of ARIMA Model")
    plt.xlabel("Time")
    plt.ylabel("Residuals")
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_forecast(train_data, test_data, forecast):
    """
    Plot the training data, test data, and forecast.

    Args:
        train_data (pd.Series): The training data.
        test_data (pd.Series): The test data.
        forecast (pd.Series): The forecasted values.

    Returns:
        None
    """
    plt.figure(figsize=(12, 6))
    plt.plot(train_data, label="Train Data", color="blue")
    plt.plot(test_data, label="Test Data", color="green")
    plt.plot(forecast, label="Forecast", color="red")
    plt.title("ARIMA Model Forecast vs Actual")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.show()


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
    
def plot_arima(data_values, order = (1,1,1), trend = 'c'):
    print('final model:', order, trend)
    model = ARIMA(data_values, order=order, trend = trend)
    results = model.fit()
    
    error = mean_squared_error(data_values, results.fittedvalues)   
    print('MSE error is:', error)
    
    from matplotlib import pyplot as plt
    f = plt.figure()
    f.set_figwidth(15)
    f.set_figheight(6)
    plt.plot(data_values, label = "original Series", linewidth = 4)
    plt.plot(results.fittedvalues, color='red', label = "Predictions", linestyle='dashed', linewidth = 3)
    plt.legend(fontsize = 25)
    plt.xlabel('Months', fontsize = 25)
    plt.ylabel('Count', fontsize = 25)
    plt.show()

from sklearn.metrics import mean_absolute_error, mean_squared_error
import math

# Initialize a list to store metrics for each iteration
metrics_log = []

# Example function to calculate and log metrics
def log_metrics(y_true, y_pred, iteration):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)
    
    # Log metrics for the current iteration
    metrics_log.append({
        'iteration': iteration,
        'MAE': mae,
        'MSE': mse,
        'RMSE': rmse
    })
    
    # Print metrics for the current iteration
    print(f"Iteration {iteration}: MAE={mae}, MSE={mse}, RMSE={rmse}")

import matplotlib.pyplot as plt

def plot_metrics(metrics_log):
    iterations = [entry['iteration'] for entry in metrics_log]
    mae_values = [entry['MAE'] for entry in metrics_log]
    mse_values = [entry['MSE'] for entry in metrics_log]
    rmse_values = [entry['RMSE'] for entry in metrics_log]

    plt.figure(figsize=(10, 6))
    plt.plot(iterations, mae_values, label='MAE')
    plt.plot(iterations, mse_values, label='MSE')
    plt.plot(iterations, rmse_values, label='RMSE')
    plt.xlabel('Iteration')
    plt.ylabel('Metric Value')
    plt.title('Metrics Over Tuning Iterations')
    plt.legend()
    plt.show()
    
metrics_storage = {}

def calculate_metrics(test, forecast_values, forecast_steps):
    """
    Calculate evaluation metrics for the forecast.
    """
    mae = mean_absolute_error(test['Threat_Event_Count'][:forecast_steps], forecast_values)
    mse = mean_squared_error(test['Threat_Event_Count'][:forecast_steps], forecast_values)
    rmse = np.sqrt(mse)
    return {'MAE': mae, 'MSE': mse, 'RMSE': rmse}

def add_metrics(storage, order, metrics):
    """
    Add metrics to the storage with the ARIMA order as the key.
    """
    storage[order] = metrics

def display_and_save_metrics(order, metrics, log_file="metrics_log.txt"):
    """
    Display metrics and save them to a log file.
    """
    mae, mse, rmse = metrics['MAE'], metrics['MSE'], metrics['RMSE']
    log_content = (
        f"ARIMA Order: {order}\n"
        f"Mean Absolute Error (MAE): {mae}\n"
        f"Mean Squared Error (MSE): {mse}\n"
        f"Root Mean Squared Error (RMSE): {rmse}\n\n"
        "Interpretation:\n"
        f"1. Mean Absolute Error (MAE): On average, the forecasted values deviate from the actual values by {mae:.2f} threat events.\n"
        f"{'   This is a good result, indicating low average deviation.' if mae < 10 else '   This is a bad result, indicating high average deviation.'}\n"
        f"2. Mean Squared Error (MSE): The average squared difference between the forecasted and actual values is {mse:.2f}. This metric penalizes larger errors more heavily.\n"
        f"{'   This is a good result, indicating low squared errors.' if mse < 100 else '   This is a bad result, indicating high squared errors.'}\n"
        f"3. Root Mean Squared Error (RMSE): The RMSE of {rmse:.2f} provides a measure of the average magnitude of the forecast errors, expressed in the same units as the data (threat events). Lower values indicate better model performance.\n"
        f"{'   This is a good result, indicating low forecast error magnitude.' if rmse < 10 else '   This is a bad result, indicating high forecast error magnitude.'}\n"
    )