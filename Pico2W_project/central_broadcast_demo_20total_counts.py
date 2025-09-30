# central_broadcast_demo_20total_counts.py
import socket, json, time

BCAST_IP, BCAST_PORT = "255.255.255.255", 5005
TOTAL = 20
ORDER = ["N", "E", "S", "W"]
CAR_THRESH = 3  # 3대 이상이면 혼잡

def decide_segments(car_counts):
    congested = [d for d in ORDER if car_counts.get(d, 0) >= CAR_THRESH]
    if len(congested) == 1:
        # 그 방향만 8초, 나머지 4초
        seg = {d: (8 if d in congested else 4) for d in ORDER}
    else:
        # 0개, 2개 이상(또는 모두) 혼잡이면 기본 유지
        seg = {d: 5 for d in ORDER}
    assert sum(seg.values()) == TOTAL
    return seg, congested

def build_timeline(segments):
    tl, t = [], TOTAL
    for d in ORDER:  # N,E,S,W 순서로 20..1에 배치
        L = segments[d]
        tl.append((d, L, t-L+1, t))  # (방향,길이,시작,끝)
        t -= L
    return tl

def state_for_time(tl, t_now):
    for d, L, start, end in tl:
        if start <= t_now <= end:
            return d, end - t_now + 1  # 활성방향, 그 슬롯 남은초
    return ORDER[0], 1

def pack_payload(tl, t_now, segments, car_counts):
    dirs = {}
    for d, L, start, end in tl:
        if start <= t_now <= end:
            dirs[d] = {"phase":"GREEN", "t_rem": end - t_now + 1, "g_dur": L, "cars": car_counts.get(d,0)}
        else:
            # 다음 자기 GREEN 시작까지 남은 시간(래핑 포함)
            t_to_start = start - t_now
            if t_to_start <= 0: t_to_start += TOTAL
            dirs[d] = {"phase":"RED", "t_rem": t_to_start, "g_dur": L, "cars": car_counts.get(d,0)}
    return {"schema":1, "total":TOTAL, "order":ORDER, "directions":dirs}

# === 데모 루프 ===
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# 테스트: 여기서 차량 수를 바꿔보며 확인 (실전은 하트비트로 갱신)
car_counts = {"N":2, "E":1, "S":0, "W":2}  # ★ N=2면 8초가 아니라 5초가 내려감

while True:
    segments, congested = decide_segments(car_counts)
    tl = build_timeline(segments)
    for t_now in range(TOTAL, 0, -1):
        payload = pack_payload(tl, t_now, segments, car_counts)
        s.sendto(json.dumps(payload).encode(), (BCAST_IP, BCAST_PORT))
        time.sleep(1)
