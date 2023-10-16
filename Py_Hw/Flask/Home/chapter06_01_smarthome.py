'''chapter06_01_smarthome.py v1.0'''

from flask import Flask, request, jsonify
from flask import render_template
import RPi.GPIO as GPIO
import time
import threading


app = Flask(__name__)
LED = 14
sensor = 4
SERVO_PIN = 12

door_status = "Unknown"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(sensor, GPIO.IN)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo=GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def door_thread():
    global door_status
    while True:
        if GPIO.input(sensor) == 1:
            servo.ChangeDutyCycle(7.5)
            time.sleep(1)
            door_status = "open"
        else:
            servo.ChangeDutyCycle(12.5)
            time.sleep(1)
            door_status = "close"

@app.route("/get_door_status")
def get_door_status():
    global door_status
    return jsonify({"door_status": door_status})

@app.route("/")
def home():
    global door_status
    return render_template("index.html", door_status=door_status)

@app.route("/led/on")
def led_on():
    try:
        GPIO.output(LED, GPIO.HIGH)
        return "ok"
    except expression as identifier:
        return "fail"

@app.route("/led/off")
def led_off():
    try:
        GPIO.output(LED, GPIO.LOW)
        return "ok"
    except expression as identifier:
        return "fail"

@app.route("/door/open")
def door_open():
    try:
        servo.ChangeDutyCycle(12.5)
        time.sleep(1)
        return "ok"
    except expression as identifier:
        return "fail"

@app.route("/door/close")
def door_close():
    try:
        servo.ChangeDutyCycle(7.5)
        time.sleep(1)
        return "ok"
    except expression as identifier:
        return "fail"

if __name__ == "__main__":
    door_thread = threading.Thread(target=door_thread)
    door_thread.daemon = True
    door_thread.start()

    app.run(host="192.168.219.100")