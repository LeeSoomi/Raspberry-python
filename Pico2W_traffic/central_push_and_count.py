#!/usr/bin/env python3
import asyncio
import argparse
import subprocess
import time
from bleak import BleakScanner

# --------- 파라미터 기본값 ---------
DEFAULT_ADAPTER = "hci1"   # 동글이 쓰면 hci1, 내장만 쓰면 hci0
SCAN_WINDOW_SEC = 15       # 대기창(스캔) 길이
BASE_GREEN = 5             # 기본 녹색 시간
# 임계값: 차량수 >= TH1 -> G1, >= TH2 -> G2
TH1, G1 = 3, 8
TH2, G2 = 6, 12

ACK_UUID16 = 0xFFFF  # 피코가 보내는 ACK의 Service Data UUID

# --------- 유틸 ---------
def _now():
    return time.strftime("[%H:%M:%S] ")

def decide_green(count: int) -> int:
    if count >= TH2:
        return G2
    if count >= TH1:
        return G1
    return BASE_GREEN

def fmt_name(sec: int, direction: str, with_q: bool=True) -> str:
    # 중앙->피코 광고 포맷: S:<초>|D:<방향>|Q:1
    return f"S:{max(0,sec)}|D:{direction}|Q:{1 if with_q else 0}"

def btmgmt(*args, check=True):
    # sudo btmgmt ... 호출
    cmd = ["sudo", "btmgmt", *args]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)

def one_shot_adv(adapter: str, name: str, dur_s: float=0.28):
    """
    Legacy non-connectable 광고 1회(약 280ms) 발생.
    - add-adv -d -n "<name>" 로 추가 후 잠깐 대기
    - rm-adv 0 로 제거
    """
    try:
        btmgmt("-i", adapter, "add-adv", "-d", "-n", name, check=True)
        time.sleep(dur_s)
    except subprocess.CalledProcessError as e:
        # Busy 등 오류 시 잠시 후 복구
        time.sleep(0.05)
    finally:
        # 제거는 실패해도 무시
        subprocess.run(["sudo", "btmgmt", "-i", adapter, "rm-adv", "0"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def push_countdown(adapter: str, seconds: int, direction: str):
    # seconds .. 0 까지 1초마다 이름 광고
    for s in range(seconds, -1, -1):
        name = fmt_name(s, direction, with_q=True)
        one_shot_adv(adapter, name, dur_s=0.28)
        time.sleep(0.02)  # add/rm 사이 약간 여유
        # 1초 템포 유지
        remain = 1.0 - 0.28 - 0.02
        if remain > 0:
            time.sleep(remain)

def parse_adv_fields(raw: bytes):
    # 간단한 AD 구조 파서
    out = {}
    i = 0
    n = len(raw)
    while i < n:
        L = raw[i]
        if L == 0 or i + L >= n:
            break
        t = raw[i+1]
        v = raw[i+2:i+1+L]
        out.setdefault(t, []).append(v)
        i += 1 + L
    return out

def extract_ack_uid_and_dir(raw: bytes):
    """
    피코 ACK(Service Data 0xFFFF, 내용: b'P' + uid3 + dir1바이트)을 확인.
    성공 시 (uid_hex, dir_char) 반환, 아니면 None.
    """
    f = parse_adv_fields(raw)
    for v in f.get(0x16, []):  # Service Data
        if len(v) >= 2 and v[0] == (ACK_UUID16 & 0xFF) and v[1] == ((ACK_UUID16 >> 8) & 0xFF):
            payload = v[2:]
            if len(payload) >= 5 and payload[0:1] == b'P':
                uid3 = payload[1:4]
                direction = payload[4:5].decode(errors="ignore") or "?"
                return uid3.hex(), direction
    return None

async def scan_once(window_sec: int):
    """
    window_sec 동안 스캔하고, ACK 보낸 피코 수(유니크 uid3 기준)를 반환.
    """
    seen = set()

    def cb(d, ad):
        if ad is None:  # bleak 최신 버전 콜백은 (device, advertisement_data)
            return
        raw = ad.manufacturer_data_bytes or b""
        # manufacturer_data 가 비어있을 수 있어 전체 바이트가 필요.
        # bleak는 advertisement_data.bytes 로 전체 패킷 제공
        raw_all = getattr(ad, "bytes", None)
        if raw_all:
            found = extract_ack_uid_and_dir(raw_all)
            if found:
                uid_hex, direction = found
                seen.add(uid_hex)

    scanner = BleakScanner()  # 어댑터는 OS 기본(default) 사용
    scanner.register_detection_callback(cb)
    try:
        await scanner.start()
        await asyncio.sleep(window_sec)
    finally:
        await scanner.stop()

    return len(seen)

async def main(adapter: str, direction: str, window: int):
    print(f"{_now()}[A] single-direction controller start (adapter={adapter})")

    # 어댑터 준비(LE on)
    try:
        btmgmt("-i", adapter, "le", "on", check=False)
    except Exception:
        pass

    while True:
        # 1) 대기창(스캔) 동안 차량수 수집
        cnt = await scan_once(window)
        green = decide_green(cnt)

        print(f"{_now()}DIR={direction} window={window}s -> count={cnt}  =>  next G={green}s")

        # 2) 카운트다운 광고 송출
        push_countdown(adapter, green, direction)

        # 3) 다음 라운드 전 짧은 휴식(원하면 조정)
        time.sleep(0.5)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=DEFAULT_ADAPTER, help="hci0 or hci1")
    ap.add_argument("--direction", "-d", default="A", help="signal direction label (A/B/C/D)")
    ap.add_argument("--window", "-w", type=int, default=SCAN_WINDOW_SEC, help="scan window seconds")
    ap.add_argument("--base", type=int, default=BASE_GREEN, help="base green seconds")
    ap.add_argument("--th1", type=int, default=TH1)
    ap.add_argument("--g1", type=int, default=G1)
    ap.add_argument("--th2", type=int, default=TH2)
    ap.add_argument("--g2", type=int, default=G2)
    args = ap.parse_args()

    # 전역 임계값/시간 사용자 값 반영
    BASE_GREEN = args.base
    TH1, G1 = args.th1, args.g1
    TH2, G2 = args.th2, args.g2

    asyncio.run(main(args.adapter, args.direction, args.window))



# 실행 방법

# (처음 1회만) 패키지 준비

# sudo apt update
# sudo apt install -y bluetooth bluez bluez-tools
# python3 -m venv bleenv
# source bleenv/bin/activate
# pip install --upgrade pip bleak


# 어댑터 확인/준비

# hciconfig -a                 # hci0/hci1 확인
# sudo rfkill unblock bluetooth
# sudo hciconfig hci0 up       # 내장 쓰면 hci0
# sudo btmgmt -i hci0 le on
# # 동글이 쓰면 hci1 도 같은 방식으로 up + le on


# 실행

# cd ~/COS
# source ../bleenv/bin/activate
# sudo -E env PATH="$PATH" python3 central_push_and_count.py --adapter hci1 --direction A --window 15
