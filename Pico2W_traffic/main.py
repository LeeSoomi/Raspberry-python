# main.py (Pico W / MicroPython) — 안정판
from micropython import const
from machine import Pin, Timer, unique_id
import bluetooth, ubinascii
import utime as time

TEST_FORCE_ACK = True   # 진단용: 비콘 시 ACK(P)도 잠깐 송출
DEBUG_BEACON   = True   # 디버그 비콘 ON

# ===== 설정/튜닝 =====
TIMEOUT_MS    = const(6000)
SCAN_INT_US   = const(50_000)
SCAN_WIN_US   = const(50_000)
RESTART_MS    = const(10_000)

ACK_DELAY_MS  = const(150)
ACK_BURST_MS  = const(1800)
ADV_INT_US    = const(200_000)

BEACON_INT_US     = const(200_000)
BEACON_ON_MS      = const(300)
BEACON_PERIOD_MS  = const(1000)

# BLE IRQ
_IRQ_SCAN_RESULT  = const(5)
_IRQ_SCAN_DONE    = const(6)

# ===== 전역 =====
ble = bluetooth.BLE()
ble.active(True)

led = Pin("LED", Pin.OUT); led.off()

last_seen_ms   = 0
remaining_s    = 0
direction_char = "-"
need_ack       = 0

tick_timer    = Timer(-1)
scan_timer    = Timer(-1)
ack_timer     = Timer(-1)
beacon_timer  = Timer(-1)
beacon_off_t  = Timer(-1)

uid3 = unique_id()[-3:]
uid3_hex = ubinascii.hexlify(uid3).upper()

def _now(): return time.ticks_ms()
def _elapsed(since): return time.ticks_diff(_now(), since)

# ----- 광고 데이터 파서/빌더 -----
def _get_name_any(adv_data: bytes) -> str:
    i = 0; ln = len(adv_data)
    while i + 1 < ln:
        length = adv_data[i]
        if length == 0: break
        atype = adv_data[i+1]
        if atype in (0x09, 0x08):  # Complete/Shortened Local Name
            try:
                return adv_data[i+2 : i+1+length].decode("utf-8")
            except:
                return ""
        i += 1 + length
    return ""

def _parse_name(name: str):
    try:
        p = name.split("|")
        s = int(p[0].split(":")[1])
        d = p[1].split(":")[1]
        q = int(p[2].split(":")[1])
        return s, d, q
    except:
        return None

def _build_sd_payload(raw: bytes) -> bytes:
    # Flags + Service Data(UUID 0xFFFF) + payload
    flags = b"\x02\x01\x06"
    sd = bytes([1 + 2 + len(raw), 0x16]) + b"\xff\xff" + raw
    return flags + sd

# ----- 스캔/광고 전환 -----
def _stop_adv_and_resume_scan(_t=None):
    try:
        ble.gap_advertise(None)
    except:
        pass
    _start_scan()

def _start_scan():
    try:
        ble.gap_scan(RESTART_MS, SCAN_INT_US, SCAN_WIN_US, True)  # active
    except:
        time.sleep_ms(100)
        try:
            ble.gap_scan(RESTART_MS, SCAN_INT_US, SCAN_WIN_US, True)
        except:
            pass

def _scan_watchdog(_t=None):
    try:
        ble.gap_scan(None)
    except:
        pass
    _start_scan()

# ----- ACK 송신: 'P'+uid3+'|'+D -----
def _send_ack(direction: str):
    payload = b'P' + uid3 + b'|' + direction.encode()[:1]
    adv = _build_sd_payload(payload)
    try:
        ble.gap_scan(None)
    except:
        pass
    time.sleep_ms(ACK_DELAY_MS)
    try:
        ble.gap_advertise(ADV_INT_US, adv_data=adv)
        ack_timer.init(mode=Timer.ONE_SHOT, period=ACK_BURST_MS, callback=_stop_adv_and_resume_scan)
    except:
        _start_scan()

# ----- 디버그 비콘: 'C'+uid3 (+옵션 ACK) -----
def _beacon_on(_t=None):
    if not DEBUG_BEACON:
        return
    # 스캔 잠시 중단
    try:
        ble.gap_scan(None)
    except:
        pass
    try:
        # 비콘 광고
        adv_beacon = _build_sd_payload(b'C' + uid3)
        ble.gap_advertise(BEACON_INT_US, adv_data=adv_beacon)

        # 테스트일 때 ACK도 짧게 송출
        if TEST_FORCE_ACK:
            dch = (direction_char or "A")[:1]
            adv_ack = _build_sd_payload(b'P' + uid3 + b'|' + dch.encode())
            time.sleep_ms(50)
            ble.gap_advertise(ADV_INT_US, adv_data=adv_ack)

        # 일정 시간 후 광고 중단 + 스캔 복귀
        beacon_off_t.init(mode=Timer.ONE_SHOT, period=BEACON_ON_MS, callback=_stop_adv_and_resume_scan)

    except:
        _start_scan()

# ----- BLE IRQ -----
def _ble_irq(event, data):
    global last_seen_ms, remaining_s, direction_char, need_ack
    if event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        name = _get_name_any(adv_data)
        if not name:
            return
        parsed = _parse_name(name)
        if not parsed:
            return
        S, D, Q = parsed
        last_seen_ms   = _now()
        remaining_s    = max(0, int(S))
        direction_char = (D or "-")[:1]
        need_ack       = 1 if Q == 1 else 0
        if need_ack:
            _send_ack(direction_char)
    # _IRQ_SCAN_DONE 은 워치독으로 커버

ble.irq(_ble_irq)

# ----- 1Hz 틱 -----
def _tick(_t=None):
    global remaining_s
    if last_seen_ms == 0:
        led.off(); return
    if _elapsed(last_seen_ms) > TIMEOUT_MS:
        led.off(); return
    if remaining_s > 0:
        remaining_s -= 1
    led.on(); time.sleep_ms(100); led.off()

# ===== 초기화 =====
_start_scan()
tick_timer.init(mode=Timer.PERIODIC, period=1000, callback=_tick)
scan_timer.init(mode=Timer.PERIODIC, period=RESTART_MS, callback=_scan_watchdog)
if DEBUG_BEACON:
    beacon_timer.init(mode=Timer.PERIODIC, period=BEACON_PERIOD_MS, callback=_beacon_on)

print("[PicoW] ready. UID3=", uid3_hex.decode(), " DEBUG_BEACON=", DEBUG_BEACON, " TEST_FORCE_ACK=", TEST_FORCE_ACK)
