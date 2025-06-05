import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.abspath(os.path.join(os.path.dirname('__file__'), '..')))

base_dir = os.path.dirname(os.path.dirname(__file__))
file_path = os.path.join(base_dir,"Datasets","US30_H1.csv")

df = pd.read_csv(file_path)

def calculate_above_sma(df):
    df['Above_SMA'] = df['SMA20'] > df['SMA200']
    return df


def find_streaks(df):
    streaks = []
    current_streak = 0
    for value in df['Above_SMA']:
        if value:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
                current_streak = 0
    if current_streak > 0:
        streaks.append(current_streak)
    return streaks


def plot_streaks(streaks):
    fig, axs = plt.subplots(2, 1, figsize=(12, 10))

    axs[0].plot(streaks, marker='o')
    axs[0].set_title('Duración de las rachas donde SMA20 > SMA200 (orden original)')
    axs[0].set_xlabel('Número de racha')
    axs[0].set_ylabel('Duración en períodos')
    axs[0].grid(True)

    streaks_sorted = sorted(streaks)
    axs[1].plot(streaks_sorted, marker='o')
    axs[1].set_title('Duración de las rachas donde SMA20 > SMA200 (ordenado)')
    axs[1].set_xlabel('Índice ordenado')
    axs[1].set_ylabel('Duración en períodos')
    axs[1].grid(True)

    plt.tight_layout()
    plt.show()


def analyze_value_ranges(streaks):
    max_streak = max(streaks)
    p1 = max_streak / 4
    p2 = max_streak / 2
    p3 = max_streak * 0.75

    part_1, part_2, part_3, part_4 = [], [], [], []
    for value in streaks:
        if value <= p1:
            part_1.append(value)
        elif p1 < value <= p2:
            part_2.append(value)
        elif p2 < value <= p3:
            part_3.append(value)
        else:
            part_4.append(value)

    return part_1 + part_2 + part_3 + part_4, ['0-25%']*len(part_1) + ['25-50%']*len(part_2) + ['50-75%']*len(part_3) + ['75-100%']*len(part_4)
def analyze_manual_ranges(streaks):
    import pandas as pd
    from analytics.SMAs.SMA import df  # Asegurate de tener `df` accesible desde acá

    max_streak = max(streaks)
    p1 = max_streak / 5
    p2 = max_streak * 2 / 5
    p3 = max_streak * 3 / 5
    p4 = max_streak * 4 / 5

    part_1, part_2, part_3, part_4, part_5 = [], [], [], [], []
    end_indices = []
    current_index = 0

    for value in streaks:
        if value <= p1:
            part_1.append(value)
        elif p1 < value <= p2:
            part_2.append(value)
            current_index += value
            end_indices.append(current_index - 1)
        elif p2 < value <= p3:
            part_3.append(value)
            current_index += value
            end_indices.append(current_index - 1)
        elif p3 < value <= p4:
            part_4.append(value)
            current_index += value
            end_indices.append(current_index - 1)
        else:
            part_5.append(value)
            current_index += value
            end_indices.append(current_index - 1)
        if value <= p1:
            current_index += value

    selected_parts = part_2 + part_3 + part_4 + part_5

    print("------- Quantity Values Manual Ranges ------")
    res_sum = len(selected_parts)
    print('---> Cantidad de valores:', res_sum)
    print(sorted(selected_parts))
    print('----------------------------------------------------')
    print(sorted(part_1))
    print('----------------------------------------------------')

    # Estadísticas
    serie = pd.Series(selected_parts)
    print("📊 Estadísticas para Partes 2 a 5:")
    print(f"- Promedio: {serie.mean():.2f}")
    print(f"- Mediana: {serie.median():.2f}")
    print(f"- Desviación estándar: {serie.std():.2f}")
    print(f"- Rango intercuartílico (IQR): {serie.quantile(0.75) - serie.quantile(0.25):.2f}")
    print(f"- Mínimo: {serie.min()} | Máximo: {serie.max()}")
    print(f"- CV: {serie.std() / serie.mean():.2f}")
    print('----------------------------------------------------')

    # Validación de tendencia posterior
    print("📈 Evaluación de tendencias posteriores:")
    for idx, length in zip(end_indices, selected_parts):
        close_price = df.loc[idx, "Close"]
        tp = close_price + 500
        sl = close_price - 300
        future = df.iloc[idx + 1: idx + 51]
        status = "❓ Sin confirmación"
        for i, row in future.iterrows():
            if row["Low"] <= sl:
                status = "❌ Invalidada"
                break
            if row["High"] >= tp:
                status = "✅ Confirmada"
                break
        print(f"{df.loc[idx, 'DateTimeStr']} | Racha de {length} → {status}")

    return (
        part_1 + part_2 + part_3 + part_4 + part_5,
        ['Parte 1']*len(part_1) + ['Parte 2']*len(part_2) + ['Parte 3']*len(part_3) + ['Parte 4']*len(part_4) + ['Parte 5']*len(part_5),
        selected_parts
    )


