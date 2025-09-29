# from collections import deque
# import time, json, os, re, threading
# import central_scan

# # ===== 고정 방향 =====
# TARGET_DIR = "N"
# PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# # ===== 시간/판정 =====
# G_BASE, G_EXT = 5, 8            # 기본 5초, (대기 15초 ≥3대)면 8초
# YELLOW, ALL_RED = 2, 13         # 대기 합계 15초
# DECISION_WINDOW_SEC = 15.0      # 지난 대기 15초 창

# # ===== 이름 레지스트리 =====
# REG_PATH = "car_names.json"
# IDX_PAT  = re.compile(r"차량\s*(\d+)")

# def _load_reg():
#     if os.path.exists(REG_PATH):
#         try:
#             with open(REG_PATH, "r", encoding="utf-8") as f:
#                 d = json.load(f)
#                 return d if isinstance(d, dict) else {}
#         except: pass
#     return {}

# def _next_idx(reg):
#     mx = 0
#     for name in reg.values():
#         m = IDX_PAT.search(name)
#         if m:
#             try: mx = max(mx, int(m.group(1)))
#             except: pass
#     return mx + 1

# def name_for_uid(uid_hex, reg):
#     uid_hex = uid_hex.upper()
#     if uid_hex in reg: return reg[uid_hex]
#     idx = _next_idx(reg)
#     label = f"C  차량{idx}  UID3={uid_hex}"
#     reg[uid_hex] = label
#     try:
#         with open(REG_PATH, "w", encoding="utf-8") as f:
#             json.dump(reg, f, ensure_ascii=False, indent=2)
#     except: pass
#     return label

# # ===== 버스(스레드 세이프) =====
# class AckBus:
#     def __init__(self):
#         self.buf = deque()           # (t, dir, uid6)
#         self.lock = threading.Lock()

#     def push(self, direction, uid_hex):
#         with self.lock:
#             self.buf.append((time.time(), direction, uid_hex.upper()))

#     def recent_uids(self, direction, window_sec):
#         now = time.time()
#         cut = now - window_sec - 1.0
#         with self.lock:
#             while self.buf and self.buf[0][0] < cut:
#                 self.buf.popleft()
#             return {u for (t,d,u) in self.buf if d==direction and (now - t) <= window_sec}

# # ===== 브로드캐스터(시뮬) =====
# class Broadcaster:
#     def advertise(self, ph, dir_letter, state, rt, g, q_flag):
#         print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")

# # ===== 컨트롤러 =====
# class Controller:
#     def __init__(self):
#         self.bus = AckBus()
#         self.bc  = Broadcaster()
#         self.dir = TARGET_DIR

#         # ★★ 안전한 초기화(부트 상태)
#         self.state = "BOOT"      # BOOT -> GREEN -> YELLOW -> RED ...
#         self.rt = 0              # ← 존재만 해도 tick에서 안전
#         self.g_alloc = G_BASE
#         self.accept_acks = False
#         self.registry = _load_reg()

#     # central_scan에서 호출
#     def on_car_seen(self, direction, uid_hex):
#         if direction != self.dir: 
#             return
#         if not self.accept_acks:  # GREEN 중엔 무시
#             return
#         self.bus.push(direction, uid_hex)

#     def _window_uids(self):
#         return self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)

#     def start_green(self):
#         uids = self._window_uids()                  # 지난 대기 15초
#         self.g_alloc = G_EXT if len(uids) >= 3 else G_BASE
#         self.rt = self.g_alloc
#         names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
#         print(f"[DBG] wait=15s cars={len(uids)} nextG={self.g_alloc} names=[{names}]")

#     def next_phase(self):
#         if self.state == "BOOT":
#             self.state = "GREEN"
#             self.start_green()
#         elif self.state == "GREEN":
#             self.state, self.rt = "YELLOW", YELLOW
#         elif self.state == "YELLOW":
#             self.state, self.rt = "RED", ALL_RED
#         else:  # RED → 같은 방향 GREEN
#             self.state = "GREEN"
#             self.start_green()

#     def tick(self):
#         # ★ BOOT을 포함해 항상 rt가 존재 → AttributeError 방지
#         if self.rt <= 0:
#             self.next_phase()

#         # 대기 구간에서만 ACK 허용(Q=1)
#         self.accept_acks = (self.state != "GREEN")
#         ph = PHASE_MAP[self.dir]
#         self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, self.accept_acks)

#         # 표시
#         uids = self._window_uids()
#         names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
#         print(f"{self.state:<6} RT:{self.rt}s  cars:{len(uids)}  names:[{names}]")

#         self.rt -= 1

# def run():
#     ctrl = Controller()
#     # 스캐너 시작(발견 즉시 ctrl.on_car_seen 호출)
#     central_scan.start_scan(ctrl.on_car_seen, target_dir=TARGET_DIR)

#     while True:
#         ctrl.tick()
#         time.sleep(1)

# if __name__ == "__main__":
#     run()



# controller_sim.py
# Raspberry Pi 5 (BlueZ) 중앙장치 시뮬레이터
# - 초당 1회 상태 갱신
# - BLE Local Name(=system-alias) 로 "RT:xx|DIR:N|Q:1|T:G" 광고
# - CAR 쪽의 car_view_filtered.py 가 수신하여 OLED에 표시

from collections import deque
import time, json, os, re, threading, subprocess
import sys

# ===== 스캔 콜백을 위해 외부 스캐너 사용 시 임포트 (없으면 목업) =====
try:
    import central_scan
