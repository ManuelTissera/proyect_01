

from collections import Counter

import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import os
import sys

import matplotlib.pyplot as plt
from scipy.stats import shapiro

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

base_dir = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

print("funcion buysell")

datatrend = df[["Date", "Trend"]].to_dict(orient="records")

def get_buysell():
    return datatrend

def get_trend_streaks():
    trend_list = df["Trend"].tolist()
    streaks_trend = []

    if not trend_list:
        return streaks_trend

    count = 1
    prev_positive = trend_list[0] >= 0

    for current, next_value in zip(trend_list, trend_list[1:] + [None]):
        if next_value is None:
            streaks_trend.append(count if prev_positive else -count)
            break

        current_positive = next_value >= 0

        if current_positive == prev_positive:
            count += 1
        else:
            streaks_trend.append(count if prev_positive else -count)
            count = 1
            prev_positive = current_positive

    return streaks_trend

streak = get_trend_streaks()

# -------  CALCULO DE APERTURA Y CIERRE DE RACHA CON SMA20 Y SMA200


def find_streak_info(target_streak):
    trend_list = df["Trend"].tolist()
    date_list = df["Date"].tolist()
    open_list = df["Open"].tolist()
    close_list = df["Close"].tolist()
    diff_20_list = df["Diff-20"].tolist()
    diff_200_list = df["Diff-200"].tolist()

    streak_info = []

    count = 1
    start_index = 0
    prev_positive = trend_list[0] >= 0

    # Para los resúmenes
    start_counts = {
        "Arriba | Arriba": 0,
        "Abajo | Abajo": 0,
        "Arriba | Abajo": 0,
        "Abajo | Arriba": 0,
    }
    finish_counts = {
        "Arriba | Arriba": 0,
        "Abajo | Abajo": 0,
        "Arriba | Abajo": 0,
        "Abajo | Arriba": 0,
    }

    for i, (current, next_value) in enumerate(zip(trend_list, trend_list[1:] + [None])):
        if next_value is None:
            streak = count if prev_positive else -count
            if streak == target_streak:
                start_date = date_list[start_index]
                end_date = date_list[i]
                open_value = open_list[start_index]
                close_value = close_list[i]
                diff20_open = diff_20_list[start_index]
                diff200_open = diff_200_list[start_index]
                diff20_close = diff_20_list[i]
                diff200_close = diff_200_list[i]

                status_start_20 = "Abajo" if diff20_open < 0 else "Arriba"
                status_start_200 = "Abajo" if diff200_open < 0 else "Arriba"
                status_finish_20 = "Abajo" if diff20_close < 0 else "Arriba"
                status_finish_200 = "Abajo" if diff200_close < 0 else "Arriba"

                start_combination = f"{status_start_20} | {status_start_200}"
                finish_combination = f"{status_finish_20} | {status_finish_200}"

                start_counts[start_combination] += 1
                finish_counts[finish_combination] += 1

                streak_info.append((start_date, end_date, open_value, close_value,
                                    diff20_open, diff200_open, diff20_close, diff200_close,
                                    status_start_20, status_start_200, status_finish_20, status_finish_200))
            break

        current_positive = next_value >= 0

        if current_positive == prev_positive:
            count += 1
        else:
            streak = count if prev_positive else -count
            if streak == target_streak:
                start_date = date_list[start_index]
                end_date = date_list[i]
                open_value = open_list[start_index]
                close_value = close_list[i]
                diff20_open = diff_20_list[start_index]
                diff200_open = diff_200_list[start_index]
                diff20_close = diff_20_list[i]
                diff200_close = diff_200_list[i]

                status_start_20 = "Abajo" if diff20_open < 0 else "Arriba"
                status_start_200 = "Abajo" if diff200_open < 0 else "Arriba"
                status_finish_20 = "Abajo" if diff20_close < 0 else "Arriba"
                status_finish_200 = "Abajo" if diff200_close < 0 else "Arriba"

                start_combination = f"{status_start_20} | {status_start_200}"
                finish_combination = f"{status_finish_20} | {status_finish_200}"

                start_counts[start_combination] += 1
                finish_counts[finish_combination] += 1

                streak_info.append((start_date, end_date, open_value, close_value,
                                    diff20_open, diff200_open, diff20_close, diff200_close,
                                    status_start_20, status_start_200, status_finish_20, status_finish_200))
            start_index = i + 1
            count = 1
            prev_positive = current_positive

    if not streak_info:
        print(f"No se encontraron rachas de {target_streak}.")
    else:
        for (start, end, open_v, close_v,
             diff20_o, diff200_o, diff20_c, diff200_c,
             status_start_20, status_start_200, status_finish_20, status_finish_200) in streak_info:
            print(f"From: {start} - To: {end} - Open: {open_v} - Close: {close_v} - Start: [{status_start_20} | {status_start_200}] - Finish: [{status_finish_20} | {status_finish_200}]")

    # Resumenes
    print("-------------------------------------------------")
    print("Resumen de posición de Open respecto a SMA:")
    for key, value in start_counts.items():
        print(f"{key}: {value}")
    print("-------------------------------------------------")
    print("Resumen de posición de Close respecto a SMA:")
    for key, value in finish_counts.items():
        print(f"{key}: {value}")
    print("-------------------------------------------------")

    return streak_info

# Ejemplo de uso:
find_streak_info(-4)