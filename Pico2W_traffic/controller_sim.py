# controller_sim.py (핵심 부분만, 나머지는 이전 버전 그대로)
import time, threading
import central_scan

TARGET_DIR = "N"
DECISION_WINDOW_SEC = 15.0
YELLOW, ALL_RED = 2, 13
G_BASE, G_EXT = 5, 8
PHASE_MAP = {"N":"NS","S":"NS","E":"EW","W":"EW"}

class AckBus:
    def __init__(self):
        self.buf = deque()
        self.lock = threading.Lock()
    def push(self, direction, uid_hex):
        with self.lock:
            self.buf.append((time.time(), direction, uid_hex.upper()))
    def recent_uids(self, direction, window_sec):
        now = time.time()
        cut = now - window_sec - 1.0
        with self.lock:
            while self.buf and self.buf[0][0] < cut:
                self.buf.popleft()
            return {u for (t,d,u) in self.buf if d==direction and (now - t) <= window_sec}

class Controller:
    def __init__(self):
        ...
        self.accept_acks = False

    # ★ central_scan에서 호출
    def on_car_seen(self, direction, uid_hex):
        # 방향이 다르면 무시 (스캐너가 dir 없으면 target_dir로 넣어줌)
        if direction != self.dir: 
            return
        # GREEN 중에는 무시 (대기 중에만 집계)
        if not self.accept_acks:
            return
        self.bus.push(direction, uid_hex)

    def start_green(self):
        uids = self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)
        self.g_alloc = G_EXT if len(uids) >= 3 else G_BASE
        self.rt = self.g_alloc
        ...

    def tick(self):
        if self.rt <= 0: self.next_phase()
        self.accept_acks = (self.state != "GREEN")   # 대기에서만 ACK 허용
        ph = PHASE_MAP[self.dir]
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, self.accept_acks)
        uids = self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"{self.state:<6} RT:{self.rt}s  cars:{len(uids)}  names:[{names}]")
        self.rt -= 1

def run():
    ctrl = Controller()
    # ★ 스캐너 시작 — 발견시 ctrl.on_car_seen 호출
    central_scan.start_scan(ctrl.on_car_seen, target_dir=TARGET_DIR)
    while True:
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run()
