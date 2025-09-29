# car_pico.py
from micropython import const
from machine import unique_id
import bluetooth, ubinascii, utime

# ===== 설정 =====
SCAN_INT_US    = const(50_000)     # scan interval (μs)
SCAN_WIN_US    = const(50_000)     # scan window  (μs)

ADV_INT_US     = const(100_000)    # ACK 광고 간격(μs) ≈ 100ms
ACK_BURST_MS   = const(600)        # ACK 송신 지속(ms)
JITTER_MAX_MS  = const(250)        # 각 차량 지터(ms)

SHOW_ONLY_MINE = True              # 내 방향일 때만 출력
ALWAYS_ACK     = True              # 테스트용: Q 없어도 1Hz로 ACK (운영 시 False)

# ===== BLE 초기화 & UID =====
ble = bluetooth.BLE()
ble.active(True)
my_uid6 = ubinascii.hexlify(unique_id()).decode().upper()[-6:]  # 예: 'B3C827'

# ===== 이벤트 상수 호환(펌웨어별 차이 보정) =====
try:
    IRQ_SCAN_RESULT = bluetooth.IRQ_SCAN_RESULT
except AttributeError:
    IRQ_SCAN_RESULT = const(5)   # 표준 값

# ===== 광고 파서 (Service Data 0xFFFF 우선, Local Name 폴백) =====
def _iter_ad(adv):
    i, L = 0, len(adv)
    while i + 1 < L:
        ln = adv[i]
        if ln == 0: break
        t = adv[i + 1]
        yield t, adv[i + 2 : i + 1 + ln]
        i += 1 + ln

def parse_controller_adv(adv_data):
    # Service Data(0x16, UUID 0xFFFF)
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
                        "RT": int(parts.get("RT", "0") or 0),
                        "G":  int(parts.get("G", "0") or 0),
                        "Q":  int(parts.get("Q", "0") or 0),
                    }
    except: pass
    # Local Name(0x09) 폴백
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
                        "RT": int(parts.get("RT", "0") or 0),
                        "G":  int(parts.get("G", "0") or 0),
                        "Q":  int(parts.get("Q", "0") or 0),
                    }
    except: pass
    return None

# ===== 상태 =====
state = {"PH":"", "DIR":"", "T":"RED", "RT":0, "G":0, "Q":0, "last_ms":0}

# ===== IRQ =====
def _irq(event, data):
    if event == IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        info = parse_controller_adv(adv_data)
        if info:
            state.update(info)
            state["last_ms"] = utime.ticks_ms()

ble.irq(_irq)

# ===== 유틸 =====
def _jitter_ms_from_uid(uid6):
    h = 0
    for ch in uid6:
        h = (h * 131 + ord(ch)) & 0xFFFF
    return h % JITTER_MAX_MS

# ===== ACK 송신 =====
def send_ack_burst(direction="N", burst_ms=ACK_BURST_MS):
    # 0xFFFF Service Data + ASCII payload
    payload = "P|D:{}|UID:{}|C:1".format(direction, my_uid6).encode()
    adv_sd  = bytes([len(payload) + 3, 0x16, 0xFF, 0xFF]) + payload

    # 지터로 동시 충돌 완화
    utime.sleep_ms(_jitter_ms_from_uid(my_uid6))

    # 스캔 중지 → 광고 시작(★ 이 펌웨어는 위치 인자 2개만 허용)
    ble.gap_scan(None)
    ble.gap_advertise(ADV_INT_US, adv_sd)   # ← 두 인자만!
    utime.sleep_ms(burst_ms)
    ble.gap_advertise(None)

    # 스캔 재개 (duration_ms, interval_us, window_us)
    ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US)

# ===== 메인 =====
def main(direction="N"):
    # 지속 스캔 시작
    ble.gap_scan(0, SCAN_INT_US, SCAN_WIN_US)

    last_ack = 0
    last_print = 0

    while True:
        now = utime.ticks_ms()
        mine = (state["DIR"] == direction) if state["DIR"] else True
        want_ack = (ALWAYS_ACK or state["Q"] == 1)

        # 1Hz ACK
        if mine and want_ack and utime.ticks_diff(now, last_ack) >= 1000:
            send_ack_burst(direction)
            last_ack = now

        # 콘솔 표시(0.5s)
        if utime.ticks_diff(now, last_print) >= 500:
            if not SHOW_ONLY_MINE or mine:
                print("DIR:{}  T:{:<6} RT:{:>2}  G:{:>2}  Q:{}  UID:{}"
                      .format(state["DIR"] or "-", state["T"], state["RT"], state["G"], state["Q"], my_uid6))
             draw_oled(direction)   # ★ OLED 갱신 추가
            last_print = now

        utime.sleep_ms(50)

# 부팅 자동 실행 시:
# import car_pico; car_pico.main("N")
