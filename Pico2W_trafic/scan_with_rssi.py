# scan_with_rssi.py
import asyncio
from bleak import BleakScanner

def detection_callback(device, advertisement_data):
    # device.address, device.name
    # advertisement_data.rssi 또는 device.rssi (버전에 따라 다름)
    rssi = getattr(advertisement_data, "rssi", None)
    if rssi is None:
        rssi = getattr(device, "rssi", None)
    print(device.address, device.name, "rssi", rssi)

async def main():
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    print("Start scanning 5s...")
    await asyncio.sleep(5.0)
    await scanner.stop()
    print("Stopped.")

if __name__ == "__main__":
    asyncio.run(main())
