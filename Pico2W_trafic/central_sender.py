# 라즈베리파이는 Bleak(Python BLE client 라이브러리)를 사용해서 다음 동작을 합니다:
# 스캔 → 차량 장치들 찾기(예: advertising name prefix CAR-)
# 각 차량에 연결 → ACK notify 구독(콜백 등록)
# 모든 연결된 장치에 대해 CMD 쓰기(시퀀스 bytes)
# 특정 시간(타임아웃) 동안 ACK 콜백 카운트 → 받은 ACK 목록을 리포트

# 코드 안의  main()은 스캔 → 발견된 모든 CAR- 장치에 연결 → notify 구독 → CMD에 시퀀스 쓰고 2초 기다려 ACK 수집 → 종료합니다.
# 여러 차량이 있으면 병렬로 연결/통신이 가능하나, 환경에 따라 동시 연결 개수/성능을 조정해야 합니다.


# ****  먼저 Bleak 설치:
# pip install bleak

# central_sender.py  (on Raspberry Pi)
import asyncio
from bleak import BleakScanner, BleakClient

# UUIDs must match vehicle code
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CMD_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
ACK_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"

TARGET_PREFIX = "CAR-"   # advertising name prefix

acked = {}   # device_addr -> ack_payload

def notification_handler(device_addr):
    def _handler(sender: int, data: bytearray):
        # data is bytes like b"CAR01:123"
        s = data.decode()
        print(f"ACK from {device_addr}: {s}")
        acked[device_addr] = s
    return _handler

async def main():
    print("Scanning for vehicles...")
    devices = await BleakScanner.discover(timeout=3.0)
    targets = [d for d in devices if d.name and d.name.startswith(TARGET_PREFIX)]
    if not targets:
        print("No vehicles found.")
        return

    print("Found targets:", [ (d.address, d.name) for d in targets ])

    clients = []
    try:
        # connect to all targets (could limit number)
        for d in targets:
            client = BleakClient(d.address)
            await client.connect()
            print("Connected to", d.address)
            # subscribe to ACK notify
            await client.start_notify(ACK_CHAR_UUID, notification_handler(d.address))
            clients.append((client, d.address))

        # send sequence to all connected vehicles
        seq = 123  # 예시
        seq_bytes = str(seq).encode()
        print("Writing seq", seq)
        for client, addr in clients:
            try:
                await client.write_gatt_char(CMD_CHAR_UUID, seq_bytes, response=True)
                print("Wrote to", addr)
            except Exception as e:
                print("Write failed for", addr, e)

        # wait for ACKs with timeout (예: 2초)
        await asyncio.sleep(2.0)

        # 결과 출력
        print("ACKed devices:", acked)
        print("ACK count:", len(acked))

    finally:
        # clean up
        for client, addr in clients:
            try:
                await client.stop_notify(ACK_CHAR_UUID)
            except:
                pass
            await client.disconnect()
        print("Done")

if __name__ == "__main__":
    asyncio.run(main())
