# #!/usr/bin/env python3
# from bluepy.btle import Scanner
# import time

# # ----- 설정 -----
# IFACE = 0            # hci0 사용
# SCAN_SEC = 3.0
# SHOW_ONLY_P = False  # True면 ACK('P')만 출력

# # 차량 매핑: UID3(대문자) -> 표시명
# CAR = {
#     "B3C827": "차량1",
#     "3F06FE": "차량2",
#     "CA8756": "차량3",
# }

# # ----- 0xFFFF Service Data 파서 -----
# def parse_service_data_hex(hexstr):
#     try:
#         b = bytes.fromhex(hexstr)
#         if len(b) < 3 or b[:2] != b"\xff\xff":
#             return None
#         p = b[2:]
#         if not p:
#             return None
#         tag = p[0]             # b'C'(0x43) or b'P'(0x50)
#         if tag not in (0x43, 0x50):
#             return None
#         info = {"tag": chr(tag)}
#         if len(p) >= 4:
#             uid3 = p[1:4]
#             info["uid3"] = uid3.hex().upper()
#         if len(p) >= 6 and p[4] == 0x7C:  # '|' 다음에 방향문자 있을 수 있음
#             info["direction"] = chr(p[5])
#         return info
#     except Exception:
#         return None

# # ----- 메인 루프 -----
# def main():
#     scanner = Scanner(iface=IFACE)
#     print("[scan] start (ServiceData 0xFFFF: 'C'(beacon) / 'P'(ACK)) on hci%d" % IFACE)
#     while True:
#         devs = scanner.scan(SCAN_SEC)
#         hits = []
#         for d in devs:
#             for (adtype, desc, value) in d.getScanData():
#                 if adtype == 0x16:  # Service Data (16-bit UUID)
#                     info = parse_service_data_hex(value)
#                     if info and "uid3" in info:
#                         info.update({"mac": d.addr, "rssi": d.rssi})
#                         hits.append(info)

#         if SHOW_ONLY_P:
#             hits = [h for h in hits if h["tag"] == "P"]

#         if hits:
#             print(f"[scan] hits {len(hits)}:")
#             for h in hits:
#                 name = CAR.get(h["uid3"], h["uid3"])
#                 tag  = h["tag"]
#                 dirc = h.get("direction", "-")
#                 if tag == "P":
#                     print(f"  - P  {name}  UID3={h['uid3']}  D={dirc}  RSSI={h['rssi']}  MAC={h['mac']}")
#                 else:
#                     print(f"  - C  {name}  UID3={h['uid3']}  RSSI={h['rssi']}  MAC={h['mac']}")
#         else:
#             print("[scan] hits 0")

#         time.sleep(0.5)

# if __name__ == "__main__":
#     main()

# -----------------------
# 실행
# sudo /home/codestudio/bleenv/bin/python /home/codestudio/COS/central_scan.py

# central_scan.py
#!/usr/bin/env python3
from bluepy.btle import Scanner
import time, threading

IFACE = 0          # hci0
SCAN_SEC = 2.0
ONLY_P   = True    # True면 ACK('P')만 전달

# --- 0xFFFF Service Data 파서 (두 포맷 모두 지원) ---
def parse_servdata_hex(hexstr):
    """
    반환: {"tag": "P"/"C", "uid3": "B3C827", "direction": "N" or None}
    매칭 실패 시 None
    """
    try:
        b = bytes.fromhex(hexstr)
        # 0xFFFF + payload
        if len(b) < 3 or b[0:2] != b"\xff\xff":
            return None
        p = b[2:]  # payload

        if not p:
            return None

        tag = chr(p[0])  # 'P' or 'C'
        if tag not in ("P", "C"):
            return None

        info = {"tag": tag, "uid3": None, "direction": None}

        # --- 케이스 A: 바이너리 UID(3바이트) + "|D:N"
        #   p = b'P' + <3bytes> + b'|D:' + b'N' + ...
        if len(p) >= 4 and p[1] != 0x7C:  # 0x7C='|'
            uid3 = p[1:4].hex().upper()
            info["uid3"] = uid3
            # 방향 찾기
            pos = p.find(b"|D:")
            if pos != -1 and pos + 3 < len(p):
                info["direction"] = chr(p[pos + 3])
            return info

        # --- 케이스 B: ASCII 포맷 "P|D:N|UID:ABC123|C:1"
        try:
            s = p.decode(errors="ignore")
            # UID
            uid3 = None
            if "UID:" in s:
                # UID: 뒤 6글자만 사용
                part = s.split("UID:", 1)[1]
                uid3 = part[:6].upper()
            info["uid3"] = uid3
            # 방향
            if "|D:" in s:
                info["direction"] = s.split("|D:", 1)[1][:1]
            return info if uid3 else None
        except Exception:
            return None
    except Exception:
        return None

# --- 스캐너 스레드: on_seen(dir, uid_hex) 콜백 호출 ---
def start_scan(on_seen, target_dir=None):
    scanner = Scanner(iface=IFACE)
    def loop():
        while True:
            devs = scanner.scan(SCAN_SEC)
            for d in devs:
                for (adtype, desc, value) in d.getScanData():
                    if adtype != 0x16:       # 0x16 = Service Data(16-bit)
                        continue
                    info = parse_servdata_hex(value)
                    if not info: 
                        continue
                    if ONLY_P and info["tag"] != "P":
                        continue
                    uid = info.get("uid3")
                    if not uid:
                        continue
                    dirc = info.get("direction") or target_dir or "N"
                    on_seen(dirc, uid)
            time.sleep(0.05)
    th = threading.Thread(target=loop, daemon=True)
    th.start()
    return th

# --- 단독 실행시 콘솔 출력 데모 ---
if __name__ == "__main__":
    def _print(d, u):
        print(f"[SEEN] dir={d} uid={u}")
    print("[scan] start on hci%d" % IFACE)
    start_scan(_print, target_dir="N")
    while True:
        time.sleep(1)
