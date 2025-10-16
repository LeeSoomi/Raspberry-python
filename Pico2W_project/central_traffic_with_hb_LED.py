# 한번만 설치
# sudo apt-get update
# sudo apt-get install -y python3-gpiozero
# ------------------

# 실행 sudo python3 central_traffic_with_hb_LED.py
# ----------------------------------

# BCM 기준 기본 핀: RED=17, YELLOW=27, GREEN=22

# central_traffic_with_hb.py  (Raspberry Pi 5 / Python 3)
import socket, json, time
import os

# ===== 추가: 내 방향 / LED 핀팩토리 기본값 =====
MY_DIR = os.environ.get("MY_DIR", "N")          # 내 방향: N/E/S/W
os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

# ===== 추가: 물리 LED (BCM 핀) =====
PIN_RED, PIN_YELLOW, PIN_GREEN = 17, 27, 22
try:
    from gpiozero import LED
    _GPIO_OK = True
except Exception as e:
    print(f"[WARN] gpiozero unavailable: {e}")
    _GPIO_OK = False

class TrafficLight:
    def __init__(self, r=PIN_RED, y=PIN_YELLOW, g=PIN_GREEN):
        self.ok = _GPIO_OK
        if self.ok:
            self.red = LED(r); self.yellow = LED(y); self.green = LED(g)
            self.all_off()
    def all_off(self):
        if not self.ok: return
        self.red.off(); self.yellow.off(); self.green.off()
    def set_state(self, state: str):
        """state in {'GREEN','YELLOW','RED'}"""
        if not self.ok: return
        self.all_off()
        s = (state or "").upper()
        if s == "GREEN": self.green.on()
        elif s == "YELLOW": self.yellow.on()
        else: self.red.on()
    def close(self):
        if not self.ok: return
        self.all_off()

# ---- 설정 ----
BCAST_IP, BCAST_PORT = "255.255.255.255", 5005  # 신호 브로드캐스트
HB_PORT = 5006                                   # 하트비트 수신
TOTAL = 20
ORDER = ["N","E","S","W"]
CAR_THRESH = 3        # 3대 이상이면 혼잡
HB_TTL = 3.5          # 최근 3.5초 내 하트비트만 유효

# ---- 소켓 준비 ----
bc
