#!/usr/bin/env python3
import subprocess, time

IFACE = "hci1"  # 외장 동글

def run(ogf, ocf, bs):
    cmd = ["sudo","hcitool","-i",IFACE,"cmd",ogf,ocf] + [f"{b:02x}" for b in bs]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def setup(interval_ms=100):
    # 어댑터 up
    subprocess.run(["sudo","rfkill","unblock","bluetooth"])
    subprocess.run(["sudo","hciconfig", IFACE, "up"])
    # Set Advertising Parameters (0x08,0x0006)
    units = int(interval_ms/0.625)
    params = [
        units & 0xFF, (units>>8)&0xFF,  # min
        units & 0xFF, (units>>8)&0xFF,  # max
        0x03, 0x00, 0x00,               # nonconn, public, direct type
        0,0,0,0,0,0,                    # direct addr
        0x07, 0x00                      # chan map, filter
    ]
    run("0x08","0x0006", params)
    # Enable Advertising (0x08,0x000A)
    run("0x08","0x000A", [0x01])

def set_adv(dir_letter, state, rt, q):
    payload = f"DIR:{dir_letter}|T:{state}|RT:{int(rt)}|Q:{1 if q else 0}".encode()
    sd = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload
    pad = bytes(31 - len(sd))
    params = bytes([len(sd)]) + sd + pad
    run("0x08","0x0008", list(params))

if __name__ == "__main__":
    setup()
    # 간단한 1사이클 반복 송출
    while True:
        for rt in range(8,0,-1):
            set_adv("N","GREEN",rt,0); time.sleep(1)
        for rt in range(2,0,-1):
            set_adv("N","YELLOW",rt,1); time.sleep(1)
        for rt in range(10,0,-1):
            set_adv("N","RED",rt,1); time.sleep(1)
