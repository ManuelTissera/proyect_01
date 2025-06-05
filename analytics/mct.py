import pandas as pd
import numpy as np
import os
import sys

# Agregar stat_analysis al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from view_flask import descriptive  # Cambiá si usás otro módulo

def safe_float(value):
    try:
        value = float(value)
        if pd.isna(value) or np.isnan(value):
            return None
        return value
    except:
        return None

def get_data_mct():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    grouped = df.groupby(df["Date"].dt.date)
    print('Se ve bien')

    mct_res = []

    for day, group in grouped:
        close = group["Close"]
        print(f"{day} -- Variance {descriptive.variance(close)}")
        print('Aca es')
        mct_res.append({
            "Date": str(day),
            "Mean": safe_float(descriptive.mean(close)),
            "Median": safe_float(descriptive.median(close)),
            "Moda": safe_float(descriptive.mode(close)),
            "Variance": safe_float(descriptive.variance(close)),
            "Std. Dev.": safe_float(descriptive.std_deviation(close)),
            "Range Val.": safe_float(descriptive.range_value(close)),
            "Coef. Var": safe_float(descriptive.coefficient_of_variation(close)),
        })

    return mct_res
