
def format_seconds_to_days_time(seconds):
    if seconds == 0:
        return "(Days: 0) - (Time: 00:00:00)"
    
    days = seconds // (24 * 3600)
    remainder = seconds % (24 * 3600)
    hours = remainder // 3600
    remainder %= 3600
    minutes = remainder // 60
    secs = remainder % 60

    return f"(Days: {int(days)}) - (Time: {int(hours):02}:{int(minutes):02}:{int(secs):02})"

def calculate_streak_intervals(target_streak):
    # Detectar si tenemos 'DateTime' o solo 'Date'
    if "DateTimeStr" in df.columns:
        date_list = df["DateTimeStr"].tolist()
        date_list = pd.to_datetime(date_list)
    elif "Date" in df.columns:
        date_list = df["Date"].tolist()
        date_list = pd.to_datetime(date_list)
    else:
        raise ValueError("No se encontró columna DateTimeStr ni Date en el dataset.")

    trend_list = df["Trend"].tolist()

    streak_starts = []
    count = 1
    start_index = 0
    prev_positive = trend_list[0] >= 0

    for i, (current, next_value) in enumerate(zip(trend_list, trend_list[1:] + [None])):
        if next_value is None:
            streak = count if prev_positive else -count
            if streak == target_streak:
                streak_starts.append(date_list[start_index])
            break

        current_positive = next_value >= 0

        if current_positive == prev_positive:
            count += 1
        else:
            streak = count if prev_positive else -count
            if streak == target_streak:
                streak_starts.append(date_list[start_index])
            start_index = i + 1
            count = 1
            prev_positive = current_positive

    # Calcular las diferencias en segundos
    time_diffs = []
    for i in range(1, len(streak_starts)):
        diff = (streak_starts[i] - streak_starts[i-1]).total_seconds()
        time_diffs.append(diff)

    if not time_diffs:
        print("No hay suficientes rachas para calcular diferencias.")
        return

    diffs_array = np.array(time_diffs)

    avg_seconds = np.mean(diffs_array)
    var_seconds = np.var(diffs_array)
    std_seconds = np.std(diffs_array)
    min_seconds = np.min(diffs_array)
    max_seconds = np.max(diffs_array)
    median_seconds = np.median(diffs_array)
    iqr_seconds = np.percentile(diffs_array, 75) - np.percentile(diffs_array, 25)

    print("-------------------------------------------------")
    print(f"Cantidad de diferencias calculadas: {len(time_diffs)}")
    print(f"Promedio de intervalo: {avg_seconds:.2f} segundos {format_seconds_to_days_time(avg_seconds)}")
    print(f"Mediana de intervalo: {median_seconds:.2f} segundos {format_seconds_to_days_time(median_seconds)}")
    print(f"Rango intercuartil (IQR): {iqr_seconds:.2f} segundos {format_seconds_to_days_time(iqr_seconds)}")
    print(f"Varianza del intervalo: {var_seconds:.2f} segundos²")
    print(f"Desviación estándar del intervalo: {std_seconds:.2f} segundos")
    print(f"Intervalo mínimo: {min_seconds:.2f} segundos {format_seconds_to_days_time(min_seconds)}")
    print(f"Intervalo máximo: {max_seconds:.2f} segundos {format_seconds_to_days_time(max_seconds)}")
    print("-------------------------------------------------")

    # Histograma
    plt.figure(figsize=(10,6))
    plt.hist(diffs_array, bins=15, edgecolor='black')
    plt.xlabel("Intervalo entre rachas (segundos)")
    plt.ylabel("Frecuencia")
    plt.title(f"Histograma de diferencias de tiempo - Racha {target_streak}")
    plt.grid(True)
    plt.show()

    # Test de Shapiro-Wilk
    stat, p_value = shapiro(diffs_array)
    print(f"Resultado Shapiro-Wilk Test:")
    print(f"Estadístico W = {stat:.4f}")
    print(f"Valor p = {p_value:.4f}")

    if p_value > 0.05:
        print("Conclusión: No se rechaza la normalidad. ✅")
    else:
        print("Conclusión: Se rechaza la normalidad. ❌")

    print("-------------------------------------------------")
    # Análisis con percentiles 5% y 95%
    lower_bound = np.percentile(diffs_array, 5)
    upper_bound = np.percentile(diffs_array, 95)
    filtered_diffs = diffs_array[(diffs_array >= lower_bound) & (diffs_array <= upper_bound)]

    avg_filtered = np.mean(filtered_diffs)
    var_filtered = np.var(filtered_diffs)
    std_filtered = np.std(filtered_diffs)
    median_filtered = np.median(filtered_diffs)
    iqr_filtered = np.percentile(filtered_diffs, 75) - np.percentile(filtered_diffs, 25)

    print(f"Después de eliminar extremos (5%-95%):")
    print(f"Cantidad de diferencias consideradas: {len(filtered_diffs)}")
    print(f"Promedio filtrado: {avg_filtered:.2f} segundos {format_seconds_to_days_time(avg_filtered)}")
    print(f"Mediana filtrada: {median_filtered:.2f} segundos {format_seconds_to_days_time(median_filtered)}")
    print(f"Rango intercuartil (IQR) filtrado: {iqr_filtered:.2f} segundos {format_seconds_to_days_time(iqr_filtered)}")
    print(f"Varianza filtrada: {var_filtered:.2f} segundos²")
    print(f"Desviación estándar filtrada: {std_filtered:.2f} segundos")
    print("-------------------------------------------------")

    # Cálculo de rangos de confianza
    conf_50_lower = np.percentile(filtered_diffs, 25)
    conf_50_upper = np.percentile(filtered_diffs, 75)

    conf_80_lower = np.percentile(filtered_diffs, 10)
    conf_80_upper = np.percentile(filtered_diffs, 90)

    print(f"Rango de confianza 50% (25%-75%):")
    print(f"Desde {conf_50_lower:.2f} segundos {format_seconds_to_days_time(conf_50_lower)} hasta {conf_50_upper:.2f} segundos {format_seconds_to_days_time(conf_50_upper)}")
    print(f"Rango de confianza 80% (10%-90%):")
    print(f"Desde {conf_80_lower:.2f} segundos {format_seconds_to_days_time(conf_80_lower)} hasta {conf_80_upper:.2f} segundos {format_seconds_to_days_time(conf_80_upper)}")
    print("-------------------------------------------------")

    return time_diffs
calculate_streak_intervals(-8)