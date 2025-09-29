#!/usr/bin/env python3
# central_scan.py
from bluepy.btle import Scanner
import time, threading

SCAN_SEC = 1.2
ONLY_P   = True  # True면 ACK('P')만 전달

# central_scan.py
def parse_service_data_hex(hexstr):
    """
    0xFFFF Service Data에서 ACK/Beacon을 파싱.
    허용:
      - ASCII:  "P|D:N|UID:ABC123|C:1"
      - Binary: 0x50 'P' + UID3(3B) + b'|D:N' ...
    반환: {"tag":"P","uid3":"ABC123","direction":"N"} 등
    """
    try:
        b = bytes.fromhex(hexstr)
        if len(b) < 3 or b[:2] != b"\xff\xff":
            return None
        p = b[2:]

        # 1) ASCII 경로 우선 (가장 흔함)
        try:
            s = p.decode()
            # 최소 요건: UID:와 D:가 들어 있어야
            if "UID:" in s and "|D:" in s:
                # tag: 문자열 맨앞이 'P' 또는 'C'면 사용
                tag = s[:1] if s[:1] in ("P","C") else None
                # UID6 추출
                i = s.find("UID:")
                uid6 = s[i+4:i+10].upper() if i != -1 else None
                # 방향 추출
                j = s.find("|D:")
                direction = s[j+3:j+4] if j != -1 else None
                if uid6 and len(uid6) == 6:
                    info = {"uid3": uid6}
                    if tag:       info["tag"] = tag
                    if direction: info["direction"] = direction
                    # tag가 비어도 ACK만 쓰고 싶으면 아래 한 줄로 강제 P 처리도 가능
                    if "tag" not in info and s.startswith("P|"):
                        info["tag"] = "P"
                    return info
        except Exception:
            pass

        # 2) Binary 경로 (선두 1바이트가 'P'(0x50) or 'C'(0x43))
        if not p:
            return None
        tag = chr(p[0])
        if tag not in ("P","C"):
            return None
        info = {"tag": tag}
        if len(p) >= 4:
            info["uid3"] = p[1:4].hex().upper()
        # '|D:N' 같은 방향 필드가 뒤에 있을 수 있음
        if len(p) >= 6:
            # 0x7C == '|'
            k = p.find(b"|D:")
            if k != -1 and k + 3 < len(p):
                info["direction"] = chr(p[k+3])
        return info if "uid3" in info else None
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
