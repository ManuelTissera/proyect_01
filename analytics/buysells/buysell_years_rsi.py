import pandas as pd
import numpy as np
import os

# Cargar dataset
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")
df = pd.read_csv(file_path)

def validate_reversal(end_index, close_price, lows_list, highs_list, max_fall, min_rise, max_candles):
    stop_loss = close_price - max_fall
    target = close_price + min_rise
    for low, high in zip(lows_list[end_index + 1:end_index + 1 + max_candles],
                         highs_list[end_index + 1:end_index + 1 + max_candles]):
        if low <= stop_loss:
            return "Invalidated"
        if high >= target:
            return "Confirmed"
    return "No confirmation"

def analyze_year_data(df_year, target_streak, max_fall, min_rise, max_candles):
    trend = df_year["Trend"].tolist()
    opens = df_year["Open"].tolist()
    closes = df_year["Close"].tolist()
    lows = df_year["Low"].tolist()
    highs = df_year["High"].tolist()
    dates = df_year["DateTimeStr"].tolist()
    rsis = df_year["RSI_14"].tolist()

    goals, limits, no_confirms, summary = [], [], [], []
    count = 1
    start_idx = 0
    prev_sign = trend[0] >= 0

    for i in range(1, len(trend)):
        current_sign = trend[i] >= 0
        if current_sign == prev_sign:
            count += 1
        else:
            streak = count if prev_sign else -count
            if streak == target_streak:
                start_dt = dates[start_idx]
                end_dt = dates[i - 1]
                close_price = closes[i - 1]

                validation = validate_reversal(i - 1, close_price, lows, highs, max_fall, min_rise, max_candles)

                result = {
                    "From": start_dt,
                    "To": end_dt,
                    "Open": opens[start_idx],
                    "Close": close_price,
                    "Result": validation
                }

                rsi_slice = rsis[start_idx:i]
                mean_rsi = sum(rsi_slice) / len(rsi_slice) if rsi_slice else None

                summary.append({
                    "Start": start_dt,
                    "End": end_dt,
                    "Close": close_price,
                    "Result": validation,
                    "RSIs": rsi_slice,
                    "MeanRSI": mean_rsi,
                    "SMA20": df_year["SMA20"].iloc[i - 1],
                    "SMA200": df_year["SMA200"].iloc[i - 1]
                })

                if validation == "Confirmed":
                    goals.append(result)
                elif validation == "Invalidated":
                    limits.append(result)
                else:
                    no_confirms.append(result)

            count = 1
            start_idx = i
            prev_sign = current_sign

    return goals, limits, no_confirms, summary

def classify_by_quarter_and_month(records):
    quarters = {f"Q{i}": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0} for i in range(1, 5)}
    months = {f"{i:02d}": {"Goals": 0, "Invalidated": 0, "NoConfirmation": 0} for i in range(1, 13)}

    def get_qm(date_str):
        month = int(date_str.split("T")[0].split("-")[1])
        if 1 <= month <= 3: quarter = "Q1"
        elif 4 <= month <= 6: quarter = "Q2"
        elif 7 <= month <= 9: quarter = "Q3"
        else: quarter = "Q4"
        return quarter, f"{month:02d}"

    for cat, key in [("Goals", "From"), ("Invalidated", "From"), ("NoConfirmation", "From")]:
        for item in records[cat]:
            q, m = get_qm(item[key])
            quarters[q][cat] += 1
            months[m][cat] += 1

    return quarters, months

def get_multiple_years_data_rsi(target_streak=-5, years=None, max_fall=250, min_rise=500, max_candles=100):
    if years is None:
        return {"error": "No years provided"}

    df["Date"] = pd.to_datetime(df["Date"])
    results = {}

    for y in years:
        df_y = df[df["Date"].dt.year == y]
        if df_y.empty:
            results[str(y)] = {"error": f"No data for year {y}"}
            continue

        goals, limits, no_confirms, summary = analyze_year_data(df_y, target_streak, max_fall, min_rise, max_candles)

        data_dict = {
            "max_fall": max_fall,
            "min_rise": min_rise,
            "max_candles": max_candles,
            "Targ_str": target_streak,
            "Goals": goals,
            "Limit": limits,
            "No_confirm": no_confirms,
            "StreaksSummary": summary
        }

        quarters, months = classify_by_quarter_and_month({
            "Goals": goals,
            "Invalidated": limits,
            "NoConfirmation": no_confirms
        })

        data_dict["ByQuarter"] = quarters
        data_dict["ByMonth"] = months
        results[str(y)] = data_dict

    return results

