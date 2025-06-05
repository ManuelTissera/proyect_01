
from analytics.mct import get_data_mct
from analytics.historic_data import get_historic_data
from analytics.buysells.buysell import get_buysell, get_trend_streaks, get_streaks_average
from analytics.buysells.buysell_streaks import get_buysell_streak
from analytics.buysells.buysell_reversal import get_buysell_reversal
from analytics.buysells.buysell_years import get_dynamic_validation_by_year, get_multiple_years_data
from analytics.buysells.buysell_years_rsi import get_multiple_years_data_rsi
from analytics.trends.trends_percentage import find_bullish_trends
from analytics.trends.macd_data import get_macd_data
from analytics.SMAs.SMA import get_sma_data
from analytics.SMAs.SMA_edit import get_sma_data_edit
from analytics.SMAs.SMA_manual_range import get_sma_manual_range
from analytics.news_data.news_data import load_economic_news
from analytics.data_info.monetary_base import get_data_monetary_base


from flask import Flask, render_template, jsonify, request
import pandas as pd

app = Flask(__name__, static_folder='static')


# ==================== LINKS ============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/measures_mct")
def measures_mct():
    return render_template("measure.html")

@app.route("/historic_data")
def historic_data():
    return render_template("historic_data.html")

@app.route("/news_data")
def news_data():
    return render_template("news_data.html")

@app.route("/monetary_base")
def monetary_base():
    return render_template("monetary_base.html")

# @app.route("/study_outline")
# def study_outline():
#     return render_template("study_outline.html")

@app.route("/macd_data")
def macd_data():
    return render_template("macd_data.html")

@app.route("/buysell_trend")
def buysell_trend():
    return render_template("buysell.html")

@app.route("/buysell_reversal")
def buysell_reversal():
    return render_template("buysell_reversal.html")

@app.route("/buysell_years")
def buysell_years():
    return render_template("buysell_years.html")

@app.route("/buysell_years_rsi")
def buysell_years_rsi():
    return render_template("buysell_years_rsi.html")

@app.route("/buysell_years_sma")
def buysell_years_sma():
    return render_template("buysell_years_sma.html")

@app.route("/buysell_years_goalvsinv")
def buysell_years_goalvsinv():
    return render_template("buysell_years_goalvsinv.html")

# ----------- Trends

@app.route("/trends_percentage")
def trends_percentage():
    return render_template("trends_percentage.html")

@app.route("/SMA_calc")
def SMA_calc():
    return render_template("sma_calculate.html")

@app.route("/sma_manual_range")
def sma_manual_range():
    return render_template("sma_manual_range.html")

# ==================== REQUEST ==========================

@app.route("/SMA/edit")
def sma_edit():
    data = get_sma_data_edit()
    return jsonify(data)

@app.route("/measures/mct")
def measures():
    mct_res = get_data_mct()
    return jsonify({"values":mct_res})

@app.route("/historic_data/US30_year")
def historic_US30_year():
    data = get_historic_data()
    return jsonify(data)

@app.route("/buysell/trend")
def trend_endponint():
    trend_data, data_json = get_buysell()
    trend_streaks = get_trend_streaks()
    # avg_pos, avg_neg = get_streaks_average()
    print(sorted(trend_streaks))
    return jsonify(trend_data,trend_streaks,data_json)

@app.route("/buysell/streak")
def buysell_streak():
    streak_data = get_buysell_streak()
    return streak_data

@app.route("/buysell/dynamic_reversal", methods=["GET", "POST"])
def buysellrev():
    if request.method == "POST":
        data = request.get_json()
        start = data.get("start_date")
        end = data.get("end_date")
    else:
        start = request.args.get("start_date")
        end = request.args.get("end_date")

    try:
        max_fall = int(request.args.get("max_fall", 250))
        min_rise = int(request.args.get("min_rise", 500))
        max_candles = int(request.args.get("max_candles", 50))
    except ValueError:
        return jsonify({"error": "Invalid numeric parameters"}), 400

    dyn_data = get_buysell_reversal(
        start_date=start,
        end_date=end,
        max_fall=max_fall,
        min_rise=min_rise,
        max_candles=max_candles
    )
    return jsonify(dyn_data)


