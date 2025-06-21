from collections import defaultdict
import pandas as pd
from analytics.trends.macd_function import compute_price_streaks   # tu módulo optimizado


def get_macd_data_month():
    # 1) --- datos base -------------------------------------------------
    df = pd.read_csv("Datasets/US30_H1.csv", parse_dates=["Date"])
    df = df[(df["Date"].dt.year >= 2018) & (df["Date"].dt.year <= 2025)]

    data_info = compute_price_streaks(df)        # contiene PriceStreaks y stats
    pks = data_info["PriceStreaks"]              # alias corto

    # 2) --- contador año-mes-categoría-resultado ----------------------
    # counts[año][cat]["ObjectiveProfit" | "LimitLoss" | "NoResult"] = [12 números]
    counts = defaultdict(
        lambda: {
            cat: {
                "ObjectiveProfit": [0] * 12,
                "LimitLoss":       [0] * 12,
                "NoResult":        [0] * 12,
            }
            for cat in pks.keys()
        }
    )

    for cat, blocks in pks.items():                             # cat = Negative_Higher, …
        for result_key in ("ObjectiveProfit", "LimitLoss", "NoResult"):
            for trade in blocks[result_key]:
                y, m = map(int, trade["From"][:7].split("-"))   # “YYYY-MM-DD”
                counts[y][cat][result_key][m - 1] += 1

    # 3) --- empaquetar para tabla dinámica ----------------------------
    zone_map = {
        "Negative_Higher": ("Negative", "Higher"),
        "Negative_Lower":  ("Negative", "Lower"),
        "Positive_Higher": ("Positive", "Higher"),
        "Positive_Lower":  ("Positive", "Lower"),
    }

    table_rows = []
    for year, cat_dict in sorted(counts.items()):
        for cat, (side, zone) in zone_map.items():
            row = {
                "year":            year,
                "side":            side,          # MACD- / MACD+
                "zone":            zone,          # Higher / Lower
                "ObjectiveProfit": cat_dict[cat]["ObjectiveProfit"],
                "LimitLoss":       cat_dict[cat]["LimitLoss"],
                "NoResult":        cat_dict[cat]["NoResult"],
            }
            table_rows.append(row)

    # 4) --- respuesta del endpoint ------------------------------------
    return {
        "MonthlyObjectiveCounts": table_rows,
        "DataInfo": data_info["stats"] | {       # mantenemos la info anterior
            "RSI_reference_positive": data_info["RSI_reference_positive"],
            "RSI_reference_negative": data_info["RSI_reference_negative"],
            "target":      data_info["target"],
            "limit":       data_info["limit"],
            "max_candles": data_info["max_candles"],
            "startDate":   data_info["startDate"],
        },
    }
