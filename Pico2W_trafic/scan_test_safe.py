# scan_test_safe.py
import asyncio
from bleak import BleakScanner

async def main():
    print("Safe scanning 5s...")
    try:
        async with BleakScanner() as scanner:
            await asyncio.sleep(5.0)
            devices = await scanner.get_discovered_devices()
    except Exception as e:
        print("Scan error:", e)
        return

    if not devices:
        print("No devices found")
    for d in devices:
        print(d.address, d.name, "rssi", d.rssi)

if __name__ == "__main__":
    asyncio.run(main())