def analyze_custom_percentiles(streaks):
    streaks_series = pd.Series(streaks)
    percentiles = streaks_series.quantile([0.80, 0.90, 0.95])

    above_80 = streaks_series[streaks_series > percentiles[0.80]].tolist()
    above_90 = streaks_series[streaks_series > percentiles[0.90]].tolist()
    above_95 = streaks_series[streaks_series > percentiles[0.95]].tolist()

    values = above_80 + above_90 + above_95
    categories = ['>80%']*len(above_80) + ['>90%']*len(above_90) + ['>95%']*len(above_95)

    # print('------- Cantidad de valores en P 80% -------')
    # print(len(above_80))
    # print(above_80)
    # print("---------------------------------------------")

    return values, categories


def plot_scatter_dispersion(streaks):
    abs_values, abs_labels = analyze_value_ranges(streaks)
    manual_values, manual_labels, _ = analyze_manual_ranges(streaks)
    perc_values, perc_labels = analyze_custom_percentiles(streaks)

    fig, axs = plt.subplots(1, 3, figsize=(20, 6))

    sns.stripplot(x=abs_labels, y=abs_values, jitter=True, ax=axs[0], order=['0-25%', '25-50%', '50-75%', '75-100%'])
    axs[0].set_title('Dispersión por Rango de Valor Absoluto')
    axs[0].set_xlabel('Rango')
    axs[0].set_ylabel('Duración')

    sns.stripplot(x=manual_labels, y=manual_values, jitter=True, ax=axs[1], order=['Parte 1', 'Parte 2', 'Parte 3', 'Parte 4', 'Parte 5'])
    axs[1].set_title('Dispersión con Cortes Manuales')
    axs[1].set_xlabel('Parte')
    axs[1].set_ylabel('Duración')

    sns.stripplot(x=perc_labels, y=perc_values, jitter=True, ax=axs[2], order=['<=80%', '>80%', '>90%', '>95%'])
    axs[2].set_title('Dispersión por Percentiles (80/90/95)')
    axs[2].set_xlabel('Percentil')
    axs[2].set_ylabel('Duración')

    plt.tight_layout()
    # plt.show()


def analyze_combined(streaks):
    print("\n==============================")
    print("Análisis combinado")
    print("==============================")
    plot_scatter_dispersion(streaks)


# Ejecución del análisis (asumiendo que df ya está cargado)
df = calculate_above_sma(df)
streaks = find_streaks(df)
# print(streaks)
# plot_streaks(streaks)
analyze_combined(streaks)


#============================================================================

