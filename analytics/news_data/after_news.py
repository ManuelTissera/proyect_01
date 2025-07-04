# after_news.py
# ------------------------------------------------- #
#  CONFIGURACIÓN
# ------------------------------------------------- #
import os
from datetime import timedelta

import pandas as pd
from pandas.tseries.offsets import BDay
from sqlalchemy import create_engine, text

try:
    # helper del proyecto; no se dispara excepción si no existe
    from db_connection import get_connection
except ImportError:  # tests, notebooks, etc.
    get_connection = None

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
US30_PATH = os.path.join(BASE_DIR, "Datasets", "US30_H1.csv")


# ------------------------------------------------- #
#  FUNCIÓN PRINCIPAL
# ------------------------------------------------- #
def analyze_post_news_movements(
    id_new_name,                      # <-- identificador de la noticia
    news_dates,                       # iterable[datetime.date]
    from_date: str = "2015-01-01",
    to_date: str = "2025-04-01",
    *,
    db_url: str | None = None,        # p.ej. "postgresql+psycopg2://user:pwd@host/db"
    econ_table: str = "economic_news_data",
):
    """
    Calcula el comportamiento del US30 tras cada publicación de una noticia
    económica (id_new_name) y empareja el actual_value correspondiente.

    Devuelve: list[dict]
    """

    # 1) Precios horarios del US30 ------------------------------------
    df = pd.read_csv(US30_PATH)
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df = df[
        (df["DateTime"] >= pd.to_datetime(from_date))
        & (df["DateTime"] <= pd.to_datetime(to_date))
    ].copy()

    # Aseguramos la columna Return para volatilidad
    if "Return" not in df.columns:
        df["Return"] = df["Close"].pct_change()

    df["Day"] = df["DateTime"].dt.date
    trading_days = sorted(df["Day"].unique())

    # 2) Mapa día → actual_value  -------------------------------------
    actual_map = {}

    if db_url:
        engine = create_engine(db_url)
        sql = text(
            f"""
            SELECT publication_date::date AS day, actual_value
            FROM {econ_table}
            WHERE id_new_name = :id
              AND publication_date::date BETWEEN :from_d AND :to_d
            """
        )
        econ_df = pd.read_sql_query(
            sql,
            engine,
            params={"id": id_new_name, "from_d": from_date, "to_d": to_date},
        )
    else:
        if get_connection is None:
            raise RuntimeError(
                "No db_url proporcionado y no se encontró get_connection()"
            )
        conn = get_connection()
        sql = f"""
            SELECT publication_date::date AS day, actual_value
            FROM {econ_table}
            WHERE id_new_name = %s
              AND publication_date::date BETWEEN %s AND %s
        """
        econ_df = pd.read_sql(sql, conn, params=[id_new_name, from_date, to_date])
        conn.close()

    if not econ_df.empty:
        econ_df["day"] = pd.to_datetime(econ_df["day"]).dt.date
        actual_map = (
            econ_df.groupby("day")["actual_value"].first().to_dict()
        )  # clave = date

    # 3) Procesar cada noticia ---------------------------------------
    results = []
    for order, news_dt in enumerate(news_dates, start=1):

        # primer día de mercado posterior
        first_day_with_data = next((d for d in trading_days if d > news_dt), None)
        if first_day_with_data is None:
            continue

        # buscar actual_value con tolerancia ±1 día
        actual_val = (
            actual_map.get(news_dt)  # exacto
            or actual_map.get(news_dt - timedelta(days=1))  # -1 día
            or actual_map.get(news_dt + timedelta(days=1))  # +1 día
        )

        day1_start = pd.Timestamp(first_day_with_data)
        ranges = [
            ("return1_1d", 0, 0),
            ("return2_3d", 1, 2),
            ("return3_5d", 1, 4), # ("return3_5d", 3, 4),
            ("return4_10d", 1, 9), # ("return4_10d", 5, 9),
            ("return5_15d", 10, 14),
        ]

        result = {
            "order": order,
            "news_datetime": str(news_dt),
            "actual_value": actual_val,
        }
        for key, d_from, d_to in ranges:
            result[key] = _get_range_metrics(df, day1_start, d_from, d_to)

        results.append(result)

    return results


