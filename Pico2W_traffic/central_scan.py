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

# central_scan.py (콜백형 API 예시)
import threading

def start_scan(on_seen, target_dir=None):
    """
    on_seen(direction:str, uid_hex:str) 를 매번 호출
    target_dir: "N"|"E"|"S"|"W" (선택) — 있으면 그 방향만 전달
    """
    # ... BLE 스캔 초기화 ...

    def loop():
        while True:
            # ★ 광고 파싱 (예: Service Data "P|D:N|UID:B3C827|C:1")
            # dir_letter = "N"  # 파싱 결과
            # uid_hex    = "B3C827"
            # if target_dir and dir_letter != target_dir: continue
            # on_seen(dir_letter, uid_hex)

            pass  # ← 여기에 기존 인식 로직/파서 그대로 사용

    th = threading.Thread(target=loop, daemon=True)
    th.start()
    return th
