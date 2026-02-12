import requests

def get_open_meteo():
    """Lekéri a kültéri adatokat az Open-Meteo API-ból"""
    lat = 47.49  # Írd át a saját koordinátáidra
    lon = 19.04
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
        # Hiba esetén alapértelmezett None értékekkel térünk vissza, hogy ne álljon le a program
        return {"temp": None, "hum": None, "wind": None, "rain": None, "pres": None}

def main():
    init_db()
    sensor = init_sensors()

    print("--- Időjárás állomás elindult (BME680 + Hall + Rain + OpenMeteo) ---")

    try:
        while True:
            # 1. Kültéri adatok lekérése az internetről
            out_data = get_open_meteo()

            # 2. Szélmérés a helyi Hall-szenzorral (5 mp-ig tart)
            wind_speed_local = measure_wind(5)

            # 3. BME680 szenzor adatainak beolvasása
            # Megvárjuk, amíg a fűtőlap (heat_stable) stabilizálódik
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                timestamp = time.strftime("%Y-%m-%d %H:%M")
                
                # Beltéri adatok
                temp_in = sensor.data.temperature
                hum_in = sensor.data.humidity
                pres_in = sensor.data.pressure
                gas_in = sensor.data.gas_resistance

                # Helyi esőérzékelő mérése (GPIO)
                rain_local = 100 if GPIO.input(RAIN_PIN) == GPIO.LOW else 0

                # Konzolos kiírás a követéshez
                print(f"[{timestamp}]")
                print(f"  BENT: {temp_in:.1f}°C, {hum_in:.1f}%, {gas_in/1000:.1f} kOhm")
                print(f"  KINT (API): {out_data['temp']}°C, Szél: {out_data['wind']} km/h")
                print(f"  ESŐ: Szenzor: {rain_local}% | API: {out_data['rain']} mm")
                print("-" * 40)

                # 4. Mentés az adatbázisba (minden adatot átadunk)
                save_to_db(
                    timestamp, 
                    temp_in, hum_in, pres_in, gas_in, 
                    rain_local, wind_speed_local,
                    out_data['temp'], out_data['hum'], out_data['wind'], out_data['rain'], out_data['pres']
                )

            # Várunk a következő mérésig (600mp = 10 perc)
            # Levonjuk belőle a szélmérés 5 másodpercét
            time.sleep(595) 

    except KeyboardInterrupt:
        print("\nLeállítás...")
    finally:
        GPIO.cleanup()
        print("GPIO felszabadítva. Viszlát!")