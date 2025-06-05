import numpy as np
import pandas as pd
import os

# === Cargar dataset ===
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")
df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])
df = df[df["Date"].dt.year >= 2015].reset_index(drop=True)


def detect_macd_streaks(side="Negative", zone="Lower", mean_value=0.0, direction="ascending"):
    macd_series = df["MACD"].dropna().reset_index(drop=True)
    date_series = df.loc[macd_series.index, "Date"].reset_index(drop=True)

    results = []
    i = 0
    while i < len(macd_series):
        val = macd_series[i]

        if side == "Negative" and val >= 0:
            i += 1
            continue
        if side == "Positive" and val <= 0:
            i += 1
            continue

        if zone == "Lower" and val >= mean_value:
            i += 1
            continue    
        if zone == "Higher" and val < mean_value:
            i += 1
            continue

        current_racha = [val]
        j = i + 1
        valid = False
        while j < len(macd_series):
            next_val = macd_series[j]

            if direction == "ascending" and next_val <= current_racha[-1]:
                break
            if direction == "descending" and next_val >= current_racha[-1]:
                break

            current_racha.append(next_val)

            if side == "Negative" and next_val >= 0:
                valid = True
                break
            if side == "Positive" and next_val <= 0:
                valid = True
                break

            j += 1

        if valid:
            results.append({
                "From": str(date_series[i]),
                "To": str(date_series[j]),
                "StartValue": val,
                "EndValue": current_racha[-1],
                "MACD_Sequence": current_racha,
                "StartIdx": int(i),
                "EndIdx": int(j),
                "RSI_14": float(df.loc[i, "RSI_14"])  # <-- RSI agregado
            })
            i = j + 1
        else:
            i += 1

    return results


def find_price_streaks_after_macd_hist_cross(streaks_macd, target=700, limit=300, max_candles=80, mode="buy"):
    macd_hist = df["MACD_Hist"].tolist()
    open_list = df["Open"].tolist()
    high_list = df["High"].tolist()
    low_list = df["Low"].tolist()
    close_list = df["Close"].tolist()
    date_list = df["Date"].astype(str).tolist()

    results = {
        "ObjectiveProfit": [],
        "LimitLoss": [],
        "NoResult": []
    }

    for streak in streaks_macd:
        start_idx = streak["StartIdx"]
        end_idx = streak["EndIdx"]

        for i in range(start_idx + 1, end_idx):
            if mode == "buy" and not (macd_hist[i - 1] < 0 and macd_hist[i] >= 0):
                continue
            if mode == "sell" and not (macd_hist[i - 1] > 0 and macd_hist[i] <= 0):
                continue

            entry_idx = i
            if entry_idx >= len(df):
                continue

            start_value = open_list[entry_idx]
            if mode == "buy":
                take_profit = start_value + target
                stop_loss = start_value - limit
            else:
                take_profit = start_value - target
                stop_loss = start_value + limit

            result = {
                "From": date_list[entry_idx],
                "StartValue": start_value,
                "MACD_Hist_Cross_Date": date_list[i],
                "MACD_Hist_Cross_Idx": i,
                "RSI_14": float(df.loc[entry_idx, "RSI_14"])  # ← Agregado aquí
            }

            hit = False
            for j in range(entry_idx + 1, entry_idx + max_candles + 1):
                if j >= len(df):
                    break

                if mode == "buy":
                    if low_list[j] <= stop_loss:
                        result.update({
                            "To": date_list[j],
                            "EndValue": close_list[j],
                            "Result": "Limit"
                        })
                        results["LimitLoss"].append(result)
                        hit = True
                        break
                    if high_list[j] >= take_profit:
                        result.update({
                            "To": date_list[j],
                            "EndValue": close_list[j],
                            "Result": "Objective"
                        })
                        results["ObjectiveProfit"].append(result)
                        hit = True
                        break
                else:
                    if high_list[j] >= stop_loss:
                        result.update({
                            "To": date_list[j],
                            "EndValue": close_list[j],
                            "Result": "Limit"
                        })
                        results["LimitLoss"].append(result)
                        hit = True
                        break
                    if low_list[j] <= take_profit:
                        result.update({
                            "To": date_list[j],
                            "EndValue": close_list[j],
                            "Result": "Objective"
                        })
                        results["ObjectiveProfit"].append(result)
                        hit = True
                        break

            if not hit:
                final_idx = min(entry_idx + max_candles, len(df) - 1)
                result.update({
                    "To": date_list[final_idx],
                    "EndValue": close_list[final_idx],
                    "Result": "NoResult"
                })
                results["NoResult"].append(result)

    return results


def get_macd_data(target=700, limit=500, max_candles=150):
    data = df[["Date", "MACD", "MACD_Signal", "MACD_Hist"]].copy()

    macd_values = df["MACD"].dropna()
    macd_pos = macd_values[macd_values > 0]
    macd_neg = macd_values[macd_values < 0]

    mean_macd_pos = macd_pos.mean()
    mean_macd_neg = macd_neg.mean()

    value_groups = {
        "Negative": {
            "Higher": macd_neg[macd_neg > mean_macd_neg].tolist(),
            "Lower": macd_neg[macd_neg <= mean_macd_neg].tolist()
        },
        "Positive": {
            "Higher": macd_pos[macd_pos >= mean_macd_pos].tolist(),
            "Lower": macd_pos[macd_pos < mean_macd_pos].tolist()
        }
    }

    stats = {
        "mean_macd_pos": round(mean_macd_pos, 4),
        "std_macd_pos": round(macd_pos.std(), 4),
        "mean_macd_neg": round(mean_macd_neg, 4),
        "std_macd_neg": round(macd_neg.std(), 4)
    }

    streaks_macd = {
        "Negative_Lower": detect_macd_streaks("Negative", "Lower", mean_macd_neg, "ascending"),
        "Negative_Higher": detect_macd_streaks("Negative", "Higher", mean_macd_neg, "ascending"),
        "Positive_Lower": detect_macd_streaks("Positive", "Lower", mean_macd_pos, "descending"),
        "Positive_Higher": detect_macd_streaks("Positive", "Higher", mean_macd_pos, "descending")
    }

    price_streaks = {
        "Negative_Lower": find_price_streaks_after_macd_hist_cross(
            streaks_macd["Negative_Lower"], target, limit, max_candles, mode="buy"
        ),
        "Negative_Higher": find_price_streaks_after_macd_hist_cross(
            streaks_macd["Negative_Higher"], target, limit, max_candles, mode="buy"
        ),
        "Positive_Lower": find_price_streaks_after_macd_hist_cross(
            streaks_macd["Positive_Lower"], target, limit, max_candles, mode="sell"
        ),
        "Positive_Higher": find_price_streaks_after_macd_hist_cross(
            streaks_macd["Positive_Higher"], target, limit, max_candles, mode="sell"
        )
    }

    return {
        "data": data.to_dict(orient="records"),
        "stats": stats,
        "valueGroups": value_groups,
        "StreaksMACD": streaks_macd,
        "PriceStreaks": price_streaks
    }
