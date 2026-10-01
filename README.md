# Smart Classroom Monitoring System

ระบบตรวจสอบสภาพห้องเรียน **ST806** แบบ Realtime — ESP32 + ESPHome จำลองค่าเซ็นเซอร์ ประมวลผลบนบอร์ด แล้วส่งข้อมูลไปเก็บใน Firebase Realtime Database (`iot-118`) และแสดงผลผ่าน Web Dashboard บน GitHub Pages

- **Live Dashboard:** https://doub1ekill.github.io/smart-classroom/freeboard
- **Demo (ข้อมูลจำลองในเบราว์เซอร์):** https://doub1ekill.github.io/smart-classroom/freeboard/?demo

---

## สถาปัตยกรรมระบบ

```
ESP32 + ESPHome (ห้อง ST806)
  - สุ่มค่าเซ็นเซอร์ 8 ค่า
  - Alert + Fan logic
        │  HTTPS ทุก 10 วินาที
        ▼
Firebase Realtime Database (iot-118)
  ├── latest    ← PUT  (ค่าปัจจุบัน)
  └── history   ← POST (ประวัติสำหรับกราฟ)
        │  Realtime (WebSocket)
        ▼
GitHub Pages  /freeboard
        │
        ▼
Web Dashboard (Chart.js + Lucide Icons)
```

| ส่วน | เทคโนโลยี |
|---|---|
| อุปกรณ์ | ESP32 (esp32dev) + ESPHome 2026.x, framework ESP-IDF |
| ฐานข้อมูล | Firebase Realtime Database — `iot-118` (asia-southeast1) |
| Dashboard | HTML + Firebase JS SDK 10, Chart.js 4, Lucide Icons, ฟอนต์ IBM Plex Sans Thai |
| Hosting | GitHub Pages (branch `main` / root) |

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `esphome/smart-classroom.yaml` | Firmware ESP32: สุ่มค่าเซ็นเซอร์, ประมวลผล Alert, ควบคุมพัดลม, ส่ง Firebase |
| `esphome/secrets.example.yaml` | ตัวอย่างไฟล์ WiFi/รหัสผ่าน (คัดลอกเป็น `secrets.yaml` — ไม่ถูก commit) |
| `firebase/database.rules.json` | Security Rules ของ Realtime Database |
| `freeboard/index.html` | Web Dashboard |
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
| `alerts` | `["co2_high"]` | – | รหัสการแจ้งเตือนที่เกิดขึ้น |
| `device` | ST806 | – | ชื่อห้อง/อุปกรณ์ |
| `time` | 2026-10-01 10:15:20 | – | เวลาจาก SNTP (Asia/Bangkok) |
| `ts` | 1790824520000 | ms | timestamp ฝั่ง Firebase (`{".sv":"timestamp"}`) |

ตัวอย่าง JSON ใน Firebase:

```json
{
  "latest": { "temperature": 28.4, "humidity": 63.2, "light": 542, "co2": 812, "noise": 48,
              "people": 27, "air_quality": 72, "fan_status": "OFF", "alerts": [],
              "device": "ST806", "time": "2026-10-01 10:15:20", "ts": 1790824520000 },
  "history": { "-Nx1a...": { "...": "..." }, "-Nx1b...": { "...": "..." } }
}
```

## Logic การประมวลผล

ประมวลผลบน ESP32 (Edge logic) และ Dashboard แสดงผลซ้ำจากค่าเดียวกัน

| เงื่อนไข | ผลลัพธ์ | รหัส |
|---|---|---|
| CO₂ > 1000 ppm | คุณภาพอากาศไม่ดี | `co2_high` |
| Temperature > 30 °C | อุณหภูมิสูง | `temp_high` |
| People > 40 | ห้องมีคนหนาแน่น | `crowded` |
| Light < 200 lux | แสงสว่างไม่เพียงพอ | `light_low` |
| อุณหภูมิสูง **หรือ** CO₂ สูง | `fan_status = ON` — เปิด GPIO2 (LED บนบอร์ด แทน Relay) | – |

เมื่อพัดลมเปิด ค่าจำลองของอุณหภูมิและ CO₂ จะค่อย ๆ ลดลง ทำให้เห็นวงจรควบคุมแบบ feedback บนกราฟได้จริง

## Web Dashboard

- **ส่วนหัว** — ชื่อห้อง, สรุปสถานะห้อง, เวลาอัปเดตล่าสุด และวงแหวนคุณภาพอากาศ (%)
- **การ์ดค่าปัจจุบัน 8 ใบ** — ไอคอน, ค่า, ป้ายสถานะ 3 ระดับ (ปกติ / ควรระวัง / เกินเกณฑ์) และแถบวัดพร้อมขีดเกณฑ์สีแดง
- **การ์ดพัดลม** — ใบพัดหมุนเมื่อ ON พร้อมบอกเหตุผลที่เปิด
- **การแจ้งเตือน** — แสดงทุกเงื่อนไขที่เกิดขึ้นพร้อมค่าจริง
- **กราฟแนวโน้ม 6 กราฟ** — หนึ่งค่าต่อหนึ่งกราฟ มีเส้นเกณฑ์, ค่าต่ำสุด/สูงสุด, tooltip และเลือกช่วง 5 / 10 / 30 นาทีได้
- **ตารางประวัติ** — 12 รายการล่าสุด ค่าที่เกินเกณฑ์มี ▲ นำหน้า
- **โหมดสว่าง/มืด** — ปุ่มมุมขวาบน (จำค่าที่เลือก) และรองรับหน้าจอมือถือ

