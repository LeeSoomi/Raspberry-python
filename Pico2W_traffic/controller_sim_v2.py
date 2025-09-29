#!/usr/bin/env python3
# controller_sim.py
from collections import deque, defaultdict
import time, json, os, re, threading, subprocess
import central_scan  # 스캔 쓰레드를 내부에서 자동 실행

# ===== 어댑터 지정 =====
SCAN_IFACE = 0          # hci0 (내장)  ← 스캔
ADV_IFACE  = "hci1"     # hci1 (외장)  ← 광고

# ===== 방향/페이즈 =====
DIRS = ["N", "E", "S", "W"]
PHASE_MAP = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간/정책 =====
MIN_GREEN = 4
BASE_GREEN = 5
MAX_GREEN = 8
EXTRA_PER_HEAVY = 3          # 혼잡 요청(+3)
YELLOW = 2
ALL_RED = 1
DECISION_WINDOW_SEC = 15.0   # 혼잡 판정 창(초)
ADV_INTERVAL_MS = 100        # 광고 간격(0.625ms 단위 환산됨)

# ===== 공정성/안정성 =====
MAX_FAV_STREAK = 3
HYSTERESIS = True
BACKLOG_DECAY = 1

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

# ===== 수집 버스 =====
class AckBus:
    def __init__(self):
        self.buf = deque()  # (t, dir, uid6)
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

# ===== HCI 저수준 광고기 (외장 hci1) =====
class HCIAdvertiser:
    """
    BlueZ hcitool로 0xFFFF Service Data 광고.
    sudo 권장. 광고 데이터 ≤31B.
    """
    def __init__(self, iface=ADV_IFACE, interval_ms=ADV_INTERVAL_MS):
        self.iface = iface
        self.units = int(interval_ms / 0.625)  # 0.625ms 단위
        self.started = False
        self._setup_adapter()

    def _run(self, ogf_hex, ocf_hex, payload_bytes):
        cmd = ["sudo", "hcitool", "-i", self.iface, "cmd", ogf_hex, ocf_hex]
        cmd += [f"{b:02x}" for b in payload_bytes]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _setup_adapter(self):
        subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "hciconfig", self.iface, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Set Adv Params (0x08,0x0006)
        u = self.units
        params = [
            u & 0xFF, (u >> 8) & 0xFF,    # min
            u & 0xFF, (u >> 8) & 0xFF,    # max
            0x03,                         # ADV_NONCONN_IND
            0x00,                         # OwnAddr: Public
            0x00,                         # DirectAddrType
            0x00,0x00,0x00,0x00,0x00,0x00,# DirectAddr
            0x07,                         # Channel map
            0x00                          # Filter policy
        ]
        self._run("0x08", "0x0006", params)
        # Enable Advertising (0x08,0x000A)
        self._run("0x08", "0x000A", [0x01])
        self.started = True

    def update(self, dir_letter, state_str, rt, q_flag):
        # Service Data payload (문자열)
        payload = f"DIR:{dir_letter}|T:{state_str}|RT:{int(rt)}|Q:{1 if q_flag else 0}".encode()
        sd = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload
        if len(sd) > 31:
            # 길면 상태 약어
            s_short = {"GREEN":"G","YELLOW":"Y","RED":"R","ALLRED":"A"}.get(state_str, state_str[:1])
            payload = f"DIR:{dir_letter}|T:{s_short}|RT:{int(rt)}|Q:{1 if q_flag else 0}".encode()
            sd = bytes([len(payload)+3, 0x16, 0xFF, 0xFF]) + payload

        # Set Adv Data (0x08,0x0008): 길이 + 31바이트 패딩
        pad = bytes(31 - len(sd))
        params = bytes([len(sd)]) + sd + pad
        self._run("0x08", "0x0008", params)

# ===== 브로드캐스터 =====
class Broadcaster:
    def __init__(self):
        self.hci = HCIAdvertiser(ADV_IFACE, ADV_INTERVAL_MS)

    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        # 콘솔도 남기고
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")
        # 실제 광고 송출 (Pico는 DIR/T/RT/Q만 사용)
        self.hci.update(dir_letter, state, rt, q_flag)

