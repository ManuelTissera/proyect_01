import pandas as pd

def skewness(series: pd.Series):
    return series.skew()

def kurtosis(series: pd.Series):
    return series.kurt()
