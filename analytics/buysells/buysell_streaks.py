from collections import Counter

import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import os
import sys

import matplotlib.pyplot as plt
from scipy.stats import shapiro

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

datatrend = df[["Date", "Trend"]].to_dict(orient="records")


# ----------------------------------------------------------------------------------------------------------------------------
'''
 Esta función analiza la columna "Trend" del DataFrame y calcula la longitud de cada racha
 continua de valores positivos o negativos. Las rachas positivas se representan con números positivos,
 y las negativas con números negativos. Devuelve una lista con las longitudes de estas rachas.
'''

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

# ----------------------------------------------------------------------------------------------------------------------------
'''
Esta función recibe una lista de rachas (números positivos y negativos).
Calcula y devuelve el promedio de las rachas positivas y el promedio de las negativas (en valor absoluto).
Si no hay rachas de un tipo, su promedio será 0.
'''

def get_streaks_average(streaks):
    positives = [s for s in streaks if s > 0]
    negatives = [abs(s) for s in streaks if s < 0]

    avg_positive = sum(positives) / len(positives) if positives else 0
    avg_negative = sum(negatives) / len(negatives) if negatives else 0

    return avg_positive, avg_negative

avg_pos, avg_neg = get_streaks_average(streak)


def plot_streaks_freq(streaks):
    frequency = Counter(streaks)

    streak = list(frequency.keys())
    counts = list(frequency.values())

    plt.figure(figsize=(10, 6))
    plt.bar(streak,counts)
    plt.xlabel("Streaks (positve y negative)")
    plt.ylabel('Frequency')
    plt.title("Frequency Streaks of Trends")
    plt.grid(True)
    plt.show()

# ----------------------------------------------------------------------------------------------------------------------------
'''
Esta función toma una lista de rachas (positivas o negativas).
Calcula cuántas veces aparece cada longitud (en valor absoluto) y devuelve un diccionario con esa distribución.
El resultado está ordenado por longitud de menor a mayor.
'''

def get_streaks_distribution(streaks):
    lengths = [abs(s) for s in streaks]  # Tomamos tamaño, sin importar signo
    distribution = Counter(lengths)
    return dict(sorted(distribution.items()))


# -----------------------------------------------------------------------------------------------------------------------------
'''
Esta función cuenta cuántas rachas positivas y negativas son mayores o iguales a una longitud mínima (por defecto 4).
Devuelve una tupla con la cantidad de rachas largas positivas y negativas.
'''

def count_long_streaks(streaks, min_length=4):
    positive_long = sum(1 for s in streaks if s > 0 and s >= min_length)
    negative_long = sum(1 for s in streaks if s < 0 and abs(s) >= min_length)

    return positive_long, negative_long

pos_long_streak, neg_long_streak = count_long_streaks(streak)

# -----------------------------------------------------------------------------------------------------------------------------
'''
Esta función busca todas las veces que ocurre una racha específica (`target_streak`) en la lista `streaks`
y guarda la duración absoluta de la racha siguiente como indicativo de reversión.
Devuelve una lista con esas duraciones de reversión posteriores.
'''

def analyze_reversal_after_streak(streaks, target_streak):
    reversals = []

    for i in range(len(streaks) - 1):
        current = streaks[i]
        next_streak = streaks[i + 1]

        if current == target_streak:
            reversals.append(abs(next_streak))  # Medimos cuánto dura la reversión

    return reversals


# -----------------------------------------------------------------------------------------------------------------------------
'''
Esta función toma una lista de duraciones de reversiones (`reversals`)
y calcula el promedio de esas duraciones.
Si la lista está vacía, devuelve 0.
'''

def summarize_reversals(reversals):
    if not reversals:
        return 0
    return sum(reversals) / len(reversals)


# -----------------------------------------------------------------------------------------------------------------------------
# Esta función clasifica las duraciones de reversiones (`reversals`) en cuatro categorías:
# - Menores a 3
# - Iguales a 3
# - Mayores a 3
# - Mayores a 2
# Devuelve el porcentaje de cada categoría respecto al total.
# Si no hay reversiones, devuelve cuatro ceros.

def classify_reversal_durations(reversals):
    less_than_3 = sum(1 for r in reversals if r < 3)
    equal_to_3 = sum(1 for r in reversals if r == 3)
    greater_than_3 = sum(1 for r in reversals if r > 3)
    greater_than_2 = sum(1 for r in reversals if r > 2)
    total = len(reversals)
    if total == 0:
        return 0, 0, 0, 0
    return (less_than_3 / total) * 100, (equal_to_3 / total) * 100, (greater_than_3 / total) * 100, (greater_than_2 / total) * 100

# print('Funciona buysell streaks')

def get_buysell_streak():
    return {
        "streak":streak,
        "avg_pos":avg_pos,
        "avg_neg":avg_neg,
        "pos_long_streak":pos_long_streak, 
        "neg_long_streak":neg_long_streak
        
    }

# -------  CALCULO DE FRECUENCIA DE RACHAS

# print("-------------------------------------------------")
# print("------------------------------------")




# print("-------------------------------------------------")

# ==========================================================

# streaks_distribution = get_streaks_distribution(streak)

# for length, count in streaks_distribution.items():
#     print(f"Rachas de {length}: {count} veces - {(count / len(streak))*100}")

# avg_pos, avg_neg = get_streaks_average(streak)

# print(f"Promedio de duración positiva: {avg_pos:.2f}")
# print(f"Promedio de duración negativa: {avg_neg:.2f}")

# print("-------------------------------------------------")

# #----------------------------------------------------------------

# pos_long, neg_long = count_long_streaks(streak)

# print(f"Cantidad de rachas positivas largas (≥4): {pos_long}")
# print(f"Cantidad de rachas negativas largas (≥4): {neg_long}")

# print("-------------------------------------------------")

# # -------------------------------------------------------------

# # Ejemplo de uso para +4
# for target in range(4, 11):
#     reversals_after_plus = analyze_reversal_after_streak(streak, target)
#     avg_reversal_plus = summarize_reversals(reversals_after_plus)
#     print(f"Promedio de duración de la reversión después de +{target}: {avg_reversal_plus:.2f}")

#     reversals_after_minus = analyze_reversal_after_streak(streak, -target)
#     avg_reversal_minus = summarize_reversals(reversals_after_minus)
#     print(f"Promedio de duración de la reversión después de -{target}: {avg_reversal_minus:.2f}")

# print("-------------------------------------------------")

# # -------------------------------------------------------------

# for target in range(4, 11):
#     for direction in [1, -1]:
#         reversals = analyze_reversal_after_streak(streak, direction * target)
#         pct_less3, pct_equal3, pct_greater3, pct_greater2 = classify_reversal_durations(reversals)
#         print(f"Reversión después de {direction * target}: <3 = {pct_less3:.2f}%, =3 = {pct_equal3:.2f}%, >3 = {pct_greater3:.2f}%, >2 = {pct_greater2:.2f}%")
# print("-------------------------------------------------")

# # -------------------------------------------------------------










# ========= POSIBLES CALCULOS SOBRE STREAKS =========
# Frecuencia de rachas: cuántas veces hay rachas de +1, +2, -1, -2, etc.

# Promedio de duración: cuánto duran en promedio las rachas positivas y las negativas.

# Máxima racha positiva/negativa: la racha más larga hacia arriba y hacia abajo.

# Secuencias repetidas: ver si ciertos patrones de rachas se repiten (por ejemplo: +3 seguido de -1 varias veces).

# Frecuencia de cada racha

# Relación entre rachas: después de una racha muy positiva, ¿suele venir una negativa fuerte?

