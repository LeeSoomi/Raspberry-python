from collections import deque
import time, json, os, re

# ===== 고정 방향 =====
TARGET_DIR = "N"                          # "N","E","S","W"
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간/판정 =====
G_BASE, G_EXT = 5, 8                      # 기본 5초, (대기 15초에 ≥3대)면 8초
YELLOW, ALL_RED = 2, 13                   # 합계 15초 대기
DECISION_WINDOW_SEC = 15.0                # 바로 지난 대기 15초만 집계

# ===== 차량 이름 레지스트리 =====
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

# ===== ACK 버스 =====
class AckBus:
    """(t, dir, uid6) 저장. 최근 15초 고유 UID 집계."""
    def __init__(self): self.buf = deque()
    def push(self, direction, uid_hex): self.buf.append((time.time(), direction, uid_hex.upper()))
    def recent_uids(self, direction, window_sec):
        now = time.time()
        return {
            u for (t, d, u) in list(self.buf)
            if d == direction and (now - t) <= window_sec
        }

# ===== 브로드캐스터(시뮬 콘솔) =====
class Broadcaster:
    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

# ===== 컨트롤러 =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"              # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_BASE
        self.registry = _load_reg()

    def _current_window_uids(self):
        return self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)

    def start_green(self):
        # 직전 대기 15초 동안 들어온 고유 차량으로 다음 GREEN 결정
        uids = self._current_window_uids()
        self.g_alloc = G_EXT if len(uids) >= 3 else G_BASE
        self.rt = self.g_alloc
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"[DBG] wait=15s cars={len(uids)} nextG={self.g_alloc} names=[{names}]")

    def next_phase(self):
        if self.state == "GREEN":
            self.state, self.rt = "YELLOW", YELLOW
        elif self.state == "YELLOW":
            self.state, self.rt = "RED", ALL_RED
        else:  # RED → 같은 방향 GREEN
            self.state = "GREEN"
            self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()

        # 대기(YELLOW/RED)에서만 ACK 요청(Q=1) → 차량이 그때 1Hz로 응답
        ph = PHASE_MAP[self.dir]
        q_flag = (self.state != "GREEN")
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, q_flag)

        # 표시: 상태/남은시간/대수/이름(현재 창에 들어온 차량만)
        uids = self._current_window_uids()
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"{self.state:<6} RT:{self.rt}s  cars:{len(uids)}  names:[{names}]")

        self.rt -= 1

def run_sim():
    ctrl = Controller()
    # === 데모: 대기일 때 모든 차량이 1Hz 동시 ACK (실사용 시 central에서 push) ===
    demo_uids = ["B3C827","3F06FE","CA8756"]  # 필요 시 실 UID로 교체
    while True:
        ctrl.tick()
        if ctrl.state != "GREEN":  # 대기 15초 동안만 ACK 발생
            for uid in demo_uids:
                ctrl.bus.push(TARGET_DIR, uid)
        time.sleep(1)

if __name__ == "__main__":
    run_sim()


---------------------------

car_names.json
{
  "B3C827": "C  차량1  UID3=B3C827",
  "3F06FE": "C  차량2  UID3=3F06FE",
  "CA8756": "C  차량3  UID3=CA8756"
}

