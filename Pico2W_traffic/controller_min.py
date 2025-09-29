# controller_min.py — 깔끔/최소. bluetoothctl 로 Local Name만 갱신.
import subprocess, time

def btctl(cmds):
    p = subprocess.Popen(
        ["bluetoothctl"], stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True
    )
    for c in cmds:
        p.stdin.write(c + "\n")
    p.stdin.flush()
    return p

# 1) 전원/광고 ON (한 번만)
bt = btctl(["power on", "advertise on"])

DIR = "N"       # 고정 방향
STATE = "G"     # 상태문자: G/R/Y 중 하나 (표시 2줄 첫 글자)
Q = 1           # 대기 구간이면 1, 아니라면 0. 일단 1로 고정

sec = 30
print("Advertising via Local Name… Ctrl+C to stop")
try:
    while True:
        alias = f"RT:{sec}|DIR:{DIR}|Q:{Q}|T:{STATE}"
        bt.stdin.write(f'system-alias "{alias}"\n')
        bt.stdin.flush()
        print(alias)
        sec = sec-1 if sec>0 else 30
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    # 필요시 광고 유지하려면 아래 두 줄 주석
    bt.stdin.write("advertise off\n")
    bt.stdin.flush()
    bt.terminate()

---------------------------

# 실행
# python3 controller_min.py
