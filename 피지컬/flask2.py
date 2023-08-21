'''chapter05_02_flask2.py v1.0'''

from flask import Flask
app = Flask(__name__)

@app.route("/")
def helloworld():
    return "Hello World"

@app.route("/led/on")
def led_on():
    return "LED ON"

@app.route("/led/off")
def led_off():
    return "LED OFF"
