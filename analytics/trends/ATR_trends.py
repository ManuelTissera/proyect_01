

import os
import numpy as np
import pandas as pd
from scipy.stats import shapiro

# ---------------------------------------------------------------------------
# 1.  Cargar y filtrar tu dataset EXACTAMENTE como lo hacías
# ---------------------------------------------------------------------------
base_dir  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")
df = pd.read_csv(file_path)

start_year = 2018
end_year   = 2025
df["Date"] = pd.to_datetime(df["Date"])
df["DateTime"] = pd.to_datetime(df["DateTime"])  # ← esta línea es la que te falta

df = (
    df[
        (df["Date"].dt.year >= start_year) &
        (df["Date"].dt.year <= end_year) 
        & (df["DateTime"].dt.time >= pd.to_datetime("10:00:00").time())
    ].reset_index(drop=True)
)


def get_trend_and_diff_data(
        *,
        window: int = 5,
        min_profit: float = 0.01,
        limit_loss: float = -0.01,
        max_candles: int = 80,
        val_limit_trend: float = 0.7
    ):
    """
    Devuelve `streak_list` sin solapamientos y con ATR_coeff := |Close-BB_Lower| / ATR
    Prioridad (para conservar al depurar): Objective > Limit > NoResult
    El DataFrame global debe existir como `df`.
    """
    # ──────────────────────────── 0. seguridad ─────────────────────────────
    if "df" not in globals():
        raise RuntimeError("El DataFrame global 'df' no existe")

    data = df.copy()

    # ────────────────────── 1. columnas auxiliares ─────────────────────────
    if "Diff_BBLower" not in data.columns:
        data["Diff_BBLower"] = ((data["Close"] - data["BB_Lower"]) / data["Close"]) * 100

    if "TrendPct_N" not in data.columns:
        trend_sum   = data["Trend"].rolling(window=window).sum()
        close_start = data["Close"].shift(window - 1)
        data["TrendPct_N"] = (trend_sum / close_start) * 100

    streaks_raw = []                          # ← intentos preliminares
    last_idx    = len(data) - 1

    # ─────────────────── 2. barrido de todos los start_event ───────────────
    for i in range(last_idx - max_candles):
        row = data.iloc[i]

        # regla de start_event
        if row["TrendPct_N"] < -0.75 and row["Diff_BBLower"] < 3.0:

            start_event_idx   = i
            start_event_close = row["Close"]
            target_price      = start_event_close * (1 + min_profit)
            stop_price        = start_event_close * (1 + limit_loss)

            cumulative_trend  = 0.0
            profit_hit        = False
            result            = "NoResult"
            end_idx           = None

            # ventana de evaluación
            for j in range(1, max_candles + 1):
                idx = start_event_idx + j
                if idx > last_idx:
                    break

                r = data.iloc[idx]
                price = r["Close"]
                cumulative_trend += r["Trend"]

                # stop-loss primero
                if not profit_hit and price <= stop_price:
                    result, end_idx = "Limit", idx
                    break

                # se alcanza min_profit
                if not profit_hit and price >= target_price:
                    profit_hit = True

                # retroceso permitido tras el objetivo
                if profit_hit and r["Trend"] <= -abs(cumulative_trend) * val_limit_trend:
                    result, end_idx = "Objective", idx
                    break

            if end_idx is None:
                end_idx = min(start_event_idx + max_candles, last_idx)

            # ─────–– cálculos específicos para el registro ────────────────
            price_diff = abs(row["Close"] - row["BB_Lower"])   # puntos de precio
            atr_coeff  = price_diff / row["ATR"]               # múltiplos de ATR

            streaks_raw.append({
                "EventIdx":   int(start_event_idx),
                "EndIdx":     int(end_idx),
                "EventBB":    data.at[start_event_idx, "DateTimeStr"]
                               if "DateTimeStr" in data.columns else data.at[start_event_idx, "Date"],
                "StartStreak":  data.at[ + 1, "DateTimeStr"]
                               if "DateTimeStr" in data.columns else data.at[start_event_idx + 1, "Date"],
                "StartIdx":   int(start_event_idx + 1),
                "StartValue": float(data.at[start_event_idx + 1, "Open"]),
                "EndValue":   float(data.at[end_idx, "Close"]),
                "To":         data.at[end_idx, "DateTimeStr"]
                               if "DateTimeStr" in data.columns else data.at[end_idx, "Date"],
                "ATR_coeff":  float(atr_coeff),                # ← ahora en múltiplos de ATR
                "MACD_start": float(data.at[start_event_idx + 1, "MACD"]),
                "Momentum_10":  float(data.at[start_event_idx + 1, "Momentum_10"]),
                "ROC_10":      float(data.at[start_event_idx + 1, "ROC_10"]),
                "Result":     result
            })

    # ───────────────── 3. depuración: sin solapes, con prioridad ───────────
    priority = {"Objective": 0, "Limit": 1, "NoResult": 2}
    streaks_sorted = sorted(streaks_raw, key=lambda s: (priority[s["Result"]], s["EventIdx"]))

    streak_list: list[dict] = []
    for s in streaks_sorted:
        if not any(
            s["EventIdx"] <= x["EndIdx"] and s["EndIdx"] >= x["EventIdx"]
            for x in streak_list
        ):
            streak_list.append(s)

    streak_list.sort(key=lambda s: s["EventIdx"])  # orden cronológico final
    return {
        "streak_list": streak_list,
        "streak_stat": {
            "min_profit": min_profit,
            "limit_loss": limit_loss,
            "max_candles": max_candles,
            "val_limit_trend": val_limit_trend,
        }
        }







