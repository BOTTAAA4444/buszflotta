import requests
import json
import time
import random
import math
from datetime import datetime

# A Logstash címe (ha GCP-n fut a Docker mellett, akkor localhost:8080)
LOGSTASH_URL = "http://localhost:8080"

# 10 különböző budapesti útvonal sarokpontjai (GPS koordináták)
ROUTES = [
    # 1. útvonal: Deák tér -> Astoria -> Kálvin tér -> Fővám tér
    [{"lat": 47.4979, "lon": 19.0552}, {"lat": 47.4944, "lon": 19.0600}, {"lat": 47.4896, "lon": 19.0620}, {"lat": 47.4859, "lon": 19.0583}],
    # 2. útvonal: Széll Kálmán tér -> Déli pu. -> BAH csomópont -> Móricz
    [{"lat": 47.5074, "lon": 19.0248}, {"lat": 47.5002, "lon": 19.0249}, {"lat": 47.4883, "lon": 19.0238}, {"lat": 47.4774, "lon": 19.0475}],
    # 3. útvonal: Keleti pu. -> Blaha Lujza tér -> Astoria
    [{"lat": 47.5005, "lon": 19.0839}, {"lat": 47.4965, "lon": 19.0700}, {"lat": 47.4944, "lon": 19.0600}, {"lat": 47.4965, "lon": 19.0700}],
    # 4. útvonal: Hősök tere -> Oktogon -> Deák tér
    [{"lat": 47.5149, "lon": 19.0777}, {"lat": 47.5055, "lon": 19.0628}, {"lat": 47.4979, "lon": 19.0552}, {"lat": 47.5055, "lon": 19.0628}],
    # 5. útvonal: Margit híd (Buda) -> Nyugati pu. -> Oktogon
    [{"lat": 47.5144, "lon": 19.0390}, {"lat": 47.5106, "lon": 19.0581}, {"lat": 47.5055, "lon": 19.0628}, {"lat": 47.5106, "lon": 19.0581}],
    # 6. útvonal: Boráros tér -> Petőfi híd -> Goldmann György tér -> Gellért tér
    [{"lat": 47.4795, "lon": 19.0664}, {"lat": 47.4764, "lon": 19.0608}, {"lat": 47.4789, "lon": 19.0556}, {"lat": 47.4841, "lon": 19.0512}],
    # 7. útvonal: Árpád híd -> Flórián tér -> Kolosy tér -> Margit híd
    [{"lat": 47.5367, "lon": 19.0625}, {"lat": 47.5342, "lon": 19.0407}, {"lat": 47.5276, "lon": 19.0379}, {"lat": 47.5144, "lon": 19.0390}],
    # 8. útvonal: Váci út (Lehel tér -> Dózsa Gy. út -> Árpád híd)
    [{"lat": 47.5152, "lon": 19.0592}, {"lat": 47.5256, "lon": 19.0644}, {"lat": 47.5332, "lon": 19.0661}, {"lat": 47.5256, "lon": 19.0644}],
    # 9. útvonal: Móricz Zs. körtér -> Újbuda-központ -> Kelenföld
    [{"lat": 47.4774, "lon": 19.0475}, {"lat": 47.4746, "lon": 19.0479}, {"lat": 47.4647, "lon": 19.0227}, {"lat": 47.4746, "lon": 19.0479}],
    # 10. útvonal: Clark Ádám tér -> Lánchíd -> Széchenyi tér -> József Attila u.
    [{"lat": 47.4984, "lon": 19.0404}, {"lat": 47.4996, "lon": 19.0473}, {"lat": 47.4988, "lon": 19.0520}, {"lat": 47.4996, "lon": 19.0473}]
]

# Buszok inicializálása
buses = []
for i in range(10):
    buses.append({
        "id": f"BUS-{i+1:03d}",
        "route_index": i,              # Melyik útvonalhoz tartozik
        "target_wp": 1,                # A következő célpont indexe az útvonalon
        "lat": ROUTES[i][0]["lat"],    # Kezdő pozíció: az útvonal 1. pontja
        "lon": ROUTES[i][0]["lon"],
        "speed": random.uniform(30.0, 50.0),
        "fuel": random.uniform(60.0, 100.0)
    })

def simulate_movement():
    print("Flotta szimuláció elindítva (10 útvonal)... Kilépés: CTRL+C")
    
    while True:
        for bus in buses:
            route = ROUTES[bus["route_index"]]
            target = route[bus["target_wp"]]
            
            # Távolság kiszámítása a jelenlegi hely és a célpont között
            dx = target["lon"] - bus["lon"]
            dy = target["lat"] - bus["lat"]
            distance = math.hypot(dx, dy)
            
            # Paraméterek frissítése
            bus["speed"] = max(10, min(65, bus["speed"] + random.uniform(-3, 3)))
            bus["fuel"] -= random.uniform(0.01, 0.03)
            
            # Ha kifogyott az üzemanyag, a busz megáll
            if bus["fuel"] <= 0:
                bus["speed"] = 0
                bus["fuel"] = 0
            
            # Lépésmérték kiszámítása a sebesség alapján (leképezés térkép-fokokra)
            # Egy nagyon durva közelítés: 50 km/h = ~0.00015 fok 2 másodperc alatt
            step_size = (bus["speed"] / 50.0) * 0.00015
            
            # Ha közelebb vagyunk a ponthoz, mint egy lépés, ráugrunk, és új célt választunk
            if distance < step_size:
                bus["lat"] = target["lat"]
                bus["lon"] = target["lon"]
                # Célpont léptetése (ha a végére ért, kezdi elölről az útvonalat)
                bus["target_wp"] = (bus["target_wp"] + 1) % len(route)
            elif bus["speed"] > 0:
                # Elmozdulás a cél irányába interpolációval
                ratio = step_size / distance
                bus["lat"] += dy * ratio
                bus["lon"] += dx * ratio

            # Adatcsomag összeállítása a Logstash számára
            payload = {
                "bus_id": bus["id"],
                "latitude": bus["lat"],
                "longitude": bus["lon"],
                "speed": round(bus["speed"], 2),
                "fuel": round(bus["fuel"], 2),
                "@timestamp": datetime.utcnow().isoformat()
            }

            try:
                response = requests.post(LOGSTASH_URL, json=payload, timeout=2)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {bus['id']} -> {bus['lat']:.5f}, {bus['lon']:.5f} | Szint: {payload['fuel']}% | Állapot: {response.status_code}")
            except Exception as e:
                print(f"Hiba {bus['id']} adatküldésnél: {e}")

        # 2 másodperces várakozás a következő frissítésig
        time.sleep(2)

if __name__ == "__main__":
    simulate_movement()
