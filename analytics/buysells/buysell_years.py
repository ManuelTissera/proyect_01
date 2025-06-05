import pandas as pd
import numpy as np
import os
import sys

from analytics.buysells.buysell_reversal import find_streak_dates_with_dynamic_validation

# Obtener ruta al dataset
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..')))
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

def get_dynamic_validation_by_year(target_streak=-4, year=None, max_fall=250, min_rise=600, max_candles=200):
    if year is None:
        return {"error": "No year provided"}

    df_filtered = df.copy()
    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
    df_filtered = df_filtered[df_filtered["Date"].dt.year == int(year)]

    if df_filtered.empty:
        return {"error": f"No data found for year {year}"}

    result = find_streak_dates_with_dynamic_validation(
        target_streak,
        max_fall=max_fall,
        min_rise=min_rise,
        max_candles=max_candles,
        start_date=df_filtered["Date"].min().strftime("%Y-%m-%d"),
        end_date=df_filtered["Date"].max().strftime("%Y-%m-%d")
    )

    # Clasificar por trimestre
    quarters = {
        "Q1": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0},
        "Q2": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0},
        "Q3": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0},
        "Q4": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0},
    }

    def get_quarter(date_str):
        month = int(date_str.split("T")[0].split("-")[1])
        if 1 <= month <= 3:
            return "Q1"
        elif 4 <= month <= 6:
            return "Q2"
        elif 7 <= month <= 9:
            return "Q3"
        else:
            return "Q4"

    for row in result["Goals"]:
        q = get_quarter(row["From"])
        quarters[q]["Goals"] += 1

    for row in result["Limit"]:
        q = get_quarter(row["From"])
        quarters[q]["Invalidated"] += 1

    for row in result["No_confirm"]:
        q = get_quarter(row["From"])
        quarters[q]["NoConfirmation"] += 1

    result["ByQuarter"] = quarters

    # Clasificar por mes
    months = {
        f"{i:02d}": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0}
        for i in range(1, 13)
    }

    def get_month(date_str):
        return date_str.split("T")[0].split("-")[1]

    for row in result["Goals"]:
        m = get_month(row["From"])
        months[m]["Goals"] += 1

    for row in result["Limit"]:
        m = get_month(row["From"])
        months[m]["Invalidated"] += 1

    for row in result["No_confirm"]:
        m = get_month(row["From"])
        months[m]["NoConfirmation"] += 1

    result["ByMonth"] = months

    return result


def get_multiple_years_data(target_streak=-4, years=None, max_fall=300, min_rise=600, max_candles=200):
    if not years:
        return {"error": "No years provided"}
    
    results = {}
    for y in years:
        result = get_dynamic_validation_by_year(
            target_streak=target_streak,
            year=y,
            max_fall=max_fall,
            min_rise=min_rise,
            max_candles=max_candles
        )
        results[str(y)] = result

    return results
