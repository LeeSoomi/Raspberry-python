from collections import defaultdict, deque
import time, json, os, re

# ===== 한 방향 고정 =====
TARGET_DIR = "N"                          # "N","E","S","W"
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간 설정 =====
G_FIXED = 8                               # GREEN은 항상 8초
YELLOW  = 2
ALL_RED = 1

# 인식 안정화(윈도우/히트)
WINDOW_SEC = 4.0                          # 최근 윈도우(초)
MIN_HITS   = 2                            # 같은 UID가 윈도우 내 최소 히트 수

# ACK 요청 정책
ALWAYS_ACK = True                         # 모든 상태에서 Q=1로 광고

# ===== 차량 이름 레지스트리 =====
REG_PATH = "car_names.json"
IDX_PAT  = re.compile(r"차량\s*(\d+)")

def load_registry(path=REG_PATH):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict): return data
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
    def __init__(self): self.buf = deque()  # (t, dir, uid6hex)
    def push(self, direction, uid_hex): self.buf.append((time.time(), direction, uid_hex.upper()))
    def _recent(self, window=WINDOW_SEC):
        now = time.time()
        return [(t,d,u) for (t,d,u) in list(self.buf) if now - t <= window]
    def recent_uid_hits(self, window=WINDOW_SEC):
        rec = self._recent(window)
        hits = defaultdict(lambda: defaultdict(int))   # hits[dir][uid] = count
        for _, d, u in rec: hits[d][u] += 1
        return hits

# ===== 콘솔 브로드캐스터(시뮬) =====
class Broadcaster:
    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

# ===== 컨트롤러 =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"           # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_FIXED
        self.registry = load_registry()

    def _valid_uids(self):
        hits_by_dir = self.bus.recent_uid_hits(WINDOW_SEC)
        my_hits = hits_by_dir.get(self.dir, {})
        valid = sorted([u for u,h in my_hits.items() if h >= MIN_HITS])
        return valid, my_hits

    def start_green(self):
        self.g_alloc = G_FIXED         # ✅ 항상 8초
        self.rt = self.g_alloc

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED";    self.rt = ALL_RED
        else:
            self.state = "GREEN";  self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()

        # 표시/광고용 집계
        valid, hits = self._valid_uids()
        q = len(valid)
        names_str = ", ".join([name_for_uid(u, self.registry) for u in valid]) or "-"

        # 광고(차량이 RT를 받도록 항상 송신)
        ph = PHASE_MAP[self.dir]
        q_flag = True if ALWAYS_ACK else (self.state == "GREEN")
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, q_flag)

        # 콘솔 표시: 상태 + 남은시간 + 대수 + 이름
        print(f"{self.state:<6} RT:{self.rt}s  cars:{q}  names:[{names_str}]")

        self.rt -= 1

def run_sim():
    ctrl = Controller()
    # --- 데모 트래픽: 실제 Pico에서는 central_scan → bus.push 로 대체 ---
    demo_uids = ["B3C827","3F06FE","CA8756"]  # 예시 3대
    while True:
        # ★ 실제 상황처럼 매초 모든 차량이 동시에 ACK
        for uid in demo_uids:
            ctrl.bus.push(TARGET_DIR, uid)
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim()
