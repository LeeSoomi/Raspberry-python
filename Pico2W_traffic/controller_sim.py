# controller_sim.py
from collections import deque
import time, json, os, re, threading
import central_scan  # ← 당신의 스캐너를 import

TARGET_DIR = "N"                          # 내 쪽 방향 고정
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# 시간/판정
G_BASE, G_EXT = 5, 8                      # 기본 5초, (대기15초 ≥3대)면 8초
YELLOW, ALL_RED = 2, 13                   # 합계 15초 대기
DECISION_WINDOW_SEC = 15.0                # 지난 대기창 15초

# 이름 레지스트리
REG_PATH = "car_names.json"
IDX_PAT  = re.compile(r"차량\s*(\d+)")

def _load_reg():
    if os.path.exists(REG_PATH):
        try:
            with open(REG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
        except: pass
    return {}

def _next_idx(reg):
    mx = 0
    for name in reg.values():
        m = IDX_PAT.search(name)
        if m:
            try: mx = max(mx, int(m.group(1)))
            except: pass
    return mx + 1

def name_for_uid(uid_hex, reg):
    uid_hex = uid_hex.upper()
    if uid_hex in reg: return reg[uid_hex]
    idx = _next_idx(reg)
    label = f"C  차량{idx}  UID3={uid_hex}"
    reg[uid_hex] = label
    try:
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=2)
    except: pass
    return label

class AckBus:
    """스레드 안전하게 ACK를 저장/집계"""
    def __init__(self):
        self.buf = deque()            # (t, dir, uid6)
        self.lock = threading.Lock()

    def push(self, direction, uid_hex):
        t = time.time()
        uid_hex = uid_hex.upper()
        with self.lock:
            self.buf.append((t, direction, uid_hex))

    def recent_uids(self, direction, window_sec):
        now = time.time()
        cut = now - window_sec - 1.0
        with self.lock:
            # 오래된 항목 제거
            while self.buf and self.buf[0][0] < cut:
                self.buf.popleft()
            # 집계
            return {
                u for (t, d, u) in self.buf
                if d == direction and (now - t) <= window_sec
            }

class Broadcaster:
    """(시뮬) 광고 출력 — 실제 BLE 광고로 교체 지점"""
    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"          # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_BASE
        self.registry = _load_reg()
        self.accept_acks = False      # 대기 구간에서만 True

    # central_scan에서 호출
    def on_car_seen(self, direction, uid_hex):
        if direction != self.dir:        # 다른 방향은 무시
            return
        if not self.accept_acks:         # GREEN 동안은 무시
            return
        self.bus.push(direction, uid_hex)

    def _window_uids(self):
        return self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)

    def start_green(self):
        # 지난 대기 15초의 고유 UID로 다음 GREEN 결정
        uids = self._window_uids()
        self.g_alloc = G_EXT if len(uids) >= 3 else G_BASE
        self.rt = self.g_alloc
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"[DBG] wait=15s cars={len(uids)} nextG={self.g_alloc} names=[{names}]")

    def next_phase(self):
        if self.state == "GREEN":
            self.state, self.rt = "YELLOW", YELLOW
        elif self.state == "YELLOW":
            self.state, self.rt = "RED", ALL_RED
        else:
            self.state = "GREEN"; self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()

        # 대기 구간에서만 ACK 허용(Q=1)
        self.accept_acks = (self.state != "GREEN")
        ph = PHASE_MAP[self.dir]
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, self.accept_acks)

        # 표시
        uids = self._window_uids()
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"{self.state:<6} RT:{self.rt}s  cars:{len(uids)}  names:[{names}]")

        self.rt -= 1

def run():
    ctrl = Controller()
    # ★ central_scan 스레드 시작 — 차량 인식 즉시 ctrl.on_car_seen 호출
    central_scan.start_scan(ctrl.on_car_seen, target_dir=TARGET_DIR)

    while True:
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run()

---------------------------

car_names.json
{
  "B3C827": "C  차량1  UID3=B3C827",
  "3F06FE": "C  차량2  UID3=3F06FE",
  "CA8756": "C  차량3  UID3=CA8756"
}

