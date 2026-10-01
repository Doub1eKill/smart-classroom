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
แก้ชื่อและรหัส WiFi ใน `secrets.yaml` (ต้องเป็น **2.4 GHz** — ดูวิธีละเอียดที่ [คู่มือ: ตั้งค่า WiFi](#ขั้นที่-2-สร้างไฟล์รหัส-wifi-secretsyaml)) แล้วเสียบ ESP32 ผ่าน USB:
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

## คู่มือการใช้งาน (ทีละขั้น)

### ขั้นที่ 1: เตรียมคอมพิวเตอร์
1. ติดตั้ง **Python 3.11 ขึ้นไป** จาก <https://www.python.org/downloads/> — ตอนติดตั้งให้ติ๊ก **Add python.exe to PATH**
2. ดาวน์โหลดโปรเจกต์ (เลือกวิธีใดวิธีหนึ่ง)
   - กดปุ่ม **Code → Download ZIP** ที่หน้า repo แล้วแตกไฟล์ไว้ที่ `C:\IOT`
   - หรือใช้ git: `git clone https://github.com/Doub1eKill/smart-classroom.git C:\IOT`
3. เปิด **PowerShell** (กด `Win` พิมพ์ `PowerShell` แล้ว Enter) และติดตั้ง ESPHome:
   ```bash
   pip install esphome
   ```
4. ตรวจว่าติดตั้งสำเร็จ — ต้องเห็นเลขเวอร์ชัน เช่น `Version: 2026.8.1`
   ```bash
   python -m esphome version
   ```

### ขั้นที่ 2: สร้างไฟล์รหัส WiFi (`secrets.yaml`)

ESPHome อ่านชื่อ/รหัส WiFi จากไฟล์ `esphome/secrets.yaml` ไฟล์นี้**ไม่มีมาใน repo** (ถูกกันไว้ใน `.gitignore` เพื่อไม่ให้รหัส WiFi หลุดขึ้น GitHub) จึงต้องสร้างเองจากไฟล์ตัวอย่าง `secrets.example.yaml`

**วิธีที่ 1 — ใช้ PowerShell**
```bash
cd C:\IOT\esphome
```
```bash
copy secrets.example.yaml secrets.yaml
```
```bash
notepad secrets.yaml
```

**วิธีที่ 2 — ใช้ File Explorer**
1. เปิดโฟลเดอร์ `C:\IOT\esphome`
2. คลิกขวาที่ `secrets.example.yaml` → **Copy** แล้ว **Paste** ในโฟลเดอร์เดิม
3. เปลี่ยนชื่อไฟล์ที่ได้เป็น `secrets.yaml`
   - ถ้าไม่เห็นนามสกุลไฟล์ ให้ไปที่ **View → Show → File name extensions** ก่อน ไม่งั้นอาจได้ชื่อ `secrets.yaml.txt` ซึ่งใช้ไม่ได้
4. คลิกขวาที่ `secrets.yaml` → **Open with → Notepad**

**แก้ค่าในไฟล์** ให้เป็นแบบนี้ (เปลี่ยนเฉพาะข้อความในเครื่องหมายคำพูด)
```yaml
wifi_ssid: "ชื่อWiFiของคุณ"
wifi_password: "รหัสWiFiของคุณ"
ap_password: "classroom118"
ota_password: "change-me"
```

| ค่า | ความหมาย |
|---|---|
| `wifi_ssid` | ชื่อ WiFi ที่ให้ ESP32 เชื่อมต่อ (ตัวพิมพ์เล็ก/ใหญ่ต้องตรง) |
| `wifi_password` | รหัส WiFi |
| `ap_password` | รหัสของ WiFi สำรองที่บอร์ดปล่อยเองเมื่อต่อ WiFi หลักไม่ได้ (อย่างน้อย 8 ตัวอักษร) |
| `ota_password` | รหัสสำหรับอัปโหลด firmware ผ่าน WiFi (ตั้งอะไรก็ได้) |

กฎการเขียนไฟล์ YAML
- ต้องมี**ช่องว่าง 1 ช่องหลังเครื่องหมาย `:`** เช่น `wifi_ssid: "MyWiFi"` (ไม่ใช่ `wifi_ssid:"MyWiFi"`)
- ใส่ค่าไว้ใน**เครื่องหมายคำพูด `" "`** เสมอ โดยเฉพาะรหัสที่เป็นตัวเลขล้วนหรือมีอักขระพิเศษ
- ห้ามเว้นวรรคหน้าบรรทัด และห้ามใช้ปุ่ม Tab
- WiFi ต้องเป็นคลื่น **2.4 GHz** — ESP32 ใช้ 5 GHz ไม่ได้ (ถ้าใช้ฮอตสปอตมือถือ ให้เปิด "Maximize compatibility" หรือเลือก 2.4 GHz)

กด **Ctrl + S** เพื่อบันทึก แล้วตรวจความถูกต้องของไฟล์ — ต้องเห็น `Configuration is valid!`
```bash
python -m esphome config smart-classroom.yaml
```

### ขั้นที่ 3: อัปโหลดโปรแกรมลง ESP32
1. เสียบ ESP32 เข้าคอมด้วยสาย USB (ต้องเป็นสายที่ส่งข้อมูลได้)
2. รันคำสั่งใน PowerShell (อยู่ในโฟลเดอร์ `C:\IOT\esphome`)
   ```bash
   python -m esphome run smart-classroom.yaml
   ```
3. ครั้งแรกจะใช้เวลาคอมไพล์ 5–15 นาที (ดาวน์โหลด toolchain) จากนั้นจะถามช่องทางอัปโหลด ให้เลือกพอร์ต **COM** (เช่น `COM3`)
4. เมื่ออัปโหลดเสร็จ หน้าจอจะแสดง log ของบอร์ด ตรวจว่ามีข้อความเหล่านี้
   - `WiFi Connected!` — ต่อ WiFi สำเร็จ
   - `latest -> HTTP 200` และ `history -> HTTP 200` ทุก 10 วินาที — ส่งข้อมูลเข้า Firebase สำเร็จ
5. กด **Ctrl + C** เพื่อออกจาก log (บอร์ดยังทำงานต่อไป) — ถอดสาย USB แล้วเสียบกับที่ชาร์จมือถือก็ใช้งานได้

### ขั้นที่ 4: เปลี่ยน WiFi ภายหลัง (เช่น ย้ายบอร์ดไปที่อื่น)

**แบบ A — ผ่าน WiFi สำรองของบอร์ด (ไม่ต้องใช้คอม)**
ถ้าบอร์ดต่อ WiFi เดิมไม่ได้ประมาณ 1 นาที จะปล่อย WiFi ชื่อ **`Smart-Classroom-Fallback`** ออกมาเอง
1. ใช้มือถือเชื่อมต่อ `Smart-Classroom-Fallback` ด้วยรหัส `ap_password` (ค่าเริ่มต้น `classroom118`)
2. หน้าตั้งค่าจะเด้งขึ้นมาเอง (ถ้าไม่เด้ง เปิดเบราว์เซอร์ไปที่ `http://192.168.4.1`)
3. เลือกชื่อ WiFi ใหม่ ใส่รหัส แล้วกด **Save** — บอร์ดจะรีสตาร์ทและต่อ WiFi ใหม่

> ควรแก้ `secrets.yaml` ให้เป็น WiFi ใหม่ด้วย เพื่อให้การอัปโหลด firmware ครั้งถัดไปใช้ค่าที่ถูกต้องเสมอ

**แบบ B — แก้ไฟล์แล้วอัปโหลดใหม่**
1. แก้ `wifi_ssid` / `wifi_password` ใน `secrets.yaml` แล้วบันทึก
2. รัน `python -m esphome run smart-classroom.yaml`
3. เลือก **Over The Air** ถ้าบอร์ดยังอยู่ใน WiFi เดียวกับคอม หรือเสียบสาย USB แล้วเลือกพอร์ต **COM**

### ขั้นที่ 5: ใช้งาน Dashboard
1. เปิด <https://doub1ekill.github.io/smart-classroom/freeboard> บนคอมหรือมือถือ
2. มุมขวาบนต้องขึ้นจุดสีเขียว **Realtime** — แปลว่าเชื่อมต่อ Firebase แล้ว
3. ค่าต่าง ๆ อัปเดตเองทุก 10 วินาที ไม่ต้องกดรีเฟรช
4. อ่านสถานะจากป้ายบนการ์ด: **ปกติ** (เขียว) / **ควรระวัง** (เหลือง) / **เกินเกณฑ์** (แดง)
5. เลือกช่วงเวลาของกราฟ 5 / 10 / 30 นาที ได้ที่หัวข้อ "แนวโน้มย้อนหลัง" และชี้เมาส์บนกราฟเพื่อดูค่าแต่ละจุด
6. กดปุ่มพระจันทร์/พระอาทิตย์มุมขวาบนเพื่อสลับโหมดสว่าง/มืด

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| ไม่เห็นพอร์ต COM | ติดตั้งไดรเวอร์ CP210x หรือ CH340 และใช้สาย USB ที่ส่งข้อมูลได้ |
| ค้างที่ `Connecting....` | กดปุ่ม **BOOT** บนบอร์ดค้างไว้จนเริ่มอัปโหลด |
| ESP32 ต่อ WiFi ไม่ได้ | ใช้คลื่น 2.4 GHz และตรวจชื่อ/รหัสใน `secrets.yaml` (ตัวพิมพ์เล็ก/ใหญ่ต้องตรง) หรือตั้งผ่าน WiFi สำรองตาม [ขั้นที่ 4](#ขั้นที่-4-เปลี่ยน-wifi-ภายหลัง-เช่น-ย้ายบอร์ดไปที่อื่น) |
| `Error reading file secrets.yaml` | ยังไม่ได้สร้างไฟล์ หรือชื่อไฟล์เป็น `secrets.yaml.txt` — ดู [ขั้นที่ 2](#ขั้นที่-2-สร้างไฟล์รหัส-wifi-secretsyaml) |
| `mapping values are not allowed` | ลืมเว้นวรรคหลัง `:` หรือลืมใส่ `" "` ใน `secrets.yaml` |
| `HTTP 401` / `403` | Rules ไม่อนุญาตเขียน หรือ test mode หมดอายุ — วาง Rules จากไฟล์ใหม่ |
| `HTTP 404` | `firebase_url` ไม่ถูกต้อง |
| Dashboard ขึ้น "ขาดการเชื่อมต่อ" | ตรวจ `databaseURL` ใน `freeboard/index.html` และสิทธิ์ `.read` |
| เว็บยังเป็นเวอร์ชันเก่า | รอ 1–2 นาทีหลัง push แล้วกด **Ctrl + F5** |

## หมายเหตุ
- **ความปลอดภัย:** Rules เปิดให้อ่าน/เขียนแบบสาธารณะ (validate ว่าต้องมีครบ 8 ฟิลด์) เหมาะกับงานเรียน/สาธิต หากใช้งานจริงควรเปิด Firebase Authentication และจำกัดสิทธิ์การเขียนเฉพาะอุปกรณ์
- **GPIO2** เป็น strapping pin — ใช้กับ LED บนบอร์ดได้ แต่ถ้าต่อ Relay จริงที่มี pull-up/pull-down ควรย้ายไปขาอื่น เช่น GPIO26
- `history` จะเพิ่มขึ้นเรื่อย ๆ (~8,640 รายการ/วัน) ลบโหนด `history` ใน Firebase Console ได้เมื่อต้องการเริ่มเก็บใหม่
