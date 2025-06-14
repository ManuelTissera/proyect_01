import pandas as pd
import os
from db_connection import get_connection

# === Fechas de filtro (modificables) ===
# start_date = pd.to_datetime("2015-01-01")
# end_date = pd.to_datetime("2025-04-30")

def fetch_news_data(id_new_name, start="2015-01-01", end="2025-04-01"):
    conn = get_connection()
    query = "SELECT * FROM economic_news_data WHERE id_new_name = %s ORDER BY publication_date DESC"
    df = pd.read_sql(query, conn, params=[id_new_name])
    conn.close()

    df["publication_date"] = pd.to_datetime(df["publication_date"], utc=True).dt.tz_localize(None)
    df["publication_time"] = df["publication_time"].astype(str)

    start_date = pd.to_datetime(start)
    end_date = pd.to_datetime(end)

    df = df[
        (df["publication_date"] >= start_date) &
        (df["publication_date"] <= end_date)
    ].copy()


    
    # Obtener fecha de inicio real
    fecha_inicio = df["publication_date"].min().strftime("%Y-%m-%d") if not df.empty else "2015-01-01"

    # Convertir a string fechas y horas
    df["publication_date"] = df["publication_date"].dt.strftime("%Y-%m-%d")
    df["publication_time"] = df["publication_time"].astype(str)

    # Limpieza para jsonify
    df = df.replace({pd.NA: None, pd.NaT: None})
    df = df.where(pd.notnull(df), None)
    df = df.astype(object).where(pd.notnull(df), None)

    return {
        "data": df.to_dict(orient="records"),
        "start_date": fecha_inicio
    }


def fetch_news_name():
    conn = get_connection()
    query = "SELECT * FROM news_name"
    df = pd.read_sql(query, conn)
    conn.close()

    # Convertir NaN a None para JSON válido
    df = df.replace({pd.NA: None, pd.NaT: None})
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")




def fetch_us30_data(start="2015-01-01", end="2025-04-01"):
    import pandas as pd
    import os

    # === Fechas de filtro (modificables) ===
    start_date = pd.to_datetime(start)
    end_date = pd.to_datetime(end)

    # === Path del archivo CSV ===
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path_us30 = os.path.join(base_dir, "Datasets", "US30_H1.csv")

    # === Cargar y procesar ===
    df = pd.read_csv(file_path_us30)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

    # Agrupar por día
    df["Day"] = df["Date"].dt.date
    grouped = df.groupby("Day").agg({
        "Open": "first",
        "Close": "last",
        "High": "max",
        "Low": "min"
    }).reset_index()

    # Renombrar columna Day a Date y formatear
    grouped.rename(columns={"Day": "Date"}, inplace=True)
    grouped["Date"] = pd.to_datetime(grouped["Date"]).dt.strftime("%Y-%m-%d")

    # Convertir para enviar como JSON
    grouped = grouped.replace({pd.NA: None, pd.NaT: None})
    grouped = grouped.where(pd.notnull(grouped), None)

    return grouped.to_dict(orient="records")
