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