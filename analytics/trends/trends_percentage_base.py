import pandas as pd
import os

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
    date_list = df["DateTimeStr"].tolist()
    open_list = df["Open"].tolist()

    i = 0
    while i < len(close_list) - 1:
        entry_price = close_list[i]
        stop_loss = entry_price - limit
        take_profit = entry_price + target
        racha_detectada = False

        for j in range(1, max_candles + 1):
            if i + j >= len(close_list):
                break

            lows = low_list[i + 1:i + j + 1]
            highs = close_list[i + 1:i + j + 1]

            if any(l <= stop_loss for l in lows):
                results.append({
                    "From": date_list[i],
                    "To": date_list[i + j],
                    "Open": open_list[i],
                    "Close": close_list[i + j],
                    "Result": "Limit"
                })
                i += j
                racha_detectada = True
                break

            if any(h >= take_profit for h in highs):
                results.append({
                    "From": date_list[i],
                    "To": date_list[i + j],
                    "Open": open_list[i],
                    "Close": close_list[i + j],
                    "Result": "Objective",
                    "CandPos": CandPos
                })
                i += j
                racha_detectada = True
                break

        if not racha_detectada:
            results.append({
                "From": date_list[i],
                "To": date_list[i + max_candles] if i + max_candles < len(close_list) else date_list[-1],
                "Open": open_list[i],
                "Close": close_list[min(i + max_candles, len(close_list) - 1)],
                "Result": "NoResult"
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

    return {
        "Target":target,
        "Limit": limit,
        "MaxCandle": max_candles,
        "Results": results,
        "OpenCloseByYear": open_close_by_year
    }
