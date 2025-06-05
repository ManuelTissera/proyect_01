
import numpy as np
import pandas as pd
import os
from collections import defaultdict




# Cargar dataset
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")
df = pd.read_csv(file_path)

# Filtrar desde 2015 en adelante
df["Date"] = pd.to_datetime(df["Date"])
df = df[df["Date"].dt.year >= 2015].reset_index(drop=True)


def find_bullish_trends(target=700, limit=300, max_candles=100):
    results = []
    close_list = df["Close"].tolist()
    low_list = df["Low"].tolist()
    high_list = df["High"].tolist()
    date_list = df["DateTimeStr"].tolist()
    open_list = df["Open"].tolist()
    sma20_list = df["SMA20"].tolist()
    sma200_list = df["SMA200"].tolist()

    i = 0
    while i < len(close_list) - 1:
        entry_price = close_list[i]
        stop_loss = entry_price - limit
        take_profit = entry_price + target
        racha_detectada = False

        if i >= 10:
            prev_closes = close_list[i - 10:i]
            slope = (prev_closes[-1] - prev_closes[0]) / 10

            prev_highs = high_list[i - 10:i]
            prev_lows = low_list[i - 10:i]
            prev_ranges = [h - l for h, l in zip(prev_highs, prev_lows)]
            volatility = np.mean(prev_ranges)

            sma20 = sma20_list[i - 1]
            sma200 = sma200_list[i - 1]
            open_price = open_list[i]
            dist_start_sma20 = open_price - sma20
            dist_start_sma200 = open_price - sma200
        else:
            slope = None
            volatility = None
            sma20 = None
            sma200 = None
            dist_start_sma20 = None
            dist_start_sma200 = None

        for j in range(1, max_candles + 1):
            if i + j >= len(close_list):
                break

            lows = low_list[i + 1:i + j + 1]
            highs = close_list[i + 1:i + j + 1]

            close_val = close_list[i + j]
            dist_sma20 = close_val - sma20 if sma20 is not None else None
            dist_sma200 = close_val - sma200 if sma200 is not None else None

            if any(l <= stop_loss for l in lows):
                results.append({
                    "From": date_list[i],
                    "To": date_list[i + j],
                    "Open": open_list[i],
                    "Close": close_val,
                    "Result": "Limit",
                    "PreSlope": slope,
                    "PreVolatility": volatility,
                    "DistSMA20": dist_sma20,
                    "DistSMA200": dist_sma200,
                    "DistStartSMA20": dist_start_sma20,
                    "DistStartSMA200": dist_start_sma200
                })
                i += j
                racha_detectada = True
                break

            if any(h >= take_profit for h in highs):
                results.append({
                    "From": date_list[i],
                    "To": date_list[i + j],
                    "Open": open_list[i],
                    "Close": close_val,
                    "Result": "Objective",
                    "PreSlope": slope,
                    "PreVolatility": volatility,
                    "DistSMA20": dist_sma20,
                    "DistSMA200": dist_sma200,
                    "DistStartSMA20": dist_start_sma20,
                    "DistStartSMA200": dist_start_sma200
                })
                i += j
                racha_detectada = True
                break

        if not racha_detectada:
            close_val = close_list[min(i + max_candles, len(close_list) - 1)]
            dist_sma20 = close_val - sma20 if sma20 is not None else None
            dist_sma200 = close_val - sma200 if sma200 is not None else None

            results.append({
                "From": date_list[i],
                "To": date_list[i + max_candles] if i + max_candles < len(close_list) else date_list[-1],
                "Open": open_list[i],
                "Close": close_val,
                "Result": "NoResult",
                "PreSlope": slope,
                "PreVolatility": volatility,
                "DistSMA20": dist_sma20,
                "DistSMA200": dist_sma200,
                "DistStartSMA20": dist_start_sma20,
                "DistStartSMA200": dist_start_sma200
            })
            i += max_candles



    # ---- Open, Close, High, Low por año ----
    open_close_by_year = {}
    df_sorted = df.sort_values("DateTimeStr")

    for year in sorted(df["Date"].dt.year.unique()):
        df_y = df[df["Date"].dt.year == year]
        if df_y.empty:
            continue

        open_price = df_y.iloc[0]["Open"]
        close_price = df_y.iloc[-1]["Close"]
        high_price = df_y["High"].max()
        low_price = df_y["Low"].min()

        open_close_by_year[str(year)] = {
            "Open": round(open_price, 2),
            "Close": round(close_price, 2),
            "High": round(high_price, 2),
            "Low": round(low_price, 2)
        }

    # ---- Función para media y std ----
    def stats(values):
        return {
            "mean": round(float(np.mean(values)), 4) if values else None,
            "std": round(float(np.std(values)), 4) if values else None
        }

    # ---- Stats PreSlope ----
    slopes_objective = [r["PreSlope"] for r in results if r["Result"] == "Objective" and r["PreSlope"] is not None]
    slopes_limit = [r["PreSlope"] for r in results if r["Result"] == "Limit" and r["PreSlope"] is not None]
    slopes_noresult = [r["PreSlope"] for r in results if r["Result"] == "NoResult" and r["PreSlope"] is not None]

    stats_pre_slope = {
        "Objective": stats(slopes_objective),
        "Limit": stats(slopes_limit),
        "NoResult": stats(slopes_noresult)
    }

    # ---- Stats PreVolatility ----
    vol_objective = [r["PreVolatility"] for r in results if r["Result"] == "Objective" and r["PreVolatility"] is not None]
    vol_limit = [r["PreVolatility"] for r in results if r["Result"] == "Limit" and r["PreVolatility"] is not None]
    vol_noresult = [r["PreVolatility"] for r in results if r["Result"] == "NoResult" and r["PreVolatility"] is not None]

    stats_pre_volatility = {
        "Objective": stats(vol_objective),
        "Limit": stats(vol_limit),
        "NoResult": stats(vol_noresult)
    }



    # ---- Frecuencia por año y mes ----
    freq_by_year_month = defaultdict(lambda: defaultdict(lambda: {"Objective": 0, "Limit": 0, "NoResult": 0}))

    for r in results:
        year, month = r["From"].split("T")[0].split("-")[:2]
        result_type = r["Result"]
        freq_by_year_month[year][month][result_type] += 1


    return {
        "Results": results,
        "OpenCloseByYear": open_close_by_year,
        "StatsPreSlope": stats_pre_slope,
        "StatsPreVolatility": stats_pre_volatility,
        "FreqByYearMonth": {y: dict(freq_by_year_month[y]) for y in freq_by_year_month}
    }
