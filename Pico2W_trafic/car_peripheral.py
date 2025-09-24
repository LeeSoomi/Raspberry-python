# 저장해서 차량의 MicroPython에 올려 실행하세요. 
# 각 차량은 고유 ID를 갖도록 CAR_ID 설정
# 차량은 CMD(write)를 받으면 send_ack로 ACK notify를 보냅니다. 
# Notify payload는 b"CAR01:123" 형태입니다.


# car_peripheral.py  (MicroPython on Pico W)
# CAR_ID를 각 차량별로 다르게 설정하세요.

import bluetooth
import time
from micropython import const

# UUIDs (예시: 바꿔도 됨)
SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
CMD_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")   # write
ACK_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")   # notify

CAR_ID = b"CAR01"   # 각 차량마다 변경

ble = bluetooth.BLE()
ble.active(True)

# GATT 서비스: ( (char_uuid, flags), ... )
CMD_CHAR = (CMD_CHAR_UUID, bluetooth.FLAG_WRITE)
ACK_CHAR = (ACK_CHAR_UUID, bluetooth.FLAG_NOTIFY)
SERVICE = (SERVICE_UUID, (CMD_CHAR, ACK_CHAR))

handles = ble.gatts_register_services((SERVICE,))
# handles => tuple of services; get characteristic handles:
srv_handles = handles[0]            # 첫번째 서비스
cmd_handle = srv_handles[0]         # characteristic value handle for CMD
ack_handle = srv_handles[1]         # characteristic value handle for ACK

conn_handle = None

def bt_irq(event, data):
    global conn_handle
    if event == 1:  # _IRQ_CENTRAL_CONNECT
        conn_handle, addr_type, addr = data
        print("Connected, conn_handle:", conn_handle)
    elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
        conn_handle = None
        print("Disconnected")
        # 계속 광고 재시작
        advertise()
    elif event == 3:  # _IRQ_GATTS_WRITE
        conn, value_handle = data
        if value_handle == cmd_handle:
            val = ble.gatts_read(cmd_handle)
            print("CMD write received:", val)
            # val은 bytes(예: b'123'), 차량 동작 수행 후 ACK 보냄
            send_ack(val)

def send_ack(seq_bytes):
    # ACK payload: CAR_ID + b':' + seq_bytes
    if conn_handle is None:
        print("No connection, cannot ACK")
        return
    payload = CAR_ID + b':' + seq_bytes
    try:
        ble.gatts_notify(conn_handle, ack_handle, payload)
        print("Notified ACK:", payload)
    except Exception as e:
        print("notify failed:", e)

def advertise():
    # 간단히 이름 포함 광고
    name = b"CAR-" + CAR_ID
    adv_payload = bytearray()
    # Flags
    adv_payload += bytes((2, 0x01, 0x06))
    # Complete Local Name
    adv_payload += bytes((len(name)+1, 0x09)) + name
    # Service UUID (128-bit) omitted in adv for brevity — scanning by name ok
    ble.gap_advertise(300_000, adv_payload)  # 300 ms 간격
    print("Advertising as", name)

ble.irq(bt_irq)
advertise()

# keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ble.gap_advertise(None)
    ble.active(False)
    print("Stopped")
