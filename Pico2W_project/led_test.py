#!/usr/bin/env python3
# led_quick_test.py - 빠른 테스트

import sys
print(f"Python 경로: {sys.executable}")

try:
    from gpiozero import LED
    from time import sleep
    
    print("gpiozero 임포트 성공!")
    
    # LED 하나만 간단히 테스트
    led = LED(17)  # 빨간 LED
    
    print("빨간 LED 5회 깜빡임...")
    for i in range(5):
        led.on()
        print(f"  {i+1}회 - ON")
        sleep(0.5)
        led.off()
        print(f"  {i+1}회 - OFF")
        sleep(0.5)
    
    print("테스트 완료!")
    
except ImportError as e:
    print(f"Import 오류: {e}")
    print("\n터미널에서 다음 명령으로 실행하세요:")
    print("python3 led_quick_test.py")
    
except Exception as e:
    print(f"기타 오류: {e}")
