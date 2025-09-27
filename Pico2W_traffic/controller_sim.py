from collections import defaultdict, deque
import time

# ===== 한 방향 고정 =====
TARGET_DIR = "N"                          # "N","E","S","W"
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간/판정 =====
G_BASE = 5
G_EXT  = 8
YELLOW = 2
ALL_RED= 1
G_MIN, G_MAX = 4, 10

# 인식 안정화(필요시 조절)
WINDOW_SEC = 4.0                         # 최근 윈도우(초)
MIN_HITS   = 2                           # 같은 UID가 윈도우 내 최소 히트 수

# ACK 요청 정책
ALWAYS_ACK = True                        # True면 GREEN/YELLOW/RED 모두 Q=1

class AckBus:
    def __init__(self): self.buf = deque()         # (t, dir, uid)
    def push(self, direction, uid_hex): self.buf.append((time.time(), direction, uid_hex.upper()))
    def _recent(self, window=WINDOW_SEC):
        now=time.time()
        return [(t,d,u) for (t,d,u) in list(self.buf) if now-t<=window]
    def recent_uid_hits(self, window=WINDOW_SEC):
        rec=self._recent(window)
        hits=defaultdict(lambda: defaultdict(int))  # hits[dir][uid]=count
        for _,d,u in rec: hits[d][u]+=1
        return hits

class Broadcaster:
    """시뮬 콘솔 광고(실 BLE 교체 지점)"""
    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        # 차량은 여기서 RT를 수신한다고 가정(실 BLE 전환 시 이 부분 교체)
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"           # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_BASE

    def _count_valid(self):
        hits_by_dir = self.bus.recent_uid_hits(WINDOW_SEC)
        my_hits = hits_by_dir.get(self.dir, {})
        valid = [u for u,h in my_hits.items() if h >= MIN_HITS]
        return len(valid)

    def start_green(self):
        q = self._count_valid()
        g = G_EXT if q >= 3 else G_BASE
        self.g_alloc = max(G_MIN, min(G_MAX, g))
        self.rt = self.g_alloc

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED";    self.rt = ALL_RED
        else:                       # RED → 같은 방향 GREEN
            self.state = "GREEN";  self.start_green()

    def tick(self):
        if self.rt <= 0: self.next_phase()

        # 실시간 집계(표시용)
        q_live = self._count_valid()

        # 광고(차량이 RT를 계속 받도록 1초마다 방송)
        ph = PHASE_MAP[self.dir]
        q_flag = True if ALWAYS_ACK else (self.state == "GREEN")
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, q_flag)

        # 콘솔 표시: 모든 상태 출력(GREEN 포함)
        print(f"{self.state:<6}  RT:{self.rt}s  cars:{q_live}")

        self.rt -= 1

def run_sim():
    ctrl = Controller()
    # --- 데모 트래픽(실사용 시 central_scan에서 push 호출) ---
    demo_uids = ["B3C827","3F06FE","CA8756"]  # 예시 3대
    k=0
    while True:
        k+=1
        # 1초마다 순차로 한 대씩 들어오는 상황(히트 조건 만족)
        ctrl.bus.push(TARGET_DIR, demo_uids[k % len(demo_uids)])
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim()
