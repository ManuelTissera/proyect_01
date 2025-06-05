
from scipy.stats import shapiro
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Cargar dataset
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
file_path = os.path.join(base_dir, "Datasets", "Historic_Year_US30.csv")
df = pd.read_csv(file_path)

data = df.to_dict(orient="records")


drawdown_val = df['Drawdown'].values
drawup_val = df['Drawup'].values
variation_val = df['Variation'].values
amplitude_val = df['Amplitude'].values
def calcular_r2(x, y):
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    beta = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    alpha = y_mean - beta * x_mean
    y_pred = alpha + beta * x

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)

    if ss_tot == 0:
        return None
    else:
        return 1 - (ss_res / ss_tot)

def regresion_fn(x, y, measures):
    r2 = calcular_r2(x, y)

    # √X: filtramos donde x >= 0
    valid_sqrt = x >= 0
    r2_sqrt = calcular_r2(np.sqrt(x[valid_sqrt]), y[valid_sqrt]) if np.any(valid_sqrt) else "N/A"

    # log(X): filtramos donde x > 0
    valid_log = x > 0
    r2_log = calcular_r2(np.log(x[valid_log]), y[valid_log]) if np.any(valid_log) else "N/A"

    # Regresión base
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    beta = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    alpha = y_mean - beta * x_mean

    return {
        "Measures": measures,
        "Pendiente": round(beta, 4),
        "Intercepto": round(alpha, 4),
        "R2": round(r2, 4) if r2 is not None else "N/A",
        "R2_sqrt": round(r2_sqrt, 4) if isinstance(r2_sqrt, float) else r2_sqrt,
        "R2_log": round(r2_log, 4) if isinstance(r2_log, float) else r2_log
    }



def analizar_residuos(x, y, label=""):
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    beta = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
    alpha = y_mean - beta * x_mean
    y_pred = alpha + beta * x

    residuos = y - y_pred

    # Crear figura con 2 subplots horizontales
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))

    # Subplot 1: Residuos vs Predicciones
    axs[0].scatter(y_pred, residuos, color='blue', alpha=0.6)
    axs[0].axhline(0, color='red', linestyle='--')
    axs[0].set_title(f"Residuos vs Predicción\n{label}")
    axs[0].set_xlabel("Predicción")
    axs[0].set_ylabel("Residuo")

    # Subplot 2: Histograma de residuos
    axs[1].hist(residuos, bins=20, edgecolor='black', color='gray')
    axs[1].set_title(f"Histograma de Residuos\n{label}")
    axs[1].set_xlabel("Residuo")
    axs[1].set_ylabel("Frecuencia")

    plt.tight_layout()
    plt.show()

    # Prueba de normalidad
    stat, p = shapiro(residuos)
    print(f"Shapiro-Wilk para {label} → p-value = {p:.4f}")
    if p > 0.05:
        print("✅ Distribución normal (residuos aceptables)")
    else:
        print("❌ No normal (residuos podrían tener problemas)")


# analizar_residuos(drawup_val, variation_val, "Drawup/Variation")



def get_historic_data():

    cov_matrix = df[["Amplitude", "Variation", "Drawup", "Drawdown"]].cov()
    corr_matrix = df[["Amplitude", "Variation", "Drawup", "Drawdown"]].corr()

    # Armar pares y valores específicos
    pairs = [
        ("amp_var", "Amplitude", "Variation"),
        ("amp_up", "Amplitude", "Drawup"),
        ("amp_down", "Amplitude", "Drawdown"),
        ("var_up", "Variation", "Drawup"),
        ("var_down", "Variation", "Drawdown"),
        ("up_down", "Drawup", "Drawdown")
    ]

    cov_result = {name: cov_matrix.loc[a, b] for name, a, b in pairs}
    corr_result = {name: corr_matrix.loc[a, b] for name, a, b in pairs}

    return {
        "data_df": data,
        "covariance": cov_result,
        "correlation": corr_result,
        "regression": [
            regresion_fn(drawdown_val, amplitude_val, "Drawdown/Amplitude"),
            regresion_fn(drawup_val, amplitude_val, "Drawup/Amplitude"),
            regresion_fn(drawup_val, variation_val, "Drawup/Variation")
        ]
    }

