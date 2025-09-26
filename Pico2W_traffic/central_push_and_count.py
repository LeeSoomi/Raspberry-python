# central_one_dir_tdm.py
# 한 방향(A)만 운용, 적색(R) 동안에만 스캔(BLEAK), G 길이는 집계로 가변
import asyncio, time, subprocess
from bleak import BleakScanner

DIR = 'A'
YELLOW = 3
RED_SCAN = 15
MIN_G, BASE_G, MAX_G = 5, 5, 11
SMOOTH_STEP = 2
ADAPTER = "hci0"     # 내장만: "hci0" / 동글 추가 시: "hci1"

UUID16 = 0xFFFF      # 차량 ACK Service Data UUID

# --- bluetoothctl 헬퍼 ---
def btctl(cmds):
    script = "\n".join(cmds) + "\n"
    return subprocess.run(["bluetoothctl"], input=script, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ensure_on(controller_mac=None):
    cmds = []
    if controller_mac:
        cmds.append(f"select {controller_mac}")  # 특정 어댑터 고정할 때 사용(선택)
    cmds += ["power on", "pairable on", "discoverable on"]
    btctl(cmds)

def set_alias(txt):
    btctl([f"system-alias {txt}"])

def adv_on():
    btctl(["advertise on"])

def adv_off():
    btctl(["advertise off"])

def decide_green(n, prev):
    tgt = 5 if n <= 1 else 7 if n == 2 else 9 if n == 3 else 11
    if tgt > prev: tgt = min(tgt, prev + SMOOTH_STEP)
    if tgt < prev: tgt = max(tgt, prev - SMOOTH_STEP)
    return max(MIN_G, min(MAX_G, tgt))

# --- 스캔(적색에서만) ---
class AckCounter:
    def __init__(self): self.uids = set()
    def reset(self): self.uids.clear()
    def cb(self, dev, adv):
        if not adv or not adv.service_data: return
        sd = adv.service_data.get(UUID16)
        if not sd or len(sd) < 5 or sd[0] != 0x50:  # 'P'
            return
        uid3 = sd[1:4].hex()
        dchr = chr(sd[4])
        if dchr == DIR:
            self.uids.add(uid3)

async def scan_red_seconds(counter: AckCounter, seconds: int):
    counter.reset()
    scanner = BleakScanner(counter.cb, adapter=ADAPTER)
    await scanner.start()
    try:
        t0 = time.time()
        while time.time() - t0 < seconds:
            # 적색(R) 동안 계속 Q:1 상태로 alias 업데이트(초표시)
            remain = int(seconds - (time.time() - t0))
            set_alias(f"S:{remain}|D:{DIR}|PH:R|Q:1")
            await asyncio.sleep(0.5)
    finally:
        await scanner.stop()

# --- 메인 루프 ---
async def main():
    print(f"[{DIR}] single-direction controller start (adapter={ADAPTER})")
    ensure_on()
    set_alias(f"S:20|D:{DIR}|PH:R|Q:1")
    last_g = BASE_G

    while True:
        # 1) 녹색(G): last_g초, Q=0 (스캔 OFF)
        adv_on()
        for s in range(last_g, -1, -1):
            set_alias(f"S:{s}|D:{DIR}|PH:G|Q:0")
            await asyncio.sleep(1)
        # 2) 황색(Y): 3초
        for s in range(YELLOW, -1, -1):
            set_alias(f"S:{s}|D:{DIR}|PH:Y|Q:0")
            await asyncio.sleep(1)
        adv_off()

        # 3) 적색(R): RED_SCAN초 동안 스캔 ON (Q=1)
        counter = AckCounter()
        await scan_red_seconds(counter, RED_SCAN)
        n = len(counter.uids)
        last_g = decide_green(n, last_g)
        print(f"[{time.strftime('%H:%M:%S')}] DIR={DIR} window={RED_SCAN}s -> count={n} => next G={last_g}s")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        adv_off()
        print("stopped.")