เกณฑ์ "ควรระวัง" บน Dashboard: อุณหภูมิ > 28 °C, ความชื้น > 70 %, แสง < 300 lux, CO₂ > 800 ppm, เสียง > 60 dB, คน > 35, คุณภาพอากาศ < 70 %

## ขั้นตอนติดตั้ง

### 1) Firebase
1. ไปที่ <https://console.firebase.google.com> → **Add project** ตั้งชื่อ **`iot-118`**
2. **Build → Realtime Database → Create Database** → เลือก Singapore (`asia-southeast1`) → Start in test mode
3. คัดลอก URL ของฐานข้อมูล: `https://iot-118-default-rtdb.asia-southeast1.firebasedatabase.app`
4. แท็บ **Rules** → วางเนื้อหาจาก `firebase/database.rules.json` → **Publish** (test mode หมดอายุใน 30 วัน)

> ถ้า URL ต่างจากนี้ ต้องแก้ 3 ที่: `esphome/smart-classroom.yaml` (`firebase_url`), `freeboard/index.html` (`databaseURL`), `tools/simulate.py` (`FIREBASE_URL`)

### 2) ESP32 + ESPHome

> ใช้ **PowerShell หรือ CMD** เท่านั้น — ESP-IDF ไม่รองรับ Git Bash (MSys) จะคอมไพล์ "สำเร็จ" แต่ไม่มีไฟล์ firmware

```bash
pip install esphome
```
```bash
copy esphome\secrets.example.yaml esphome\secrets.yaml
```
แก้ชื่อและรหัส WiFi ใน `secrets.yaml` (ต้องเป็น **2.4 GHz**) แล้วเสียบ ESP32 ผ่าน USB:
```bash
python -m esphome run esphome/smart-classroom.yaml
```
- ครั้งแรกเลือกพอร์ต **COM** — ครั้งต่อไปเลือก **Over The Air** อัปโหลดผ่าน WiFi ได้
- log ที่ถูกต้องจะเห็น `latest -> HTTP 200` และ `history -> HTTP 200` ทุก 10 วินาที

ตั้งค่าที่แก้ได้ใน `substitutions` ของไฟล์ YAML: `room_id`, `firebase_url`, `publish_interval`, `co2_limit`, `temp_limit`, `people_limit`, `light_limit`

### 3) GitHub Pages
```bash
gh repo create smart-classroom --public --source . --remote origin --push
```
จากนั้น **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**
Dashboard จะอยู่ที่ `https://<username>.github.io/<repo>/freeboard`

อัปเดตเว็บหลังแก้ไขโค้ด:
```bash
git add .
```
```bash
git commit -m "อธิบายสิ่งที่แก้"
```
```bash
git push
```

### ทดสอบโดยไม่ใช้บอร์ด
- ดูหน้าจอด้วยข้อมูลจำลองในเบราว์เซอร์: `.../freeboard/?demo`
- ส่งข้อมูลจริงเข้า Firebase จากคอมพิวเตอร์: `python tools/simulate.py` (ใส่ตัวเลขต่อท้ายเพื่อกำหนดจำนวนรอบ เช่น `python tools/simulate.py 3`)

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| ไม่เห็นพอร์ต COM | ติดตั้งไดรเวอร์ CP210x หรือ CH340 และใช้สาย USB ที่ส่งข้อมูลได้ |
| ค้างที่ `Connecting....` | กดปุ่ม **BOOT** บนบอร์ดค้างไว้จนเริ่มอัปโหลด |
| ESP32 ต่อ WiFi ไม่ได้ | ใช้คลื่น 2.4 GHz และตรวจชื่อ/รหัสใน `secrets.yaml` |
| `HTTP 401` / `403` | Rules ไม่อนุญาตเขียน หรือ test mode หมดอายุ — วาง Rules จากไฟล์ใหม่ |
| `HTTP 404` | `firebase_url` ไม่ถูกต้อง |
| Dashboard ขึ้น "ขาดการเชื่อมต่อ" | ตรวจ `databaseURL` ใน `freeboard/index.html` และสิทธิ์ `.read` |
| เว็บยังเป็นเวอร์ชันเก่า | รอ 1–2 นาทีหลัง push แล้วกด **Ctrl + F5** |

## หมายเหตุ
- **ความปลอดภัย:** Rules เปิดให้อ่าน/เขียนแบบสาธารณะ (validate ว่าต้องมีครบ 8 ฟิลด์) เหมาะกับงานเรียน/สาธิต หากใช้งานจริงควรเปิด Firebase Authentication และจำกัดสิทธิ์การเขียนเฉพาะอุปกรณ์
- **GPIO2** เป็น strapping pin — ใช้กับ LED บนบอร์ดได้ แต่ถ้าต่อ Relay จริงที่มี pull-up/pull-down ควรย้ายไปขาอื่น เช่น GPIO26
- `history` จะเพิ่มขึ้นเรื่อย ๆ (~8,640 รายการ/วัน) ลบโหนด `history` ใน Firebase Console ได้เมื่อต้องการเริ่มเก็บใหม่
