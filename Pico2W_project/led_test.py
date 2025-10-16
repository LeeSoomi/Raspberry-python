# led_test.py - 라즈베리파이 LED 테스트
import RPi.GPIO as GPIO
import time

# GPIO 핀 설정
LED_RED = 17    # 빨간 LED
LED_YELLOW = 27 # 노란 LED  
LED_GREEN = 22  # 녹색 LED

# GPIO 모드 설정
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# LED 핀을 출력으로 설정
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_YELLOW, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)

def all_off():
    """모든 LED 끄기"""
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(LED_YELLOW, GPIO.LOW)
    GPIO.output(LED_GREEN, GPIO.LOW)

def test_individual():
    """각 LED 개별 테스트"""
    print("LED 개별 테스트 시작...")
    
    # 빨간 LED
    print("빨간 LED ON")
    GPIO.output(LED_RED, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LED_RED, GPIO.LOW)
    time.sleep(0.5)
    
    # 노란 LED
    print("노란 LED ON")
    GPIO.output(LED_YELLOW, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LED_YELLOW, GPIO.LOW)
    time.sleep(0.5)
    
    # 녹색 LED
    print("녹색 LED ON")
    GPIO.output(LED_GREEN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LED_GREEN, GPIO.LOW)
    time.sleep(0.5)

def test_pattern():
    """신호등 패턴 테스트"""
    print("\n신호등 패턴 테스트 시작...")
    
    for i in range(3):
        print(f"사이클 {i+1}")
        
        # 녹색
        print("  녹색 신호")
        GPIO.output(LED_GREEN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(LED_GREEN, GPIO.LOW)
        
        # 노랑
        print("  노란 신호")
        GPIO.output(LED_YELLOW, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(LED_YELLOW, GPIO.LOW)
        
        # 빨강
        print("  빨간 신호")
        GPIO.output(LED_RED, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(LED_RED, GPIO.LOW)
        
        time.sleep(0.5)

def test_all_on():
    """모든 LED 동시 점등 테스트"""
    print("\n모든 LED 동시 점등 테스트...")
    GPIO.output(LED_RED, GPIO.HIGH)
    GPIO.output(LED_YELLOW, GPIO.HIGH)
    GPIO.output(LED_GREEN, GPIO.HIGH)
    time.sleep(2)
    all_off()

try:
    # 초기화
    all_off()
    
    # 테스트 실행
    test_individual()  # 개별 테스트
    test_pattern()     # 신호등 패턴
    test_all_on()      # 모두 켜기
    
    print("\nLED 테스트 완료!")

except KeyboardInterrupt:
    print("\n프로그램 종료")

finally:
    # 정리
    all_off()
    GPIO.cleanup()
    print("GPIO 정리 완료")
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
