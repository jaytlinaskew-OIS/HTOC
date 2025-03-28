import pandas as pd

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