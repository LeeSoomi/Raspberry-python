# controller_sim.py
from collections import defaultdict, deque
import time

DIRECTIONS = ["N","E","S","W"]
PHASE_MAP = {"N":"NS", "S":"NS", "E":"EW", "W":"EW"}

# 기본/확장 시간
G_BASE = 5          # 기본 녹색
G_EXT  = 8          # 혼잡 방향(>=3대) 녹색: 8초로 상향
YELLOW = 2
ALL_RED = 1
G_MIN, G_MAX = 4, 10

class AckBus:
    """실 BLE 대신 메모리 큐로 수신 ACK를 시뮬레이션"""
    def __init__(self):
        self.buf = deque()

    def push(self, direction, uid):
        self.buf.append((time.time(), direction, uid))

    def drain_recent_uids(self, window=2.0):
        """최근 window초 안의 ACK를 방향별 유니크 UID 수로 집계"""
        now = time.time()
        recent = [(t,d,u) for (t,d,u) in list(self.buf) if now - t <= window]
        uniq = defaultdict(set)
        for _, d, u in recent:
            uniq[d].add(u)
        return {d: len(s) for d, s in uniq.items()}

class Broadcaster:
    def __init__(self):
        self.last_adv = None
    def advertise(self, ph, state, rt, g_for_dir, q_flag):
        msg = f"PH:{ph}|T:{state}|RT:{rt}|G:{g_for_dir}|Q:{int(q_flag)}"
        self.last_adv = msg
        print("[ADV]", msg)

class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.phase_idx = 0
        self.state = "GREEN"   # GREEN -> YELLOW -> RED
        self.current_dir = DIRECTIONS[self.phase_idx]
        self.rt = 0
        self.g_alloc = G_BASE
        # ✅ 차감/가산 예약(다음 해당 방향 GREEN 때 반영)
        self.adjust = {d: 0 for d in DIRECTIONS}
        self.last_donor = None

    def choose_donor(self, qcount, current_dir):
        """혼잡 방향을 8초로 늘릴 때, 1초를 빼올 방향 선택(가장 한산한 방향)"""
        candidates = [d for d in DIRECTIONS if d != current_dir]
        candidates.sort(key=lambda d: (qcount.get(d, 0), DIRECTIONS.index(d)))
        return candidates[0]

    def start_green(self):
        # 최근 2초간 ACK 집계
        qcount = self.bus.drain_recent_uids()
        q = qcount.get(self.current_dir, 0)

        # 기본 결정: 혼잡이면 8초, 아니면 5초
        base_g = G_EXT if q >= 3 else G_BASE

        # 이전에 예약된 가감 반영(최소/최대 클램프)
        g = max(G_MIN, min(G_MAX, base_g + self.adjust[self.current_dir]))
        self.adjust[self.current_dir] = 0  # 소진

        # 혼잡으로 8초를 썼다면, 다른 방향 한 곳에서 1초 빼오도록 예약
        self.last_donor = None
        if base_g == G_EXT:
            donor = self.choose_donor(qcount, self.current_dir)
            self.adjust[donor] -= 1
            self.last_donor = donor

        self.g_alloc = g
        self.rt = self.g_alloc

        # ✅ 요청하신 DBG 로그
        print(f"[DBG] qcount={qcount}, dir={self.current_dir}, donor={self.last_donor}, G={self.g_alloc}")

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED"; self.rt = ALL_RED
        else:  # RED 끝 → 다음 방향 GREEN 시작
            self.phase_idx = (self.phase_idx + 1) % 4
            self.current_dir = DIRECTIONS[self.phase_idx]
            self.state = "GREEN"
            self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()
        ph = PHASE_MAP[self.current_dir]
        q_flag = (self.state == "GREEN")  # GREEN 때만 차량 ACK 요청
        self.bc.advertise(ph, self.state, self.rt, self.g_alloc, q_flag)
        self.rt -= 1

def run_sim():
    ctrl = Controller()
    demo_n = ["A1","B2","C3"]
    demo_e = ["E1"]

    while True:
        # 데모 트래픽 (원하면 자유롭게 수정)
        for uid in demo_n:
            ctrl.bus.push("N", uid)
        # 2초마다 E에서 1대
        if int(time.time()) % 2 == 0:
            ctrl.bus.push("E", demo_e[0])

        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim()  
