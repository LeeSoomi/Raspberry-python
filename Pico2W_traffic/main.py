# main.py (Pico 2 W, MicroPython v1.26.x)
from bluetooth import BLE
from machine import Pin, unique_id
import time

TIMEOUT_MS = 3000
SCAN_WIN_US = 30000
SCAN_INT_US = 30000
ACK_UUID16 = 0xFFFF
ACK_INTERVAL_S = 1
ACK_ADV_US = 250_000
ACK_DUR_S = 0.35

ble = BLE(); ble.active(True)
LED = Pin("LED", Pin.OUT)

remain = None
last_rx_ms = time.ticks_ms()
last_tick = time.ticks_ms()
last_ack_s = -1
uid3 = unique_id()[-3:]
cur_dir = b'?'

def led_blink(on_ms=60, off_ms=0):
    LED.on(); time.sleep_ms(on_ms); LED.off()
    if off_ms: time.sleep_ms(off_ms)

def parse_fields(b: bytes):
    i = 0; out = {}; ln = len(b)
    while i < ln:
        L = b[i]
        if L == 0 or i + L >= ln: break
        t = b[i+1]; v = b[i+2:i+1+L]
        out.setdefault(t, []).append(v)
        i += 1 + L
    return out

def parse_center_adv(adv: bytes):
    s = None; d = None; q = 0
    f = parse_fields(adv)
    if 0x09 in f:
        for v in f[0x09]:
            try:
                txt = v.decode()
                for p in txt.split('|'):
                    if p.startswith("S:"):
                        k = ''.join(ch for ch in p[2:] if ch.isdigit())
                        if k: s = max(0, min(99, int(k)))
                    elif p.startswith("D:") and len(p) >= 3:
                        d = p[2:3].encode()
                    elif p.startswith("Q:"):
                        q = 1 if p.endswith("1") else 0
            except: pass
    return s, d, q

def adv_payload_service_data(uuid16, data: bytes):
    p = bytearray()
    p += b"\x02\x01\x06"
    p += bytes((len(data)+3, 0x16, uuid16 & 0xFF, (uuid16>>8)&0xFF))
    p += data
    return bytes(p)

def send_ack_once(direction: bytes):
    data = b'P' + uid3 + (direction[:1] if direction else b'?')
    payload = adv_payload_service_data(ACK_UUID16, data)
    try:
        ble.gap_advertise(ACK_ADV_US, payload)
        time.sleep(ACK_DUR_S)
    except: pass
    finally:
        try: ble.gap_advertise(None)
        except: pass

def bt_irq(event, data):
    global remain, last_rx_ms, cur_dir, last_ack_s
    if event == 5:  # _IRQ_SCAN_RESULT
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

ble.irq(bt_irq)
try:
    ble.gap_scan(0, SCAN_WIN_US, SCAN_INT_US)
except:
    try: ble.gap_scan(0xFFFFFFFF, SCAN_WIN_US, SCAN_INT_US)
    except: pass

for _ in range(2): led_blink(200, 300)

while True:
    now = time.ticks_ms()
    age = time.ticks_diff(now, last_rx_ms)
    if remain is not None and age < TIMEOUT_MS:
        if time.ticks_diff(now, last_tick) >= 1000:
            last_tick = now
            if remain > 0: remain -= 1
            led_blink(60)
            ns = time.time()
            if ns != last_ack_s:
                last_ack_s = ns
                send_ack_once(cur_dir)
        else:
            time.sleep_ms(50)
    else:
        remain = None
        led_blink(60, 440)