def analyze_diff_statistics():
    diff20 = df["Diff-20"].dropna()
    diff200 = df["Diff-200"].dropna()

    def calc_stats(series, label):
        mean_val = np.mean(series)
        median_val = np.median(series)
        std_val = np.std(series)
        iqr_val = np.percentile(series, 75) - np.percentile(series, 25)
        lower_10 = np.percentile(series, 10)
        upper_90 = np.percentile(series, 90)

        print(f"--- Estadísticas para {label} ---")
        print(f"Media: {mean_val:.2f}")
        print(f"Mediana: {median_val:.2f}")
        print(f"Desviación estándar: {std_val:.2f}")
        print(f"Rango intercuartílico (IQR): {iqr_val:.2f}")
        print(f"Rango de confianza 80% (10%-90%): {lower_10:.2f} a {upper_90:.2f}")
        print("----------------------------------")

    calc_stats(diff20, "Diff-20")
    calc_stats(diff200, "Diff-200")


def plot_diff_histograms():
    diff20 = df["Diff-20"].dropna()
    diff200 = df["Diff-200"].dropna()

    plt.figure(figsize=(12, 5))

    # Histograma Diff-20
    plt.subplot(1, 2, 1)
    plt.hist(diff20, bins=30, edgecolor='black')
    plt.title('Histograma Diff-20')
    plt.xlabel('Diferencia con SMA20')
    plt.ylabel('Frecuencia')
    plt.grid(True)

    # Histograma Diff-200
    plt.subplot(1, 2, 2)
    plt.hist(diff200, bins=30, edgecolor='black')
    plt.title('Histograma Diff-200')
    plt.xlabel('Diferencia con SMA200')
    plt.ylabel('Frecuencia')
    plt.grid(True)

    plt.tight_layout()
    plt.show()


def classify_diff_distances():
    diff20 = df["Diff-20"].dropna()
    diff200 = df["Diff-200"].dropna()

    # Umbrales configurables
    close_threshold = 100
    moderate_threshold = 300

    def classify(series, label):
        total = len(series)
        close = np.sum(np.abs(series) <= close_threshold)
        moderate = np.sum((np.abs(series) > close_threshold) & (np.abs(series) <= moderate_threshold))
        far = np.sum(np.abs(series) > moderate_threshold)

        print(f"--- Clasificación de distancias para {label} ---")
        print(f"Cerca (|diff| <= {close_threshold}): {close} ({(close/total)*100:.2f}%)")
        print(f"Moderado ({close_threshold} < |diff| <= {moderate_threshold}): {moderate} ({(moderate/total)*100:.2f}%)")
        print(f"Lejos (|diff| > {moderate_threshold}): {far} ({(far/total)*100:.2f}%)")
        print("----------------------------------------------")

    classify(diff20, "Diff-20")
    classify(diff200, "Diff-200")


def analyze_diff_correlation_with_streaks():
    # Preparamos las columnas necesarias
    streaks_list = get_trend_streaks()

    # Creamos una lista de indices donde terminan las rachas
    indices = []
    count = 0
    for s in streaks_list:
        count += abs(s)
        indices.append(count - 1)  # -1 porque el índice empieza en 0

    # Sacamos las filas correspondientes
    valid_indices = [i for i in indices if i < len(df)]

    # Creamos nuevo DataFrame para el análisis
    analysis_df = df.iloc[valid_indices].copy()
    analysis_df["StreakLength"] = [abs(s) for s in streaks_list if (abs(s) > 0)]

    # Ahora correlacionamos
    corr_diff20 = np.corrcoef(np.abs(analysis_df["Diff-20"]), analysis_df["StreakLength"])[0,1]
    corr_diff200 = np.corrcoef(np.abs(analysis_df["Diff-200"]), analysis_df["StreakLength"])[0,1]

    print("-------------------------------------------------")
    print(f"Correlación entre |Diff-20| y duración de racha: {corr_diff20:.4f}")
    print(f"Correlación entre |Diff-200| y duración de racha: {corr_diff200:.4f}")
    print("-------------------------------------------------")


def get_sma_data():
   return