# ───────────────────────── FUNCIÓN NUEVA ─────────────────────────
def analyze_streaks(
        *,
        metric: str = "ATR_coeff",
        **get_trend_kwargs
    ):
    """
    Ejecuta get_trend_and_diff_data(**get_trend_kwargs),
    separa los resultados por tipo (Objective / Limit / NoResult)
    y devuelve estadísticas básicas + test de Shapiro-Wilk.

    ----------
    Parámetros
    ----------
    metric : str
        Clave numérica del diccionario de cada streak sobre la que
        se calculan las medidas (por defecto 'ATR_coeff').
    get_trend_kwargs : dict
        Cualquier parámetro que quieras enviar a get_trend_and_diff_data,
        p. ej. min_profit=0.01, max_candles=15, …

    ----------
    Retorno
    ----------
    dict  con la estructura exacta solicitada:
      {
        "data_result": { … },
        "data_info":   { … }
      }
    """
    # — 1. obtener la lista de streaks —
    result = get_trend_and_diff_data(**get_trend_kwargs)
    streaks = result["streak_list"]

    # — 2. clasificar en tres listas —
    list_objective = [s[metric] for s in streaks if s["Result"] == "Objective"]
    list_limit     = [s[metric] for s in streaks if s["Result"] == "Limit"]
    list_no_result = [s[metric] for s in streaks if s["Result"] == "NoResult"]

    # — 3. helper para describir cada lista —
    def describe(arr):
        if len(arr) == 0:
            return {"mean": None, "std": None,
                    "max_val": None, "min_val": None,
                    "distribution": "N/A"}
        a = np.asarray(arr, dtype=float)
        mean_ = float(np.mean(a))
        std_  = float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
        max_  = float(np.max(a))
        min_  = float(np.min(a))

        if len(a) >= 3:
            _, p = shapiro(a)
            distr = "normal" if p >= 0.05 else "non-normal"
        else:
            distr = "undetermined"

        return {"mean": mean_, "std": std_,
                "max_val": max_, "min_val": min_,
                "distribution": distr}

    stat_objective = describe(list_objective)
    stat_limit     = describe(list_limit)
    stat_nores     = describe(list_no_result)

    # — 4. empaquetar todo y devolver —
    return {
        "data_result": {
            "Objective": list_objective,
            "Limit":     list_limit,
            "NoResult":  list_no_result
        },
        "data_info": {
            "stat_objective": stat_objective,
            "stat_limit":     stat_limit,
            "stat_no_result": stat_nores
        }
    }















    # return {
    #     data_result : {
    #         "Objective": list_objective,
    #         "Limit": list_limit,
    #         "NoResult": list_no_result
    #     },
    #     data_info : {
    #         "stat_objective":{
    #             "mean": mean_obj,
    #             "std": std_obj,
    #             "max_val": max_val_obj,
    #             "min_val": min_val_obj,
    #             "distribution": distr_obj
    #         },
    #         "stat_limit":{
    #             "mean": mean_limit,
    #             "std": std_limit,
    #             "max_val": max_val_limit,
    #             "min_val": min_val_limit,
    #             "distribution": distr_limit
    #         },
    #         "stat_no_result":{
    #             "mean": mean_nores,
    #             "std": std_nores,
    #             "max_val": max_val_nores,
    #             "min_val": min_val_nores,
    #             "distribution": distr_nores
    #         }
    #     }

    # }






















