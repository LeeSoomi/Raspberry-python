# car_pico.py  (MicroPython for Raspberry Pi Pico W)
# - OLED 자동 감지(I2C0/1, 0x3C/0x3D)
# - 부팅 스플래시 + NO SIGNAL 표시
# - 컨트롤러 광고 수신(Service Data 0xFFFF: DIR/T/RT/Q)
# - GREEN 남은 시간 OLED 표시
# - 1Hz ACK 송신(지터/버스트)

from micropython import const
from machine import unique_id, I2C, Pin
import bluetooth, ubinascii, utime

# ===== 사용자 설정 =====
SCAN_INT_US    = const(50_000)     # scan interval (μs)
SCAN_WIN_US    = const(50_000)     # scan window  (μs)

ADV_INT_US     = const(100_000)    # ACK 광고 간격(μs) ≈ 100ms
ACK_BURST_MS   = const(600)        # ACK 송신 지속(ms)
JITTER_MAX_MS  = const(250)        # 차량간 지터(ms)

SHOW_ONLY_MINE = True              # 내 방향일 때만 콘솔 표시
ALWAYS_ACK     = True              # 테스트용: Q 없어도 1Hz ACK (운영시 False 권장)

# ===== BLE 초기화 & UID =====
ble = bluetooth.BLE()
ble.active(True)
my_uid6 = ubinascii.hexlify(unique_id()).decode().upper()[-6:]  # 예: 'B3C827'

# 이벤트 상수 호환
try:
    IRQ_SCAN_RESULT = bluetooth.IRQ_SCAN_RESULT
except AttributeError:
    IRQ_SCAN_RESULT = const(5)

# ===== OLED 자동 감지 =====
oled = None
def _try_oled(i2c_id, sda, scl):
    try:
        i2c = I2C(i2c_id, sda=Pin(sda), scl=Pin(scl), freq=400_000)
        devs = i2c.scan()
        # 가장 흔한 주소 0x3C, 그다음 0x3D
        for addr in (0x3C, 0x3D):
            if addr in devs:
                # 지연 임포트(메모리 절약)
                from ssd1306 import SSD1306_I2C
                return SSD1306_I2C(128, 64, i2c, addr=addr)
    except Exception as e:
        pass
    return None

def init_oled():
    # I2C0: SDA=GP0, SCL=GP1  → 가장 흔한 배선
    o = _try_oled(0, 0, 1)
    if o: return o
    # I2C1: SDA=GP2, SCL=GP3  → 다른 배선일 수 있음
    o = _try_oled(1, 2, 3)
    return o

oled = init_oled()

