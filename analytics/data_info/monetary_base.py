import pandas as pd
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path_M2 = os.path.join(base_dir, "Datasets_info", "WM2NS.csv")
file_path_QE = os.path.join(base_dir, "Datasets_info", "QE_Data.csv")
file_path_US = os.path.join(base_dir, "Datasets", "US30_H1.csv")

# === Cargar datasets ===
dfM2 = pd.read_csv(file_path_M2)
dfQE = pd.read_csv(file_path_QE)
dfUS = pd.read_csv(file_path_US)

# === Procesar velas semanales ===
dfUS["Date"] = pd.to_datetime(dfUS["Date"])
dfUS = dfUS[dfUS["Date"].dt.year >= 2015].copy()

# Crear columna 'Week' como la semana de cada año
dfUS["Week"] = dfUS["Date"].dt.to_period("W").apply(lambda r: r.start_time)

# Agrupar por semana y construir las velas OHLC
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

# Formatear para Chart.js (OHLC)
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

def get_data_monetary_base():
    return result
