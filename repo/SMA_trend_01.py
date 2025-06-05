import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname('__file__'), '..')))

base_dir = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

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

    print("------- Quantity Values Manual Ranges ------")
    res_sum = len(selected_parts)
    print('---> Cantidad de valores:', res_sum)
    print(sorted([v for v, _ in selected_parts]))
    print('----------------------------------------------------')
    # print(sorted([v for v, _ in part_1]))
    print('----------------------------------------------------')

    serie = pd.Series([v for v, _ in selected_parts])
    print("📊 Estadísticas para Partes 2 a 5:")
    print(f"- Promedio: {serie.mean():.2f}")
    print(f"- Mediana: {serie.median():.2f}")
    print(f"- Desviación estándar: {serie.std():.2f}")
    print(f"- Rango intercuartílico (IQR): {serie.quantile(0.75) - serie.quantile(0.25):.2f}")
    print(f"- Mínimo: {serie.min()} | Máximo: {serie.max()}")
    print(f"- CV: {serie.std() / serie.mean():.2f}")
    print('----------------------------------------------------')

    # print("🗓️  Fechas, horas, cierre y resultado tras ruptura:")
    streaks_with_info = []
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
    # for val, datetime_str, close, resultado in streaks_with_info:
    #     print(f"{val}, {datetime_str}, Close: {close}, Resultado: {resultado}")

    print("\n📈 Resumen:")
    print(f"Objetivo: {OBJETIVO_DELTA:+} | Limite: {LIMITE_DELTA:+}")
    print("          -------------------------------------")
    print(f"Velas analizadas por evento: {MAX_CANDLES}")
    print(f"Objetivo: {conteo_objetivo}")
    print(f"Limite: {conteo_limite}")
    print(f"Sin resultado: {conteo_sin_resultado}")
    print("-------------------------------------------------------------")

    return (
        [v for v, _ in part_1 + part_2 + part_3 + part_4 + part_5],
        ['Parte 1']*len(part_1) + ['Parte 2']*len(part_2) + ['Parte 3']*len(part_3) + ['Parte 4']*len(part_4) + ['Parte 5']*len(part_5),
        [v for v, _ in selected_parts]
    )

# Ejecución del análisis (asumiendo que df ya está cargado)
df = calculate_above_sma(df)
streaks_info = find_streaks(df)
analyze_manual_ranges(streaks_info)

def get_sma_data():
    return
