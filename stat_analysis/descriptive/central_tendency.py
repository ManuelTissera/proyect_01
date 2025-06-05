import pandas as pd

def mean(series: pd.Series):
    return series.mean()

def median(series: pd.Series):
    return series.median()

def mode(series: pd.Series):
    return series.mode().iloc[0] if not series.mode().empty else None