def oled_splash():
    if not oled: return
    oled.fill(0)
    title = "CAR " + my_uid6
    oled.text(title, max(0, (128 - len(title)*8)//2), 8)
    oled.text("BOOT...", 32, 28)
    oled.show()
    utime.sleep_ms(1000)

def oled_no_signal():
    if not oled: return
    oled.fill(0)
    oled.text("NO SIGNAL", 20, 16)
    oled.text("WAITING...", 16, 36)
    oled.show()

def oled_draw(direction, state):
    if not oled: return
    oled.fill(0)
    # 정보 라인
    dirv = state.get("DIR","-") or "-"
    phv  = state.get("PH","-")  or "-"
    oled.text("PH:{} DIR:{}".format(phv, dirv), 0, 0)
    oled.text("STATE:{}".format(state.get("T","-")), 0, 12)

    mine = (dirv == direction)
    is_green = (state.get("T") == "GREEN")
    rt = state.get("RT", 0) if (mine and is_green) else 0

    if mine and is_green:
        oled.text("G-LEFT", 0, 30)
        oled.text("{:02d}s".format(int(rt)), 64, 30)
    else:
        oled.text("WAIT", 44, 30)

    oled.text("Q:{}".format(state.get("Q",0)), 0, 48)
    oled.show()

# ===== 광고 파서 (Service Data 0xFFFF 우선, Name 폴백) =====
def _iter_ad(adv):
    i, L = 0, len(adv)
    while i + 1 < L:
        ln = adv[i]
        if ln == 0: break
        t  = adv[i + 1]
        yield t, adv[i + 2 : i + 1 + ln]
        i += 1 + ln

def parse_controller_adv(adv_data):
    # Service Data (0x16, UUID=0xFFFF)
    try:
        for t, p in _iter_ad(adv_data):
            if t == 0x16 and len(p) >= 2 and p[0] == 0xFF and p[1] == 0xFF:
                s = p[2:].decode()
                parts = {}
                for kv in s.split("|"):
                    if ":" in kv:
                        k, v = kv.split(":", 1); parts[k] = v
                if "DIR" in parts and "T" in parts and "RT" in parts and "Q" in parts:
                    return {
                        "PH": parts.get("PH", ""),
                        "DIR": parts.get("DIR", ""),
                        "T":  parts.get("T", ""),
                        "RT": int(parts.get("RT","0") or 0),
                        "G":  int(parts.get("G","0") or 0),
                        "Q":  int(parts.get("Q","0") or 0),
                    }
    except: pass
    # 폴백: Local Name (0x09)
    try:
        for t, p in _iter_ad(adv_data):
            if t == 0x09:
                s = p.decode()
                parts = {}
                for kv in s.split("|"):
                    if ":" in kv:
                        k, v = kv.split(":", 1); parts[k] = v
                if "DIR" in parts and "T" in parts and "RT" in parts and "Q" in parts:
                    return {
                        "PH": parts.get("PH", ""),
                        "DIR": parts.get("DIR", ""),
                        "T":  parts.get("T", ""),
                        "RT": int(parts.get("RT","0") or 0),
                        "G":  int(parts.get("G","0") or 0),
                        "Q":  int(parts.get("Q","0") or 0),
                    }
    except: pass
    return None

# ===== 상태 =====
state = {"PH":"", "DIR":"", "T":"RED", "RT":0, "G":0, "Q":0, "last_ms":0}

# ===== IRQ 핸들러 =====
def _irq(event, data):
    if event == IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        info = parse_controller_adv(adv_data)
        if info:
            state.update(info)
            state["last_ms"] = utime.ticks_ms()

ble.irq(_irq)

# ===== 유틸/ACK =====
def _jitter_ms_from_uid(uid6):
    h = 0
    for ch in uid6:
        h = (h * 131 + ord(ch)) & 0xFFFF
    return h % JITTER_MAX_MS

def send_ack_burst(direction="N", burst_ms=ACK_BURST_MS):
    payload = "P|D:{}|UID:{}|C:1".format(direction, my_uid6).encode()
    sd = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload
    utime.sleep_ms(_jitter_ms_from_uid(my_uid6))  # 충돌 완화 지터
    ble.gap_scan(None)
    ble.gap_advertise(ADV_INT_US, sd)             # 위치 인자 2개(펌웨어 호환)
    utime.sleep_ms(burst_ms)
    ble.gap_advertise(None)
    ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US)

# ===== 메인 =====
def main(direction="N"):
    # OLED 없을 때도 진행(콘솔만)
    if oled:
        oled_splash()
    else:
        print("[OLED] not detected: try I2C0 GP0/1 or I2C1 GP2/3, addr 0x3C/0x3D")

    # 지속 스캔
    ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US)

    last_ack   = 0
    last_draw  = 0
    last_print = 0
    no_signal_shown = False

    while True:
        now = utime.ticks_ms()

        mine = (state["DIR"] == direction) if state["DIR"] else False
        want_ack = (ALWAYS_ACK or state["Q"] == 1)

        # 1) ACK 1Hz
        if mine and want_ack and utime.ticks_diff(now, last_ack) >= 1000:
            send_ack_burst(direction)
            last_ack = now

        # 2) OLED 0.25s
        if utime.ticks_diff(now, last_draw) >= 250:
            if state["DIR"]:
                oled_draw(direction, state)
                no_signal_shown = False
            else:
                if not no_signal_shown:
                    oled_no_signal()
                    no_signal_shown = True
            last_draw = now

        # 3) 콘솔 0.5s
        if utime.ticks_diff(now, last_print) >= 500:
            if not SHOW_ONLY_MINE or mine:
                print("DIR:{}  T:{:<6} RT:{:>2}  G:{:>2}  Q:{}  UID:{}"
                      .format(state["DIR"] or "-", state["T"], state["RT"], state["G"], state["Q"], my_uid6))
            last_print = now

        utime.sleep_ms(50)

# 스크립트 직접 실행 시
if __name__ == "__main__":
    main("N")   # 필요 시 "E"/"S"/"W"로 변경
