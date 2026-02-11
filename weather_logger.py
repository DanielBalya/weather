#!/usr/bin/env python3
import time
import sqlite3
import os
import bme680

DB_PATH = "/home/dani/weather.db"

# Adatbázik létrehozása
def init_db():
    if not os.path.exists(DB_PATH):
        print("Adatbázis nem létezett, létrehozom...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                temperature REAL,
                humidity REAL,
                pressure REAL,
                gas REAL
            );
        """)
        conn.commit()
        conn.close()
        print("Adatbázis és weather tábla létrehozva.")
    else:
        print("Adatbázis OK.")


def save_to_db(timestamp, temp, hum, pres, gas):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO weather (timestamp, temperature, humidity, pressure, gas)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, temp, hum, pres, gas))
    conn.commit()
    conn.close()

# --- BME680 ÉRZÉKELŐ INICIALIZÁLÁS ---
def init_sensor():
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    return sensor


# --- FŐ PROGRAM ---
def main():
    init_db()
    sensor = init_sensor()

    print("Mérés indul... (Ctrl+C a leállításhoz)\n")

    try:
        while True:
            if sensor.get_sensor_data() and sensor.data.heat_stable:

                timestamp = time.strftime("%Y-%m-%d %H:%M")

                temp = sensor.data.temperature
                hum = sensor.data.humidity
                pres = sensor.data.pressure
                gas = sensor.data.gas_resistance

                print(f"{timestamp} | Temp={temp:.2f}°C | Hum={hum:.2f}% | Pres={pres:.2f} hPa | Gas={gas:.2f} Ohm")

                save_to_db(timestamp, temp, hum, pres, gas)

            time.sleep(900)

    except KeyboardInterrupt:
        print("\nLeállítva.")


if __name__ == "__main__":
    main()
