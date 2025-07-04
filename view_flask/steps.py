

'''



  "ObjectiveProfit": [
{
  "EventBB":   "2024-05-14 13:00:00",  // vela que rompió la banda
  "EventMACD": "2024-05-14 14:00:00",  // vela del cruce MACD_Hist
  "EventIdx":  42117,                  // índice de EventBB en el DataFrame
  "StartIdx":  42118,                  // índice de la vela de entrada
  "StartValue": 38910.0,               // Open de la vela de entrada
  "EndIdx":   42125,                   // índice de la vela de salida
  "EndValue": 39342.0,                 // Close de la vela de salida
  "To":       "2024-05-14 20:00:00",   // fecha-hora de la salida
  "Diff":     132.8,                   // BB_Lower − Low en la ruptura
  "RSI_14":   26.7,                    // RSI en EventBB
  "Result":   "Objective"              // "Objective" | "Limit" | "NoResult"
}
  ],

  


  Busco clasificar los tipos de rebotes alcistas de acuerdo a apmlitud. Entonces encuentro tendecias bajistas 
  que coincidan con un "Diff_BB_Lower" determinado y a partir de la siguiente vela busco tendecias alcistas con determinadas caracteristicas
  Almaceno datos de cada resultado y luego los clasifico para poder determinar "tipos de rebotes"

  
  "min_profit: 0.008", "limit_loss: -0.008", "max_candles: 10", "val_limit_trend: 0.7" - estos tienes que ser variables de la funcion para ser modificados

 • TrendPct_N < -0.75
 • Diff_BB_Lower < 3%
 • "start_event": TrendPct_N < -0.75  &  Diff_BB_Lower < 3% ( vela en la que ocurren los dos sucesos)
 • "start_streak" =  +1 vela posterior a "start_event"
 • Buscamos "strek" de por lo menos 0.8% al valor de "Close" de "start_event"
 • Si el "streak" alcanza primero "limit_loss" que "min_profit", se corta el streak y es "Result: Limit"
 • Si no se alcanza ninguno de los dos puntos antes de las "max_candles: 10", se corta el "streak" y es "Result: NoResult"
 • Si el "streak" alcanza "min_profit", se determinan dos variables 
    . "cumulative_trend" -> la suma de todos los "Trend" desde que inicio el "streak"
    . "limit_trend" ->      -70% el valor de "cumulative_trend" | "limit_trend" = "cumulative_trend * val_limit_trend" 
    . se alcanza este nuevo limite y el trend se corta y es "Result: Objective"

    - vela 0 - "start_event"  | TrendPct_N < -0.75  &  Diff_BB_Lower < 3%
    - vela 1 - "start_streak" | Trend: 80   | "cumulative_trend: 80"
    - vela 2 -                | Trend: 120  | "cumulative_trend: 200"
    - vela 3 -                | Trend: -110 | "cumulative_trend: 90"
    - vela 4 -                | Trend: 76   | "cumulative_trend: 166"
    - vela 5 -                | Trend: -12  | "cumulative_trend: 154"
    - vela 6 -                | Trend: 6    | "cumulative_trend: 160"
    - vela 7 -                | Trend: -113 | "Trend" -71% que "cumulative_trend". Se corta el streak y medimos de cuanto fue.

  • Hasta que un "streak" no termina, no puede empezar otro

  • El While debe seguir buscando "streak_event" incluso cuando haya un "streak" en proceso,
    almacenla los "idx" de los "streak_event" en una variable "idx_standby", si el "streak" en proceso termina en "Limit" o "NoResult"
    inicia nuevos "streaks" con los "idx" de "idx_standby", si alguno de estos "streak" con "idx" en "idx_standby" temrina en "Objective",
    desestima todos los "streak" que hayan terminado en "Limit" o "NoResult" con "EventIdx" o "EndIdx"
     dentro del rango de los indices del nuevo "streak" que termina en "Objective"


Cada uno de estos eventos debe ser almacenado en una lista de la siguiente manera 



  "streak_list": [
{
  "EventBB":   "2024-05-14 13:00:00",  // vela que rompió la banda
  "EventMACD": "2024-05-14 14:00:00",  // vela del cruce MACD_Hist
  "EventIdx":  42117,                  // índice de EventBB en el DataFrame
  "StartIdx":  42118,                  // índice de la vela de entrada
  "StartValue": 38910.0,               // Open de la vela de entrada
  "EndIdx":   42125,                   // índice de la vela de salida
  "EndValue": 39342.0,                 // Close de la vela de salida
  "To":       "2024-05-14 20:00:00",   // fecha-hora de la salida
  "ATR_coeff": "0.0002832",            // Diff_BB_Lower / ATR
  "Result":   "Objective"              // "Objective" | "Limit" | "NoResult"
}
  ],

  








'''

