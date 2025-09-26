# car_gatt_receiver.py — Pico W / MicroPython v1.26.x
from bluetooth import BLE, UUID
import struct, time

ble = BLE(); ble.active(True)

NAME = "CAR-CAR01"   # 차량별로 CAR-CAR02, CAR-CAR03 등으로 바꿔주세요

# 16-bit 커스텀 UUID (Central에서는 128-bit로 접근)
SVC_UUID  = UUID(0x1234)
RX_UUID   = UUID(0xABCD)   # 중앙 → 차량 (write로 남은 시간/seq 전달)
TX_UUID   = UUID(0xBEEF)   # 차량 → 중앙 (notify로 ACK 반환)

# GATT 권한 플래그
FLAG_READ   = 0x0002
FLAG_WRITE  = 0x0008
FLAG_NOTIFY = 0x0010

conn_handle = None
rx_handle = None
tx_handle = None

# 마지막으로 받은 값(디버그 표시용)
last_seq = -1
last_secs = -1

def start_adv():
    name = NAME.encode()
    adv = bytearray()
    adv += bytes((2, 0x01, 0x06))                 # Flags
    adv += bytes((len(name)+1, 0x09)) + name      # Complete Local Name
    # connectable advertising (interval 300ms)
    ble.gap_advertise(300_000, adv)
    print("Advertising(connectable):", NAME)

def irq(event, data):
    global conn_handle, last_seq, last_secs
    if event == 1:  # _IRQ_CENTRAL_CONNECT
        conn_handle, _, _ = data
        print("Central connected:", conn_handle)

    elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
        print("Central disconnected")
        conn_handle = None
        start_adv()

    elif event == 3:  # _IRQ_GATTS_WRITE
        # 중앙이 RX 특성에 write할 때 호출
        handle = data[0]
        if handle == rx_handle:
            raw = ble.gatts_read(rx_handle)
            # 중앙에서 struct.pack("<HH", seq, seconds) 전송
            if len(raw) >= 4:
                seq, secs = struct.unpack("<HH", raw[:4])
                last_seq, last_secs = seq, secs
                # 여기서 수신 숫자를 표시: 예) 프린트/7세그/LED 등
                print("RECV → SEQ:", seq, "SECS:", secs)
                # 즉시 ACK notify (같은 형식으로 응답)
                if conn_handle is not None:
                    ble.gatts_write(tx_handle, struct.pack("<HH", seq, secs))
                    try:
                        ble.gatts_notify(conn_handle, tx_handle)
                    except Exception as e:
                        print("notify err:", e)

# GATT 테이블 생성: RX(write), TX(notify)
rx_char = (RX_UUID, FLAG_READ | FLAG_WRITE)
tx_char = (TX_UUID, FLAG_READ | FLAG_NOTIFY)
svc = (SVC_UUID, (rx_char, tx_char))
((rx_handle, tx_handle),) = ble.gatts_register_services((svc,))
ble.irq(irq)
start_adv()

try:
    while True:
        # 필요시 last_secs를 사용해 별도 로직 수행(예: 1초마다 화면 갱신 등)
        time.sleep(1)
except KeyboardInterrupt:
    ble.gap_advertise(None)
    ble.active(False)
    print("Stopped.")
