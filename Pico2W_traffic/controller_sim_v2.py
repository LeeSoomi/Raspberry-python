#!/usr/bin/env python3
from collections import deque, defaultdict
import time, json, os, re, threading
import central_scan  # on_seen(direction:str, uid_hex:str) 콜백 호출

# ===== 방향/페이즈 =====
DIRS = ["N", "E", "S", "W"]
PHASE_MAP = {"N":"NS","S":"NS","E":"EW","W":"EW"}  # 광고/표시 용

# ===== 시간/정책 =====
MIN_GREEN = 4
BASE_GREEN = 5
MAX_GREEN = 8
EXTRA_PER_HEAVY = 3          # 혼잡방향 요청(+3초)
YELLOW = 2
ALL_RED = 1                   # 페이즈 전환 클리어타임
DECISION_WINDOW_SEC = 15.0    # 혼잡 판정을 위한 최근 윈도우

# ===== 우대/공정성 파라미터 =====
MAX_FAV_STREAK = 3            # 같은 방향 연속 우대 한도
HYSTERESIS = True             # ≥3 진입/이탈에 1사이클 지연
BACKLOG_DECAY = 1             # 비혼잡/무우대 시 크레딧 자연감쇠

# ===== 이름 레지스트리 =====
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

# ===== 버스(스레드 세이프) : 모든 방향 수신 =====
class AckBus:
    def __init__(self):
        self.buf = deque()           # (t, dir, uid6)
        self.lock = threading.Lock()

    def push(self, direction, uid_hex):
        t = time.time()
        with self.lock:
            self.buf.append((t, direction, uid_hex.upper()))

    def recent_uids(self, direction, window_sec):
        now = time.time()
        cut = now - window_sec - 1.0
        with self.lock:
            while self.buf and self.buf[0][0] < cut:
                self.buf.popleft()
            return {u for (t,d,u) in self.buf if d==direction and (now - t) <= window_sec}

# ===== 브로드캐스터(시뮬 출력) =====
class Broadcaster:
    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        # 실제 BLE 광고 송출 버전이 필요하면 여기 교체 (이 버전은 콘솔만)
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

