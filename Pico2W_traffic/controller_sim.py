from collections import defaultdict, deque
import time

# ===== 단일 방향 고정 =====
TARGET_DIR = "N"               # ← 여기만 바꾸면 됩니다: "N","E","S","W"
PHASE_MAP = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간 설정 =====
G_BASE = 5     # 기본 녹색
G_EXT  = 8     # 혼잡(≥3대) 녹색
YELLOW = 2
ALL_RED = 1
G_MIN, G_MAX = 4, 10

class AckBus:
    def __init__(self): self.buf = deque()
    def push(self, direction, uid): self.buf.append((time.time(), direction, uid))
    def drain_recent_uids(self, window=2.0):
        now = time.time()
        recent = [(t,d,u) for (t,d,u) in list(self.buf) if now - t <= window]
        uniq = defaultdict(set)
        for _, d, u in recent: uniq[d].add(u)
        return {d: len(s) for d, s in uniq.items()}

class Broadcaster:
    def advertise(self, ph, state, rt, g_for_dir, q_flag, dir_letter):
        msg = f"PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g_for_dir}|Q:{int(q_flag)}"
        print("[ADV]", msg)

class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"   # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_BASE

    def start_green(self):
        qcount = self.bus.drain_recent_uids()
        q = qcount.get(self.dir, 0)
        g = G_EXT if q >= 3 else G_BASE
        self.g_alloc = max(G_MIN, min(G_MAX, g))
        self.rt = self.g_alloc
        # DBG 로그
        print(f"[DBG] qcount={qcount}, dir={self.dir}, G={self.g_alloc}")

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED"; self.rt = ALL_RED
        else:  # RED 끝 → 같은 방향 GREEN 재시작
            self.state = "GREEN"; self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()
        ph = PHASE_MAP[self.dir]
        q_flag = (self.state == "GREEN")  # GREEN 동안 ACK 요청
        self.bc.advertise(ph, self.state, self.rt, self.g_alloc, q_flag, self.dir)
        self.rt -= 1

def run_sim():
    ctrl = Controller()
    # --- 데모 트래픽: 여기서 차량 대수를 원하는 만큼 주입 ---
    demo_uids = ["A1","B2"]     # ← 2대로 테스트 (8초 안 나옴)
    # demo_uids = ["A1","B2","C3"]  # ← 3대로 테스트 (8초 나옴)

    while True:
        for uid in demo_uids:
            ctrl.bus.push(TARGET_DIR, uid)
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim()
