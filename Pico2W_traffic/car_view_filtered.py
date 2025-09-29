# car_view_filtered.py  (Pico 2 W / MicroPython)
from micropython import const
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import bluetooth, utime

CAR_ID="CAR - 01"
I2C_SCL, I2C_SDA, OLED_ADDR = 1, 0, 0x3C
SCAN_INT_US, SCAN_WIN_US = const(50_000), const(50_000)
IRQ_SCAN_RESULT = getattr(bluetooth, "IRQ_SCAN_RESULT", const(5))
WAIT_MS = const(6000)

i2c  = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)
oled = SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)

def cx(s): return max(0, (128-len(s)*8)//2)

def draw_wait():
    oled.fill(0); oled.text(CAR_ID, cx(CAR_ID), 0)
    oled.text("WAIT...", cx("WAIT..."), 24); oled.show()

def draw_state(dir_, sec, tchar="-"):
    line2 = "{} {:>2}s".format((tchar or "-")[:1].upper(), sec)
    line3 = "DIR:{}".format(dir_ or "-")
    oled.fill(0); oled.text(CAR_ID, cx(CAR_ID), 0)
    oled.text(line2, cx(line2), 24)
    oled.text(line3, cx(line3), 40)
    oled.show()

def parse_kv(s):
    # 허용: "S:15|D:A|Q:1" 또는 "RT:15|DIR:A|Q:1"
    d = {}
    for kv in s.split("|"):
        if ":" in kv:
            k, v = kv.split(":", 1)
            d[k] = v
    if not d:
        return None
    dir_ = d.get("DIR", d.get("D", ""))
    sec  = d.get("RT",  d.get("S", ""))
    if not (dir_ and sec.isdigit()):
        return None
    tchar = d.get("T", d.get("PH", ""))[:1] if d.get("T", d.get("PH", "")) else "-"
    q     = int(d.get("Q", d.get("ACK", "0")) or 0)
    return {"DIR": dir_, "SEC": int(sec), "TCHAR": tchar, "Q": q}

ble = bluetooth.BLE()
ble.active(True)
last_ms = 0
last_info = None

def iter_ad(adv):
    i, L = 0, len(adv)
    while i + 1 < L:
        ln = adv[i]
        if ln == 0:
            break
        t = adv[i+1]
        v = adv[i+2:i+1+ln]
        yield t, v
        i += 1 + ln

def irq(event, data):
    global last_ms, last_info
    if event == IRQ_SCAN_RESULT:
        _, _, _, _, adv_data = data
        adv = bytes(adv_data)

        # 1) Service Data (0x16) → UUID 0xFFFF
        for t, v in iter_ad(adv):
            if t == 0x16 and len(v) >= 2 and (v[0] | (v[1] << 8)) == 0xFFFF:
                try:
                    info = parse_kv(v[2:].decode("utf-8", "ignore"))
                    if info:
                        last_info = info
                        last_ms = utime.ticks_ms()
                        return
                except: pass

        # 2) Local or Short Name (0x09, 0x08)
        for t, v in iter_ad(adv):
            if t in (0x09, 0x08):
                try:
                    info = parse_kv(v.decode("utf-8", "ignore"))
                    if info:
                        last_info = info
                        last_ms = utime.ticks_ms()
                        return
                except: pass

ble.irq(irq)
ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US, True)  # 액티브 스캔
draw_wait()

while True:
    now = utime.ticks_ms()
    if last_info and utime.ticks_diff(now, last_ms) < WAIT_MS:
        draw_state(last_info["DIR"], last_info["SEC"], last_info["TCHAR"])
    else:
        draw_wait()
    utime.sleep_ms(100)
