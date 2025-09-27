from collections import defaultdict, deque
import time, json, os, re

# ===== 한 방향 고정 =====
TARGET_DIR = "N"                          # "N","E","S","W"
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간/판정 =====
G_BASE = 5
G_EXT  = 8                                # 대기 15초 동안 ≥3대면 다음 GREEN을 8초로
YELLOW = 2
ALL_RED= 1
DECISION_WINDOW_SEC = 15.0                # ← '대기시간' 창

# 이름 레지스트리 저장 파일
REG_PATH = "car_names.json"
IDX_PAT  = re.compile(r"차량\s*(\d+)")

def load_registry():
    if os.path.exists(REG_PATH):
        try:
            with open(REG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print("[WARN] car_names.json 로드 실패:", e)
    return {}   # {"B3C827": "C  차량1  UID3=B3C827", ...}

def next_index(reg):
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
    idx = next_index(reg)
    label = f"C  차량{idx}  UID3={uid_hex}"
    reg[uid_hex] = label
    try:
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[WARN] car_names.json 저장 실패:", e)
    return label

# ===== ACK 버스 =====
class AckBus:
    """대기 구간에서 들어온 ACK를 버퍼에 저장 (t, dir, uid)"""
    def __init__(self): self.buf = deque()

    def push(self, direction, uid_hex):
        self.buf.append((time.time(), direction, uid_hex.upper()))

    def recent_uids(self, direction, window_sec):
        """최근 window_sec 내에 들어온 고유 UID 집합(해당 방향만)"""
        now = time.time()
        return {
            u for (t, d, u) in list(self.buf)
            if d == direction and (now - t) <= window_sec
        }

# ===== 콘솔 광고(시뮬) =====
class Broadcaster:
    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        # 차량은 여기서 RT/G/Q를 수신한다고 가정 (실 BLE로 교체 가능)
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

# ===== 컨트롤러 =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"           # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_BASE
        self.registry = load_registry()

    def start_green(self):
        # 지난 '대기 15초' 동안 들어온 고유 차량으로 다음 GREEN 결정
        uids = self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)
        q = len(uids)
        self.g_alloc = G_EXT if q >= 3 else G_BASE
        self.rt = self.g_alloc

        # 보기 좋게 이름도 출력
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"[DBG] wait_window={DECISION_WINDOW_SEC:.0f}s, cars={q}, nextG={self.g_alloc}, names=[{names}]")

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED";    self.rt = ALL_RED
        else:                       # RED → 같은 방향 GREEN
            self.state = "GREEN";  self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()

        # 대기(노란/빨간) 동안에만 차량들이 ACK 보내게 Q=1
        ph = PHASE_MAP[self.dir]
        q_flag = (self.state != "GREEN")
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, q_flag)

        # 표시는 상태/남은 시간/대수/이름
        uids = self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)
        q = len(uids)
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"{self.state:<6} RT:{self.rt}s  cars:{q}  names:[{names}]")

        self.rt -= 1

def run_sim():
    ctrl = Controller()

    # === 데모 트래픽 (실 Pico 사용 시 central_scan → ctrl.bus.push 로 대체) ===
    demo_uids = ["B3C827","3F06FE","CA8756"]  # 3대 예시

    while True:
        # 실제처럼 'Q=1일 때 모든 차량이 동시에 1Hz ACK'를 가정
        # (tick 내부에서 상태/RT와 Q가 결정되므로, tick 후에 push)
        ctrl.tick()
        if ctrl.state != "GREEN":                 # 대기 구간에만 ACK 발생
            for uid in demo_uids:
                ctrl.bus.push(TARGET_DIR, uid)
        time.sleep(1)

if __name__ == "__main__":
    run_sim()
