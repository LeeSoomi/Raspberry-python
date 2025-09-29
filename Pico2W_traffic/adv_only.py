#!/usr/bin/env python3
# adv_only.py : 0xFFFF ServiceData로 DIR/T/RT/Q를 1Hz로 광고(테스트용)

import subprocess, time

HCI = "hci0"
ADV_INT_MS = 100  # 100ms

def run(cmd):
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def hci_cmd(ogf_hex, ocf_hex, payload):
    run(["sudo","hcitool","-i",HCI,"cmd",ogf_hex,ocf_hex] + [f"{b:02x}" for b in payload])

def setup():
    run(["sudo","rfkill","unblock","bluetooth"])
    run(["sudo","hciconfig",HCI,"up"])
    # LE Set Advertising Parameters (0x08, 0x0006)
    units = int(ADV_INT_MS/0.625)
    params = [
        units & 0xFF, (units>>8)&0xFF,  # min
        units & 0xFF, (units>>8)&0xFF,  # max
        0x00,  # ADV_IND(연결가능 일반 광고) ← 수신 호환성 높음
        0x00,  # Own addr public
        0x00,  # Direct addr type
        0,0,0,0,0,0,  # Direct addr
        0x07,  # Channel map
        0x00,  # Filter policy
    ]
    hci_cmd("0x08","0x0006",params)
    # Enable advertising
    hci_cmd("0x08","0x000A",[0x01])

def set_adv(dir_letter, state, rt, q):
    # AD Flags(0x01) + ServiceData(0x16, UUID 0xFFFF)
    flags = bytes([2,0x01,0x06])
    payload = f"DIR:{dir_letter}|T:{state}|RT:{int(rt)}|Q:{int(bool(q))}".encode()
    sd = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload
    ad = flags + sd
    if len(ad) > 31:
        # 길면 T를 약어화
        s = {"GREEN":"G","YELLOW":"Y","RED":"R"}.get(state, state[:1])
        payload = f"DIR:{dir_letter}|T:{s}|RT:{int(rt)}|Q:{int(bool(q))}".encode()
        sd = bytes([len(payload)+3,0x16,0xFF,0xFF]) + payload
        ad = flags + sd
    buf = bytes([len(ad)]) + ad + bytes(31-len(ad))
    hci_cmd("0x08","0x0008",buf)  # Set Advertising Data

if __name__ == "__main__":
    setup()
    rt = 8
    while True:
        set_adv("N","GREEN",rt,0)  # 1Hz로 내용 갱신
        rt = rt-1 if rt>0 else 8
        time.sleep(1)
