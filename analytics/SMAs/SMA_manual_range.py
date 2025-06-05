import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname('__file__'), '..')))

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

# Filtro de fechas
START_DATE = pd.to_datetime("2015-01-01")
END_DATE = pd.to_datetime("2025-01-01")
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
df = df[(df['DateTime'] >= START_DATE) & (df['DateTime'] <= END_DATE)].reset_index(drop=True)

# Parámetros configurables
OBJETIVO_DELTA = 500
LIMITE_DELTA = -250
MAX_CANDLES = 200


def calculate_above_sma(df):
    df['Above_SMA'] = df['SMA20'] > df['SMA200']
    return df


def find_streaks(df):
    streaks = []
    end_indices = []
    current_streak = 0
    for i, value in enumerate(df['Above_SMA']):
        if value:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
                end_indices.append(i)  # donde se rompe la condición
                current_streak = 0
    if current_streak > 0:
        streaks.append(current_streak)
        end_indices.append(len(df))
    return streaks, end_indices


def analyze_manual_ranges(streaks_with_indices):
    streaks, end_indices = streaks_with_indices
    max_streak = max(streaks)
    p1 = max_streak / 5
    p2 = max_streak * 2 / 5
    p3 = max_streak * 3 / 5
    p4 = max_streak * 4 / 5

    part_1, part_2, part_3, part_4, part_5 = [], [], [], [], []

    for value, idx in zip(streaks, end_indices):
        if value <= p1:
            part_1.append((value, idx))
        elif p1 < value <= p2:
            part_2.append((value, idx))
        elif p2 < value <= p3:
            part_3.append((value, idx))
        elif p3 < value <= p4:
            part_4.append((value, idx))
        else:
            part_5.append((value, idx))

    selected_parts = part_2 + part_3 + part_4 + part_5

    serie = pd.Series([v for v, _ in selected_parts])

    streaks_with_info = []
    list_obj = []
    list_lim = []
    conteo_objetivo = 0
    conteo_limite = 0
    conteo_sin_resultado = 0

    for val, idx in selected_parts:
        if idx < len(df):
            fecha = df.loc[idx, 'Date']
            hora = df.loc[idx, 'Time']
            close = df.loc[idx, 'Close']
            objetivo = close + OBJETIVO_DELTA
            limite = close + LIMITE_DELTA
            resultado = "Sin resultado"

            future_lows = df['Low'].iloc[idx+1:idx+1+MAX_CANDLES].tolist()
            future_highs = df['High'].iloc[idx+1:idx+1+MAX_CANDLES].tolist()

            for low, high in zip(future_lows, future_highs):
                if low <= limite:
                    resultado = "Limite"
                    conteo_limite += 1
                    break
                if high >= objetivo:
                    resultado = "Objetivo"
                    conteo_objetivo += 1
                    break
            else:
                conteo_sin_resultado += 1

            streaks_with_info.append((val, f"{fecha} {hora}", close, resultado))

    streaks_with_info.sort(key=lambda x: pd.to_datetime(x[1]))

    for val, datetime_str, close, resultado in streaks_with_info:
        if resultado in ["Objetivo", "Limite"]:
            idx = df[(df['Date'] + ' ' + df['Time']) == datetime_str].index[0]
            sma200 = df.loc[idx, 'SMA200']
            diff_sma200_close = close - sma200
            data = {"Val": val, "Date": datetime_str, "Close": close, "ΔSMA200": diff_sma200_close, "Resultado": resultado}
            if resultado == "Objetivo":
                list_obj.append(data)
            elif resultado == "Limite":
                list_lim.append(data)

    delta_obj_values = [item['ΔSMA200'] for item in list_obj]
    delta_lim_values = [item['ΔSMA200'] for item in list_lim]

    stats_obj = pd.Series(delta_obj_values).describe()
    stats_obj['cv'] = stats_obj['std'] / stats_obj['mean']
    stats_obj['median'] = pd.Series(delta_obj_values).median()

    stats_lim = pd.Series(delta_lim_values).describe()
    stats_lim['cv'] = stats_lim['std'] / stats_lim['mean']
    stats_lim['median'] = pd.Series(delta_lim_values).median()

    return delta_obj_values, delta_lim_values, stats_obj, stats_lim, list_obj, list_lim


