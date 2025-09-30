# main.py  (Pico 2 W / MicroPython)
import network, socket, ujson as json
from machine import Pin, I2C
import utime as time

# ===== 사용자 설정 =====
WIFI_SSID = "COS_ROOM"
WIFI_PASS = "cos15511118"
MY_DIR    = "N"     # "N" | "E" | "S" | "W"
UDP_PORT  = 5005

# ===== OLED 초기화 (부팅 배너 먼저) =====
I2C_ID, PIN_SDA, PIN_SCL = 0, 0, 1   # 필요시 4,5로 바꿔보세요
OLED_W, OLED_H = 128, 64

try:
    import ssd1306
except ImportError:
    raise SystemExit("ssd1306.py 필요")

i2c  = I2C(I2C_ID, sda=Pin(PIN_SDA), scl=Pin(PIN_SCL), freq=400000)
oled = ssd1306.SSD1306_I2C(OLED_W, OLED_H, i2c)

def banner(msg1, msg2=""):
    oled.fill(0)
    oled.text(msg1, 0, 0)
    if msg2:
        oled.text(msg2, 0, 10)
    oled.show()

# 부팅 배너 + I2C 주소 표시
try:
    addrs = i2c.scan()
    banner("BOOT...", "I2C:"+str(addrs))
except Exception as e:
    banner("I2C FAIL", str(e)[:16])
    raise

# ===== 선명한 3x5 숫자 폰트 (스케일 가능) =====
GLYPH_3x5 = {
    "0": ["###","# #","# #","# #","###"],
    "1": [" ##","  #","  #","  #"," ###"],
    "2": ["###","  #","###","#  ","###"],
    "3": ["###","  #"," ##","  #","###"],
    "4": ["# #","# #","###","  #","  #"],
    "5": ["###","#  ","###","  #","###"],
    "6": ["###","#  ","###","# #","###"],
    "7": ["###","  #","  #"," # "," # "],
    "8": ["###","# #","###","# #","###"],
    "9": ["###","# #","###","  #","###"],
    "s": [" ##","#  "," ##","  #","## "],
}

def draw_char_scaled(x, y, ch, scale=3):
    """3x5 글꼴을 scale배로 그립니다. 반환값은 그린 뒤의 x 증가폭."""
    g = GLYPH_3x5.get(ch)
    if not g:
        return (3 + 1) * scale  # 미정의 문자는 공백 폭
    for r, row in enumerate(g):
        for c, pix in enumerate(row):
            if pix == "#":
                for dy in range(scale):
                    for dx in range(scale):
                        oled.pixel(x + c*scale + dx, y + r*scale + dy, 1)
    return (3 + 1) * scale  # 글자폭(3) + 1칸 간격



# ===== 표시 함수(헤더 한 줄↓, 숫자 깨끗하게) =====
# === 교체: 숫자만 크게 찍는 함수 ===
def draw_big_number(value, x=70, y=26, scale=3):
    s = str(value)
    cx = x
    for ch in s:
        cx += draw_char_scaled(cx, y, ch, scale)

# === 교체: 화면 레이아웃 ===
def draw_wait(dir_tag, trem, gdur):
    oled.fill(0)
    # 1줄: 상태만
    oled.text("WAIT", 0, 8)
    # 2줄: 시간(숫자만 크게)
    draw_big_number(trem, y=26, scale=3)
    # 3줄: 보조정보(그대로)
    oled.text(f"next g: {gdur}s", 0, 54)
    oled.show()

def draw_go(dir_tag, trem, gdur):
    oled.fill(0)
    # 1줄: 상태만
    oled.text("GO", 0, 8)
    # 2줄: 시간(숫자만 크게)
    draw_big_number(trem, y=26, scale=3)
    # 3줄: 보조정보(그대로)
    oled.text(f"slot g: {gdur}s", 0, 54)
    oled.show()

# ===== Wi‑Fi 연결 =====
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 15000:
                banner("WiFi FAIL", "Check SSID/PASS")
                raise SystemExit("WiFi timeout")
            time.sleep_ms(200)
    ip = wlan.ifconfig()[0]
    banner("WiFi OK:"+ip, "DIR:"+MY_DIR)
    time.sleep(1)
    return ip

# ===== UDP 수신 루프 =====
def recv_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        pass
    s.bind(("0.0.0.0", UDP_PORT))
    banner("Listening "+str(UDP_PORT), "DIR:"+MY_DIR)
    while True:
        try:
            data, addr = s.recvfrom(1024)
            obj  = json.loads(data)
            dirs = obj.get("directions", {})
            my   = dirs.get(MY_DIR)
            if not my:
                banner("NO DIR "+MY_DIR, "check payload")
                continue
            phase = my.get("phase", "RED")
            trem  = int(my.get("t_rem", 0))
            gdur  = int(my.get("g_dur", 5))
            if phase == "GREEN":
                draw_go(MY_DIR, trem, gdur)
            else:
                draw_wait(MY_DIR, trem, gdur)
        except Exception as e:
            banner("RX ERROR", str(e)[:16])
            time.sleep(0.3)

# ===== 메인 =====
try:
    wifi_connect()
    recv_loop()
except Exception as e:
    banner("FATAL", str(e)[:16])
    raise

