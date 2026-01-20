import serial
import json
import time
import threading
import requests
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_TOKEN = "YOUR_INFLUX_TOKEN_HERE" 
INFLUX_ORG = "YOUR_ORG_ID_HERE" 
INFLUX_BUCKET = "sensor_verileri"
INFLUX_URL = "http://localhost:8086"

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

SERIAL_PORT = 'COM5' 
BAUD_RATE = 115200

LOCALIZATION = {
    "EN": {
        "welcome": "🛡️ **AeroStat Guardian Active**\n\nSystem is monitoring for critical anomalies.\n\n🔹 **/status** - Safety Report\n🔹 **/test** - Simulate Emergency\n🔹 **/mute** - Silence Alerts\n🔹 **/tr** - Switch to Turkish",
        "emergency_fire": "🔥 **CRITICAL: FIRE DETECTED! ({val}°C)**\nImmediate Action Required!\nEvacuate safely.\n[📞 CALL FIRE DEPT (112)](tel:112)",
        "emergency_freeze": "❄️ **CRITICAL: FREEZING HAZARD ({val}°C)**\nPipe burst risk.\n[📞 CALL EMERGENCY](tel:112)",
        "sensor_fault": "⚠️ **Sensor Data Rejected**\nValue {val} is physically impossible. Check sensor.",
        "advice_high": "🌡️ **High Temp Warning ({val}°C)**\nRisk: Heat Stroke.\nAction: Hydrate and cool down.",
        "advice_low": "🧥 **Low Temp Warning ({val}°C)**\nRisk: Cold Stress.\nAction: Wear thermal clothing.",
        "normal": "✅ **System Normal**\nTemp: {temp}°C | Hum: {hum}%",
        "muted": "🔕 System Muted.",
        "unmuted": "🔔 System Active.",
        "lang_set": "🇬🇧 Language: **English**"
    },
    "TR": {
        "welcome": "🛡️ **AeroStat Koruyucu Aktif**\n\nSistem kritik anormallikleri izliyor.\n\n🔹 **/durum** - Güvenlik Raporu\n🔹 **/test** - Acil Durum Simülasyonu\n🔹 **/sustur** - Bildirimleri Kapat\n🔹 **/en** - Switch to English",
        "emergency_fire": "🔥 **ACİL: YANGIN TEHLİKESİ! ({val}°C)**\nDerhal ortamı terk edin!\n[📞 İTFAİYEYİ ARA (112)](tel:112)",
        "emergency_freeze": "❄️ **ACİL: DONMA RİSKİ ({val}°C)**\nSu boruları patlayabilir.\n[📞 ACİL YARDIM (112)](tel:112)",
        "sensor_fault": "⚠️ **Hatalı Sensör Verisi**\n{val} değeri fiziksel olarak imkansız. Sensörü kontrol edin.",
        "advice_high": "🌡️ **Yüksek Sıcaklık ({val}°C)**\nRisk: Sıcak Çarpması.\nÖneri: Bol sıvı tüketin ve serinleyin.",
        "advice_low": "🧥 **Düşük Sıcaklık ({val}°C)**\nRisk: Hipotermi.\nÖneri: Termal giysiler giyin.",
        "normal": "✅ **Sistem Normal**\nSıcaklık: {temp}°C | Nem: %{hum}",
        "muted": "🔕 Bildirimler Susturuldu.",
        "unmuted": "🔔 Bildirimler Aktif.",
        "lang_set": "🇹🇷 Dil: **Türkçe**"
    }
}

db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = db_client.write_api(write_options=SYNCHRONOUS)

serial_lock = threading.Lock()
ser = None

state = {
    "temp": 0.0,
    "hum": 0.0,
    "last_valid_time": time.time(),
    "is_muted": False,
    "language": "TR" 
}

class SafetyManager:
    def __init__(self):
        self.last_alert_time = 0
        self.alert_cooldown = 300
        self.min_valid_temp = -20.0
        self.max_valid_temp = 80.0
        self.fire_threshold = 50.0
        self.freeze_threshold = 5.0

    def get_text(self, key, **kwargs):
        return LOCALIZATION[state["language"]].get(key, "").format(**kwargs)

    def validate_reading(self, t, h):
        if t < self.min_valid_temp or t > self.max_valid_temp:
            return False, self.get_text("sensor_fault", val=t)
        if h < 0.0 or h > 100.0:
            return False, self.get_text("sensor_fault", val=h)
        return True, ""

    def analyze_safety(self, t, h):
        timestamp = time.time()

        if t >= self.fire_threshold:
            return self.get_text("emergency_fire", val=t)
        if t <= self.freeze_threshold:
            return self.get_text("emergency_freeze", val=t)

        if state["is_muted"]: return None
        if timestamp - self.last_alert_time < self.alert_cooldown: return None

        alert = None
        if t > 30.0: 
            alert = self.get_text("advice_high", val=t)
        elif t < 15.0:
            alert = self.get_text("advice_low", val=t)

        if alert:
            self.last_alert_time = timestamp
            return alert
        
        return None

safety = SafetyManager()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Telegram Hatası: {e}")

def telegram_thread():
    last_id = 0
    print("🤖 Telegram Servisi Başlatıldı...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_id + 1}&timeout=30"
            resp = requests.get(url, timeout=35).json()
            if resp["ok"] and resp["result"]:
                for upd in resp["result"]:
                    last_id = upd["update_id"]
                
                    if str(upd["message"]["chat"]["id"]) == str(TELEGRAM_CHAT_ID):
                        txt = upd["message"].get("text", "").lower()
                        print(f"📩 Komut Alındı: {txt}")
                        
                        if "/start" in txt: 
                            send_telegram(safety.get_text("welcome"))
                        elif "/tr" in txt: 
                            state["language"] = "TR"
                            send_telegram(safety.get_text("lang_set"))
                        elif "/en" in txt or "/eng" in txt: 
                            state["language"] = "EN"
                            send_telegram(safety.get_text("lang_set"))
                        elif "/durum" in txt or "/status" in txt:
                            send_telegram(safety.get_text("normal", temp=state["temp"], hum=state["hum"]))
                        elif "/test" in txt: 
                            send_telegram(safety.get_text("emergency_fire", val=55.5))
                        elif "/sustur" in txt or "/mute" in txt:
                            state["is_muted"] = not state["is_muted"]
                            msg = "muted" if state["is_muted"] else "unmuted"
                            send_telegram(safety.get_text(msg))
        except Exception as e:
            print(f"Bot Bağlantı Hatası: {e}")
            time.sleep(5)

def sensor_thread():
    print("🌡️ Sensör Servisi Başlatıldı...")
    while True:
        try:
            line = ""
            with serial_lock:
                if ser and ser.in_waiting: line = ser.readline().decode().strip()
            
            if line:
                try:
                    data = json.loads(line)
                    t, h = float(data["temp"]), float(data["hum"])
                    
                    is_valid, error_msg = safety.validate_reading(t, h)
                    
                    if not is_valid:
                        print(f"Hatalı Veri: {error_msg}")
                        continue

                    state["temp"] = t
                    state["hum"] = h
                    state["last_valid_time"] = time.time()
                    
                    p = Point("hava_durumu").field("sicaklik", t).field("nem", h)
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
                    print(f"Veri: {t}°C | {h}%")
                    
                    alert = safety.analyze_safety(t, h)
                    if alert: send_telegram(alert)
                    
                except json.JSONDecodeError: pass
        except: pass
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        threading.Thread(target=sensor_thread).start()
        threading.Thread(target=telegram_thread).start()
    except Exception as e: print(f"BAŞLATMA HATASI: {e}")