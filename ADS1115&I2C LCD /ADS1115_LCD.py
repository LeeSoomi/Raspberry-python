import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# I2C 초기화
i2c = busio.I2C(board.SCL, board.SDA)

# ADS1115 초기화 (주소 0x48)
ads = ADS1115(i2c, address=0x48)
chan = AnalogIn(ads, ADS1115.P0)

# I2C LCD 초기화 (주소 0x27)
lcd_columns = 16
lcd_rows = 2
lcd = character_lcd.Character_LCD_I2C(i2c, lcd_columns, lcd_rows, address=0x27)

# 데이터를 읽어와서 LCD에 출력
while True:
    sound_level = chan.value    # ADC 값을 읽음
    voltage = chan.voltage      # 전압으로 변환
    lcd.clear()
    lcd.message = f"Sound: {sound_level}\nVoltage: {voltage:.2f}V"
    time.sleep(1)  # 1초마다 갱신