# @app.route("/buysell/years")
# def buysell_years_stats():
#     year = request.args.get("year")
#     if not year:
#         return jsonify({"error": "Missing 'year' parameter"}), 400

#     dyn_data = get_dynamic_validation_by_year(year=year)
#     return jsonify(dyn_data)

@app.route("/buysell/multi_years")
def multi_years_stats():
    years_param = request.args.get("years")
    if not years_param:
        return jsonify({"error": "Missing 'years' parameter"}), 400

    try:
        years = [int(y) for y in years_param.split(",") if y.strip()]
    except ValueError:
        return jsonify({"error": "Invalid 'years' format"}), 400

    try:
        max_fall = int(request.args.get("max_fall", 250))
        min_rise = int(request.args.get("min_rise", 500))
        max_candles = int(request.args.get("max_candles", 50))
    except ValueError:
        return jsonify({"error": "Invalid numeric parameters"}), 400

    data = get_multiple_years_data(
        years=years,
        max_fall=max_fall,
        min_rise=min_rise,
        max_candles=max_candles
    )
    return jsonify(data)

@app.route("/buysell/years_rsi")
def multi_years_stats_rsi():
    years_param = request.args.get("years")
    if not years_param:
        return jsonify({"error": "Missing 'years' parameter"}), 400

    try:
        years = [int(y) for y in years_param.split(",") if y.strip()]
    except ValueError:
        return jsonify({"error": "Invalid 'years' format"}), 400

    try:
        target_streak = int(request.args.get("st", -5))
        max_fall = int(request.args.get("max_fall", 250))
        min_rise = int(request.args.get("min_rise", 500))
        max_candles = int(request.args.get("max_candles", 100))
    except ValueError:
        return jsonify({"error": "Invalid numeric parameters"}), 400

    from analytics.buysells.buysell_years_rsi import get_multiple_years_data_rsi

    data = get_multiple_years_data_rsi(
        target_streak=target_streak,
        years=years,
        max_fall=max_fall,
        min_rise=min_rise,
        max_candles=max_candles
    )
    return jsonify(data)



@app.route("/buysell/bullish_percentage", methods=["GET"])
def get_bullish_percentage():
    try:
        # Obtener parámetros de la URL con valores por defecto
        target = int(request.args.get("target", 500))
        limit = int(request.args.get("limit", 300))
        max_candles = int(request.args.get("max_candles", 100))

        # Ejecutar análisis de tendencias alcistas
        result_data = find_bullish_trends(target=target, limit=limit, max_candles=max_candles)
        raw_results = result_data["Results"]
        open_close = result_data["OpenCloseByYear"]
        freq_month = result_data["FreqByYearMonth"]

        # Agrupar resultados por tipo
        grouped = {
            "Objective": [],
            "Limit": [],
            "NoResult": []
        }

        for row in raw_results:
            result_type = row.get("Result")
            if result_type in grouped:
                grouped[result_type].append(row)
            else:
                grouped["NoResult"].append(row)

        # Devolver resultados agrupados + open/close anual
        return jsonify({
            "Objective": grouped["Objective"],
            "Limit": grouped["Limit"],
            "NoResult": grouped["NoResult"],
            "OpenCloseByYear": open_close,
            "StatsPreSlope": result_data["StatsPreSlope"],
            "FreqByYearMonth": freq_month
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


# -------- MACD  request--------------------

@app.route("/api/macd_data")
def macd_data_req():
    data = get_macd_data()
    return jsonify(data)


# ------------==--------------------




@app.route("/SMAs/SMA/calculate")
def calculate_sma():
    data = get_sma_data()
    return jsonify(data)

@app.route("/SMA/manual_range")
def manual_range():
    data = get_sma_manual_range()
    return jsonify(data)


# ==================== Data info ==========================


@app.route("/api/monetary_base")
def monetary_base_data():
    data = get_data_monetary_base()
    return jsonify(data)

# ==================== NEWS ==========================

@app.route("/api/economic-news")
def get_economic_news():
    df = load_economic_news()
    data = df.to_dict(orient="records")
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)




if __name__ == "__main__":
    app.run(debug=True)