"""
Secuencia operativa
-------------------
1) Detecta ruptura Bollinger (Low < BB_Lower, Diff > P25).
   Guarda su índice como `candidate_event_idx`.
2) Mientras se espera un cruce MACD_Hist alcista (<0 → ≥0):
     • si aparece otra ruptura Bollinger antes del cruce,
       `candidate_event_idx` se actualiza a ese nuevo evento.
3) Cuando ocurre el cruce:
     • abre trade en el Open de la vela siguiente.
     • TP = +tp_pct ; SL = -sl_pct ; máx. velas = max_candles.
   (No se bloquean nuevas operaciones SIEMPRE Y CUANDO ESTE "TRADE"/"STREAK" QUE ESTA OCURRIENDO
     TERMINE EN "Limit" o "NoResult": otras rupturas posteriores
    pueden iniciar nuevas búsquedas aun con trades abiertos).
     • Si el "Trade"/"Streak" termina en "Objective", NO PUEDE HABER SOLAPAMIENTO
4) Cada trade se registra en un solo diccionario con la clave "Result".

     • Se abre el "Trade"
     • El "Trade" no concluye aun, pero se detecta otra ruptura Bollinger (Low < BB_Lower, Diff > P25) 
     Ahora debe ser "Ignorada" hasta no saber si el "Trade"/"Streak" actual termina en "Objective" o "Limit".
     "Ignorada" o dejada en "Standby" hasta que el "Trade"/"Streak" actual termine para ver si desde esa "Ruptura" se abre un nuevo "Trade"/"Streak".
    - Esto es lo que no se como se puede resolver.
     



Que es lo que pretendo con esto? Encontrar todos los "Trades"/"Streaks" que terminen en "Objective" TODOS, para poder buscarles una relacion. 
Por eso no deben solaparse cuando sen "Objective"


"""

'''
| Foco                                 | ¿Qué medir antes del evento?                                                                           | Cómo usarlo                                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **1. Contexto MACD**                 | Nº de barras (velas) que el MACD llevaba < 0 antes del cruce; pendiente media del MACD y de la Signal. | Descarta cruces “demasiado frescos” (poca divergencia) o exige que la pendiente sea crecientemente alcista. |
| **2. Volatilidad local**             | ATR(14) o % de ampliación de la BandWidth de Bollinger en las 20 velas previas.                        | Limita operaciones cuando la volatilidad está “inflada” (stop salta fácil).                                 |
| **3. Profundidad del rebote**        | Relación `Diff / ATR` o `Diff / Amplitude diaria`.                                                     | A mayor “choque” contra la banda (en múltiplos ATR), mayor probabilidad de rebote efectivo.                 |
| **4. Hora del día / sesión**         | Timestamp → sesión Asia-EU-US.                                                                         | Filtra o pondera trades según la sesión con mejor histórico de Objectives.                                  |
| **5. RSI & estocástico**             | RSI(14) y/o Stoch < 20 justo en el evento.                                                             | Solo operar rebotes cuando el mercado está realmente sobrevendido.                                          |
| **6. Estructura de máximos-mínimos** | Conteo de mínimos descendentes en las 10–20 velas previas.                                             | Evitar compras si la secuencia bajista es demasiado sólida (tendencia dominante).                           |
| **7. Clúster de eventos**            | Distancia en velas al evento Bollinger anterior.                                                       | Saltar trades si los eventos llegan “encadenados” (mercado muy nervioso).                                   |
| **8. Regresión rápida**              | Mini-pendiente de precio (slope de Close) en las 10 velas previas.                                     | Prefiere entrar cuando ya hay indicio de giro alcista, no en plena caída.                                   |


------ Para trabajar con ATR -----
- `MACD_Hist`  
- `RSI_14`  
- `Momentum_1`  
- `ROC_10`  
- `Return`  
- `R_CloToClo`  
- `Stoch_%D`  
- `ZScore_20`  
- `Diff-20`  
- `Trend`


Performance	Si el dataset es grande y vas a probar muchas ventanas, quizá uses vectorized operations o numba para acelerar.


'''



