from flask import Flask, render_template, jsonify
import sqlite3
import sys
import os
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import weather_logger


app = Flask(__name__)

# --- DB lekérés ---
def get_data():
    conn = sqlite3.connect("/home/dani/weather.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, temperature, humidity, pressure, gas, rain, wind_speed FROM weather ORDER BY timestamp DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    return rows


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    rows = get_data()

    timestamps = [r[0] for r in rows]
    temps = [r[1] for r in rows]
    hums = [r[2] for r in rows]
    press = [r[3] for r in rows]
    gas = [r[4] for r in rows]
    rain = [r[5] for r in rows]
    wind = [r[6] for r in rows]

    return jsonify({
        "timestamps": timestamps,
        "temperature": temps,
        "humidity": hums,
        "pressure": press,
        "gas": gas,
        "rain":rain,
        "wind_speed":wind
    })


if __name__ == "__main__":
    log_thread=threading.Thread(target=weather_logger.main,daemon=True)
    log_thread.start()
    app.run(host="0.0.0.0", port=8080, debug=True,use_reloader=False)
