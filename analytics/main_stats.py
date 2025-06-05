
import pandas as pd
import sys
import os

# Agregar stat_analysis al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stat_analysis import descriptive

# Cargar dataset
df = pd.read_csv("US30_H1.csv")

# Asegurarse que Date sea tipo datetime
df["Date"] = pd.to_datetime(df["Date"])


# Agrupar por día
grouped = df.groupby(df["Date"].dt.date)

# Aplicar funciones por grupo
for day, group in grouped:
   close = group["Close"]
   print(f"\n📅 Día: {day}")
   print("Media:", descriptive.mean(close))
   print("Mediana:", descriptive.median(close))
   print("Moda:", descriptive.mode(close))
   print("Varianza:", descriptive.variance(close))
   print("Des. Estand.:", descriptive.std_deviation(close))
   print("Rango:", descriptive.range_value(close))
   print("Coef. Var:", descriptive.coefficient_of_variation(close))
   # print(f"\n📅 Día: {day}",sum(close))





