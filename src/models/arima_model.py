import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults 
from sklearn.metrics import mean_squared_error
import joblib

def build_arima_model(train_data, order):
    model = ARIMA(train_data, order=order)
    return model

def fit_arima_model(model):
    model_fit = model.fit()
    return model_fit

def make_arima_forecast(model_fit, start, end):
    forecast = model_fit.predict(start=start, end=end)
    return forecast

def plot_arima_forecast(train_data, test_data, forecast, title, x_label, y_label):
    plt.figure(figsize=(10, 6))
    plt.plot(train_data, color='skyblue')
    plt.plot(test_data, color='green')
    plt.plot(forecast, color='red')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()
    
def evaluate_arima_model(test_data, forecast):
    rmse = np.sqrt(mean_squared_error(test_data, forecast))
    return rmse

def save_arima_model(model_fit, file_path):
    model_fit.save(file_path)

def load_arima_model(file_path):
    model_fit = ARIMAResults.load(file_path)
    return model_fit

def save_arima_forecast(forecast, file_path):
    forecast.to_csv(file_path)
    
def load_arima_forecast(file_path):
    forecast = pd.read_csv(file_path)
    return forecast

def save_plot(plt, file_path):
    plt.savefig(file_path)
    
def load_plot(file_path):
    plt = plt.imread(file_path)
    return plt

def save_model(model, file_path):
    joblib.dump(model, file_path)
    