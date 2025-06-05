import pandas as pd
import os

def load_economic_news():
    # Ruta al CSV
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path = os.path.join(base_dir, "Datasets", "Economic_data_CSV.csv")

    # Leer y procesar
    df = pd.read_csv(file_path)
    df["publication_date"] = pd.to_datetime(df["publication_date"])
    df = df[df["publication_date"].dt.year >= 2015]
    df["DateTime"] = pd.to_datetime(df["publication_date"].dt.strftime("%Y-%m-%d") + " " + df["publication_time"])

    # Convertir fechas a string para que sean JSON serializables
    df["DateTime"] = df["DateTime"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df["publication_date"] = df["publication_date"].dt.strftime("%Y-%m-%d")

    return df

def get_id_title_dict():
    df = load_economic_news()
    unique_ids = df.drop_duplicates(subset="id_new_name")[["id_new_name", "title"]]
    return dict(zip(unique_ids["id_new_name"], unique_ids["title"]))
