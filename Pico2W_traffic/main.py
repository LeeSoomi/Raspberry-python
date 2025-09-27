# main.py  (Raspberry Pi Pico W / MicroPython)
# 기능 요약
# - 중앙 라즈베리 광고의 이름/축약이름(0x09/0x08) "S:15|D:A|Q:1" 파싱
# - S(초) 카운트다운을 LED 점멸로 표시
# - Q==1이면 ACK(Service Data 0xFFFF)로 'P'+uid3+'|'+D 송신
# - 타이밍 안정화를 위해 ACK 전 짧은 지연 및 광고 지속시간 연장
# - 디버그 비콘: 1초마다 300ms 동안 'C'+uid3 를 0xFFFF Service Data로 광고(가시성↑)
# - 스캔 워치독/주기적 재시작

from micropython import const
from machine import Pin, Timer, unique_id
import bluetooth
import ubinascii
import utime as time


TEST_FORCE_ACK = True   # 진단용: 비콘 때 P(ACK)도 함께 송출

# ===== 설정/튜닝 =====
# 스캔 동작
TIMEOUT_MS    = const(6000)       # 마지막 수신 후 표시 유지 타임아웃
SCAN_INT_US   = const(50_000)     # 스캔 간격
SCAN_WIN_US   = const(50_000)     # 스캔 윈도우
RESTART_MS    = const(10_000)     # 주기적 스캔 재시작 주기

# ACK(응답) 광고
ACK_DELAY_MS  = const(150)        # 중앙이 광고→스캔 전환할 때까지 기다리기
ACK_BURST_MS  = const(1800)       # ACK 광고 유지시간
ADV_INT_US    = const(200_000)    # ACK 광고 간격(200ms)

# 디버그 비콘(항상 보이게)
DEBUG_BEACON      = True          # 필요 시 False로 끄기
BEACON_INT_US     = const(200_000)  # 비콘 광고 간격(200ms)
BEACON_ON_MS      = const(300)      # 비콘 유지시간(300ms)
BEACON_PERIOD_MS  = const(1000)     # 1초마다 한 번 비콘 ON

# ===== BLE IRQ 코드 =====
_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)
_IRQ_SCAN_RESULT        = const(5)
_IRQ_SCAN_DONE          = const(6)

# ===== 전역 상태 =====
ble = bluetooth.BLE()
ble.active(True)

led = Pin("LED", Pin.OUT); led.off()

last_seen_ms   = 0
remaining_s    = 0
direction_char = "-"
need_ack       = 0

# 타이머들
tick_timer    = Timer(-1)
scan_timer    = Timer(-1)
ack_timer     = Timer(-1)
beacon_timer  = Timer(-1)
beacon_off_t  = Timer(-1)

# 디바이스 ID(하위 3바이트)
_uid = unique_id()
uid3 = _uid[-3:]
uid3_hex = ubinascii.hexlify(uid3).upper()

def _now(): return time.ticks_ms()
def _elapsed(since): return time.ticks_diff(_now(), since)

# ----- ADV 이름/축약이름 파서 (0x09/0x08) -----
def _get_name_any(adv_data: bytes) -> str:
    i = 0
    ln = len(adv_data)
    while i + 1 < ln:
        length = adv_data[i]
        if length == 0:
            break
        atype = adv_data[i+1]
        if atype in (0x09, 0x08):  # Complete Local Name / Shortened Local Name
            name_bytes = adv_data[i+2 : i+1+length]
            try:
                return name_bytes.decode("utf-8")
            except:
                return ""
        i += 1 + length
    return ""

def _parse_name(name: str):
    # 기대 포맷: "S:15|D:A|Q:1"
    try:
        parts = name.split("|")
        s = int(parts[0].split(":")[1])
        d = parts[1].split(":")[1]
        q = int(parts[2].split(":")[1])
        return s, d, q
    except:
        return None

