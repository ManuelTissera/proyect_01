import pandas as pd
import os

# === Parámetros de fechas (modificables) ===
start_date = pd.to_datetime("2015-01-01")
end_date = pd.to_datetime("2025-04-30")

# === Paths ===
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path_M2 = os.path.join(base_dir, "Datasets_info", "WM2NS.csv")
file_path_QE = os.path.join(base_dir, "Datasets_info", "QE_Data.csv")
file_path_US = os.path.join(base_dir, "Datasets", "US30_H1.csv")

# === Cargar datasets ===
dfM2 = pd.read_csv(file_path_M2)
dfQE = pd.read_csv(file_path_QE)
dfUS = pd.read_csv(file_path_US)

# === Asegurar formato de fecha ===
dfM2["Date"] = pd.to_datetime(dfM2["Date"])
dfQE["Date"] = pd.to_datetime(dfQE["Date"])
dfUS["Date"] = pd.to_datetime(dfUS["Date"])

# === Filtrar por rango de fechas ===
dfM2 = dfM2[(dfM2["Date"] >= start_date) & (dfM2["Date"] <= end_date)].copy()
dfQE = dfQE[(dfQE["Date"] >= start_date) & (dfQE["Date"] <= end_date)].copy()
dfUS = dfUS[(dfUS["Date"] >= start_date) & (dfUS["Date"] <= end_date)].copy()

# === Procesar velas semanales para dfUS ===
dfUS["Week"] = dfUS["Date"].dt.to_period("W").apply(lambda r: r.start_time)
weekly_candles = (
    dfUS.groupby("Week")
    .agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last"
    })
    .reset_index()
)

data_candles = [
    {
        "x": row["Week"].strftime("%Y-%m-%d"),
        "o": round(row["Open"], 2),
        "h": round(row["High"], 2),
        "l": round(row["Low"], 2),
        "c": round(row["Close"], 2),
    }
    for _, row in weekly_candles.iterrows()
]

# === Convertir los otros datasets a listas de dicts ===
data_M2 = dfM2.to_dict(orient="records")
data_QE = dfQE.to_dict(orient="records")

# === Resultado final ===
result = {
    "data_M2": data_M2,
    "data_QE": data_QE,
    "data_ohlc": data_candles
}

print("Filas M2 después del filtro:", len(dfM2))
print(dfM2.isna().sum())


def get_data_monetary_base():
    return result
