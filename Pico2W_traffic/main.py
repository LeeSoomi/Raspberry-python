# main.py  (Pico 2 W, MicroPython v1.26.x)
from bluetooth import BLE
from machine import Pin, I2C
import time, ubinascii

# ==== 디스플레이(SSD1306) 선택: 없으면 자동으로 LED fallback ====
USE_OLED = True
oled = None
try:
    from ssd1306 import SSD1306_I2C
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    oled = SSD1306_I2C(128, 64, i2c)
except:
    USE_OLED = False

LED = Pin("LED", Pin.OUT)

def show_text(txt):
    if USE_OLED and oled:
        oled.fill(0)
        oled.text("REMAIN", 0, 0)
        oled.text(str(txt), 0, 20)
        oled.show()
    else:
        # 간단 LED 표시: 숫자면 빠르게 secs회 점멸, 'N'이면 천천히 2회
        LED.off()
        if isinstance(txt, int):
            for _ in range(min(5, max(1, txt))):
                LED.on(); time.sleep(0.08)
                LED.off(); time.sleep(0.12)
        else:
            for _ in range(2):
                LED.on(); time.sleep(0.3)
                LED.off(); time.sleep(0.3)

# ==== 광고 파싱 ====
def parse_adv_fields(adv_bytes: bytes):
    i = 0; out = {}
    b = adv_bytes
    while i < len(b):
        ln = b[i]
        if ln == 0: break
        t = b[i+1]
        v = b[i+2:i+1+ln]
        out.setdefault(t, []).append(v)
        i += 1 + ln
    return out

def read_remain_from_adv(adv_bytes: bytes):
    """
    우선순위:
      1) Complete Local Name(0x09) 'S:nn'
      2) Service Data(0x16, uuid=0xFFFF) 첫 바이트 'S', 뒤에 ASCII 숫자
    둘 중 하나만 오면 됨.
    """
    f = parse_adv_fields(adv_bytes)
    # 1) Name
    for v in f.get(0x09, []):
        try:
            s = v.decode()
            if s.startswith("S:"):
                n = int(''.join([ch for ch in s[2:] if ch.isdigit()]) or "0")
                return n
        except: pass
    # 2) Service Data
    for v in f.get(0x16, []):
        if len(v) >= 3 and v[0] == 0xFF and v[1] == 0xFF:
            # v[2:] 예: b'S:20'
            try:
                payload = v[2:]
                if payload.startswith(b'S:'):
                    num = int(''.join([chr(c) for c in payload[2:] if 48 <= c <= 57]) or "0")
                    return num
            except: pass
    return None

# ==== BLE 스캔 & 표시 ====
ble = BLE(); ble.active(True)

last_seen_ms = time.ticks_ms()
remain = None

def bt_irq(event, data):
    global last_seen_ms, remain
    if event == 5:  # _IRQ_SCAN_RESULT (빌드별 번호가 다르면 5가 기본)
        _addr_type, _addr, _adv_type, _rssi, adv_data = data
        adv_bytes = bytes(adv_data)
        val = read_remain_from_adv(adv_bytes)
        if val is not None:
            remain = max(0, min(99, val))
            last_seen_ms = time.ticks_ms()

ble.irq(bt_irq)
ble.gap_scan(0, 30000, 30000)  # 연속 스캔

# 부팅 알림
show_text("N")

# 메인 루프: 1Hz로 로컬 카운트다운, 타임아웃 시 'N'
while True:
    now = time.ticks_ms()
    age = time.ticks_diff(now, last_seen_ms)
    if remain is not None and age < 3000:
        # 1초마다 감소
        show_text(remain)
        time.sleep(1.0)
        if remain > 0:
            remain -= 1
    else:
        remain = None
        show_text("N")
        time.sleep(0.5)
