'''chapter03_01_servo.py v1.0'''

import RPi.GPIO as GPIO
import time

SERVO_PIN = 12

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

servo=GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

try:
    while True:
        servo.ChangeDutyCycle(7.5)
        time.sleep(3)
        servo.ChangeDutyCycle(12.5)
        time.sleep(3)
        
except KeyboardInterrupt:
    servo.stop()
    GPIO.Cleanup()