# ------------------------------------------------- #
#  MÉTRICAS DE UN RANGO
# ------------------------------------------------- #
def _get_range_metrics(df, day1_start, day_from, day_to):
    start_day = (day1_start + BDay(day_from)).date()
    end_day = (day1_start + BDay(day_to)).date()
    df_range = df[(df["Day"] >= start_day) & (df["Day"] <= end_day)]

    if df_range.empty:
        return dict.fromkeys(
            ["Close", "Open", "High", "Low", "Range", "Trend", "Volatility"], None
        )

    open_p = df_range.iloc[0]["Open"]
    close_p = df_range.iloc[-1]["Close"]
    high_p = df_range["High"].max()
    low_p = df_range["Low"].min()
    trend = close_p - open_p
    volat = df_range["Return"].std()

    return {
        "Close": round(close_p, 2),
        "Open": round(open_p, 2),
        "High": round(high_p, 2),
        "Low": round(low_p, 2),
        "Range": round(high_p - low_p, 2),
        "Trend": round(trend, 2),
        "Volatility": round(volat, 6),
    }


# ------------------------------------------------- #
#  CORRELACIÓN ENTRE ACTUAL_VALUE Y MÉTRICA
from typing import Literal, Iterable, Dict, Any

def correlate_post_news(
    results: Iterable[Dict[str, Any]],
    range_key: str = "return1_1d",
    metric: str = "Trend",
    min_obs: int = 10,
) -> Dict[str, Any]:
    """
    Calcula la correlación entre `actual_value` y la métrica elegida
    (por defecto Trend del rango return1_1d).

    Parámetros
    ----------
    results   : iterable de dicts devueltos por analyze_post_news_movements()
    range_key : uno de los keys de rango ('return1_1d', 'return2_3d', …)
    metric    : 'Trend', 'Volatility', 'Range', etc.
    min_obs   : mínimo de pares (x, y) para devolver la métrica

    Devuelve
    --------
    {
        'n': <observaciones>,
        'pearson': <coeficiente o None>,
        'spearman': <coeficiente o None>
    }
    """
    # --- construir DataFrame con las dos columnas necesarias ---
    df = pd.DataFrame(results, copy=False)

    # extraer Y del rango elegido
    df["_y"] = df[range_key].apply(
        lambda d: d.get(metric) if isinstance(d, dict) else None
    )

    # filtrar pares válidos
    df_valid = df[["actual_value", "_y"]].dropna()

    n = len(df_valid)
    if n < min_obs:
        return {"n": n, "pearson": None, "spearman": None}

    pearson = df_valid["actual_value"].corr(df_valid["_y"], method="pearson")
    spearman = df_valid["actual_value"].corr(df_valid["_y"], method="spearman")

    return {"n": n, "pearson": float(pearson), "spearman": float(spearman)}






'''


# Análisis de movimientos posteriores a noticias económicas

Este módulo analiza el comportamiento del índice US30 (Dow Jones) luego de la publicación de datos económicos, utilizando un dataset horario (`US30_H1.csv`). Se basa en una lista de fechas de publicaciones (`news_datetime_list`).

---

## 📌 Funciones involucradas
- `analyze_post_news_movements(news_datetime_list, from_date, to_date)`
- `_get_range_metrics(df, day1_start, day_from, day_to)`

---

## 🔁 Pasos que realiza `analyze_post_news_movements()`

1. **Carga el archivo CSV** `US30_H1.csv`.
2. Convierte la columna `"DateTime"` a tipo `datetime` y filtra las filas entre `from_date` y `to_date`.
3. Crea una nueva columna `"Day"` con la fecha sin hora (`.dt.date`).
4. Recorre cada fecha de publicación (`news_dt`) en la lista:
   - Busca el **primer día disponible con datos posterior** a esa fecha.
   - Si no encuentra ninguno, omite esa publicación.
5. Usa ese primer día (`day1_start`) como referencia base para construir los siguientes rangos de análisis:
   - `return_1d`: Día 1
   - `return_3d`: Días 2 y 3
   - `return_5d`: Días 4 y 5
   - `return_10d`: Días 6 al 10
   - `return_15d`: Días 11 al 15
6. Para cada rango, llama a `_get_range_metrics()` para calcular:

   - **Open**: precio de apertura del primer día del rango.
   - **Close**: precio de cierre del último día del rango.
   - **High**: máximo precio entre todas las velas del rango.
   - **Low**: mínimo precio entre todas las velas del rango.
   - **Range**: diferencia `High - Low`.
   - **Trend**: diferencia `Close - Open`.
   - **Volatility**: desviación estándar de los retornos (`Return`) si existe la columna.

7. Almacena los resultados en un diccionario por cada noticia.
8. Devuelve una lista de resultados con la estructura completa.

---



'''
