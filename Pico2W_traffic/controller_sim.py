# controller_sim_single.py
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

# 출력 모드
SHOW_ONLY_WAIT = True                    # True면 대기(YELLOW/RED)에서만 출력
SHOW_NAMES     = False                   # 이름/UID 표시는 숨김(요청사항 반영)

def icon(s): return {"GREEN":"🟩","YELLOW":"🟨","RED":"🟥"}.get(s, "⬜")

# ===== ACK 버스 =====
class AckBus:
    def __init__(self): self.buf = deque()  # (t, dir, uid)
    def push(self, direction, uid_hex): self.buf.append((time.time(), direction, uid_hex.upper()))
    def _recent(self, window=WINDOW_SEC):
        now=time.time()
        return [(t,d,u) for (t,d,u) in list(self.buf) if now-t<=window]
    def recent_uid_hits(self, window=WINDOW_SEC):
        rec=self._recent(window)
        hits=defaultdict(lambda: defaultdict(int))  # hits[dir][uid]=count
        for _,d,u in rec: hits[d][u]+=1
        return hits

# ===== 컨트롤러 =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
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
        # 실시간 대수(대기시간 동안 보여줄 값)
        q_live = self._count_valid()
        # 출력: 대기(YELLOW/RED)에서만 or 항상
        if (self.state != "GREEN") if SHOW_ONLY_WAIT else True:
            print(f"{icon(self.state)} {self.state:<6}  RT:{self.rt}s  cars:{q_live}")
        # 다음 초로
        self.rt -= 1

def run_sim():
    ctrl = Controller()
    # --- 데모 트래픽(실사용 시 central_scan에서 push 호출) ---
    demo_uids = ["B3C827","3F06FE","CA8756"]  # 세 대 예시
    k=0
    while True:
        k+=1
        # 1초마다 순차로 한 대씩 들어오는 상황(히트 조건 만족)
        ctrl.bus.push(TARGET_DIR, demo_uids[k % len(demo_uids)])
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run_sim()
