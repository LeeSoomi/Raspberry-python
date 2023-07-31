'''chapter03_CA_autogate.py v1.0'''

import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

TRGI=23
ECHO=24
SERVO_PIN = 12
print("Auto gate")
GPIO.setup(TRGI, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.output(TRGI, False)

servo=GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

print("Waiting for sensor to settle")
time.sleep(2)

try:
    while True:
        GPIO.output(TRGI, True)
        time.sleep(0.00001)
        GPIO.output(TRGI, False)
        
        while GPIO.input(ECHO)==0:
            start=time.time()
        while GPIO.input(ECHO)==1:
            stop=time.time()
        check_time = stop - start
        distance=check_time * 34300/2
        if distance <= 10:
            servo.ChangeDutyCycle(7.5)
            time.sleep(5)
        elif distance > 10:
            servo.ChangeDutyCycle(2.5)
            time.sleep(0.5)
        
except KeyboardInterrupt:
    print("Measurement stopped by User")
    GPIO.cleanup()
