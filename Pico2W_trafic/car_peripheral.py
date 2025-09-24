# 차량(Peripheral, MicroPython) — 수신 + 파싱 + ACK

# 저장해서 차량의 MicroPython에 올려 실행
# 각 차량은 고유 ID를 갖도록 CAR_ID 설정

# parse_cmd에서 "SEQ:123;T:30" 처럼 오면 seq와 remain을 얻는다
# 수신 즉시 send_ack로 중앙에 notify(ACK) 보냄. ACK payload는 b"CAR01:123" 형식.


# CAR_ID를 각 차량별로 다르게 설정
# car_peripheral_with_time.py  (MicroPython on Pico W)

import bluetooth, time
from micropython import const

SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
CMD_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")   # write
ACK_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef2")   # notify

CAR_ID = b"CAR01"   # 차량별 고유값

ble = bluetooth.BLE()
ble.active(True)

CMD_CHAR = (CMD_CHAR_UUID, bluetooth.FLAG_WRITE)
ACK_CHAR = (ACK_CHAR_UUID, bluetooth.FLAG_NOTIFY)
SERVICE = (SERVICE_UUID, (CMD_CHAR, ACK_CHAR))

handles = ble.gatts_register_services((SERVICE,))
srv_handles = handles[0]
cmd_handle = srv_handles[0]
ack_handle = srv_handles[1]

conn_handle = None

def parse_cmd(val_bytes):
    try:
        s = val_bytes.decode()
        # 포맷: "SEQ:123;T:30"
        parts = s.split(';')
        seq = None
        remain = None
        for p in parts:
            if p.startswith("SEQ:"):
                seq = p.split(":",1)[1]
            if p.startswith("T:"):
                remain = p.split(":",1)[1]
        return seq, remain
    except Exception as e:
        print("parse err", e)
        return None, None

def send_ack(seq_bytes):
    if conn_handle is None:
        print("No conn -> cannot ack")
        return
    payload = CAR_ID + b':' + seq_bytes  # e.g. b"CAR01:123"
    try:
        ble.gatts_notify(conn_handle, ack_handle, payload)
        print("ACK notify:", payload)
    except Exception as e:
        print("notify failed:", e)

def bt_irq(event, data):
    global conn_handle
    if event == 1:  # central connected
        conn_handle, addr_type, addr = data
        print("Connected", conn_handle)
    elif event == 2: # central disconnected
        conn_handle = None
        print("Disconnected -> advertising restart")
        advertise()
    elif event == 3: # write to GATT
        conn, value_handle = data
        if value_handle == cmd_handle:
            val = ble.gatts_read(cmd_handle)
            seq, remain = parse_cmd(val)
            print("CMD recv:", val, "-> seq:", seq, "remain:", remain)
            # 차량이 남은 시간으로 동작을 시작/표시하면 됨.
            # (예: 표준 출력/LED 등)
            send_ack(seq.encode() if seq else b'')
    # (다른 이벤트 생략)

ble.irq(bt_irq)

def advertise():
    name = b"CAR-" + CAR_ID
    adv = bytearray()
    adv += bytes((2, 0x01, 0x06))
    adv += bytes((len(name)+1, 0x09)) + name
    ble.gap_advertise(300_000, adv)
    print("Advertising as", name)

advertise()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ble.gap_advertise(None)
    ble.active(False)
    print("Stopped")
