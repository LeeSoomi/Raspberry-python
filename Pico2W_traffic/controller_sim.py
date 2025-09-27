# controller_sim_single.py
from collections import defaultdict, deque
import time, json, os

# ===== 단일 방향 고정 =====
TARGET_DIR = "N"  # ← 내 쪽(고정) 방향: "N","E","S","W"
PHASE_MAP = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간/판정 설정 =====
G_BASE = 5       # 기본 녹색
G_EXT  = 8       # 혼잡(≥3대) 녹색
YELLOW = 2
ALL_RED = 1
G_MIN, G_MAX = 4, 10

# 3대 판정을 위한 집계 방식
COUNT_MODE = "uid"     # "uid" | "message"  (uid: 고유차량수, message: 메시지수)
WINDOW_SEC = 4.0       # 최근 윈도우(초). 2.0→4.0으로 넉넉히

# ===== 차량 이름 로드 (선택) =====
def load_car_names(path="car_names.json"):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)  # {"A1":"은우카", "B2":"나래카", ...}
    except Exception as e:
        print("[WARN] car_names.json 로드 실패:", e)
    return {}  # 없으면 UID 그대로 표시

CAR_NAME = load_car_names()

def uid_to_name(uid: str) -> str:
    return CAR_NAME.get(uid, uid)

def pretty_names(uids):
    # ["A1","B2"] -> "은우카(A1), 나래카(B2)" 식의 문자열
    return ", ".join([f"{uid_to_name(u)}({u})" for u in uids]) if uids else "-"

# ===== ACK 버스 =====
class AckBus:
    def __init__(self):
        self.buf = deque()  # (t, direction, uid)

    def push(self, direction, uid):
        self.buf.append((time.time(), direction, uid))

    def _recent(self, window=WINDOW_SEC):
        now = time.time()
        return [(t,d,u) for (t,d,u) in list(self.buf) if now - t <= window]

    def recent_uid_sets_and_msg_counts(self, window=WINDOW_SEC):
        rec = self._recent(window)
        uid_sets = defaultdict(set)
        msg_cnts = defaultdict(int)
        for _, d, u in rec:
            uid_sets[d].add(u)
            msg_cnts[d] += 1
        return uid_sets, msg_cnts

# ===== 브로드캐스터(시뮬 콘솔) =====
class Broadcaster:
    def advertise(self, ph, state, rt, g_for_dir, q_flag, dir_letter):
        msg = f"PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g_for_dir}|Q:{int(q_flag)}"
        print("[ADV]", msg)

# ===== 컨트롤러 =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR
        self.state = "GREEN"   # GREEN -> YELLOW -> RED
        self.rt = 0
        self.g_alloc = G_BASE

    def start_green(self):
        uid_sets, msg_cnts = self.bus.recent_uid_sets_and_msg_counts()
        # 현재 방향 기준으로 3대 판정
        if COUNT_MODE == "message":
            q = msg_cnts.get(self.dir, 0)
        else:
            q = len(uid_sets.get(self.dir, set()))
        g = G_EXT if q >= 3 else G_BASE
        self.g_alloc = max(G_MIN, min(G_MAX, g))
        self.rt = self.g_alloc

        # DBG + 내 방향 인식 차량 목록 출력
        names_str = pretty_names(sorted(uid_sets.get(self.dir, set())))
        print(f"[DBG] q={q}, mode={COUNT_MODE}, window={WINDOW_SEC}s, dir={self.dir}, G={self.g_alloc}, cars=[{names_str}]")

    def next_phase(self):
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "RED"; self.rt = ALL_RED
        else:  # RED → 같은 방향 GREEN 재시작
            self.state = "GREEN"; self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()
        ph = PHASE_MAP[self.dir]
        q_flag = (self.state == "GREEN")  # GREEN일 때만 ACK 요청
        self.bc.advertise(ph, self.state, self.rt, self.g_alloc, q_flag, self.dir)
        self.rt -= 1

def run_sim():
    ctrl = Controller()

    # ==== 데모 트래픽 ====
    # 아래를 실제 ACK 수신으로 대체하면 실 Pico에서도 동일 표시됨.
    demo_uids = ["A1","B2"]       # 2대 테스트(기본 5초)
    # demo_uids = ["A1","B2","C3"] # 3대 테스트(확장 8초)

    while True:
        for uid in demo_uids:
            ctrl.bus.push(TARGET_DIR, uid)
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim()


-----------------

car_names.json
{
  "A1": "은우카",
  "B2": "나래카",
  "C3": "하람카",
  "E1": "동쪽카"
}
