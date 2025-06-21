import pandas as pd
import os
from pandas.tseries.offsets import BDay   # ← para saltar fines de semana

# === Configuración base ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
US30_PATH = os.path.join(BASE_DIR, "Datasets", "US30_H1.csv")


# --------------------------------------------------------------------------------------
#  Función principal
# --------------------------------------------------------------------------------------
def analyze_post_news_movements(
    news_datetime_list,
    from_date: str = "2015-01-01",
    to_date:   str = "2025-04-01"
):
    """
    news_datetime_list : iterable de datetime.date (fechas de publicación económica)
    from_date, to_date : rango general (inclusive) a analizar
    """
    # === 1) Cargar dataset horario del US30  ===
    df = pd.read_csv(US30_PATH)

    # --- limpieza / pre-procesado ---
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df = df[
        (df["DateTime"] >= pd.to_datetime(from_date)) &
        (df["DateTime"] <= pd.to_datetime(to_date))
    ].copy()

    # columna "Day" sin hora
    df["Day"] = df["DateTime"].dt.date

    # lista ordenada de todos los días de trading presentes (por si faltan festivos)
    trading_days = sorted(df["Day"].unique())

    # === 2) Recorrer cada fecha de noticia ===
    results = []

    for news_dt in news_datetime_list:
        # día de mercado inmediatamente posterior a la noticia
        first_day_with_data = next((d for d in trading_days if d > news_dt), None)
        if first_day_with_data is None:
            # no hay datos posteriores
            continue

        day1_start = pd.Timestamp(first_day_with_data)  # base como Timestamp

        # construir rangos
        result = {
            "news_datetime": str(news_dt),
            # Día 1
            "return_1d":  _get_range_metrics(df, day1_start, 0, 0),
            # Días 2-3
            "return_3d":  _get_range_metrics(df, day1_start, 1, 2),
            # Días 4-5
            "return_5d":  _get_range_metrics(df, day1_start, 3, 4),
            # Días 6-10
            "return_10d": _get_range_metrics(df, day1_start, 5, 9),
            # Días 11-15
            "return_15d": _get_range_metrics(df, day1_start, 10, 14),
        }
        results.append(result)

    return results


# --------------------------------------------------------------------------------------
#  Métricas para un rango
# --------------------------------------------------------------------------------------
def _get_range_metrics(df, day1_start, day_from: int, day_to: int):
    """
    Calcula métricas de precios entre los *días de trading*:
        start = day1_start + day_from
        end   = day1_start + day_to
    Ambos extremos incluidos.

    Usa desplazamiento BDay -> evita sábados y domingos
    """
    # desplazamiento solo por días hábiles (weekdays)
    start_day = (day1_start + BDay(day_from)).date()
    end_day   = (day1_start + BDay(day_to)).date()

    # Sub-dataframe del rango
    df_range = df[(df["Day"] >= start_day) & (df["Day"] <= end_day)]

    if df_range.empty:
        return {
            "Close": None, "Open": None, "High": None, "Low": None,
            "Range": None, "Trend": None, "Volatility": None
        }

    open_price  = df_range.iloc[0]["Open"]
    close_price = df_range.iloc[-1]["Close"]
    high_price  = df_range["High"].max()
    low_price   = df_range["Low"].min()
    price_range = high_price - low_price
    trend       = close_price - open_price

    # Desviación estándar de los retornos, si existe la columna
    volatility = (
        df_range["Return"].std()
        if "Return" in df_range.columns
        else None
    )

    return {
        "Close":      round(close_price, 2),
        "Open":       round(open_price, 2),
        "High":       round(high_price, 2),
        "Low":        round(low_price, 2),
        "Range":      round(price_range, 2),
        "Trend":      round(trend, 2),
        "Volatility": round(volatility, 6) if volatility is not None else None,
    }
