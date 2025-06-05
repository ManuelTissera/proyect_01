
import pandas as pd
import numpy as np
import os
import sys

import matplotlib.pyplot as plt
from scipy.stats import shapiro

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..')))

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")

df = pd.read_csv(file_path)

datatrend = df[["Date", "Trend"]].to_dict(orient="records")

target_str = -4

def find_streak_dates_with_dynamic_validation(target_streak, max_fall=250, min_rise=600, max_candles=200, start_date=None, end_date=None):
    df_filtered = df.copy()

    if start_date:
        df_filtered = df_filtered[df_filtered["Date"] >= start_date]
    if end_date:
        df_filtered = df_filtered[df_filtered["Date"] <= end_date]

    trend_list = df_filtered["Trend"].tolist()
    dates_list = df_filtered["DateTimeStr"].tolist()
    opens_list = df_filtered["Open"].tolist()
    closes_list = df_filtered["Close"].tolist()
    lows_list = df_filtered["Low"].tolist()
    highs_list = df_filtered["High"].tolist()

    objetivos = []
    limit = []
    no_confirmation_list = []

    if not trend_list:
        return {"Objetivos": objetivos, "Limit": limit, "No confirmation": no_confirmation_list}

    count = 1
    start_index = 0
    prev_positive = trend_list[0] >= 0

    for i, (current, next_value) in enumerate(zip(trend_list, trend_list[1:] + [None])):
        if next_value is None:
            streak = count if prev_positive else -count
            if streak == target_streak:
                start_date = dates_list[start_index]
                end_date = dates_list[i]
                open_price = opens_list[start_index]
                close_price = closes_list[i]
                validation = validate_dynamic_reversal(i, close_price, lows_list, highs_list, max_fall, min_rise, max_candles)
                result = {
                    "From": start_date,
                    "To": end_date,
                    "Open": open_price,
                    "Close": close_price,
                    "Result": validation
                }
                if "Confirmed" in validation:
                    objetivos.append(result)
                elif "Invalidated" in validation:
                    limit.append(result)
                else:
                    no_confirmation_list.append(result)
            break

        current_positive = next_value >= 0

        if current_positive == prev_positive:
            count += 1
        else:
            streak = count if prev_positive else -count
            if streak == target_streak:
                start_date = dates_list[start_index]
                end_date = dates_list[i]
                open_price = opens_list[start_index]
                close_price = closes_list[i]
                validation = validate_dynamic_reversal(i, close_price, lows_list, highs_list, max_fall, min_rise, max_candles)
                result = {
                    "From": start_date,
                    "To": end_date,
                    "Open": open_price,
                    "Close": close_price,
                    "Result": validation
                }
                if "Confirmed" in validation:
                    objetivos.append(result)
                elif "Invalidated" in validation:
                    limit.append(result)
                else:
                    no_confirmation_list.append(result)
            start_index = i + 1
            count = 1
            prev_positive = current_positive

    return {
        "max_fall":max_fall,
        "min_rise":min_rise,
        "max_candles":max_candles,
        "Targ_str":target_str,
        "Goals": objetivos,
        "Limit": limit,
        "No_confirm": no_confirmation_list
    }


def validate_dynamic_reversal(end_index, close_price, lows_list, highs_list, max_fall, min_rise, max_candles):
    stop_loss_level = close_price - max_fall
    target_level = close_price + min_rise

    future_lows = lows_list[end_index + 1:end_index + 1 + max_candles]
    future_highs = highs_list[end_index + 1:end_index + 1 + max_candles]

    for idx, (low, high) in enumerate(zip(future_lows, future_highs), start=1):
        if low <= stop_loss_level:
            return f"Invalidated"
            # return f"❌ Invalidated after {idx} candles (Low {low} ≤ Stop {stop_loss_level})"
        if high >= target_level:
            return f"Confirmed"
            # return f"✅ Confirmed after {idx} candles (High {high} ≥ Target {target_level})"

    return f"No confirmation"
    #return f"❓ No confirmation after {max_candles} candles"


def get_buysell_reversal(start_date=None, end_date=None, max_fall=250, min_rise=500, max_candles=50):
    return find_streak_dates_with_dynamic_validation(
        target_streak=target_str,
        max_fall=max_fall,
        min_rise=min_rise,
        max_candles=max_candles,
        start_date=start_date,
        end_date=end_date
    )



# ----- EL FIND DE BUSCAR TENDECIAS CONTRARIA ----



# 🧩 Función principal: find_streak_dates_with_dynamic_validation(...)
# Entrada:

#    target_streak: número de velas consecutivas con misma dirección (positivo o negativo).
#    max_fall: caída máxima tolerable desde el cierre antes de considerar que se invalidó el giro.
#    min_rise: suba mínima necesaria para confirmar el giro.
#    max_candles: cuántas velas se observan después de la racha para validar.
#    
#    Qué hace:
#    
#    Recorre la columna Trend buscando rachas consecutivas del mismo signo.
#    Cuando encuentra una racha de longitud igual a target_streak, guarda los datos: fecha de inicio, fin, precio de apertura y cierre.
#    Llama a validate_dynamic_reversal(...) para ver si en las siguientes velas el precio se movió lo suficiente como para confirmar o invalidar un cambio de tendencia.

# 🧪 Función secundaria: validate_dynamic_reversal(...)
# Entrada:

#    end_index: índice final de la racha encontrada.
#    close_price: precio de cierre en ese punto.
#    lows_list y highs_list: para revisar los precios futuros.
#    max_fall, min_rise, max_candles: parámetros de validación.
#    
#    Qué hace:
#    
#    Calcula un stop loss (close_price - max_fall) y un target (close_price + min_rise).
#    Mira vela por vela en el futuro inmediato (hasta max_candles) para ver si:
#    El precio baja al nivel del stop → ❌ Invalidado.
#    El precio sube al nivel del target → ✅ Confirmado.
#    Si no pasa ninguna de las dos cosas → ❓ Sin confirmación.

# 📤 Salida
# Una lista con tuplas de cada racha encontrada: (start_date, end_date, open_price, close_price, validation).
#   Y un resumen final:
#   Cuántas rachas se confirmaron.
#   Cuántas se invalidaron.
#   Cuántas no se definieron.




