import serial
import time

# ✅ TGAM 장치 COM 포트 (장치 관리자에서 확인)
COM_PORT = "COM9"  # 본인 환경에 맞게 수정
BAUD_RATE = 57600

# 시리얼 포트 열기
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"✅ TGAM 연결 성공: {COM_PORT} ({BAUD_RATE}bps)")
except serial.SerialException:
    print("❌ TGAM을 찾을 수 없습니다. 장치 관리자에서 COM 포트 확인 필요!")
    exit()

print("🔍 EEG 데이터 수신 중...")

def parse_packet(packet):
    """TGAM 패킷을 분석하여 Attention, Meditation 값 추출"""
    if len(packet) < 4:
        return None
    
    # HEX 데이터를 바이트 리스트로 변환
    payload_length = packet[2]  # Payload 길이
    payload = packet[3:-1]  # Payload 데이터
    checksum = packet[-1]  # Checksum 값
    
    # Checksum 검증
    calculated_checksum = sum(payload) & 0xFF  # 합산 후 하위 8비트 유지
    if (0xFF - calculated_checksum) != checksum:
        print("❌ Checksum 오류: 데이터 손상 가능")
        return None
    
    # EEG 데이터 추출
    attention = None
    meditation = None

    index = 0
    while index < len(payload):
        code = payload[index]
        if code == 0x04:  # Attention 값
            attention = payload[index + 1]
            index += 2
        elif code == 0x05:  # Meditation 값
            meditation = payload[index + 1]
            index += 2
        else:
            index += 1  # 다음 데이터로 이동

    return attention, meditation

# 데이터 수신 루프
buffer = []
while True:
    if ser.in_waiting:
        byte = ser.read(1)  # 1바이트씩 읽기
        buffer.append(ord(byte))

        # TGAM 패킷의 시작은 항상 0xAA 0xAA
        if len(buffer) > 2 and buffer[-2] == 0xAA and buffer[-1] == 0xAA:
            if len(buffer) > 3:
                packet_length = buffer[-3]
                if len(buffer) >= packet_length + 4:
                    parsed_data = parse_packet(buffer[-(packet_length + 4):])
                    if parsed_data:
                        attention, meditation = parsed_data
                        print(f"🧠 집중도(Attention): {attention}, 이완도(Meditation): {meditation}")
                    buffer = []  # 버퍼 초기화
    time.sleep(0.1)
