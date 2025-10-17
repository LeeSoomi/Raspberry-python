# 한번만 설치
# sudo apt-get update
# sudo apt-get install -y python3-gpiozero
# ------------------

# 실행 sudo -E python3 central_traffic_with_hb_LED.py
#!/usr/bin/env python3
# central_traffic_with_hb.py  (Raspberry Pi / Python 3)
# - 차량 하트비트 수신(HB_PORT)
# - 4방향 신호 스케줄 계산(기본 20초 사이클)
# - 신호 상태를 초당 한 번 브로드캐스트(UDP)

import socket, json, time

# ===== 설정 =====
BCAST_IP, BCAST_PORT = "255.255.255.255", 5005  # 신호 브로드캐스트
HB_PORT = 5006                                   # 하트비트 수신 포트
TOTAL = 20                                       # 전체 사이클(초)
ORDER = ["N", "E", "S", "W"]                     # 진행 순서
CAR_THRESH = 3                                   # 혼잡 기준(>=3대)
HB_TTL = 3.5                                     # 하트비트 유효 시간(초)

PRINT_DEBUG = True                               # 콘솔 로그 여부

# ===== 소켓 준비 =====
bcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

hb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hb.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
hb.bind(("0.0.0.0", HB_PORT))
hb.setblocking(False)

# ===== 차량 DB(uid -> {dir,last}) =====
vehicles = {}

def pump_hb(now):
    """하트비트 수신 버퍼를 비우며 DB 갱신"""
    while True:
        try:
            data, addr = hb.recvfrom(256)
        except BlockingIOError:
            break
        except Exception:
            break
        try:
            obj = json.loads(data)
            uid = str(obj.get("uid", ""))
            d   = obj.get("dir", "")
            if uid and d in ORDER:
                vehicles[uid] = {"dir": d, "last": now}
        except Exception:
            pass  # 이상 패킷 무시

def counts_from_db(now):
    """TTL 내 차량만 집계하고, 오래된 항목은 제거"""
    counts = {d: 0 for d in ORDER}
    drop = []
    for uid, rec in vehicles.items():
        if (now - rec["last"]) <= HB_TTL:
            counts[rec["dir"]] += 1
        else:
            drop.append(uid)
    for uid in drop:
        vehicles.pop(uid, None)
    return counts

def decide_segments(car_counts):
    """
    정책:
      - 정확히 1방향만 혼잡(>=3대)이면: 그 방향 8초, 나머지 4초 → 8/4/4/4
      - 그 외(모두 고르게 분포 또는 2방향 이상 혼잡): 5/5/5/5
    """
    congested = [d for d in ORDER if car_counts.get(d, 0) >= CAR_THRESH]
    if len(congested) == 1:
        seg = {d: (8 if d in congested else 4) for d in ORDER}
    else:
        seg = {d: 5 for d in ORDER}
    assert sum(seg.values()) == TOTAL
    return seg, congested

def build_timeline(segments):
    """사이클 1..TOTAL에서 각 방향 GREEN 구간(start..end)을 계산"""
    tl, t = [], TOTAL
    for d in ORDER:
        L = segments[d]
        tl.append((d, L, t - L + 1, t))  # (dir, len, start, end)
        t -= L
    return tl

def pack_payload(tl, t_now, segments, car_counts):
    """
    t_now는 1..TOTAL(증가)로 진행.
    - 현재 GREEN이면 남은 시간 = end - t_now + 1  (→ 8,7,6..1 로 감소)
    - 그 외(RED): 다음 GREEN 시작까지 대기 = start - t_now (≤0 이면 TOTAL 더하기)
    """
    dirs = {}
    for d, L, start, end in tl:
        if start <= t_now <= end:
            dirs[d] = {
                "phase": "GREEN",
                "t_rem": end - t_now + 1,
                "g_dur": L,
                "cars": car_counts.get(d, 0),
            }
        else:
            t_to_start = start - t_now
            if t_to_start <= 0:
                t_to_start += TOTAL
            dirs[d] = {
                "phase": "RED",
                "t_rem": t_to_start,
                "g_dur": L,
                "cars": car_counts.get(d, 0),
            }
    return {
        "src": "central_hb_v1",
        "schema": 1,
        "total": TOTAL,
        "order": ORDER,
        "directions": dirs,
    }

# ===== 메인 루프 =====
cycle = 0
while True:
    now = time.time()
    pump_hb(now)
    car_counts = counts_from_db(now)
    segments, congested = decide_segments(car_counts)

    if PRINT_DEBUG:
        print(f"[cycle {cycle}] counts={car_counts} congested={congested} segments={segments}")

    tl = build_timeline(segments)

    # ★ 중요: 1 → TOTAL 로 증가시키며 전송
    for t_now in range(1, TOTAL + 1):
        now = time.time()
        pump_hb(now)                    # 주기 중에도 수신/만료 갱신
        car_counts = counts_from_db(now)

        payload = pack_payload(tl, t_now, segments, car_counts)
        try:
            bcast.sendto(json.dumps(payload).encode(), (BCAST_IP, BCAST_PORT))
        except Exception as e:
            if PRINT_DEBUG:
                print("[WARN] send fail:", e)
        time.sleep(1)

    cycle += 1
