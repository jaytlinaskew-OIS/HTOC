import pandas as pd

def convert_to_lower_case(data, column):
    data[column] = data[column].str.lower()
    return data

def convert_to_upper_case(data, column):
    data[column] = data[column].str.upper()
    return data

def remove_whitespace(data, column):
    data[column] = data[column].str.strip()
    return data

def split_column(data, column, delimiter, new_columns):
    """
    Splits a column into multiple columns based on a delimiter.

    Args:
        data (pd.DataFrame): The input DataFrame.
        column (str): The name of the column to split.
        delimiter (str): The delimiter to split the column on.
        new_columns (list): A list of new column names for the split parts.

    Returns:
        pd.DataFrame: The DataFrame with the new columns added.
    """
    splits = data[column].str.split(delimiter, expand=True)
    splits.columns = new_columns
    data = pd.concat([data, splits], axis=1)
    return data