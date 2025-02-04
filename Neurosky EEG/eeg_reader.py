import serial
import time

# ✅ TGAM 연결할 COM 포트 설정 (장치 관리자에서 확인)
COM_PORT = "COM9"  # 본인 장치의 포트 번호로 변경!
BAUD_RATE = 57600

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"✅ TGAM 연결 성공: {COM_PORT} ({BAUD_RATE}bps)")
except serial.SerialException:
    print("❌ TGAM을 찾을 수 없습니다. 장치 관리자에서 COM 포트 확인 필요!")
    exit()

print("🔍 데이터 수신 대기 중...")

while True:
    if ser.in_waiting:
        raw_data = ser.read(10)  # 10바이트씩 읽기
        hex_data = " ".join(f"{byte:02X}" for byte in raw_data)  # HEX 변환
        print(f"[Taurus TGAM EEG] Raw HEX Data: {hex_data}")
    else:
        print("❌ 데이터 없음. TGAM이 신호를 보내는지 확인하세요!")
    time.sleep(1)
