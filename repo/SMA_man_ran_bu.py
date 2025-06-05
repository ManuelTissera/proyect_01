


# ===================================================
# =======  MANUAL RANGE BUCLE =======================
# ===================================================

"""
SMA_man_ran_bu.py

Este script analiza rachas en las que SMA20 está por encima de SMA200, segmentándolas en rangos manuales.
Luego evalúa, para cada racha relevante, el comportamiento posterior del precio:
- Si alcanza un objetivo de precio positivo (OBJETIVO_DELTA)
- Si cae por debajo de un límite negativo (LIMITE_DELTA)
- O si no ocurre ninguno dentro de un máximo de velas (MAX_CANDLES)

Permite ejecutar múltiples escenarios variando esos parámetros para comparar resultados.
"""


import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname('__file__'), '..')))

base_dir = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

# Filtro de fechas
START_DATE = pd.to_datetime("2015-01-01")
END_DATE = pd.to_datetime("2025-01-01")
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
df = df[(df['DateTime'] >= START_DATE) & (df['DateTime'] <= END_DATE)].reset_index(drop=True)

# Parámetros configurables
MAX_CANDLES = 180

# Lista de pruebas (objetivo, límite)
pruebas = [
    (500, -300),
    (400, -150),
    (400, -200),
    (400, -250),
    (500, -150),
    (500, -200),
    (500, -250),
    (600, -200),
    (600, -250),
    (600, -300),
    (700, -250),
    (700, -300),
    (700, -350), 
]

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
                end_indices.append(i)
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

    resultados_finales = []
    for OBJETIVO_DELTA, LIMITE_DELTA in pruebas:
        conteo_objetivo = 0
        conteo_limite = 0
        conteo_sin_resultado = 0

        for val, idx in selected_parts:
            if idx < len(df):
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

        resultados_finales.append({
            "Objetivo": f"{OBJETIVO_DELTA:.2f}",
            "Limite": f"{LIMITE_DELTA:.2f}",
            "Obj-Alcan": conteo_objetivo,
            "Limit-Alca": conteo_limite,
            "Sin Resultados": conteo_sin_resultado
        })

    print("Objetivo\tLimite\t\tObj-Alcan\tLimit-Alca\tSin Resultados")
    for r in resultados_finales:
        print(f"{r['Objetivo']}\t\t{r['Limite']}\t\t{r['Obj-Alcan']}\t\t{r['Limit-Alca']}\t\t{r['Sin Resultados']}")

    return (
        [v for v, _ in part_1 + part_2 + part_3 + part_4 + part_5],
        ['Parte 1']*len(part_1) + ['Parte 2']*len(part_2) + ['Parte 3']*len(part_3) + ['Parte 4']*len(part_4) + ['Parte 5']*len(part_5),
        [v for v, _ in selected_parts]
    )

# Ejecución del análisis

df = calculate_above_sma(df)
streaks_info = find_streaks(df)
analyze_manual_ranges(streaks_info)

def get_sma_data():
    return
