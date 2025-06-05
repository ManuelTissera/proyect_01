import pandas as pd

def variance(series: pd.Series):
    return series.var()

def std_deviation(series: pd.Series):
    return series.std()

def range_value(series: pd.Series):
    return series.max() - series.min()

def coefficient_of_variation(series: pd.Series):
    mean = series.mean()
    return series.std() / mean if mean != 0 else None