# ===== 컨트롤러(4방향 재분배) =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.registry = _load_reg()

        self.dir_idx = 0
        self.dir = DIRS[self.dir_idx]
        self.state = "BOOT"
        self.rt = 0

        self.plan_g = {d: BASE_GREEN for d in DIRS}
        self.fav_streak = defaultdict(int)
        self.backlog = defaultdict(int)
        self.heavy_prev = {d: False for d in DIRS}

    # 스캐너 콜백 (모든 방향 수신)
    def on_car_seen(self, direction, uid_hex):
        if direction not in DIRS: return
        self.bus.push(direction, uid_hex)

    def _count_recent(self):
        return {d: len(self.bus.recent_uids(d, DECISION_WINDOW_SEC)) for d in DIRS}

    def _compute_plan(self):
        cnt = self._count_recent()
        heavy_now = {d: (cnt[d] >= 3) for d in DIRS}
        heavy_use = {}
        for d in DIRS:
            heavy_use[d] = (self.heavy_prev[d] or heavy_now[d]) if HYSTERESIS else heavy_now[d]

        req = {d: (EXTRA_PER_HEAVY if heavy_use[d] else 0) for d in DIRS}
        donors = {d: (BASE_GREEN - MIN_GREEN) if not heavy_use[d] else 0 for d in DIRS}  # 비혼잡 1초 기부

        # 연속 우대 제한
        if any(heavy_use.values()):
            for d in DIRS:
                if heavy_use[d] and self.fav_streak[d] >= MAX_FAV_STREAK:
                    if sum(1 for x in DIRS if heavy_use[x] and x != d) > 0:
                        req[d] = 0

        R = sum(req.values())
        C = sum(donors.values())
        assignable = min(R, C)

        # 크레딧 우선 라운드로빈
        heavy_list = [d for d in DIRS if req[d] > 0]
        heavy_list.sort(key=lambda d: self.backlog[d], reverse=True)

        extra = {d: 0 for d in DIRS}
        i = 0
        while assignable > 0 and heavy_list:
            d = heavy_list[i % len(heavy_list)]
            cap = min(req[d], MAX_GREEN - BASE_GREEN)  # 최대 +3
            if extra[d] < cap:
                extra[d] += 1
                assignable -= 1
            i += 1

        # 크레딧 이월/감쇠
        for d in DIRS:
            if req[d] > 0:
                self.backlog[d] += (req[d] - extra[d])
            else:
                self.backlog[d] = max(0, self.backlog[d] - BACKLOG_DECAY)

        # 도너 배분(각 non-heavy 최대 1초)
        donate_need = sum(extra.values())
        donate = {d: 0 for d in DIRS}
        donor_list = [d for d in DIRS if donors[d] > 0]
        di = 0
        while donate_need > 0 and donor_list:
            d = donor_list[di % len(donor_list)]
            if donate[d] < donors[d]:
                donate[d] += 1
                donate_need -= 1
            di += 1

        # 최종 GREEN (합 20 유지)
        g = {}
        for d in DIRS:
            g_d = BASE_GREEN + extra[d] - donate[d]
            g[d] = max(MIN_GREEN, min(MAX_GREEN, g_d))

        # 우대 카운트/히스테리시스 갱신
        for d in DIRS:
            self.fav_streak[d] = self.fav_streak[d] + 1 if extra[d] > 0 else 0
        self.heavy_prev = heavy_now

        print(f"[PLAN] cnt={cnt} heavy={heavy_use} req={req} donors={donors} extra={extra} g={g} backlog={dict(self.backlog)}")
        return g

    def _names_for_dir(self, d):
        uids = self.bus.recent_uids(d, DECISION_WINDOW_SEC)
        return ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"

    def _start_cycle_if_needed(self):
        if self.state == "BOOT" or (self.state == "GREEN" and self.dir_idx == 0 and self.rt == 0):
            self.plan_g = self._compute_plan()

    def _start_green(self, d):
        self.dir = d
        self.state = "GREEN"
        self.rt = self.plan_g[d]
        names = self._names_for_dir(d)
        print(f"[DBG] start GREEN dir={d} g={self.rt} names=[{names}]")

    def _next_phase(self):
        if self.state == "BOOT":
            self._start_cycle_if_needed()
            self._start_green(DIRS[self.dir_idx]); return
        if self.state == "GREEN":
            self.state = "YELLOW"; self.rt = YELLOW
        elif self.state == "YELLOW":
            self.state = "ALLRED"; self.rt = ALL_RED
        else:
            self.dir_idx = (self.dir_idx + 1) % len(DIRS)
            if self.dir_idx == 0:
                self._start_cycle_if_needed()
            self._start_green(DIRS[self.dir_idx])

    def tick(self):
        if self.rt <= 0:
            self._next_phase()

        q_flag = (self.state != "GREEN")  # 대기 구간만 Q=1
        self.bc.advertise(PHASE_MAP[self.dir], self.dir, self.state, self.rt, self.plan_g[self.dir], q_flag)

        names = self._names_for_dir(self.dir)
        cars_now = 0 if names == "-" else len(names.split(", "))
        print(f"{self.state:<6} dir:{self.dir} RT:{self.rt}s  cars:{cars_now}  names:[{names}]")

        self.rt -= 1

def run():
    ctrl = Controller()
    # 내장(hci0)으로 스캔 쓰레드 시작(자동)
    central_scan.start_scan(ctrl.on_car_seen, target_dir=None, iface=SCAN_IFACE)
    while True:
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run()