# ----- Service Data(0x16, UUID=0xFFFF) 빌더 -----
def _build_sd_payload(raw: bytes) -> bytes:
    # Flags
    flags = b"\x02\x01\x06"
    # Service Data (len, type=0x16, uuid=0xffff, payload)
    sd = bytes([1 + 2 + len(raw), 0x16]) + b"\xff\xff" + raw
    return flags + sd

def _stop_adv_and_resume_scan(_t=None):
    try:
        ble.gap_advertise(None)
    except:
        pass
    _start_scan()

# ----- ACK 송신: 'P'+uid3+'|'+D -----
def _send_ack(direction: str):
    payload = b'P' + uid3 + b'|' + direction.encode()[:1]
    adv = _build_sd_payload(payload)
    try:
        ble.gap_scan(None)  # 스캔 잠시 중단
    except:
        pass
    # 중앙이 광고→스캔으로 넘어갈 시간을 조금 확보
    time.sleep_ms(ACK_DELAY_MS)
    try:
        ble.gap_advertise(ADV_INT_US, adv_data=adv)
        # 일정 시간 후 광고 중단 + 스캔 재개
        ack_timer.init(mode=Timer.ONE_SHOT, period=ACK_BURST_MS, callback=_stop_adv_and_resume_scan)
    except:
        _start_scan()

# ----- 디버그 비콘: 'C'+uid3 -----
def _beacon_on(_t=None):
    if not DEBUG_BEACON:
        return
    try:
        ble.gap_scan(None)
    except:
        pass
    try:
        adv = _build_sd_payload(b'C' + uid3)
        ble.gap_advertise(BEACON_INT_US, adv_data=adv)
        # BEACON_ON_MS 후 광고 중단 & 스캔 재개
        beacon_off_t.init(mode=Timer.ONE_SHOT, period=BEACON_ON_MS, callback=_stop_adv_and_resume_scan)
    except:
        _start_scan()
    try:
        adv = _build_sd_payload(b'C' + uid3)
        ble.gap_advertise(BEACON_INT_US, adv_data=adv)
        if TEST_FORCE_ACK:
            # 비콘과 함께 ACK도 추가로 짧게 한 번 더 송출
            ack = _build_sd_payload(b'P' + uid3 + b'|' + direction_char.encode()[:1] if direction_char else b'P' + uid3 + b'|A')
            time.sleep_ms(50)
            ble.gap_advertise(ADV_INT_US, adv_data=ack)

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

    elif event == _IRQ_SCAN_DONE:
        # 주기적 재시작 타이머가 있어 별도 처리 불필요
        pass

ble.irq(_ble_irq)

# ----- 스캔 제어 -----
def _start_scan():
    try:
        ble.gap_scan(RESTART_MS, SCAN_INT_US, SCAN_WIN_US, True)  # active scan
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

# ----- 1Hz 틱: LED/카운트다운 -----
def _tick(_t=None):
    global remaining_s
    if last_seen_ms == 0:
        led.off()
        return
    if _elapsed(last_seen_ms) > TIMEOUT_MS:
        led.off()
        return

    if remaining_s > 0:
        remaining_s -= 1

    led.on()
    time.sleep_ms(100)
    led.off()

# ===== 초기화 =====
_start_scan()
tick_timer.init(mode=Timer.PERIODIC, period=1000, callback=_tick)
scan_timer.init(mode=Timer.PERIODIC, period=RESTART_MS, callback=_scan_watchdog)
if DEBUG_BEACON:
    beacon_timer.init(mode=Timer.PERIODIC, period=BEACON_PERIOD_MS, callback=_beacon_on)

print("[PicoW] ready. UID3=", uid3_hex.decode(), " DEBUG_BEACON=", DEBUG_BEACON)

-----------------------------

빠른 확인 절차

Thonny로 main.py 저장 → Ctrl+D로 리부트

스마트폰 nRF Connect에서 스캔 → Service Data 0xFFFF가 주기적으로(C) 보여야 정상

라즈베리에서:

sudo /home/codestudio/bleenv/bin/python /home/codestudio/COS/central_scan.py

→ C UID3=...가 떠야 함 (ACK는 중앙 트리거 쏘면 P로 뜸)
