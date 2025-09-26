#!/usr/bin/env python3
import asyncio
import argparse
import subprocess
import time
from bleak import BleakScanner

# --------- 기본 파라미터 ---------
DEFAULT_ADAPTER = "hci1"     # 동글이=hci1, 내장만=hci0
SCAN_WINDOW_SEC = 15         # 대기(스캔) 구간 길이
BASE_GREEN = 5               # 기본 녹색 신호 시간
TH1, G1 = 3, 8               # cnt>=TH1 → G1
TH2, G2 = 6, 12              # cnt>=TH2 → G2

# (옵션) 대기 중 하트비트 광고 주기
BEACON_PERIOD_S = 2

ACK_UUID16 = 0xFFFF          # 피코 ACK(Service Data) UUID

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
    # 중앙 -> 피코 광고 문자열 (Complete Local Name 로 보냄)
    # 예: "S:7|D:A|Q:1"
    return f"S:{max(0,sec)}|D:{direction}|Q:{1 if with_q else 0}"

def btmgmt(*args, check=True):
    # sudo btmgmt ...
    cmd = ["sudo", "btmgmt", *args]
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check
    )

def one_shot_adv(adapter: str, name: str, dur_s: float=0.28):
    """Legacy non-connectable 광고 1회(약 280ms)"""
    try:
        btmgmt("-i", adapter, "add-adv", "-d", "-n", name, check=True)
        time.sleep(dur_s)
    except subprocess.CalledProcessError:
        time.sleep(0.05)  # busy 등일 때 잠깐 쉬고 넘어감
    finally:
        subprocess.run(
            ["sudo", "btmgmt", "-i", adapter, "rm-adv", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

def push_countdown(adapter: str, seconds: int, direction: str):
    """seconds..0 까지 초마다 카운트다운 광고"""
    for s in range(seconds, -1, -1):
        name = fmt_name(s, direction, with_q=True)
        one_shot_adv(adapter, name, dur_s=0.28)
        # 1초 템포 맞추기 (0.28 + 0.02 대기가 있으므로 나머지 보정)
        remain = 1.0 - 0.28 - 0.02
        if remain > 0:
            time.sleep(remain)
        else:
            time.sleep(0.02)

# ---- 스캔 유틸 ----
def parse_adv_fields(raw: bytes):
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
    """ Service Data 0xFFFF 에 담긴 피코 ACK 확인(b'P'+uid3+dir) """
    f = parse_adv_fields(raw)
    for v in f.get(0x16, []):
        if len(v) >= 2 and v[0] == (ACK_UUID16 & 0xFF) and v[1] == ((ACK_UUID16 >> 8) & 0xFF):
            payload = v[2:]
            if len(payload) >= 5 and payload[0:1] == b'P':
                uid3 = payload[1:4]
                direction = payload[4:5].decode(errors="ignore") or "?"
                return uid3.hex(), direction
    return None

async def scan_once(window_sec: int) -> int:
    """window_sec 동안 스캔하고 ACK 보낸 피코(고유 uid3) 수 반환"""
    seen = set()

    def cb(device, ad):
        if ad is None:
            return
        # 1) service_data 경로 (권장)
        svc = getattr(ad, "service_data", None)
        if isinstance(svc, dict):
            for k, payload in svc.items():
                ks = str(k).lower()
                if ks.endswith("ffff"):
                    if isinstance(payload, (bytes, bytearray)) and len(payload) >= 5 and payload[0:1] == b'P':
                        uid3 = payload[1:4]
                        seen.add(uid3.hex())
        # 2) 보조 루트: raw bytes 접근 가능할 때
        raw_all = getattr(ad, "bytes", None)
        if raw_all:
            found = extract_ack_uid_and_dir(raw_all)
            if found:
                uid_hex, _ = found
                seen.add(uid_hex)

    scanner = BleakScanner(detection_callback=cb)
    try:
        await scanner.start()
        await asyncio.sleep(window_sec)
    finally:
        await scanner.stop()
    return len(seen)

# (옵션) 대기 중 하트비트 광고
def idle_beacon(adapter: str, direction: str):
    name = fmt_name(0, direction, with_q=False)  # Q:0 으로 가볍게
    one_shot_adv(adapter, name, dur_s=0.20)

# --------- 메인 ---------
async def main(adapter: str, direction: str, window: int):
    print(f"{_now()}[A] single-direction controller start (adapter={adapter})")

    # 어댑터 LE 준비
    try:
        btmgmt("-i", adapter, "le", "on", check=False)
    except Exception:
        pass

    last_beacon = 0.0

    while True:
        # 1) 대기-스캔 단계: 몇 대가 있는지 집계
        cnt = await scan_once(window)
        green = decide_green(cnt)
        print(f"{_now()}DIR={direction} window={window}s -> count={cnt}  =>  next G={green}s")

        # 2) 실제 신호 구간: 카운트다운을 피코로 송출
        push_countdown(adapter, green, direction)

        # 3) (옵션) 대기 동안 주기적 하트비트 광고
        now = time.time()
        if now - last_beacon >= BEACON_PERIOD_S:
            idle_beacon(adapter, direction)   # 필요 없으면 이 줄 주석 처리
            last_beacon = now

        time.sleep(0.5)  # 다음 라운드까지 짧은 휴식
        

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=DEFAULT_ADAPTER, help="hci0 or hci1")
    ap.add_argument("--direction", "-d", default="A", help="A/B/C/D")
    ap.add_argument("--window", "-w", type=int, default=SCAN_WINDOW_SEC)
    ap.add_argument("--base", type=int, default=BASE_GREEN)
    ap.add_argument("--th1", type=int, default=TH1)
    ap.add_argument("--g1", type=int, default=G1)
    ap.add_argument("--th2", type=int, default=TH2)
    ap.add_argument("--g2", type=int, default=G2)
    args = ap.parse_args()

    # 사용자 설정 반영
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
