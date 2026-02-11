from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

# --- DB lekérés ---
def get_data():
    conn = sqlite3.connect("/home/dani/weather.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, temperature, humidity, pressure, gas FROM weather ORDER BY timestamp DESC LIMIT 100")
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

    return jsonify({
        "timestamps": timestamps,
        "temperature": temps,
        "humidity": hums,
        "pressure": press,
        "gas": gas
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
