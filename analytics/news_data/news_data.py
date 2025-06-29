import pandas as pd
import os
from db_connection import get_connection

# === Fechas de filtro (modificables) ===
start_date = pd.to_datetime("2015-01-01")
end_date = pd.to_datetime("2025-04-30")


# === Leer CSV original (usado para los títulos) ===
def load_economic_news():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path = os.path.join(base_dir, "Datasets", "Economic_data_CSV.csv")

    df = pd.read_csv(file_path)
    df["publication_date"] = pd.to_datetime(df["publication_date"])
    df = df[df["publication_date"].dt.year >= 2015]
    df["DateTime"] = pd.to_datetime(df["publication_date"].dt.strftime("%Y-%m-%d") + " " + df["publication_time"])

    # Serialización segura
    df["DateTime"] = df["DateTime"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df["publication_date"] = df["publication_date"].dt.strftime("%Y-%m-%d")

    return df


# === Diccionario de títulos por ID ===
def get_id_title_dict():
    df = load_economic_news()
    unique_ids = df.drop_duplicates(subset="id_new_name")[["id_new_name", "title"]]
    return dict(zip(unique_ids["id_new_name"], unique_ids["title"]))


# === Leer desde PostgreSQL ===
def fetch_news_data():
    conn = get_connection()
    query = "SELECT * FROM economic_news_data"
    df = pd.read_sql(query, conn)
    conn.close()

    # Procesar fechas y hora
    df["publication_date"] = pd.to_datetime(df["publication_date"], utc=True).dt.tz_localize(None)
    df["publication_time"] = df["publication_time"].astype(str)

    # Filtro por fechas
    df = df[
        (df["publication_date"] >= start_date) &
        (df["publication_date"] <= end_date)
    ].copy()

    # Convertir fecha a string para evitar errores en jsonify
    # Convertir a string fechas y horas
    df["publication_date"] = df["publication_date"].dt.strftime("%Y-%m-%d")
    df["publication_time"] = df["publication_time"].astype(str)

    # Convertir NaN/NaT a None para que jsonify no falle
    df = df.replace({pd.NA: None, pd.NaT: None})
    df = df.where(pd.notnull(df), None)

    # (opcional extra fuerte)
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