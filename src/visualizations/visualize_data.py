import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def create_histogram(data, column_name, title, x_label, y_label, bins=10):
    """
    Create a histogram of the data.
    
    :param data: DataFrame
    :param column_name: str
    :param title: str
    :param x_label: str
    :param y_label: str
    :param bins: int
    """
    plt.figure(figsize=(10, 6))
    plt.hist(data[column_name], bins=bins, color='skyblue', edgecolor='black')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()
    
def create_boxplot(data, x_column, y_column, title, x_label, y_label):
    """
    Create a boxplot of the data.
    
    :param data: DataFrame
    :param x_column: str
    :param y_column: str
    :param title: str
    :param x_label: str
    :param y_label: str
    """
    plt.figure(figsize=(10, 6))
    sns.boxplot(x=x_column, y=y_column, data=data)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()
    
def create_scatterplot(data, x_column, y_column, title, x_label, y_label):
    """
    Create a scatterplot of the data.
    
    :param data: DataFrame
    :param x_column: str
    :param y_column: str
    :param title: str
    :param x_label: str
    :param y_label: str
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(data[x_column], data[y_column], color='skyblue')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()

def create_lineplot(data, x_column, y_column, title, x_label, y_label):
    """
    Create a lineplot of the data.
    
    :param data: DataFrame
    :param x_column: str
    :param y_column: str
    :param title: str
    :param x_label: str
    :param y_label: str
    """
    plt.figure(figsize=(10, 6))
    plt.plot(data[x_column], data[y_column], color='skyblue')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()
    
def create_heatmap(data, title):
    """
    Create a heatmap of the data.
    
    :param data: DataFrame
    :param title: str
    """
    plt.figure(figsize=(10, 6))
    sns.heatmap(data.corr(), annot=True, cmap='coolwarm')
    plt.title(title)
    plt.show()

def create_pairplot(data, title):
    """
    Create a pairplot of the data.
    
    :param data: DataFrame
    :param title: str
    """
    plt.figure(figsize=(10, 6))
    sns.pairplot(data)
    plt.title(title)
    plt.show()

def create_barplot(data, x_column, y_column, title, x_label, y_label):
    """
    Create a barplot of the data.
    
    :param data: DataFrame
    :param x_column: str
    :param y_column: str
    :param title: str
    :param x_label: str
    :param y_label: str
    """
    plt.figure(figsize=(10, 6))
    sns.barplot(x=x_column, y=y_column, data=data)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()

def create_countplot(data, column, title, x_label, y_label):
    """
    Create a countplot of the data.
    
    :param data: DataFrame
    :param column: str
    :param title: str
    :param x_label: str
    :param y_label: str
    """
    plt.figure(figsize=(10, 6))
    sns.countplot(x=column, data=data)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()
    
def create_piechart(data, column, title):
    """
    Create a pie chart of the data.
    
    :param data: DataFrame
    :param column: str
    :param title: str
    """
    plt.figure(figsize=(10, 6))
    data[column].value_counts().plot.pie(autopct='%1.1f%%')
    plt.title(title)
    plt.show()
    
def create_correration_matrix(data, title):
    """
    Create a correlation matrix of the data.
    
    :param data: DataFrame
    :param title: str
    """
    plt.figure(figsize=(10, 6))
    sns.heatmap(data.corr(), annot=True, cmap='coolwarm')
    plt.title(title)
    plt.show()

def create_scatter_matrix(data, title):
    """
    Create a scatter matrix of the data.
    
    :param data: DataFrame
    :param title: str
    """
    plt.figure(figsize=(10, 6))
    pd.plotting.scatter_matrix(data, figsize=(10, 6))
    plt.title(title)
    plt.show()
    