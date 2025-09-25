# scan_test.py
import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning 5s...")
    devices = await BleakScanner.discover(timeout=5.0)
    if not devices:
        print("No devices found")
    for d in devices:
        name = d.name or "(no name)"
        print(d.address, name, "rssi", d.rssi)
        # 광고 데이터 자세히 보고 싶으면 advertisement_data 접근 (Bleak v0.20+)
        # print(d.metadata)

if __name__ == "__main__":
    asyncio.run(main())
