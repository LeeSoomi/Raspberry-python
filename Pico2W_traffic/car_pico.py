# car_pico.py (MicroPython)
from micropython import const
from machine import Pin, unique_id
import bluetooth, ubinascii, utime

SCAN_INT_US = const(50_000)
SCAN_WIN_US = const(50_000)
ACK_SERVICE_UUID = bluetooth.UUID(0xFFFF)

ble = bluetooth.BLE(); ble.active(True)
my_uid = ubinascii.hexlify(unique_id())[:6].decode().upper()

# 간단한 광고 파서 (Complete Local Name만 사용)
def parse_adv_name(adv_data):
    i = 0
    while i + 1 < len(adv_data):
        length = adv_data[i]
        if length == 0: break
        t = adv_data[i+1]
        if t == 0x09:  # Complete Local Name
            try:
                return adv_data[i+2:i+1+length].decode()
            except: return None
        i += 1 + length
    return None

state = {"T":"RED", "RT":0, "PH":"NS", "G":5, "Q":0, "last_ts":0}

def on_scan(addr_type, addr, adv_type, rssi, adv_data):
    name = parse_adv_name(adv_data)
    if not name: return
    # 기대 형식: "PH:NS|T:GREEN|RT:12|G:7|Q:1"
    try:
        parts = dict(p.split(":") for p in name.split("|"))
        state["PH"] = parts.get("PH", state["PH"])
        state["T"]  = parts.get("T", state["T"])
        state["RT"] = int(parts.get("RT", state["RT"]))
        state["G"]  = int(parts.get("G", state["G"]))
        state["Q"]  = int(parts.get("Q", state["Q"]))
        state["last_ts"] = utime.ticks_ms()
    except Exception as e:
        pass

def send_ack(direction="N"):
    # Service Data 0xFFFF: b"P|D:N|UID:ABC123|C:1"
    payload = "P|D:{}|UID:{}|C:1".format(direction, my_uid).encode()
    sd = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload
    # 비컨식 확대로 간단 송신(연속 광고), 실제 환경에서는 GATT로도 가능
    ble.gap_advertise(100, adv_data=sd)

def main(direction="N"):
    ble.gap_scan(0, SCAN_WIN_US, SCAN_INT_US)
    ble.irq(handler=lambda e, d: on_scan(*d) if e==bluetooth.IRQ_SCAN_RESULT else None)

    last_ack = 0
    while True:
        # 콘솔 표시(대신 NeoPixel/LED로 매핑 가능)
        print("T={} RT={} PH={} G={} Q={}".format(state["T"], state["RT"], state["PH"], state["G"], state["Q"]))
        # ACK 요청 시 1Hz 송신
        now = utime.ticks_ms()
        if state["Q"] and utime.ticks_diff(now, last_ack) >= 1000:
            send_ack(direction)
            last_ack = now
        utime.sleep_ms(500)

main("N")  # 차량이 향하는 기본 방향(필요 시 변경)
