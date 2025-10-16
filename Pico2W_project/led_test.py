
# 0.5초 점등 테스트
GPIOZERO_PIN_FACTORY=lgpio python3 - <<'PY'
from gpiozero import LED
from time import sleep

for pin in (17,27,22):
    led=LED(pin); led.on(); print(f"ON BCM{pin}"); sleep(0.5); led.off(); print(f"OFF BCM{pin}")
print("OK: lgpio")
PY


# 켜졌다 꺼지면 성공. 그럼 본 프로그램도 같은 방식으로 실행:
# GPIOZERO_PIN_FACTORY=lgpio sudo -E python3 central_traffic_with_hb.py

lgpio가 실패하면 rpigpio로 재시도
sudo apt-get install -y python3-rpi.gpio
GPIOZERO_PIN_FACTORY=rpigpio python3 - <<'PY'
from gpiozero import LED
from time import sleep
for pin in (17,27,22):
    led=LED(pin); led.on(); print(f"ON BCM{pin}"); sleep(0.5); led.off(); print(f"OFF BCM{pin}")
print("OK: rpigpio")
PY


# 성공시
# GPIOZERO_PIN_FACTORY=rpigpio sudo -E python3 central_traffic_with_hb.py

# led_test.py (BCM 17/27/22)
import os, time
from gpiozero import LED

print("factory:", os.environ.get("GPIOZERO_PIN_FACTORY"))
pins = [17,27,22]
leds = [LED(p) for p in pins]
for p,l in zip(pins, leds):
    l.on(); print(f"ON BCM{p}"); time.sleep(0.5); l.off(); print(f"OFF BCM{p}")
print("done.")

실행
GPIOZERO_PIN_FACTORY=lgpio python3 led_test.py
# 또는
GPIOZERO_PIN_FACTORY=rpigpio python3 led_test.py
