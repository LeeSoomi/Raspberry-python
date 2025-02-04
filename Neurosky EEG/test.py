import serial

COM_PORT = "COM9"  # TGAM이 연결된 포트 확인 후 수정
BAUD_RATE = 57600

ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

print("🔍 TGAM 데이터 수신 중...")
while True:
    if ser.in_waiting > 0:
        data = ser.read(10)  # 10바이트씩 읽기
        print(f"📡 데이터 수신: {data.hex().upper()}")  # HEX 형식 출력
