# 한번만 설치
# sudo apt-get update
# sudo apt-get install -y python3-gpiozero
# ------------------

# 실행 sudo python3 central_traffic_with_hb_LED.py
# ----------------------------------

# central_traffic_with_hb.py  (Raspberry Pi 5 / Python 3)
import socket, json, time
import os

# ===== 추가: 내 방향 / LED 핀팩토리 기본값 =====
MY_DIR = os.environ.get("MY_DIR", "N")          # 내 방향: N/E/S/W
os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

# ===== 추가: 물리 LED (BCM 핀) =====
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
        """state in {'GREEN','YELLOW','RED'}"""
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
BCAST_IP, BCAST_PORT = "255.255.255.255", 5005  # 신호 브로드캐스트
HB_PORT = 5006                                   # 하트비트 수신
TOTAL = 20
ORDER = ["N","E","S","W"]
CAR_THRESH = 3        # 3대 이상이면 혼잡
HB_TTL = 3.5          # 최근 3.5초 내 하트비트만 유효

# ---- 소켓 준비 ----
bcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

hb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hb.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
hb.bind(("0.0.0.0", HB_PORT))
hb.setblocking(False)

# ---- 차량 DB(uid -> {dir,last}) ----
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
            uid = str(obj.get("uid",""))
            d   = obj.get("dir","")
            if uid and d in ORDER:
                vehicles[uid] = {"dir": d, "last": now}
        except Exception:
            pass  # 이상 패킷 무시

def counts_from_db(now):
    """TTL 내 차량만 집계하고, 오래된 항목은 제거"""
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
    """정책: 단 1방향만 혼잡이면 8/4/4/4, 그 외는 5/5/5/5"""
    congested = [d for d in ORDER if car_counts.get(d, 0) >= CAR_THRESH]
    if len(congested) == 1:
        seg = {d: (8 if d in congested else 4) for d in ORDER}
    else:
        seg = {d: 5 for d in ORDER}
    assert sum(seg.values()) == TOTAL
    return seg, congested

def build_timeline(segments):
    """20..1 카운트다운 윈도우에 각 방향 슬롯 배치"""
    tl, t = [], TOTAL
    for d in ORDER:
        L = segments[d]
        tl.append((d, L, t-L+1, t))  # (dir, len, start, end)
        t -= L
    return tl

def pack_payload(tl, t_now, segments, car_counts):
    """현재 시각 t_now에 대한 directions 패키징 (원본 포맷 유지)"""
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

# ===== 추가: 내 방향 LED 상태 계산(마지막 1초는 YELLOW) =====
def mydir_led_state(tl, t_now, my_dir, total=TOTAL):
    seg = next((x for x in tl if x[0] == my_dir), None)
    if not seg:
        return "RED"
    _, L, start, end = seg
    if start <= t_now <= end:
        g_left = end - t_now + 1
        return "YELLOW" if g_left == 1 else "GREEN"
    return "RED"

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
            pump_hb(now)                   # 주기 중에도 수신/만료 갱신
            car_counts = counts_from_db(now)

            # ===== 추가: 내 방향만 LED 표시 =====
            traffic_light.set_state(mydir_led_state(tl, t_now, MY_DIR))

            payload = pack_payload(tl, t_now, segments, car_counts)
            bcast.sendto(json.dumps(payload).encode(), (BCAST_IP, BCAST_PORT))
            time.sleep(1)

        cycle += 1
finally:
    traffic_light.close()
