# 중앙(라즈베리파이, Bleak 사용) — 쓰기(시퀀스+시간) + ACK 수집

# payload에 SEQ와 T 값을 넣어 보낸다.
# notification_handler에서 들어오는 ACK들을 acked에 저장 → 중앙이 몇 대가 응답했는지 확인.

# 1. 시스템 업데이트
# sudo apt update
# sudo apt upgrade -y

# 2. Python 버전 확인
# Bleak는 Python 3.8 이상 권장입니다.
# python3 --version

# 3. Bluetooth(BlueZ) 서비스·종속성 확인/설치 (라즈베리파이/라즈비안인 경우)
# sudo apt install -y bluetooth bluez bluez-tools
# (일반적으로 기본적으로 설치되어 있는 경우가 많음)
# Bluetooth 서비스 시작/확인
# sudo systemctl enable --now bluetooth
# systemctl status bluetooth

# 4. Bleak 설치
# 일반 전역 설치 (권한 필요):
# sudo python3 -m pip install bleak

# 5. 설치 확인
# python3 -c "import bleak; print('bleak ok', bleak.__version__)"

----------------------------------------------------------------

# central_sender_with_time.py (Linux / Raspberry Pi with Bleak)
import asyncio
from bleak import BleakScanner, BleakClient
import time

CMD_CHAR = "12345678-1234-5678-1234-56789abcdef1"
ACK_CHAR = "12345678-1234-5678-1234-56789abcdef2"
TARGET_PREFIX = "CAR-"

acked = {}   # addr -> ack_payload string

def make_notif_handler(addr):
    def handler(sender, data: bytearray):
        s = data.decode(errors='ignore')
        print(f"ACK recv from {addr}: {s}")
        acked[addr] = s
    return handler

async def main():
    devices = await BleakScanner.discover(timeout=3.0)
    targets = [d for d in devices if d.name and d.name.startswith(TARGET_PREFIX)]
    if not targets:
        print("No targets")
        return

    clients = []
    try:
        for d in targets:
            client = BleakClient(d.address)
            await client.connect()
            print("Connected:", d.address, d.name)
            await client.start_notify(ACK_CHAR, make_notif_handler(d.address))
            clients.append((client, d.address))

        # 보낼 데이터 준비
        seq = 123
        remain_sec = 30
        payload = f"SEQ:{seq};T:{remain_sec}".encode()
        print("Writing payload:", payload)
        # 모두에게 쓰기
        for client, addr in clients:
            try:
                await client.write_gatt_char(CMD_CHAR, payload, response=True)
                print("Wrote to", addr)
            except Exception as e:
                print("Write failed", addr, e)

        # ACK 기다리기 (타임아웃)
        await asyncio.sleep(2.0)

        print("ACKed:", acked)
        print("ACK count:", len(acked))

    finally:
        for client, addr in clients:
            try:
                await client.stop_notify(ACK_CHAR)
            except:
                pass
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