def plot_sma200_distributions(list_obj, list_lim, stats_obj, stats_lim):
    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    obj_values = [item['ΔSMA200'] for item in list_obj]
    lim_values = [item['ΔSMA200'] for item in list_lim]

    axs[0].scatter(range(len(obj_values)), obj_values, label='ΔSMA200 Objetivo', color='blue')
    axs[0].axhline(stats_obj['mean'], color='green', linestyle='-', label='Promedio')
    axs[0].axhline(stats_obj['mean'] + stats_obj['std'], color='green', linestyle='--', label='+1 Desv')
    axs[0].axhline(stats_obj['mean'] - stats_obj['std'], color='green', linestyle='--', label='-1 Desv')
    axs[0].axhline(stats_obj['75%'], color='orange', linestyle=':', label='Q3')
    axs[0].axhline(stats_obj['25%'], color='orange', linestyle=':', label='Q1')
    axs[0].set_title('ΔSMA200 - Objetivo')
    axs[0].legend()

    axs[1].scatter(range(len(lim_values)), lim_values, label='ΔSMA200 Limite', color='red')
    axs[1].axhline(stats_lim['mean'], color='green', linestyle='-', label='Promedio')
    axs[1].axhline(stats_lim['mean'] + stats_lim['std'], color='green', linestyle='--', label='+1 Desv')
    axs[1].axhline(stats_lim['mean'] - stats_lim['std'], color='green', linestyle='--', label='-1 Desv')
    axs[1].axhline(stats_lim['75%'], color='orange', linestyle=':', label='Q3')
    axs[1].axhline(stats_lim['25%'], color='orange', linestyle=':', label='Q1')
    axs[1].set_title('ΔSMA200 - Limite')
    axs[1].legend()

    plt.tight_layout()
    plt.show()


def plot_obj_with_lim_overlay(list_obj, list_lim, stats_obj):
    fig, ax = plt.subplots(figsize=(12, 6))

    obj_values = [item['ΔSMA200'] for item in list_obj]
    lim_values = [item['ΔSMA200'] for item in list_lim]

    ax.scatter(range(len(obj_values)), obj_values, label='ΔSMA200 Objetivo', color='blue')
    ax.scatter(range(len(lim_values)), lim_values, label='ΔSMA200 Limite', color='red')

    ax.axhline(stats_obj['mean'], color='green', linestyle='-', label='Promedio')
    ax.axhline(stats_obj['mean'] + stats_obj['std'], color='green', linestyle='--', label='+1 Desv')
    ax.axhline(stats_obj['mean'] - stats_obj['std'], color='green', linestyle='--', label='-1 Desv')
    ax.axhline(stats_obj['75%'], color='orange', linestyle=':', label='Q3')
    ax.axhline(stats_obj['25%'], color='orange', linestyle=':', label='Q1')

    ax.set_title('ΔSMA200 - Objetivo + Limite (overlay)')
    ax.legend()
    plt.tight_layout()
    plt.show()


df = calculate_above_sma(df)
streaks_info = find_streaks(df)
delta_obj_values, delta_lim_values, stats_obj, stats_lim, list_obj, list_lim = analyze_manual_ranges(streaks_info)


# plot_sma200_distributions(list_obj, list_lim, stats_obj, stats_lim)
# plot_obj_with_lim_overlay(list_obj, list_lim, stats_obj)

def get_sma_manual_range():
    stats_obj_clean = {k: float(round(v, 4)) for k, v in stats_obj.items()}
    stats_lim_clean = {k: float(round(v, 4)) for k, v in stats_lim.items()}

    def clean_list(data):
        return [
            {
                "Val": int(item["Val"]),
                "Date": str(item["Date"]),
                "Close": float(item["Close"]),
                "ΔSMA200": float(item["ΔSMA200"]),
                "Resultado": str(item["Resultado"])
            }
            for item in data
        ]

    return {
        "delta_obj_values": list(map(float, delta_obj_values)),
        "delta_lim_values": list(map(float, delta_lim_values)),
        "stats_obj": stats_obj_clean,
        "stats_lim": stats_lim_clean,
        "list_obj": clean_list(list_obj),
        "list_lim": clean_list(list_lim)
    }

