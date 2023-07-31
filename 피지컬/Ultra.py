'''chapter03_02_Ultra.py v1.0'''

import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

TRGI=23
ECHO=24
print("Distance measurement in progress")

GPIO.setup(TRGI, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.output(TRGI, False)
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
        print("Distance : %.1f cm" % distance)
        time.sleep(0.4)
        
except KeyboardInterrupt:
    print("Measurement stopped by User")
    GPIO.cleanup()
