#!/usr/bin/env python3
import time
import sqlite3
import os
import bme680
import RPi.GPIO as GPIO

DB_PATH = "/home/dani/weather.db"
RAIN_PIN = 17 
HALL_PIN = 27 # Új: Hall szenzor a GPIO 27-en

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                temperature REAL,
                humidity REAL,
                pressure REAL,
                gas REAL,
                rain INTEGER,
                wind_speed REAL
            );
        """)
        conn.commit()
        conn.close()
    else:
        # Ha már létezik az adatbázis, de nincs benne a szél oszlop, 
        # a lenti kóddal hozzáadhatod (egyszeri futtatás után törölhető):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("ALTER TABLE weather ADD COLUMN wind_speed REAL DEFAULT 0")
            conn.commit()
            conn.close()
        except:
            pass

def save_to_db(timestamp, temp, hum, pres, gas, rain, wind):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO weather (timestamp, temperature, humidity, pressure, gas, rain, wind_speed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, temp, hum, pres, gas, rain, wind))
    conn.commit()
    conn.close()

# --- SZÉLSEBESSÉG MÉRÉSE ---
def measure_wind(duration=5):
    count = 0
    def count_pulse(channel):
        nonlocal count
        count += 1
    
    # Feliratkozunk az impulzusokra (felfutó élre)
    GPIO.add_event_detect(HALL_PIN, GPIO.FALLING, callback=count_pulse)
    
    time.sleep(duration) # Mérünk X másodpercig
    
    GPIO.remove_event_detect(HALL_PIN)
    
    # Kiszámoljuk a sebességet (példa: 1 fordulat/mp = 2.4 km/h)
    # Ezt a szélkereked mérete alapján kell majd kalibrálnod!
    rps = count / duration
    wind_kmh = rps * 2.4 
    return wind_kmh

def init_sensors():
    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RAIN_PIN, GPIO.IN)
    GPIO.setup(HALL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Felhúzó ellenállás kell a Hall-hoz

    # BME680 setup
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except:
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
    
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)
    
    return sensor

def main():
    init_db()
    sensor = init_sensors()

    print("Logger fut: BME680 + Eső + Szél...")

    try:
        while True:
            # 1. Szélmérés (5 mp-ig tart)
            wind_speed = measure_wind(5)

            # 2. BME680 mérés
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                timestamp = time.strftime("%Y-%m-%d %H:%M")
                temp = sensor.data.temperature
                hum = sensor.data.humidity
                pres = sensor.data.pressure
                gas = sensor.data.gas_resistance
                
                # 3. Esőmérés
                rain_val = 100 if GPIO.input(RAIN_PIN) == GPIO.LOW else 0

                print(f"{timestamp} | Szél: {wind_speed:.1f} km/h | Eső: {rain_val}%")
                save_to_db(timestamp, temp, hum, pres, gas, rain_val, wind_speed)

            time.sleep(895) # Korrigálva a szélmérés 5 másodpercével (összesen 15 perc)

    except KeyboardInterrupt:
        print("Leállítva.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()