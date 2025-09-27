# controller_sim.py
from collections import defaultdict, deque
import time

DIRECTIONS = ["N","E","S","W"]
PHASE_MAP = {"N":"NS", "S":"NS", "E":"EW", "W":"EW"}
G_BASE, G_EXT = 5, 7
YELLOW, ALL_RED = 2, 1
G_MIN, G_MAX = 4, 10

class AckBus:
    """실 BLE 대신 메모리 큐로 수신 ACK를 시뮬레이션"""
    def __init__(self): self.buf = deque()
    def push(self, direction, uid): self.buf.append((time.time(), direction, uid))
    def drain_recent_uids(self, window=2.0):
        now = time.time()
        recent = [(t,d,u) for (t,d,u) in list(self.buf) if now - t <= window]
        uniq = defaultdict(set)
        for _, d, u in recent: uniq[d].add(u)
        return {d: len(s) for d,s in uniq.items()}

class Broadcaster:
    def __init__(self): self.last_adv = None
    def advertise(self, ph, state, rt, g_for_dir, q_flag):
        # 실 BLE 광고 대신 콘솔 문자열로 대체 (형식 고정)
        msg = f"PH:{ph}|T:{state}|RT:{rt}|G:{g_for_dir}|Q:{int(q_flag)}"
        self.last_adv = msg
        print("[ADV]", msg)

class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.phase_idx = 0
        self.state = "GREEN"   # GREEN -> YELLOW -> RED(all-red)
        self.rt = 0
        self.current_dir = DIRECTIONS[self.phase_idx]
        self.g_alloc = G_BASE

    def decide_green(self, qcount):
        q = qcount.get(self.current_dir, 0)
        g = G_EXT if q >= 3 else G_BASE
        return max(G_MIN, min(G_MAX, g))

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED"; self.rt = ALL_RED
        else:  # RED -> 다음 방향 GREEN 시작
            self.phase_idx = (self.phase_idx + 1) % 4
            self.current_dir = DIRECTIONS[self.phase_idx]
            qcount = self.bus.drain_recent_uids()
            self.g_alloc = self.decide_green(qcount)
            self.state = "GREEN"; self.rt = self.g_alloc

    def tick(self):
        if self.rt <= 0: self.next_phase()
        ph = PHASE_MAP[self.current_dir]
        q_flag = (self.state == "GREEN")  # GREEN 동안에만 ACK 요구
        self.bc.advertise(ph, self.state, self.rt, self.g_alloc, q_flag)
        self.rt -= 1

def run_sim(total_seconds=60):
    ctrl = Controller()
    # 데모용: 가짜 차량 UID들이 N방향에 몰리는 상황 주입
    demo_uids = ["A1","B2","C3"]
    t0 = time.time()
    while time.time() - t0 < total_seconds:
        # 데모: 매초 N방향에서 3대가 ACK 보낸다고 가정
        for uid in demo_uids:
            ctrl.bus.push("N", uid)
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim(45)
