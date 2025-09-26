# 라즈베리파이 에서 가상환경 활성화 후 실행: source bleenv/bin/activate && python3 central_push_and_count.py

# central_push_and_count.py — Raspberry Pi (Bleak)
import asyncio
import struct
from bleak import BleakScanner, BleakClient

TARGET_PREFIX = "CAR-"   # 이 이름으로 시작하는 주변 장치들을 대상
SVC_UUID  = "00001234-0000-1000-8000-00805f9b34fb"
RX_UUID   = "0000abcd-0000-1000-8000-00805f9b34fb"  # write target
TX_UUID   = "0000beef-0000-1000-8000-00805f9b34fb"  # notify source

# 각 장치별로 마지막 SEQ의 ACK를 받았는지 추적
class CarConn:
    def __init__(self, dev):
        self.dev = dev
        self.client: BleakClient | None = None
        self.last_ack_seq = -1

    async def connect(self):
        self.client = BleakClient(self.dev)
        await self.client.connect()
        await self.client.start_notify(TX_UUID, self._on_notify)

    async def disconnect(self):
        try:
            if self.client:
                await self.client.stop_notify(TX_UUID)
                await self.client.disconnect()
        except Exception:
            pass

    def _on_notify(self, _handle, data: bytearray):
        # 차량이 struct("<HH", seq, secs) 로 ACK 보냄
        if len(data) >= 4:
            seq, secs = struct.unpack("<HH", data[:4])
            # print(f"[ACK] {self.dev.name} {self.dev.address} seq={seq} secs={secs}")
            self.last_ack_seq = seq

    async def push_count(self, seq: int, secs: int) -> bool:
        """seq/secs 쓰고, 짧은 타임아웃 안에 해당 seq ACK를 받으면 True"""
        if not (self.client and self.client.is_connected):
            return False
        self.last_ack_seq = -1
        payload = struct.pack("<HH", seq, secs)
        try:
            await self.client.write_gatt_char(RX_UUID, payload, response=True)
        except Exception as e:
            print(f"write fail {self.dev.name}: {e}")
            return False
        # 최대 0.8초 대기(환경에 따라 조정)
        for _ in range(8):
            await asyncio.sleep(0.1)
            if self.last_ack_seq == seq:
                return True
        return False

async def discover_targets(timeout=5.0):
    devs = await BleakScanner.discover(timeout=timeout)
    targets = [d for d in devs if (d.name or "").startswith(TARGET_PREFIX)]
    return targets

async def main():
    print("Scanning targets…")
    targets = await discover_targets(5.0)
    if not targets:
        print("No targets")
        return
    print(f"Found {len(targets)} car(s):")
    for d in targets:
        print(" -", d.name, d.address)

    # 연결(순차 연결 예시 — 동시 연결도 가능하나 안정화 후 권장)
    cars: list[CarConn] = []
    try:
        for d in targets:
            c = CarConn(d)
            print(f"Connecting to {d.name}…")
            await c.connect()
            cars.append(c)
        print("All connected.")

        # 카운트다운: 20 → 0
        seq = 0
        for secs in range(20, -1, -1):
            seq += 1
            print(f"\n[SEQ {seq}] push secs={secs}")
            ack_count = 0
            # 모든 차량에 같은 값 전송 후 ACK 집계
            for c in cars:
                ok = await c.push_count(seq, secs)
                if ok:
                    ack_count += 1
            print(f"ACK {ack_count}/{len(cars)} received")

            # 1초 주기
            await asyncio.sleep(1.0)

    finally:
        print("Disconnecting…")
        for c in cars:
            await c.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
