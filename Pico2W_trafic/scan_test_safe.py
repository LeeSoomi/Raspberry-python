# /home/pi/scan_test_safe.py
import asyncio
from bleak import BleakScanner

async def main():
    print("Safe scanning 5s...")
    try:
        # class method: discover(…) -> returns list of devices
        devices = await BleakScanner.discover(timeout=5.0)
    except Exception as e:
        print("Scan error:", e)
        return

    if not devices:
        print("No devices found")
        return

    for d in devices:
        # d.address, d.name, d.rssi 는 대부분의 플랫폼에서 있음
        print(d.address, d.name, "rssi", getattr(d, "rssi", None))

if __name__ == "__main__":
    asyncio.run(main())
