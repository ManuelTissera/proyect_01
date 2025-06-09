import pandas as pd
import os
from db_connection import get_connection

# === Fechas de filtro (modificables) ===
start_date = pd.to_datetime("2015-01-01")
end_date = pd.to_datetime("2025-04-30")

def fetch_news_data(id_new_name):
    conn = get_connection()
    query = "SELECT * FROM economic_news_data WHERE id_new_name = %s"
    df = pd.read_sql(query, conn, params=[id_new_name])
    conn.close()

    # Procesar fechas y hora
    df["publication_date"] = pd.to_datetime(df["publication_date"], utc=True).dt.tz_localize(None)
    df["publication_time"] = df["publication_time"].astype(str)

    # Filtro por fechas
    df = df[
        (df["publication_date"] >= start_date) &
        (df["publication_date"] <= end_date)
    ].copy()

    # Convertir a string fechas y horas
    df["publication_date"] = df["publication_date"].dt.strftime("%Y-%m-%d")
    df["publication_time"] = df["publication_time"].astype(str)

    # Limpieza para jsonify
    df = df.replace({pd.NA: None, pd.NaT: None})
    df = df.where(pd.notnull(df), None)
    df = df.astype(object).where(pd.notnull(df), None)

    return df.to_dict(orient="records")


def fetch_news_name():
    conn = get_connection()
    query = "SELECT * FROM news_name"
    df = pd.read_sql(query, conn)
    conn.close()

    # Convertir NaN a None para JSON válido
    df = df.replace({pd.NA: None, pd.NaT: None})
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")