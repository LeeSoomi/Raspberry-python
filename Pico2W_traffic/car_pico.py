# car_pico.py  (MicroPython for Pico W)
from micropython import const
from machine import unique_id, I2C, Pin
import bluetooth, ubinascii, utime
import ssd1306

# ===== 설정 =====
SCAN_INT_US    = const(50_000)     # scan interval (μs)
SCAN_WIN_US    = const(50_000)     # scan window  (μs)
ADV_INT_US     = const(100_000)    # ACK 광고 간격(μs) ≈ 100ms
ACK_BURST_MS   = const(600)        # ACK 송신 지속(ms)
ALWAYS_ACK     = True              # 테스트: Q 없어도 1Hz ACK

# ===== BLE 초기화 & UID =====
ble = bluetooth.BLE()
ble.active(True)
my_uid6 = ubinascii.hexlify(unique_id()).decode().upper()[-6:]

# IRQ 상수 호환
try:
    IRQ_SCAN_RESULT = bluetooth.IRQ_SCAN_RESULT
except AttributeError:
    IRQ_SCAN_RESULT = const(5)

# ===== 컨트롤러 광고 파서 (Service Data 0xFFFF / Local Name 폴백) =====
def _iter_ad(adv):
    i, L = 0, len(adv)
    while i + 1 < L:
        ln = adv[i]
        if ln == 0: break
        t  = adv[i + 1]
        yield t, adv[i + 2 : i + 1 + ln]
        i += 1 + ln

def parse_controller_adv(adv_data):
    # Service Data(0x16, UUID 0xFFFF) : "DIR:N|T:GREEN|RT:8|Q:1"
    try:
        for t, p in _iter_ad(adv_data):
            if t == 0x16 and len(p) >= 2 and p[0] == 0xFF and p[1] == 0xFF:
                s = p[2:].decode()
                parts = {}
                for kv in s.split("|"):
                    if ":" in kv:
                        k,v = kv.split(":",1); parts[k]=v
                if "DIR" in parts and "T" in parts and "RT" in parts and "Q" in parts:
                    return {"PH":parts.get("PH",""), "DIR":parts["DIR"],
                            "T":parts["T"], "RT":int(parts["RT"]), "G":int(parts.get("G","0") or 0),
                            "Q":int(parts["Q"])}
    except: pass
    # Local Name(0x09) 폴백
    try:
        for t, p in _iter_ad(adv_data):
            if t == 0x09:
                s = p.decode()
                parts = {}
                for kv in s.split("|"):
                    if ":" in kv:
                        k,v = kv.split(":",1); parts[k]=v
                if "DIR" in parts and "T" in parts and "RT" in parts and "Q" in parts:
                    return {"PH":parts.get("PH",""), "DIR":parts["DIR"],
                            "T":parts["T"], "RT":int(parts["RT"]), "G":int(parts.get("G","0") or 0),
                            "Q":int(parts["Q"])}
    except: pass
    return None

state = {"PH":"", "DIR":"", "T":"RED", "RT":0, "G":0, "Q":0, "last_ms":0}

def _irq(event, data):
    if event == IRQ_SCAN_RESULT:
        _, _, _, _, adv_data = data
        info = parse_controller_adv(adv_data)
        if info:
            state.update(info)
            state["last_ms"] = utime.ticks_ms()

ble.irq(_irq)

# ===== ACK 송신 =====
def _jitter_ms(uid6):
    h=0
    for ch in uid6: h=(h*131+ord(ch)) & 0xFFFF
    return h % 250

def send_ack_burst(direction="N", burst_ms=ACK_BURST_MS):
    payload = ("P|D:{}|UID:{}|C:1".format(direction, my_uid6)).encode()
    adv_sd  = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload
    utime.sleep_ms(_jitter_ms(my_uid6))
    ble.gap_scan(None)
    ble.gap_advertise(ADV_INT_US, adv_sd)  # 펌웨어가 위치 인자 2개만 허용
    utime.sleep_ms(burst_ms)
    ble.gap_advertise(None)
    ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US)

# ===== OLED: I2C0( GP0=SDA, GP1=SCL ), addr=0x3C 로 강제 초기화 =====
i2c  = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

def splash():
    oled.fill(0)
    oled.text("PICO CAR", 0, 0)
    oled.text("UID:"+my_uid6, 0, 12)
    oled.text("Waiting...", 0, 28)
    oled.show()

def draw_oled(direction):
    mine = (state["DIR"] == direction) if state["DIR"] else False
    show_rt = state["RT"] if (mine and state["T"] == "GREEN") else 0

    oled.fill(0)
    if state["DIR"]:
        oled.text("PH:{} DIR:{}".format(state.get("PH","-"), state["DIR"]), 0, 0)
        oled.text("STATE:{}".format(state["T"]), 0, 12)
    else:
        oled.text("NO SIGNAL", 0, 0)

    oled.text("G-LEFT", 0, 32)
    oled.text("{:02d}s".format(int(show_rt)), 64, 32)
    oled.text("Q:{}".format(state.get("Q",0)), 0, 50)
    oled.show()

# ===== 메인 =====
def main(direction="N"):
    ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US)
    splash()
    utime.sleep_ms(800)

    last_ack = 0
    last_draw = 0
    while True:
        now = utime.ticks_ms()

        mine = (state["DIR"] == direction) if state["DIR"] else True
        want_ack = (ALWAYS_ACK or state["Q"] == 1)

        if mine and want_ack and utime.ticks_diff(now, last_ack) >= 1000:
            send_ack_burst(direction); last_ack = now

        if utime.ticks_diff(now, last_draw) >= 500:
            draw_oled(direction); last_draw = now

        utime.sleep_ms(50)

# 자동 실행하지 않으면 REPL에서:  import car_pico; car_pico.main("N")
