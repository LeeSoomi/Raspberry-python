import serial
import struct
import time

# 시리얼 포트 설정
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=2)

def read_pms3003():
    byte = 0
    while byte != b'\x42':
        byte = ser.read(size=1)
    data = ser.read(size=31)

    if data[0] == 0x4d:
        frame_len = struct.unpack(">H", data[1:3])[0]
        if frame_len == 28:
            values = struct.unpack(">HHHHHHHHHHHHHH", data[3:])
            pm1_0_cf = values[0]
            pm2_5_cf = values[1]
            pm10_cf = values[2]
            pm1_0_atm = values[3]
            pm2_5_atm = values[4]
            pm10_atm = values[5]
            return pm1_0_atm, pm2_5_atm, pm10_atm
    return None, None, None

try:
    while True:
        pm1_0, pm2_5, pm10 = read_pms3003()
        if pm1_0 is not None:
            print(f"PM1.0: {pm1_0} µg/m³, PM2.5: {pm2_5} µg/m³, PM10: {pm10} µg/m³")
        time.sleep(1)

except KeyboardInterrupt:
    ser.close()
