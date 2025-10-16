# 한번만 설치
# sudo apt-get update
# sudo apt-get install -y python3-gpiozero
# ------------------

# 실행 sudo python3 central_traffic_with_hb_LED.py
# ----------------------------------

# central_traffic_with_hb.py  (Raspberry Pi 5 / Python 3)
# central_traffic_with_hb.py  (Raspberry Pi 5 / Python 3)
import socket, json, time
import os

# ===== 내 방향 / 핀팩토리 기본 =====
MY_DIR = os.environ.get("MY_DIR", "N")          # N/E/S/W
os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

# ===== 물리 LED (BCM 핀) =====
PIN_RED, PIN_YELLOW, PIN_GREEN = 17, 27, 22
try:
    from gpiozero import LED
    _GPIO_OK = True
except Exception as e:
    print(f"[WARN] gpiozero unavailable: {e}")
    _GPIO_OK = False

class TrafficLight:
    def __init__(self, r=PIN_RED, y=PIN_YELLOW, g=PIN_GREEN):
        self.ok = _GPIO_OK
        if self.ok:
            self.red = LED(r); self.yellow = LED(y); self.green = LED(g)
            self.all_off()
    def all_off(self):
        if not self.ok: return
        self.red.off(); self.yellow.off(); self.green.off()
    def set_state(self, state: str):
        if not self.ok: return
        self.all_off()
        s = (state or "").upper()
        if s == "GREEN": self.green.on()
        elif s == "YELLOW": self.yellow.on()
        else: self.red.on()
    def close(self):
        if not self.ok: return
        self.all_off()

# ---- 설정 ----
BCAST_IP, BCAST_PORT = "255.255.255.255", 5005  # 브로드캐스트
HB_PORT = 5006                                   # 하트비트 수신
TOTAL = 20
ORDER = ["N","E","S","W"]
CAR_THRESH = 3
HB_TTL = 3.5

# ---- 소켓 ----
bcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

hb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hb.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
hb.bind(("0.0.0.0", HB_PORT))
hb.setblocking(False)

# ---- 차량 DB ----
vehicles = {}

def pump_hb(now):
    while True:
        try:
            data, addr = hb.recvfrom(256)
        except BlockingIOError:
            break
        except Exception:
            break
        try:
            obj = json.loads(data)
            uid = str(obj.get("uid",""))
            d   = obj.get("dir","")
            if uid and d in ORDER:
                vehicles[uid] = {"dir": d, "last": now}
        except Exception:
            pass

def counts_from_db(now):
    counts = {d:0 for d in ORDER}
    drop = []
    for uid, rec in list(vehicles.items()):
        if (now - rec["last"]) <= HB_TTL:
            counts[rec["dir"]] += 1
        else:
            drop.append(uid)
    for uid in drop:
        vehicles.pop(uid, None)
    return counts

def decide_segments(car_counts):
    congested = [d for d in ORDER if car_counts.get(d, 0) >= CAR_THRESH]
    if len(congested) == 1:
        seg = {d: (8 if d in congested else 4) for d in ORDER}
    else:
        seg = {d: 5 for d in ORDER}
    assert sum(seg.values()) == TOTAL
    return seg, congested

def build_timeline(segments):
    tl, t = [], TOTAL
    for d in ORDER:
        L = segments[d]
        tl.append((d, L, t-L+1, t))  # (dir, len, start, end)
        t -= L
    return tl

def pack_payload(tl, t_now, segments, car_counts):
    dirs = {}
    for d, L, start, end in tl:
        if start <= t_now <= end:
            dirs[d] = {"phase":"GREEN", "t_rem": end - t_now + 1, "g_dur": L, "cars": car_counts.get(d,0)}
        else:
            t_to_start = start - t_now
            if t_to_start <= 0:
                t_to_start += TOTAL
            dirs[d] = {"phase":"RED", "t_rem": t_to_start, "g_dur": L, "cars": car_counts.get(d,0)}
    return {"src":"central_hb_v1", "schema":1, "total":TOTAL, "order":ORDER, "directions":dirs}

# ===== 내 방향 상태 + “표시용 남은 시간” (역카운트) =====
def mydir_state_and_time(tl, t_now, my_dir, total=TOTAL):
    """
    반환: (state, seconds)
      - GREEN이면 seconds = GREEN 남은 시간
      - YELLOW(마지막 1초) / RED이면 seconds = 다음 GREEN까지 대기 시간(역카운트)
    """
    seg = next((x for x in tl if x[0] == my_dir), None)
    if not seg:
        return "RED", None
    _, L, start, end = seg

    # 내 GREEN 구간
    if start <= t_now <= end:
        g_left = end - t_now + 1
        if g_left == 1:
            # ← (버그 수정) YELLOW에서도 다음 GREEN까지 '대기 시간'을 계산해서 표시
            t_to_start = start - t_now
            if t_to_start <= 0:
                t_to_start += total
            return "YELLOW", t_to_start
        else:
            return "GREEN", g_left

    # RED 구간: 다음 GREEN까지 대기
    t_to_start = start - t_now
    if t_to_start <= 0:
        t_to_start += total
    return "RED", t_to_start


# ---- 메인 루프 ----
traffic_light = TrafficLight()
cycle = 0
try:
    while True:
        now = time.time()
        pump_hb(now)
        car_counts = counts_from_db(now)
        segments, congested = decide_segments(car_counts)
        print(f"[cycle {cycle}] counts={car_counts} congested={congested} segments={segments}")

        tl = build_timeline(segments)
        for t_now in range(TOTAL, 0, -1):
            now = time.time()
            pump_hb(now)
            car_counts = counts_from_db(now)

            # 내 방향 LED + 남은 시간 역카운트 출력
            st, sec = mydir_state_and_time(tl, t_now, MY_DIR, TOTAL)
            traffic_light.set_state(st)
            # 콘솔 숫자 역카운트(요청사항)
            if st == "GREEN":
                print(f"[{MY_DIR}] GREEN  남은시간: {sec:2d}s")
            elif st == "YELLOW":
                print(f"[{MY_DIR}] YELLOW 다음 GREEN까지: {sec:2d}s")
            else:
                print(f"[{MY_DIR}] RED    다음 GREEN까지: {sec:2d}s")

            payload = pack_payload(tl, t_now, segments, car_counts)
            bcast.sendto(json.dumps(payload).encode(), (BCAST_IP, BCAST_PORT))
            time.sleep(1)

        cycle += 1
finally:
    traffic_light.close()
