"""ตัวจำลอง ESP32 บนคอมพิวเตอร์ — ส่งข้อมูลรูปแบบเดียวกับ ESPHome ไป Firebase
ใช้ทดสอบ Dashboard ก่อนมีบอร์ดจริง:  python tools/simulate.py [จำนวนรอบ]
"""
import json, random, sys, time, urllib.request
from datetime import datetime

FIREBASE_URL = "https://iot-118-default-rtdb.asia-southeast1.firebasedatabase.app"
INTERVAL = 10
LIMIT = {"co2": 1000, "temp": 30, "people": 40, "light": 200}


def send(method, path, data):
    req = urllib.request.Request(f"{FIREBASE_URL}/{path}.json", data=json.dumps(data).encode(),
                                 method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def main(rounds):
    s = {"p": 25, "t": 28.0, "h": 62.0, "lux": 500.0, "fan": False}
    for i in range(rounds):
        s["p"] = clamp(s["p"] + random.uniform(-3, 3.2), 0, 50)
        p = round(s["p"])
        s["t"] = clamp(s["t"] + random.uniform(-.35, .35) + (p - 25) * .012 - (.3 if s["fan"] else 0), 24, 34)
        s["h"] = clamp(s["h"] + random.uniform(-1.5, 1.5) - (.4 if s["fan"] else 0), 40, 85)
        s["lux"] = clamp(s["lux"] + random.uniform(-60, 60), 100, 850)
        co2 = clamp(420 + p * 16.5 + random.uniform(-60, 60) - (150 if s["fan"] else 0), 400, 1800)

        alerts = [code for code, hit in [
            ("co2_high", co2 > LIMIT["co2"]), ("temp_high", s["t"] > LIMIT["temp"]),
            ("crowded", p > LIMIT["people"]), ("light_low", s["lux"] < LIMIT["light"])] if hit]
        s["fan"] = s["t"] > LIMIT["temp"] or co2 > LIMIT["co2"]

        data = {
            "temperature": round(s["t"], 1), "humidity": round(s["h"], 1), "light": round(s["lux"]),
            "co2": round(co2), "noise": round(clamp(35 + p * .5 + random.uniform(-4, 8), 30, 90)),
            "people": p, "air_quality": round(clamp(100 - (co2 - 400) / 15, 0, 100)),
            "fan_status": "ON" if s["fan"] else "OFF", "alerts": alerts, "device": "ST806",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ts": {".sv": "timestamp"},
        }
        print(i + 1, send("PUT", "latest", data), send("POST", "history", data), data)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10**9)