# ===== 컨트롤러(4방향) =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.registry = _load_reg()

        # 스케줄 상태
        self.dir_idx = 0
        self.dir = DIRS[self.dir_idx]
        self.state = "BOOT"
        self.rt = 0

        # 계획값
        self.plan_g = {d: BASE_GREEN for d in DIRS}   # 이번 사이클 GREEN
        self.fav_streak = defaultdict(int)            # 연속 우대 횟수
        self.backlog = defaultdict(int)               # 못 채운 요청의 크레딧
        self.heavy_prev = {d: False for d in DIRS}    # 히스테리시스

    # 스캐너 콜백: 모든 방향 수신 (GREEN/대기와 무관하게 기록)
    def on_car_seen(self, direction, uid_hex):
        if direction not in DIRS: return
        self.bus.push(direction, uid_hex)

    def _count_recent(self):
        # 각 방향 최근 윈도우 고유차량 수
        return {d: len(self.bus.recent_uids(d, DECISION_WINDOW_SEC)) for d in DIRS}

    def _compute_plan(self):
        """
        고정 주기 + 재분배:
        - heavy(d): 최근창 ≥3 (히스테리시스 적용)
        - 요청: heavy → +3초
        - 도너: non-heavy → 최대 1초(= BASE - MIN)
        - 총 도너합 한도 내에서 라운드로빈 배분(크레딧 높은 방향 우선)
        - 부족분은 backlog로 이월, 비혼잡/무우대는 감쇠
        """
        cnt = self._count_recent()
        heavy_now = {d: (cnt[d] >= 3) for d in DIRS}
        heavy_use = {}
        for d in DIRS:
            heavy_use[d] = (self.heavy_prev[d] or heavy_now[d]) if HYSTERESIS else heavy_now[d]

        # 요청/도너 계산
        req = {d: (EXTRA_PER_HEAVY if heavy_use[d] else 0) for d in DIRS}
        donors = {d: (BASE_GREEN - MIN_GREEN) if not heavy_use[d] else 0 for d in DIRS}  # 보통 1/0

        # 연속 우대 제한 적용
        if any(heavy_use.values()):
            for d in DIRS:
                if heavy_use[d] and self.fav_streak[d] >= MAX_FAV_STREAK:
                    # 다른 heavy가 있으면 이 방향은 이번 사이클 요청을 0으로 떨어뜨림
                    if sum(1 for x in DIRS if heavy_use[x] and x != d) > 0:
                        req[d] = 0

        R = sum(req.values())
        C = sum(donors.values())
        assignable = min(R, C)

        # heavy 정렬(크레딧 높은 방향 우선)
        heavy_list = [d for d in DIRS if req[d] > 0]
        heavy_list.sort(key=lambda d: self.backlog[d], reverse=True)

        extra = {d: 0 for d in DIRS}
        # 라운드로빈 배분(정수 초)
        i = 0
        while assignable > 0 and heavy_list:
            d = heavy_list[i % len(heavy_list)]
            # 이 방향이 아직 최대(+3) 미만이면 1초 할당
            cap = min(req[d], MAX_GREEN - BASE_GREEN)  # 최대 +3
            if extra[d] < cap:
                extra[d] += 1
                assignable -= 1
            i += 1
            # 더 줄 수 없다면 계속 돌다 자연스레 다음으로 넘어감

        # 못 준 요청은 backlog로 이월, 비혼잡/무우대 감쇠
        for d in DIRS:
            if req[d] > 0:
                self.backlog[d] += (req[d] - extra[d])
            else:
                # 비혼잡/요청 0인 경우 자연감쇠
                self.backlog[d] = max(0, self.backlog[d] - BACKLOG_DECAY)

        # 도너 분배: 각 non-heavy는 최대 1초 기부
        donate_need = sum(extra.values())
        donate_cap = donors.copy()
        donate = {d: 0 for d in DIRS}
        di = 0
        donor_list = [d for d in DIRS if donate_cap[d] > 0]
        while donate_need > 0 and donor_list:
            d = donor_list[di % len(donor_list)]
            if donate[d] < donate_cap[d]:
                donate[d] += 1
                donate_need -= 1
            di += 1

        # 최종 GREEN
        g = {}
        for d in DIRS:
            g_d = BASE_GREEN + extra[d] - donate[d]
            g[d] = max(MIN_GREEN, min(MAX_GREEN, g_d))

        # 연속 우대 카운트 갱신
        for d in DIRS:
            if extra[d] > 0:
                self.fav_streak[d] += 1
            else:
                # heavy인데 못 받았으면 0으로 리셋하여 다음 배분 때 우선권 상승
                self.fav_streak[d] = 0

        # 히스테리시스 다음 기준 저장
        self.heavy_prev = heavy_now

        # 디버그
        print(f"[PLAN] cnt={cnt} heavy={heavy_use} req={req} donors={donors} extra={extra} donate={donate} g={g} backlog={dict(self.backlog)}")
        return g

    def _names_for_dir(self, d):
        uids = self.bus.recent_uids(d, DECISION_WINDOW_SEC)
        return ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"

    def _start_cycle_if_needed(self):
        # 한 사이클의 시작은 방향 인덱스가 0으로 돌아올 때로 정의
        if self.state == "BOOT" or (self.state == "GREEN" and self.dir_idx == 0 and self.rt == 0):
            self.plan_g = self._compute_plan()

    def _start_green(self, d):
        self.dir = d
        self.state = "GREEN"
        self.rt = self.plan_g[d]

        # (선택) 직전 대기창 내용 출력
        names = self._names_for_dir(d)
        print(f"[DBG] start GREEN dir={d} g={self.rt} names=[{names}]")

    def _next_phase(self):
        if self.state == "BOOT":
            self._start_cycle_if_needed()
            self._start_green(DIRS[self.dir_idx])
            return

        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "ALLRED"; self.rt = ALL_RED
        else:  # ALLRED → 다음 방향 GREEN
            self.dir_idx = (self.dir_idx + 1) % len(DIRS)
            if self.dir_idx == 0:
                # 새 사이클 시작 전에 계획 갱신
                self._start_cycle_if_needed()
            self._start_green(DIRS[self.dir_idx])

    def tick(self):
        if self.rt <= 0:
            self._next_phase()

        # Q 플래그: 현재 GREEN일 때만 False, 그 외(True) — (차량 ALWAYS_ACK면 영향 없음)
        q_flag = (self.state != "GREEN")

        # 광고/표시
        self.bc.advertise(PHASE_MAP[self.dir], self.dir, self.state, self.rt, self.plan_g[self.dir], q_flag)

        # 현재 방향 실시간 집계
        names = self._names_for_dir(self.dir)
        cars_now = len(names.split(", ")) if names != "-" else 0
        print(f"{self.state:<6} dir:{self.dir} RT:{self.rt}s  cars:{cars_now}  names:[{names}]")

        self.rt -= 1

def run():
    ctrl = Controller()
    # 스캐너 시작: 어떤 방향이든 보이면 on_car_seen 호출
    central_scan.start_scan(ctrl.on_car_seen, target_dir=None)

    while True:
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run()
