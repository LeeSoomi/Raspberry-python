# central_broadcast_demo_20total.py
import socket, json, time

BCAST_IP   = "255.255.255.255"
BCAST_PORT = 5005
TOTAL      = 20
ORDER      = ["N", "E", "S", "W"]

# 데모: 짝수사이클은 모두 5초, 홀수사이클은 N만 8초(혼잡), 나머지 4초
def make_segments(cycle):
    if cycle % 2 == 0:
        seg = {d:5 for d in ORDER}              # 5,5,5,5
    else:
        seg = {"N":8, "E":4, "S":4, "W":4}      # 8,4,4,4  (예시)
    assert sum(seg.values()) == TOTAL
    return seg

def build_timeline(segments):
    # 타임라인: [(dir, len, start, end)]  (end는 포함)
    tl, t = [], TOTAL
    for d in ORDER:
        L = segments[d]
        tl.append((d, L, t-L+1, t))
        t -= L
    return tl

def state_for_time(tl, t_now):
    # 현재 t_now(20..1)에 해당하는 활성 방향/남은초 계산
    for d, L, start, end in tl:
        if start <= t_now <= end:
            active = d
            t_rem  = end - t_now + 1
            return active, t_rem
    return ORDER[0], 1  # fallback (안 나올 상황)

def pack_payload(tl, active, t_rem, segments):
    # 각 방향 상태 생성
    dirs = {}
    for d, L, start, end in tl:
        if d == active:
            phase = "GREEN"
            # GREEN 남은 시간은 현재 슬롯 내 남은초
            g_left = t_rem
            dirs[d] = {"phase": phase, "t_rem": int(g_left), "g_dur": L}
        else:
            # 대기는 다음 자기 슬롯 GREEN 시작까지 남은 전체 시간
            # 현재 t_now에서 자기 슬롯 start까지의 차이를 이용
            # 주기 내에서 start가 현재보다 앞에 있으면 래핑(+TOTAL)
            t_to_start = start - t_now_global
            if t_to_start <= 0:
                t_to_start += TOTAL
            dirs[d] = {"phase": "RED", "t_rem": int(t_to_start), "g_dur": L}
    return {
        "schema": 1,
        "total": TOTAL,
        "order": ORDER,
        "directions": dirs
    }

# ---- main ----
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

cycle = 0
while True:
    seg = make_segments(cycle)
    timeline = build_timeline(seg)   # 20..1 카운트다운 윈도우
    for t_now_global in range(TOTAL, 0, -1):
        active, t_rem = state_for_time(timeline, t_now_global)
        payload = pack_payload(timeline, active, t_rem, seg)
        s.sendto(json.dumps(payload).encode(), (BCAST_IP, BCAST_PORT))
        time.sleep(1)
    cycle += 1
