# band_boll_data.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt   # se usa en otras funciones

# === cargar dataset ===
base_dir  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
file_path = os.path.join(base_dir, "Datasets", "US30_H1.csv")
df = pd.read_csv(file_path)

# Filtrar fechas
start_date = 2018
end_date   = 2025
df["Date"] = pd.to_datetime(df["Date"])
df = df[(df["Date"].dt.year >= start_date) & (df["Date"].dt.year <= end_date)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 1) Funciones originales
# ---------------------------------------------------------------------------
def get_bollinger_band_extremes():
    """
    Devuelve, día por día, los valores mínimos de BB_Lower y
    máximos de BB_Upper, junto con la amplitud diaria.
    """
    result = (
        df.groupby(df["Date"].dt.date)
          .agg({"BB_Lower": "min", "BB_Upper": "max"})
          .reset_index()
    )
    result["Amplitude"] = result["BB_Upper"] - result["BB_Lower"]
    return result.to_dict(orient="records")


def get_low_below_lower_band():
    """
    Lista todas las velas cuyo Low < BB_Lower y devuelve su Diff
    junto con estadísticas básicas.
    """
    filtered = df[df["Low"] < df["BB_Lower"]][["Date", "Low", "BB_Lower"]].copy()
    filtered["Date"] = (
        pd.to_datetime(filtered["Date"])
          .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    diff_list = (filtered["BB_Lower"] - filtered["Low"]).tolist()
    P25 = sorted(diff_list)[int(0.25 * len(diff_list))]

    diff_list_more_P25 = [
        {"Date": date, "Diff": diff}
        for date, diff in zip(filtered["Date"], diff_list)
        if diff > P25
    ]

    return {
        "data_info": {
            "start_date": start_date,
            "end_date":   end_date,
            "diff_list_more_P25":  diff_list_more_P25,
            "max_diff":   max(diff_list) if diff_list else None,
            "min_diff":   min(diff_list) if diff_list else None,
        }
    }


# ---------------------------------------------------------------------------
# 2) Nueva función: get_bollinger_streaks
# ---------------------------------------------------------------------------
def get_bollinger_streaks(tp_pct: float = 0.01,
                          sl_pct: float = 0.01,
                          max_candles: int = 350):
    """
    • Detecta rupturas de la banda inferior cuyo Diff > P25.
    • Abre un trade en la vela siguiente:
         TP = +tp_pct  (High ≥ Open*(1+tp_pct))  → ObjectiveProfit
         SL = -sl_pct  (Low  ≤ Open*(1-sl_pct))  → LimitLoss
         Sin TP/SL en max_candles               → NoResult
    • No se solapan trades.
    • Devuelve:
        {
          "data": {
            "ObjectiveProfit": [...],
            "LimitLoss":       [...],
            "NoResult":        [...]
          },
          "data_info": { fechas y estadísticas de diff }
        }
    """

    # ---------- 1. calcular diferencias ----------
    mask_break = df["Low"] < df["BB_Lower"]
    breaks_df  = df.loc[mask_break, ["Low", "BB_Lower", "RSI_14"]].copy()
    breaks_df["Diff"] = breaks_df["BB_Lower"] - breaks_df["Low"]
    diff_list  = breaks_df["Diff"].tolist()

    if not diff_list:   # sin rupturas
        return {
            "data": {"ObjectiveProfit": [], "LimitLoss": [], "NoResult": []},
            "data_info": {
                "start_date": start_date,
                "end_date":   end_date,
                "diff_list":  [],
                "max_diff":   None,
                "min_diff":   None
            }
        }

    p25_value = np.percentile(diff_list, 25)

    # ---------- 2. filtrar eventos ----------
    events = breaks_df[breaks_df["Diff"] > p25_value].copy()
    events["EventIdx"] = events.index              # índice dentro de df
    events.sort_values("EventIdx", inplace=True)

    # ---------- 3. listas de salida ----------
    streaksData = {
        "ObjectiveProfit": [],
        "LimitLoss": [],
        "NoResult": []
    }

    # arrays para velocidad
    open_arr   = df["Open"].values
    high_arr   = df["High"].values
    low_arr    = df["Low"].values
    close_arr  = df["Close"].values
    date_arr   = df["Date"].astype(str).values

    cursor = 0   # primera vela libre

    # ---------- 4. recorrer eventos ----------
    for _, ev in events.iterrows():
        ev_idx = int(ev["EventIdx"])
        if ev_idx < cursor:
            continue  # trade anterior sigue activo

        entry_idx = ev_idx + 1
        if entry_idx >= len(df):
            break  # sin vela posterior

        open_entry = open_arr[entry_idx]
        tp_value   = open_entry * (1 + tp_pct)
        sl_value   = open_entry * (1 - sl_pct)
        last_idx   = min(entry_idx + max_candles, len(df) - 1)

        record = {
            "From":       date_arr[entry_idx],
            "StartValue": float(open_entry),
            "StartIdx":   int(entry_idx),
            "Diff":       float(ev["Diff"]),
            "RSI_14":     float(ev["RSI_14"]) if not pd.isna(ev["RSI_14"]) else None
        }

        hit = False
        for j in range(entry_idx + 1, last_idx + 1):
            if low_arr[j] <= sl_value:   # SL tocado primero
                record.update({
                    "To":       date_arr[j],
                    "EndValue": float(close_arr[j]),
                    "EndIdx":   int(j),
                    "Result":   "Limit"
                })
                streaksData["LimitLoss"].append(record)
                hit = True
                break

            if high_arr[j] >= tp_value:  # TP tocado primero
                record.update({
                    "To":       date_arr[j],
                    "EndValue": float(close_arr[j]),
                    "EndIdx":   int(j),
                    "Result":   "Objective"
                })
                streaksData["ObjectiveProfit"].append(record)
                hit = True
                break

        if not hit:  # no TP ni SL
            record.update({
                "To":       date_arr[last_idx],
                "EndValue": float(close_arr[last_idx]),
                "EndIdx":   int(last_idx),
                "Result":   "NoResult"
            })
            streaksData["NoResult"].append(record)

        cursor = record["EndIdx"] + 1  # bloquear hasta vela posterior

    # ---------- 5. retornar ----------
    return {
        "data": streaksData,
        "data_info": {
            "start_date": start_date,
            "end_date":   end_date,
            "diff_list":  diff_list,
            "max_diff":   max(diff_list),
            "min_diff":   min(diff_list)
        }
    }


def get_bollinger_macd_streaks(tp_pct: float = 0.01,
                               sl_pct: float = 0.01,
                               max_candles: int = 350):
    """
    1. Ruptura Bollinger (Low < BB_Lower) con Diff > P25
    2. Primer cruce MACD_Hist <0 → ≥0 tras la ruptura
    3. Trade: Open de la vela siguiente al cruce
    4. Cierre: TP (+tp_pct), SL (−sl_pct) o max_candles
       – sin solapamientos
    """

    mask_break = df["Low"] < df["BB_Lower"]
    bb_df      = df.loc[mask_break, ["Low", "BB_Lower", "RSI_14"]].copy()
    bb_df["Diff"] = bb_df["BB_Lower"] - bb_df["Low"]
    diff_list  = bb_df["Diff"].tolist()

    if not diff_list:
        return {
            "data": {"ObjectiveProfit": [], "LimitLoss": [], "NoResult": []},
            "data_info": {
                "start_date": start_date,
                "end_date":   end_date,
                "diff_list":  [],
                "max_diff":   None,
                "min_diff":   None
            }
        }

    p25_val = np.percentile(diff_list, 25)
    events  = bb_df[bb_df["Diff"] > p25_val].copy()
    events["EventIdx"] = events.index
    events.sort_values("EventIdx", inplace=True)

    macd_hist = df["MACD_Hist"].values
    open_arr  = df["Open"].values
    high_arr  = df["High"].values
    low_arr   = df["Low"].values
    close_arr = df["Close"].values
    date_arr  = df["Date"].astype(str).values

    streaksData = {"ObjectiveProfit": [], "LimitLoss": [], "NoResult": []}
    cursor = 0

    for _, ev in events.iterrows():
        ev_idx = int(ev["EventIdx"])
        if ev_idx < cursor:
            continue

        # ── cruce MACD_Hist alcista ──
        buy_idx = None
        for k in range(ev_idx + 1, len(df)):
            if macd_hist[k - 1] < 0 <= macd_hist[k]:
                buy_idx = k
                break
        if buy_idx is None or buy_idx + 1 >= len(df):
            continue

        entry_idx  = buy_idx + 1
        open_entry = open_arr[entry_idx]
        tp_val     = open_entry * (1 + tp_pct)
        sl_val     = open_entry * (1 - sl_pct)
        last_idx   = min(entry_idx + max_candles, len(df) - 1)

        record = {
            "EventBB":    df["DateTime"][ev_idx],
            "EventMACD":  df["DateTime"][buy_idx],
            "StartValue": float(open_entry),
            "StartIdx":   entry_idx,
            "Diff":       float(ev["Diff"]),
            "RSI_14":     float(ev["RSI_14"]) if not pd.isna(ev["RSI_14"]) else None
        }

        hit = False
        for j in range(entry_idx + 1, last_idx + 1):
            if low_arr[j] <= sl_val:                       # SL
                record.update({
                    "EndValue": float(close_arr[j]),
                    "To":       date_arr[j],
                    "EndIdx":   j,
                    "Result":   "Limit"
                })
                streaksData["LimitLoss"].append(record)
                hit = True
                break
            if high_arr[j] >= tp_val:                      # TP
                record.update({
                    "EndValue": float(close_arr[j]),
                    "To":       date_arr[j],
                    "EndIdx":   j,
                    "Result":   "Objective"
                })
                streaksData["ObjectiveProfit"].append(record)
                hit = True
                break

        if not hit:                                       # NoResult
            record.update({
                "EndValue": float(close_arr[last_idx]),
                "To":       date_arr[last_idx],
                "EndIdx":   last_idx,
                "Result":   "NoResult"
            })
            streaksData["NoResult"].append(record)

        cursor = record["EndIdx"] + 1                     # ← corrección

    return {
        "data": streaksData,
        "data_info": {
            "start_date": start_date,
            "end_date":   end_date,
            "diff_list":  diff_list,
            "max_diff":   max(diff_list),
            "min_diff":   min(diff_list)
        }
    }


# ---------------------------------------------------------------------------
# 4) NUEVA FUNCIÓN  ▸  get_bollinger_macd_dynamic_streaks
#     – Si aparece otro Evento BB antes del cruce MACD, ese evento lo remplaza.
#     – Cada trade se guarda en UN solo diccionario con la clave "Result".
# ---------------------------------------------------------------------------
def get_bollinger_macd_dynamic_streaks(tp_pct: float = 0.01,
                                       sl_pct: float = 0.01,
                                       max_candles: int = 350):
    """
    Secuencia:
      1) Detecta primera ruptura Bollinger (Low < BB_Lower, Diff > P25)
      2) Mientras busca el primer cruce MACD_Hist <0→≥0:
           • si aparece otra ruptura Bollinger (Diff > P25) ANTES del cruce,
             esa nueva ruptura sustituye a la anterior y se reinicia la espera.
      3) Cuando se produce el cruce:
           trade = Open de la vela siguiente, TP/SL fijos, max_candles.
      4) Sin solapamientos; cada trade en un dict con "Result".
    """

    # ── preparar las rupturas y el percentil 25 ──
    mask_break = df["Low"] < df["BB_Lower"]
    bb_df      = df.loc[mask_break, ["Low", "BB_Lower", "RSI_14"]].copy()
    bb_df["Diff"] = bb_df["BB_Lower"] - bb_df["Low"]
    diff_list  = bb_df["Diff"].tolist()

    if not diff_list:                       # no hay rupturas
        return {
            "data": [],
            "data_info": {
                "start_date": start_date,
                "end_date":   end_date,
                "diff_list":  [],
                "max_diff":   None,
                "min_diff":   None
            }
        }

    p25_val = np.percentile(diff_list, 25)

    # ── arrays rápidos ──
    macd_hist = df["MACD_Hist"].values
    open_arr  = df["Open"].values
    high_arr  = df["High"].values
    low_arr   = df["Low"].values
    close_arr = df["Close"].values
    date_arr  = df["Date"].astype(str).values
    diff_arr  = (df["BB_Lower"] - df["Low"]).values
    rsi_arr   = df["RSI_14"].values

    trades = []
    i = 1                   # empezamos en la segunda vela (para mirar i-1)
    n = len(df)
    cursor = 0              # evita solapamientos

    current_event_idx = None

    def is_boll_event(idx: int) -> bool:
        return (low_arr[idx] < df["BB_Lower"].values[idx]) and (diff_arr[idx] > p25_val)

    while i < n:
        # ─────────────────────────────
        #  si estamos dentro de un trade, saltamos hasta cursor
        # ─────────────────────────────
        if i < cursor:
            i += 1
            continue

        # ─────────────────────────────
        #  Fase 1: encontrar/actualizar Evento BB
        # ─────────────────────────────
        if current_event_idx is None:
            if is_boll_event(i):
                current_event_idx = i
            i += 1
            continue
        else:
            # Si aparece otra ruptura antes del cruce, la sustituye
            if is_boll_event(i):
                current_event_idx = i
                i += 1
                continue

            # ─────────────────────────
            #  Fase 2: esperar cruce MACD_Hist <0 → ≥0
            # ─────────────────────────
            if macd_hist[i - 1] < 0 <= macd_hist[i]:
                buy_idx = i
                entry_idx = buy_idx + 1
                if entry_idx >= n:
                    break

                open_entry = open_arr[entry_idx]
                tp_val = open_entry * (1 + tp_pct)
                sl_val = open_entry * (1 - sl_pct)
                last_idx = min(entry_idx + max_candles, n - 1)

                record = {
                    "EventBB":    df["DateTime"][current_event_idx],
                    "EventMACD":  df["DateTime"][buy_idx],
                    "StartValue": float(open_entry),
                    "StartIdx":   entry_idx,
                    "EventIdx":   current_event_idx,
                    "Diff":       float(diff_arr[current_event_idx]),
                    "RSI_14":     float(rsi_arr[current_event_idx]) if not np.isnan(rsi_arr[current_event_idx]) else None,
                    "EndValue":   None,
                    "To":         None,
                    "EndIdx":     None,
                    "Result":     None
                }

                # ── evaluar TP / SL ──
                hit = False
                for j in range(entry_idx + 1, last_idx + 1):
                    if low_arr[j] <= sl_val:                # SL
                        record.update({
                            "EndValue": float(close_arr[j]),
                            "To":       df["DateTime"][j],
                            "EndIdx":   j,
                            "Result":   "Limit"
                        })
                        hit = True
                        break
                    if high_arr[j] >= tp_val:               # TP
                        record.update({
                            "EndValue": float(close_arr[j]),
                            "To":       df["DateTime"][j],
                            "EndIdx":   j,
                            "Result":   "Objective"
                        })
                        hit = True
                        break

                if not hit:                                 # NoResult
                    record.update({
                        "EndValue": float(close_arr[last_idx]),
                        "To":       df["DateTime"][last_idx],
                        "EndIdx":   last_idx,
                        "Result":   "NoResult"
                    })

                trades.append(record)
                cursor = record["EndIdx"] + 1               # bloquear solape
                current_event_idx = None                    # reset
                i = cursor                                   # saltar directo
            else:
                i += 1
                continue

    # ── retorno ──
    return {
        "data": trades,           # una sola lista; filtrable por Result
        "data_info": {
            "start_date": start_date,
            "end_date":   end_date,
            "diff_list":  diff_list,
            "max_diff":   max(diff_list),
            "min_diff":   min(diff_list)
        }
    }


# ---------------------------------------------------------------------------
# 6) FUNCIÓN ▸ get_bollinger_macd_dynamic_rule
#     – Solapa solo si el trade previo terminó en Limit / NoResult
# ---------------------------------------------------------------------------
# def get_bollinger_macd_dynamic_rule(tp_pct: float = 0.01,
#                                     sl_pct: float = 0.01,
#                                     max_candles: int = 350):
#     """
#     1) Detecta ruptura Bollinger (Low < BB_Lower, Diff > P25)  → candidate_event_idx
#     2) Mientras espera cruce MACD_Hist <0→≥0:
#          • si aparece otra ruptura antes del cruce, sustituye la anterior.
#     3) Cuando cruza:
#          • abre trade (Open de la vela siguiente) con TP/SL/max_candles.
#          • Durante el trade registra la ÚLTIMA ruptura Bollinger que aparezca.
#     4) Al cerrar el trade:
#          • Si Result == "Objective":  se DESCARTAN las rupturas vistas
#            ⇒ se empieza de cero a buscar nueva ruptura.
#          • Si Result ∈ {"Limit", "NoResult"}:
#            candidate_event_idx := última ruptura vista
#            ⇒ se reinicia la búsqueda de cruce desde ahí.
#     """

#     # -- rupturas iniciales y percentil --
#     mask_break = df["Low"] < df["BB_Lower"]
#     bb_df      = df.loc[mask_break, ["Low", "BB_Lower", "RSI_14"]].copy()
#     bb_df["Diff"] = bb_df["BB_Lower"] - bb_df["Low"]
#     diff_list  = bb_df["Diff"].tolist()

#     if not diff_list:
#         return {
#             "data": [],
#             "data_info": {
#                 "start_date": start_date,
#                 "end_date":   end_date,
#                 "diff_list":  [],
#                 "max_diff":   None,
#                 "min_diff":   None
#             }
#         }

#     p25_val = np.percentile(diff_list, 25)

#     # -- arrays rápidos --
#     macd_hist = df["MACD_Hist"].values
#     open_arr  = df["Open"].values
#     high_arr  = df["High"].values
#     low_arr   = df["Low"].values
#     close_arr = df["Close"].values
#     date_arr  = df["Date"].astype(str).values
#     diff_arr  = (df["BB_Lower"] - df["Low"]).values
#     rsi_arr   = df["RSI_14"].values
#     bb_lower  = df["BB_Lower"].values

#     trades = []
#     n = len(df)
#     i = 1
#     candidate_event_idx = None     # ruptura activa
#     standby_event_idx   = None     # para acumular durante un trade

#     while i < n:
#         # =========================  BÚSQUEDA DE RUPTURA ======================
#         if candidate_event_idx is None:
#             if (low_arr[i] < bb_lower[i]) and (diff_arr[i] > p25_val):
#                 candidate_event_idx = i
#             i += 1
#             continue

#         # ===========================  RUPTURAS ANTES DEL CRUCE ===============
#         if (low_arr[i] < bb_lower[i]) and (diff_arr[i] > p25_val):
#             candidate_event_idx = i                     # se sustituye
#             i += 1
#             continue

#         # ===========================  CRUCE MACD HIST ========================
#         if macd_hist[i - 1] < 0 <= macd_hist[i]:
#             buy_idx   = i
#             entry_idx = buy_idx + 1
#             if entry_idx >= n:
#                 break

#             open_entry = open_arr[entry_idx]
#             tp_val     = open_entry * (1 + tp_pct)
#             sl_val     = open_entry * (1 - sl_pct)
#             last_idx   = min(entry_idx + max_candles, n - 1)

#             record = {
#                 "EventBB":    date_arr[candidate_event_idx],
#                 "EventMACD":  date_arr[buy_idx],
#                 "StartValue": float(open_entry),
#                 "StartIdx":   entry_idx,
#                 "EventIdx":   candidate_event_idx,
#                 "Diff":       float(diff_arr[candidate_event_idx]),
#                 "RSI_14":     float(rsi_arr[candidate_event_idx]) if not np.isnan(rsi_arr[candidate_event_idx]) else None,
#                 "EndValue":   None,
#                 "To":         None,
#                 "EndIdx":     None,
#                 "Result":     None
#             }

#             standby_event_idx = None  # se reinicia dentro del trade
#             hit = False
#             for j in range(entry_idx + 1, last_idx + 1):

#                 # -- capturar nuevas rupturas DURANTE el trade --
#                 if (low_arr[j] < bb_lower[j]) and (diff_arr[j] > p25_val):
#                     standby_event_idx = j     # se guarda la última vista

#                 # -- comprobar SL --
#                 if low_arr[j] <= sl_val:
#                     record.update({
#                         "EndValue": float(close_arr[j]),
#                         "To":       date_arr[j],
#                         "EndIdx":   j,
#                         "Result":   "Limit"
#                     })
#                     hit = True
#                     break

#                 # -- comprobar TP --
#                 if high_arr[j] >= tp_val:
#                     record.update({
#                         "EndValue": float(close_arr[j]),
#                         "To":       date_arr[j],
#                         "EndIdx":   j,
#                         "Result":   "Objective"
#                     })
#                     hit = True
#                     break

#             if not hit:   # Ni TP ni SL
#                 record.update({
#                     "EndValue": float(close_arr[last_idx]),
#                     "To":       date_arr[last_idx],
#                     "EndIdx":   last_idx,
#                     "Result":   "NoResult"
#                 })

#             trades.append(record)

#             # ===== lógica de solapamiento según Result ======================
#             if record["Result"] == "Objective":
#                 candidate_event_idx = None              # bloquear solape
#             else:
#                 candidate_event_idx = standby_event_idx  # puede ser None

#             # avanzar el cursor detrás del cierre
#             i = record["EndIdx"] + 1
#             continue

#         # si no hubo cruce ni nueva ruptura, avanzar
#         i += 1

#     # ------------------- retorno -------------------
#     return {
#         "data": trades,
#         "data_info": {
#             "start_date": start_date,
#             "end_date":   end_date,
#             "diff_list":  diff_list,
#             "max_diff":   max(diff_list),
#             "min_diff":   min(diff_list)
#         }
#     }




# ---------------------------------------------------------------------------
# 7) FUNCIÓN ▸ get_bollinger_macd_dynamic_rule
#     – NO solapa trades “Objective”     (cola vacía)
#     – Tras “Limit/NoResult” abre solo con la primera ruptura > EndIdx
# ---------------------------------------------------------------------------
def get_bollinger_macd_dynamic_rule(tp_pct: float = 0.01,
                                    sl_pct: float = 0.01,
                                    max_candles: int = 350):
    """
    1) Ruptura Bollinger (Low<BB_Lower, Diff>P25) → queue_events.append(idx)
    2) Espera cruce MACD_Hist <0→≥0:
         • si llega otra ruptura antes del cruce, también se apila.
    3) Cuando cruza:
         • abre trade en Open de la vela siguiente; TP/SL/max_candles.
         • Sigue apilando rupturas que aparezcan DURANTE el trade.
    4) Al cerrar el trade:
         • Si Result == "Objective":     queue_events.clear()
         • Si Result in {"Limit","NoResult"}:
              – descarta de la cola todo idx ≤ EndIdx_active
              – toma el primer idx > EndIdx_active (si hay) como nuevo
                candidate_event_idx y mantiene el resto en la cola.
    """

    # ---------- datos base ----------
    mask_break = df["Low"] < df["BB_Lower"]
    bb_df      = df.loc[mask_break, ["Low", "BB_Lower", "RSI_14"]].copy()
    bb_df["Diff"] = bb_df["BB_Lower"] - bb_df["Low"]
    diff_list = bb_df["Diff"].tolist()
    if not diff_list:
        return {
            "data": [],
            "data_info": {
                "start_date": start_date,
                "end_date":   end_date,
                "diff_list":  [],
                "max_diff":   None,
                "min_diff":   None
            }
        }

    p25_val = np.percentile(diff_list, 25)

    macd_hist = df["MACD_Hist"].values
    open_arr  = df["Open"].values
    high_arr  = df["High"].values
    low_arr   = df["Low"].values
    close_arr = df["Close"].values
    diff_arr  = (df["BB_Lower"] - df["Low"]).values
    rsi_arr   = df["RSI_14"].values
    date_arr  = df["Date"].astype(str).values
    bb_lower  = df["BB_Lower"].values

    trades = []
    queue_events = []          # rupturas acumuladas
    candidate_event_idx = None
    i, n = 1, len(df)

    while i < n:
        # --- detectar ruptura y apilarla ---
        if (low_arr[i] < bb_lower[i]) and (diff_arr[i] > p25_val):
            queue_events.append(i)
            if candidate_event_idx is None:
                candidate_event_idx = i

        # --- si no hay candidato aún o no hay cruce, avanzar ---
        if candidate_event_idx is None or macd_hist[i-1] >= 0 or macd_hist[i] < 0:
            i += 1
            continue

        # ============ cruce MACD_Hist <0 → ≥0 detectado ============
        buy_idx = i
        entry_idx = buy_idx + 1
        if entry_idx >= n:
            break

        open_entry = open_arr[entry_idx]
        tp_val = open_entry * (1 + tp_pct)
        sl_val = open_entry * (1 - sl_pct)
        last_idx = min(entry_idx + max_candles, n - 1)

        record = {
            "EventBB":    date_arr[candidate_event_idx],
            "EventMACD":  date_arr[buy_idx],
            "StartValue": float(open_entry),
            "StartIdx":   entry_idx,
            "EventIdx":   candidate_event_idx,
            "Diff":       float(diff_arr[candidate_event_idx]),
            "RSI_14":     float(rsi_arr[candidate_event_idx]) if not np.isnan(rsi_arr[candidate_event_idx]) else None,
            "EndValue":   None,
            "To":         None,
            "EndIdx":     None,
            "Result":     None
        }

        # ---- correr el trade ----
        hit = False
        for j in range(entry_idx + 1, last_idx + 1):
            # apilar rupturas durante el trade
            if (low_arr[j] < bb_lower[j]) and (diff_arr[j] > p25_val):
                queue_events.append(j)

            if low_arr[j] <= sl_val:                     # SL
                record.update({
                    "EndValue": float(close_arr[j]),
                    "To":       date_arr[j],
                    "EndIdx":   j,
                    "Result":   "Limit"
                })
                hit = True
                break
            if high_arr[j] >= tp_val:                    # TP
                record.update({
                    "EndValue": float(close_arr[j]),
                    "To":       date_arr[j],
                    "EndIdx":   j,
                    "Result":   "Objective"
                })
                hit = True
                break

        if not hit:                                     # NoResult
            record.update({
                "EndValue": float(close_arr[last_idx]),
                "To":       date_arr[last_idx],
                "EndIdx":   last_idx,
                "Result":   "NoResult"
            })

        trades.append(record)
        EndIdx_active = record["EndIdx"]

        # ------------ gestionar cola según resultado ---------------
        if record["Result"] == "Objective":
            queue_events.clear()
            candidate_event_idx = None
        else:  # Limit o NoResult
            # descartar rupturas ≤ EndIdx_active
            queue_events = [idx for idx in queue_events if idx > EndIdx_active]
            candidate_event_idx = queue_events.pop(0) if queue_events else None

        # avanzar i justo después del cierre
        i = EndIdx_active + 1

    return {
        "data": trades,
        "data_info": {
            "start_date": start_date,
            "end_date":   end_date,
            "diff_list":  diff_list,
            "max_diff":   max(diff_list),
            "min_diff":   min(diff_list)
        }
    }



