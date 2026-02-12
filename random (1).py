import requests
import time
import bme680
import sqlite3

# ... szenzor inicializálás marad ...

def get_all_open_meteo_data():
    lat = 47.49  # Koordinátáid
    lon = 19.04
    # Lekérjük az összes kért paramétert
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&current=temperature_2m,relative_humidity_2m,rain,surface_pressure,wind_speed_10m"
           f"&timezone=auto")
    try:
        r = requests.get(url, timeout=10)
        curr = r.json()['current']
        return {
            "temp": curr['temperature_2m'],
            "hum": curr['relative_humidity_2m'],
            "wind": curr['wind_speed_10m'],
            "rain": curr['rain'],
            "pres": curr['surface_pressure']
        }
    except Exception as e:
        print(f"API hiba: {e}")
        return None

def main():
    sensor = init_sensor() # BME680
    while True:
        # 1. Kinti adatok az API-ból
        out = get_all_open_meteo_data()
        
        # 2. Benti adatok a BME680-ról
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            
            # Mentés az adatbázisba
            conn = sqlite3.connect("/home/dani/weather.db")
            c = conn.cursor()
            c.execute("""
                INSERT INTO weather 
                (timestamp, temperature, humidity, pressure, gas, temp_out, hum_out, wind_speed_out, rain_out, pressure_out)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, 
                sensor.data.temperature, sensor.data.humidity, sensor.data.pressure, sensor.data.gas_resistance,
                out['temp'], out['hum'], out['wind'], out['rain'], out['pres']
            ))
            conn.commit()
            conn.close()
            print(f"Adatok mentve: {timestamp}")

        time.sleep(900) # 15 perc várakozás