# 🏫 Smart Classroom Monitoring System

ระบบตรวจสอบสภาพห้องเรียนแบบ Realtime — ESP32 + ESPHome จำลองค่าเซ็นเซอร์ → Firebase Realtime Database (`iot-118`) → Dashboard บน GitHub Pages (`/freeboard`)

```
ESP32 + ESPHome ──► Firebase RTDB (iot-118)
                         ├── latest    (PUT  ทุก 10 วินาที — ค่าปัจจุบัน)
                         └── history   (POST ทุก 10 วินาที — ใช้ทำกราฟ)
                                │
                                ▼
                    GitHub Pages  /freeboard/index.html
                                │
                                ▼
                         Web Dashboard (Realtime)
```

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `esphome/smart-classroom.yaml` | Firmware ESP32: สุ่มค่าเซ็นเซอร์, ประมวลผล Alert, ควบคุมพัดลม, ส่ง Firebase |
| `esphome/secrets.example.yaml` | ตัวอย่าง WiFi/รหัสผ่าน (คัดลอกเป็น `secrets.yaml`) |
| `firebase/database.rules.json` | Security Rules ของ Realtime Database |
| `freeboard/index.html` | Web Dashboard (GitHub Pages) |
| `index.html` | หน้าแรก redirect ไป `/freeboard` |
| `tools/simulate.py` | จำลอง ESP32 บนคอมพิวเตอร์ (ทดสอบโดยไม่ต้องมีบอร์ด) |

## ข้อมูลที่จัดเก็บ (8 คอลัมน์ + metadata)

| Field | ตัวอย่าง | หน่วย | หมายเหตุ |
|---|---:|---|---|
| `temperature` | 28.4 | °C | random-walk, คนเยอะร้อนขึ้น, พัดลมเปิดเย็นลง |
| `humidity` | 63.2 | % | |
| `light` | 542 | lux | |
| `co2` | 812 | ppm | สัมพันธ์กับจำนวนคน, พัดลมช่วยลด |
| `noise` | 48 | dB | สัมพันธ์กับจำนวนคน |
| `people` | 27 | คน | 0–50 |
| `air_quality` | 72 | % | คำนวณจาก CO₂ |
| `fan_status` | ON | สถานะ | คำนวณจาก Logic |
| `alerts` | `["co2_high"]` | – | รหัสการแจ้งเตือน |
| `device`, `time`, `ts` | ST806 | – | ชื่ออุปกรณ์, เวลา (SNTP), timestamp ของ Firebase |

ตัวอย่าง JSON ใน Firebase:

```json
{
  "latest": { "temperature": 28.4, "humidity": 63.2, "light": 542, "co2": 812, "noise": 48,
              "people": 27, "air_quality": 72, "fan_status": "OFF",
              "device": "ST806", "time": "2026-10-01 10:15:20", "ts": 1790824520000 },
  "history": { "-Nx1a...": { "...": "..." }, "-Nx1b...": { "...": "..." } }
}
```

## Logic การประมวลผล (ทำบน ESP32 และแสดงซ้ำบน Dashboard)

| เงื่อนไข | ผลลัพธ์ |
|---|---|
| CO₂ > 1000 ppm | ⚠️ คุณภาพอากาศไม่ดี (`co2_high`) |
| Temperature > 30 °C | 🔥 อุณหภูมิสูง (`temp_high`) |
| People > 40 | ⚠️ ห้องมีคนหนาแน่น (`crowded`) |
| Light < 200 lux | 💡 แสงสว่างไม่เพียงพอ (`light_low`) |
| อุณหภูมิสูง **หรือ** CO₂ สูง | 🌀 `fan_status = ON` (เปิด GPIO2/LED บนบอร์ดแทน Relay) |

เมื่อพัดลมเปิด ค่าจำลองของอุณหภูมิและ CO₂ จะค่อย ๆ ลดลง — ทำให้เห็นวงจรควบคุมแบบ feedback ได้จริงบนกราฟ

## ขั้นตอนติดตั้ง

### 1) Firebase
1. ไปที่ <https://console.firebase.google.com> → **Add project** ตั้งชื่อ **`iot-118`**
2. เมนู **Build → Realtime Database → Create Database** เลือก location (เช่น Singapore `asia-southeast1`)
3. คัดลอก URL ของฐานข้อมูล เช่น `https://iot-118-default-rtdb.asia-southeast1.firebasedatabase.app`
4. แท็บ **Rules** → วางเนื้อหาจาก `firebase/database.rules.json` → **Publish**

> URL นี้ต้องใส่ 3 ที่: `esphome/smart-classroom.yaml` (`firebase_url`), `freeboard/index.html` (`databaseURL`), `tools/simulate.py` (`FIREBASE_URL`)

### 2) ESP32 + ESPHome
```bash
pip install esphome
```
```bash
cp esphome/secrets.example.yaml esphome/secrets.yaml
```
แก้ WiFi ใน `secrets.yaml` แล้วเสียบ ESP32 ผ่าน USB:
```bash
esphome run esphome/smart-classroom.yaml
```
ดู log จะเห็น `latest -> HTTP 200` และ `history -> HTTP 200` ทุก 10 วินาที

### 3) GitHub Pages
```bash
git init
git add .
git commit -m "Smart Classroom Monitoring System"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```
จากนั้นใน GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**

Dashboard จะอยู่ที่: `https://<username>.github.io/<repo>/freeboard`

### ทดสอบโดยไม่ใช้บอร์ด
- ดูหน้าจอด้วยข้อมูลจำลองในเบราว์เซอร์: `.../freeboard/?demo`
- ส่งข้อมูลจริงเข้า Firebase จากคอมพิวเตอร์: `python tools/simulate.py`

## หมายเหตุด้านความปลอดภัย
Rules ในโปรเจกต์นี้เปิดให้อ่าน/เขียนแบบสาธารณะ (มีการ validate ว่าต้องมีครบ 8 ฟิลด์) เหมาะกับงานเรียน/สาธิต หากใช้งานจริงควรเปิด Firebase Authentication และจำกัดสิทธิ์การเขียนเฉพาะอุปกรณ์
