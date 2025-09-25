# continuous_scan_count.py
import asyncio
from bleak import BleakScanner

seen = set()

def detection_callback(device, advertisement_data):
    # 이름이나 service_data, manufacturer 등으로 필터 가능
    # 예: device.name startswith("CAR-") 또는 특정 service UUID 포함 여부
    name = device.name or ""
    if name.startswith("CAR-") or b"S:123" in (advertisement_data.local_name or "").encode():
        if device.address not in seen:
            seen.add(device.address)
            print("NEW car:", device.address, name, "total:", len(seen))

async def main(duration=30):
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    print("Started scanning...")
    await asyncio.sleep(duration)
    await scanner.stop()
    print("Stopped. Total cars seen:", len(seen))

if __name__ == "__main__":
    asyncio.run(main(30))
