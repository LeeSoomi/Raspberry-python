# main.py  (Raspberry Pi Pico W / MicroPython v1.26.x)
# - 센터(라즈베리)가 Complete Local Name(0x09)로 "S:15|D:A|Q:1" 형식 광고를 내보낸다고 가정
# - 남은 시간(S)을 수신해 1초마다 LED 깜빡이며 카운트다운
# - Q=1이면 초당 1회 ACK를 0xFFFF Service Data로 송신 (P + uid3 + direction)
# - 스캔이 오래가다 멈추는 경우를 대비해 10초마다 스캔 재시작

from bluetooth import BLE
from machine import Pin, unique_id
import time

# ===== 튜닝 파라미터 =====
TIMEOUT_MS   = 6000          # 수신 끊긴 후 유지 시간(표시 타임아웃)
SCAN_WIN_US  = 50_000        # 스캔 윈도우
SCAN_INT_US  = 50_000        # 스캔 인터벌
ACK_UUID16   = 0xFFFF        # ACK Service Data UUID
ACK_ADV_US   = 200_000       # ACK 광고 간격(us)
ACK_DUR_S    = 0.6           # ACK 송신 지속(초) → 이 동안 여러 프레임 송출
SCAN_KICK_MS = 10_000        # 스캔 재시작 주기(안전장치)

# ===== 초기화 =====
ble = BLE()
ble.active(True)
LED = Pin("LED", Pin.OUT)
BEACON_PERIOD_S = 2
last_beacon_s = 0

remain = None          # 남은 초 (수신 시 갱신)
last_rx_ms = time.ticks_ms()
last_tick  = time.ticks_ms()
last_ack_s = -1        # 마지막 ACK를 보낸 "초" (중복 방지)
uid3  = unique_id()[-3:]  # 장치 식별 3바이트
cur_dir = b'?'         # 현재 수신한 방향 한 글자
scan_kick_ms = time.ticks_ms()

# ===== 유틸 =====
def led_blink(on_ms=60, off_ms=0):
    LED.on();  time.sleep_ms(on_ms)
    LED.off()
    if off_ms: time.sleep_ms(off_ms)

def parse_fields(b: bytes):
    """AD 구조 파싱: {type: [values...]}"""
    i = 0; out = {}; ln = len(b)
    while i < ln:
        L = b[i]
        if L == 0 or i + L >= ln:
            break
        t = b[i+1]
        v = b[i+2:i+1+L]
        out.setdefault(t, []).append(v)
        i += 1 + L
    return out

def parse_center_adv(adv: bytes):
    """0x09(Local Name)에서 'S:..|D:..|Q:..' 추출"""
    s = None; d = None; q = 0
    f = parse_fields(adv)
    if 0x09 in f:
        for v in f[0x09]:
            try:
                txt = v.decode()
                for p in txt.split('|'):
                    if p.startswith("S:"):
                        digits = ''.join(ch for ch in p[2:] if ch.isdigit())
                        if digits:
                            s = max(0, min(99, int(digits)))
                    elif p.startswith("D:") and len(p) >= 3:
                        d = p[2:3].encode()
                    elif p.startswith("Q:"):
                        q = 1 if p.endswith("1") else 0
            except:
                pass
    return s, d, q

def adv_payload_service_data(uuid16, data: bytes):
    """0x16(Service Data) 페이로드 구성 + 플래그(0x01,0x06)"""
    p = bytearray()
    p += b"\x02\x01\x06"
    p += bytes((len(data)+3, 0x16, uuid16 & 0xFF, (uuid16>>8) & 0xFF))
    p += data
    return bytes(p)

def send_ack_once(direction: bytes):
    """ACK 한 번 송신 (실제로는 ACK_DUR_S 동안 여러 프레임 송출)"""
    data = b'P' + uid3 + (direction[:1] if direction else b'?')
    payload = adv_payload_service_data(ACK_UUID16, data)
    try:
        ble.gap_advertise(ACK_ADV_US, payload)
        time.sleep(ACK_DUR_S)
    except:
        pass
    finally:
        try:
            ble.gap_advertise(None)
        except:
            pass

# ===== IRQ =====
def bt_irq(event, data):
    global remain, last_rx_ms, cur_dir, last_ack_s
    # _IRQ_SCAN_RESULT = 5 (MicroPython BLE 이벤트 값)
    if event == 5:
        _addr_type, _addr, _adv_type, _rssi, adv_data = data
        s, d, q = parse_center_adv(bytes(adv_data))
        if s is not None:
            remain = s
            if d: cur_dir = d
            last_rx_ms = time.ticks_ms()
            if q == 1:
                now_s = time.time()
                if now_s != last_ack_s:
                    last_ack_s = now_s
                    send_ack_once(cur_dir)

# ===== 스캔 시작 =====
ble.irq(bt_irq)
def start_scan():
    try:
        ble.gap_scan(0, SCAN_WIN_US, SCAN_INT_US)            # 무한 스캔
    except:
        try:
            ble.gap_scan(0xFFFFFFFF, SCAN_WIN_US, SCAN_INT_US)  # 보정
        except:
            pass

start_scan()

# 부팅 확인 깜빡
for _ in range(2):
    led_blink(200, 300)

# ===== 메인 루프 =====
while True:
    now = time.ticks_ms()

    # (안전장치) 주기적으로 스캔 재시작
    if time.ticks_diff(now, scan_kick_ms) > SCAN_KICK_MS:
        scan_kick_ms = now
        try: ble.gap_scan(None)
        except: pass
        start_scan()

    age = time.ticks_diff(now, last_rx_ms)

    if remain is not None and age < TIMEOUT_MS:
        # 1초당 1 감소 + ACK(초당 1회)
        if time.ticks_diff(now, last_tick) >= 1000:
            last_tick = now
            if remain > 0:
                remain -= 1
            led_blink(60)
            ns = time.time()
            if ns != last_ack_s:
                last_ack_s = ns
                send_ack_once(cur_dir)
        else:
            time.sleep_ms(50)
    else:
        # 수신 끊김 표시: 느린 깜빡이
        remain = None
        led_blink(60, 440)
        # 대기 비콘: BEACON_PERIOD_S 주기로 한 번 ACK 송출
        ns = time.time()
        if ns - last_beacon_s >= BEACON_PERIOD_S:
            last_beacon_s = ns
            # 마지막 방향 정보가 없으면 '?' 전송
            send_ack_once(cur_dir)
