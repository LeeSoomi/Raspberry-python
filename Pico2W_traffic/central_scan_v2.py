#!/usr/bin/env python3
# central_scan.py
from bluepy.btle import Scanner
import time, threading

SCAN_SEC = 1.2
ONLY_P   = True  # True면 ACK('P')만 전달

def parse_servdata_hex(hexstr):
    """Service Data(0xFFFF)에서 'P|D:N|UID:ABC123|C:1' 또는
       바이너리('P'<UID3>|D:N...)를 파싱해서 {'tag','uid3','direction'} 리턴"""
    try:
        b = bytes.fromhex(hexstr)
        if len(b) < 3 or b[0:2] != b"\xff\xff":
            return None
        p = b[2:]
        if not p:
            return None
        tag = chr(p[0])
        if tag not in ("P", "C"):
            return None
        info = {"tag": tag, "uid3": None, "direction": None}

        # Case A: 바이너리 'P' + UID3 + "|D:N"
        if len(p) >= 4 and p[1] != 0x7C:  # '|'=0x7C
            info["uid3"] = p[1:4].hex().upper()
            pos = p.find(b"|D:")
            if pos != -1 and pos + 3 < len(p):
                info["direction"] = chr(p[pos + 3])
            return info if info["uid3"] else None

        # Case B: ASCII "P|D:N|UID:ABC123|C:1"
        try:
            s = p.decode(errors="ignore")
            if "UID:" in s:
                info["uid3"] = s.split("UID:", 1)[1][:6].upper()
            if "|D:" in s:
                info["direction"] = s.split("|D:", 1)[1][:1]
            return info if info["uid3"] else None
        except Exception:
            return None
    except Exception:
        return None

def start_scan(on_seen, target_dir=None, iface=0):
    """
    on_seen(direction, uid_hex) 콜백을 호출.
    iface: 0→hci0(내장), 1→hci1(외장) ...
    """
    scanner = Scanner(iface=iface)

    def loop():
        while True:
            devs = scanner.scan(SCAN_SEC)
            for d in devs:
                for (adtype, desc, value) in d.getScanData():
                    if adtype != 0x16:   # Service Data (16-bit)
                        continue
                    info = parse_servdata_hex(value)
                    if not info:
                        continue
                    if ONLY_P and info["tag"] != "P":
                        continue
                    uid = info.get("uid3")
                    dirc = info.get("direction") or target_dir or "N"
                    if uid:
                        on_seen(dirc, uid)
            time.sleep(0.05)

    th = threading.Thread(target=loop, daemon=True)
    th.start()
    return th
