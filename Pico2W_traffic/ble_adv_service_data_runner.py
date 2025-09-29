# ble_adv_service_data_runner.py
# Simple helper: read a status line from stdin and advertise using dbus-next method (restarts adv)
# Requires: pip3 install dbus-next
import asyncio, sys, json
from dbus_next.aio import MessageBus
from dbus_next.message import Message
from dbus_next.constants import MessageType

ADAPTER = "hci0"

def mk_props(payload: str):
    data = payload.encode("utf-8")
    return {
        "Type": "peripheral",
        "LocalName": "Pi5",
        "ServiceData": { "ffff": bytes(data) },
        "IncludeTxPower": False,
        "Discoverable": True,
        "Timeout": 0,
    }

class LEAdvertisement:
    PATH = "/com/example/adv0"
    IFACE = "org.bluez.LEAdvertisement1"
    def __init__(self, props): self.props = props
    def get_properties(self): return { self.IFACE: self.props }
    async def Release(self): pass

async def register(bus, props):
    adv = LEAdvertisement(props)
    bus.export(LEAdvertisement.PATH, adv)
    msg = Message(destination="org.bluez",
                  path=f"/org/bluez/{ADAPTER}",
                  interface="org.bluez.LEAdvertisingManager1",
                  member="RegisterAdvertisement",
                  signature="oa{sv}",
                  body=[LEAdvertisement.PATH, {}])
    reply = await bus.call(msg)
    if reply.message_type == MessageType.ERROR:
        raise RuntimeError("RegisterAdvertisement failed")
    return adv

async def unregister(bus):
    msg = Message(destination="org.bluez",
                  path=f"/org/bluez/{ADAPTER}",
                  interface="org.bluez.LEAdvertisingManager1",
                  member="UnregisterAdvertisement",
                  signature="o",
                  body=["/com/example/adv0"])
    try:
        await bus.call(msg)
    except: pass

async def main():
    bus = await MessageBus(system=True).connect()
    adv_obj = None
    while True:
        line = sys.stdin.readline()
        if not line: break
        payload = line.strip()
        try:
            if adv_obj:
                await unregister(bus)
            props = mk_props(payload)
            adv_obj = await register(bus, props)
            print("ADV->", payload, flush=True)
        except Exception as e:
            print("ADVERR", e, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