except ImportError:
    # 중앙에서 스캔을 쓰지 않을 때를 위한 목업
    class central_scan:
        @staticmethod
        def start_scan(cb, target_dir="N"):
            # 실제 스캐너가 없다면 아무것도 하지 않음
            print("[INFO] central_scan 모듈이 없어 스캔은 생략합니다.")

# ===== 고정 방향 =====
TARGET_DIR = "N"
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# ===== 시간/판정 =====
G_BASE, G_EXT = 5, 8            # 기본 5초, (대기 15초 ≥3대)면 8초
YELLOW, ALL_RED = 2, 13         # 대기 합계 15초
DECISION_WINDOW_SEC = 15.0      # 지난 대기 15초 창

# ===== 이름 레지스트리 =====
REG_PATH = "car_names.json"
IDX_PAT  = re.compile(r"차량\s*(\d+)")

def _load_reg():
    if os.path.exists(REG_PATH):
        try:
            with open(REG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
        except:
            pass
    return {}

def _next_idx(reg):
    mx = 0
    for name in reg.values():
        m = IDX_PAT.search(name)
        if m:
            try:
                mx = max(mx, int(m.group(1)))
            except:
                pass
    return mx + 1

def name_for_uid(uid_hex, reg):
    uid_hex = uid_hex.upper()
    if uid_hex in reg:
        return reg[uid_hex]
    idx = _next_idx(reg)
    label = f"C  차량{idx}  UID3={uid_hex}"
    reg[uid_hex] = label
    try:
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=2)
    except:
        pass
    return label

# ===== 버스(스레드 세이프) =====
class AckBus:
    def __init__(self):
        self.buf = deque()           # (t, dir, uid6)
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
            return {u for (t, d, u) in self.buf if d == direction and (now - t) <= window_sec}

# ===== 브로드캐스터 (bluetoothctl 이용, 간단/권장) =====
class Broadcaster:
    """
    bluetoothctl을 백그라운드로 띄우고 system-alias(=Local Name)를 매초 갱신.
    CAR 수신기(car_view_filtered.py)는 Local Name의 텍스트를 파싱함.
    """
    def __init__(self):
        self.proc = subprocess.Popen(
            ["bluetoothctl"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self._cmd("power on")
        self._cmd("advertise on")
        self._last_alias = None

    def _cmd(self, s):
        try:
            self.proc.stdin.write(s + "\n")
            self.proc.stdin.flush()
        except Exception as e:
            print("[BTCTL ERR]", e)

    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        # car_view_filtered.py가 이해하는 키: RT, DIR, Q (+T는 선택)
        alias = f"RT:{rt}|DIR:{dir_letter}|Q:{int(q_flag)}|T:{state[:1]}"
        if alias != self._last_alias:
            self._cmd(f'system-alias "{alias}"')
            self._last_alias = alias
        # 디버그 로그
        print(f"[ADV] {alias}")

# ===== 컨트롤러 =====
class Controller:
    def __init__(self):
        self.bus = AckBus()
        self.bc  = Broadcaster()
        self.dir = TARGET_DIR

        # 안전한 초기화(부트 상태)
        self.state = "BOOT"      # BOOT -> GREEN -> YELLOW -> RED ...
        self.rt = 0
        self.g_alloc = G_BASE
        self.accept_acks = False
        self.registry = _load_reg()

    # central_scan에서 호출
    def on_car_seen(self, direction, uid_hex):
        if direction != self.dir:
            return
        if not self.accept_acks:  # GREEN 중엔 무시
            return
        self.bus.push(direction, uid_hex)

    def _window_uids(self):
        return self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)

    def start_green(self):
        # 지난 대기 15초 내 차량 수(동일 UID 중복 제거)
        uids = self._window_uids()
        self.g_alloc = G_EXT if len(uids) >= 3 else G_BASE
        self.rt = self.g_alloc
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"[DBG] wait=15s cars={len(uids)} nextG={self.g_alloc} names=[{names}]")

    def next_phase(self):
        if self.state == "BOOT":
            self.state = "GREEN"
            self.start_green()
        elif self.state == "GREEN":
            self.state, self.rt = "YELLOW", YELLOW
        elif self.state == "YELLOW":
            self.state, self.rt = "RED", ALL_RED
        else:  # RED -> 같은 방향 GREEN
            self.state = "GREEN"
            self.start_green()

    def tick(self):
        if self.rt <= 0:
            self.next_phase()

        # 대기 구간에서만 ACK 허용(Q=1)
        self.accept_acks = (self.state != "GREEN")
        ph = PHASE_MAP[self.dir]

        # 광고 내보내기 (CAR는 Local Name or Service Data 텍스트를 파싱)
        self.bc.advertise(ph, self.dir, self.state, self.rt, self.g_alloc, self.accept_acks)

        # 콘솔 표시(디버그)
        uids = self._window_uids()
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"{self.state:<6} RT:{self.rt}s  cars:{len(uids)}  names:[{names}]")

        self.rt -= 1

def run():
    ctrl = Controller()
    # 스캐너 시작(발견 즉시 ctrl.on_car_seen 호출) — 스캐너 모듈이 없으면 생략됨
    try:
        central_scan.start_scan(ctrl.on_car_seen, target_dir=TARGET_DIR)
    except Exception as e:
        print("[WARN] central_scan.start_scan 실패:", e)

    try:
        while True:
            ctrl.tick()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBye")

if __name__ == "__main__":
    run()



