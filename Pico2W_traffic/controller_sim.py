#!/usr/bin/env python3
# controller_sim.py  (한 방향 · 15초 대기창 집계 · BLE 광고 송출)

from collections import deque
import time, json, os, re, threading, subprocess

import central_scan  # 기존 스캐너 그대로 사용

# ===== 사용자 설정 =====
HCI_IFACE = "hci0"          # 어댑터
TARGET_DIR = "N"            # 내 쪽 방향 고정 ("N","E","S","W")
PHASE_MAP  = {"N":"NS","S":"NS","E":"EW","W":"EW"}

# 시간/판정
G_BASE, G_EXT = 5, 8        # 기본 5초, (대기15초 ≥3대)면 8초
YELLOW, ALL_RED = 2, 13     # 합계 15초 대기
DECISION_WINDOW_SEC = 15.0  # 지난 대기 15초 집계 창
ADV_INTERVAL_MS = 100       # 광고 간격(100ms ≈ 10Hz 프레임, 내용은 1Hz로 갱신)

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

# ===== HCI 저수준 광고 송출기 =====
class HCIAdvertiser:
    """
    BlueZ hcitool로 0xFFFF Service Data 광고 업데이트.
    - sudo 필요: 실행 자체를 sudo로 권장
    - 광고 데이터는 31바이트 제한 → 'DIR|T|RT|Q'만 보냅니다.
    """
    def __init__(self, iface=HCI_IFACE, interval_ms=ADV_INTERVAL_MS):
        self.iface = iface
        self.units = int(interval_ms / 0.625)  # 0.625ms 단위
        self.started = False
        self._setup_adapter()

    def _run(self, ogf_hex, ocf_hex, payload_bytes):
        # ex) hcitool -i hci0 cmd 0x08 0x0008 <...>
        cmd = ["sudo", "hcitool", "-i", self.iface, "cmd", ogf_hex, ocf_hex]
        cmd += [f"{b:02x}" for b in payload_bytes]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _setup_adapter(self):
        subprocess.run(["sudo", "hciconfig", self.iface, "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # LE Set Advertising Parameters (0x08, 0x0006)
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
        # Enable advertising (we will set data next)
        self._run("0x08", "0x000A", [0x01])  # 1=enable
        self.started = True

    def update(self, dir_letter, state_str, rt, q_flag):
        """
        Service Data(0xFFFF): "DIR:N|T:GREEN|RT:8|Q:1"  (≤ 28바이트 권장)
        """
        payload_str = f"DIR:{dir_letter}|T:{state_str}|RT:{int(rt)}|Q:{1 if q_flag else 0}"
        payload = payload_str.encode()
        # AD structure: [len, 0x16, 0xFF, 0xFF, payload...]
        sd = bytes([len(payload) + 3, 0x16, 0xFF, 0xFF]) + payload  # <=31 bytes
        if len(sd) > 31:
            # 안전장치: 길면 T를 약어화
            state_short = {"GREEN":"G","YELLOW":"Y","RED":"R"}.get(state_str, state_str[:1])
            payload = f"DIR:{dir_letter}|T:{state_short}|RT:{int(rt)}|Q:{1 if q_flag else 0}".encode()
            sd = bytes([len(payload) + 3, 0x16, 0xFF, 0xFF]) + payload

        # LE Set Advertising Data (0x08, 0x0008): <len> <31바이트 데이터>
        pad = bytes(31 - len(sd))
        params = bytes([len(sd)]) + sd + pad
        self._run("0x08", "0x0008", params)

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
            return {u for (t,d,u) in self.buf if d==direction and (now - t) <= window_sec}

# ===== 브로드캐스터(실 광고 송출) =====
class Broadcaster:
    def __init__(self):
        self.hci = HCIAdvertiser(HCI_IFACE, ADV_INTERVAL_MS)

    def advertise(self, ph, dir_letter, state, rt, g, q_flag):
        # 콘솔도 남기고
        print(f"[ADV] PH:{ph}|DIR:{dir_letter}|T:{state}|RT:{rt}|G:{g}|Q:{int(q_flag)}")
        # 실제 광고 송출 (Pico는 DIR/T/RT/Q만 필요)
        self.hci.update(dir_letter, state, rt, q_flag)

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
        if not self.accept_acks:   # GREEN 중엔 무시
            return
        self.bus.push(direction, uid_hex)

    def _window_uids(self):
        return self.bus.recent_uids(self.dir, DECISION_WINDOW_SEC)

    def start_green(self):
        # 지난 대기 15초의 고유 UID 수로 다음 GREEN 결정
        uids = self._window_uids()
        self.g_alloc = G_EXT if len(uids) >= 3 else G_BASE
        self.rt = self.g_alloc
        names = ", ".join([name_for_uid(u, self.registry) for u in sorted(uids)]) or "-"
        print(f"[DBG] wait=15s cars={len(uids)} nextG={self.g_alloc} names=[{names}]")

        # (선택) 바로 0으로 보이게 하고 싶으면 다음 줄 주석 해제
        # self.bus.buf.clear()

    def next_phase(self):
        if self.state == "BOOT":
            self.state = "GREEN"
            self.start_green()
        elif self.state == "GREEN":
            self.state, self.rt = "YELLOW", YELLOW
        elif self.state == "YELLOW":
            self.state, self.rt = "RED", ALL_RED
        else:  # RED → 같은 방향 GREEN
            self.state = "GREEN"
            self.start_green()

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
    # 스캐너 시작(ACK 발견 시 ctrl.on_car_seen 호출)
    central_scan.start_scan(ctrl.on_car_seen, target_dir=TARGET_DIR)

    while True:
        ctrl.tick()
        time.sleep(1)

if __name__ == "__main__":
    run()
