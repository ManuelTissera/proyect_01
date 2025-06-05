import pandas as pd
import os
import shutil
from datetime import datetime

# === FUNCIONES ===
def leer_csv_flexible(filepath):
    for enc in ['utf-8', 'utf-16']:
        try:
            df = pd.read_csv(filepath, encoding=enc, sep='\t')
            print(f"\n✓ Leído correctamente: {os.path.basename(filepath)} con codificación: {enc}")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo leer el archivo con utf-8 ni utf-16")

def estandarizar_fecha(df):
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    if "Date" not in df.columns:
        raise KeyError(f'Columna "Date" no encontrada. Columnas actuales: {df.columns.tolist()}')
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.strftime("%Y-%m-%d")
    return df

def estandarizar_fecha_hora(df):
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    if "Date" not in df.columns or "Time" not in df.columns:
        raise KeyError(f'Columnas requeridas no encontradas. Columnas actuales: {df.columns.tolist()}')
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.strftime("%Y-%m-%d")
    df["Time"] = df["Time"].astype(str).str.strip().apply(
        lambda x: x + ":00" if len(x) == 4 or len(x) == 5 else x
    )
    df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors='coerce')
    df["DateTimeStr"] = df["DateTime"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df

def calcular_rsi(df, n=14):
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=n).mean()
    avg_loss = loss.rolling(window=n).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_macd(df, short=12, long=26, signal=9):
    ema_short = df["Close"].ewm(span=short, adjust=False).mean()
    ema_long = df["Close"].ewm(span=long, adjust=False).mean()
    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def add_columns(df):
    df["MidPrice"] = (df["High"] + df["Low"]) / 2
    df["TypicalPrice"] = (df["High"] + df["Low"] + df["Close"]) / 3
    df["Range"] = df["High"] - df["Low"]
    df["Trend"] = df["Close"] - df["Open"]
    df["Return"] = (df["Close"] - df["Open"]) / df["Open"]
    df["R_CloToClo"] = df["Close"].pct_change()
    df["Diff-20"] = df["Open"] - df["SMA20"]
    df["Diff-200"] = df["Open"] - df["SMA200"]
    df["RSI_14"] = calcular_rsi(df)
    df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = calcular_macd(df)
    return df

def calcular_bollinger_bands(df, columna='Close', periodo=20, num_std=2):
    """
    Agrega columnas con Bandas de Bollinger:
    - BB_Upper: Banda superior
    - BB_Lower: Banda inferior
    - BB_Width: Diferencia entre ambas
    """
    sma = df[columna].rolling(window=periodo).mean()
    std = df[columna].rolling(window=periodo).std()

    df["BB_Upper"] = sma + num_std * std
    df["BB_Lower"] = sma - num_std * std
    df["BB_Width"] = df["BB_Upper"] - df["BB_Lower"]

    return df

def calcular_volatilidad(df, columna='Close', ventana=20):
    """
    Calcula la desviación estándar móvil (volatilidad) sobre una columna.
    - Agrega la columna: Volatility_20 (o del período definido)
    """
    nombre_columna = f"Volatility_{ventana}"
    df[nombre_columna] = df[columna].rolling(window=ventana).std()
    return df

def calculate_true_range_atr(df, window=14):
    """
    Calcula:
    - True Range (TR)
    - Average True Range (ATR)
    """

    prev_close = df["Close"].shift(1)

    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - prev_close).abs()
    low_prev_close = (df["Low"] - prev_close).abs()

    df["TrueRange"] = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    df["ATR"] = df["TrueRange"].rolling(window=window).mean()

    return df

def calcular_zscore(df, period=20):
    media = df["Close"].rolling(window=period).mean()
    std = df["Close"].rolling(window=period).std()
    df["ZScore_20"] = (df["Close"] - media) / std
    return df

def calculate_stochastic_oscillator(df, k_period=14, d_period=3):
    """
    Calcula el Oscilador Estocástico:
    - %K = (Close - Low_min) / (High_max - Low_min) * 100
    - %D = media móvil simple de %K

    Devuelve dos columnas nuevas:
    - Stoch_%K
    - Stoch_%D
    """
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()

    df["Stoch_%K"] = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    df["Stoch_%D"] = df["Stoch_%K"].rolling(window=d_period).mean()

    return df

def calculate_momentum_roc(df, period=10):
    """
    Calcula:
    - Momentum: Close - Close(n períodos atrás)
    - ROC: Variación relativa en porcentaje (decimal)

    Agrega dos columnas:
    - Momentum_10
    - ROC_10
    """
    prev_close = df["Close"].shift(period)
    df["Momentum_10"] = df["Close"] - prev_close
    df["ROC_10"] = (df["Close"] - prev_close) / prev_close
    return df

def add_temporal_columns(df):
    """
    Agrega columnas temporales:
    - DayOfWeek (0=Lunes, ..., 6=Domingo)
    - DayOfMonth (1–31)
    - Month (1–12)
    - Hour (si existe columna Time)
    """
    if "DateTime" in df.columns:
        df["DayOfWeek"] = df["DateTime"].dt.dayofweek
        df["DayOfMonth"] = df["DateTime"].dt.day
        df["Month"] = df["DateTime"].dt.month
        df["Hour"] = df["DateTime"].dt.hour
    elif "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df["DayOfWeek"] = df["Date"].dt.dayofweek
        df["DayOfMonth"] = df["Date"].dt.day
        df["Month"] = df["Date"].dt.month
    return df




# === EJECUCIÓN ===
carpeta_crudos = "../CRUDOS"
carpeta_destino = "./"
carpeta_backup = os.path.join(carpeta_crudos, "BACKUPS_CRUDOS")
os.makedirs(carpeta_backup, exist_ok=True)

for archivo in os.listdir(carpeta_crudos):
    if archivo.endswith("_C.csv") and ("US30" in archivo or "USSPX500" in archivo):
        path_entrada = os.path.join(carpeta_crudos, archivo)
        df = leer_csv_flexible(path_entrada)

        # Selección de estandarizador según nombre
        if "D1" in archivo:
            df = estandarizar_fecha(df)
        else:
            df = estandarizar_fecha_hora(df)

        columnas_a_numericas = df.columns.difference(["Date", "Time", "DateTime", "DateTimeStr"])
        df[columnas_a_numericas] = df[columnas_a_numericas].apply(pd.to_numeric, errors='coerce')

        df = add_columns(df)
        df = calcular_bollinger_bands(df)
        df = calcular_zscore(df)
        df = calculate_stochastic_oscillator(df)
        df = calcular_volatilidad(df)
        df = calculate_true_range_atr(df) 
        df = calculate_momentum_roc(df)
        df = add_temporal_columns(df)





        # Guardar con nombre sin "_C"
        nombre_salida = archivo.replace("_C", "")
        path_salida = os.path.join(carpeta_destino, nombre_salida)
        df.to_csv(path_salida, index=False, encoding="utf-8")
        print(f"✓ Archivo procesado: {nombre_salida}")

        # Backup antes de eliminar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = archivo.replace(".csv", f"_backup_{timestamp}.csv")
        path_backup = os.path.join(carpeta_backup, nombre_backup)
        shutil.copy(path_entrada, path_backup)
        print(f"⬇️ Backup guardado: {nombre_backup}")

        # Eliminar crudo
        os.remove(path_entrada)
        print(f"✗ Crudo eliminado: {archivo}")
