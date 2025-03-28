from sklearn.preprocessing import LabelEncoder, StandardScaler
import pandas as pd
import numpy as np

def find_missing_values (data):
    missing_values = data.isnull().sum()
    return missing_values

def drop_missing_values(data):
    data = data.dropna()
    return data

def fill_missing_values(data, value):
    data = data.fillna(value)
    return data

def remove_duplicates(data):
    data = data.drop_duplicates()
    return data

def remove_outliers(data, column, threshold):
    data = data[data[column] < threshold]
    return data

def remove_columns(data, columns):
    data = data.drop(columns, axis=1)
    return data

def convert_to_datetime(data, column):
    data[column] = pd.to_datetime(data[column])
    return data

def convert_to_numeric(data, column):
    data[column] = pd.to_numeric(data[column])
    return data

def convert_to_categorical(data, column):
    data[column] = data[column].astype('category')
    return data

def convert_to_string(data, column):
    data[column] = data[column].astype(str)
    return data

def convert_to_lower_case(data, column):
    data[column] = data[column].str.lower()
    return data

def convert_to_upper_case(data, column):
    data[column] = data[column].str.upper()
    return data

def remove_whitespace(data, column):
    data[column] = data[column].str.strip()
    return data

def replace_characters(data, column, old, new):
    data[column] = data[column].str.replace(old, new)
    return data

def standardize_data(data, column):
    data[column] = (data[column] - data[column].mean()) / data[column].std()
    return data

def normalize_data(data, column):
    data[column] = (data[column] - data[column].min()) / (data[column].max() - data[column].min())
    return data

def log_transform(data, column):
    data[column] = np.log(data[column])
    return data

def one_hot_encode(data, column):
    data = pd.get_dummies(data, columns=[column])
    return data

def label_encode(data, column):
    le = LabelEncoder()
    data[column] = le.fit_transform(data[column])
    return data

def scale_data(data):
    scaler = StandardScaler()
    data = scaler.fit_transform(data)
    return data

def split_data(data, target):
    X = data.drop(target, axis=1)
    y = data[target]
    return X, y

def train_test_split(X, y, test_size):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
    return X_train, X_test, y_train, y_test

def save_data(data, file_path):
    data.to_csv(file_path, index=False)

def split_columns(data, column):
    data = data[column].str.split(',', expand=True)
    return data

