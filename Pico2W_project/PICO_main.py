# main.py  (Pico 2 W / MicroPython)
import network, socket, ujson as json
from machine import Pin, I2C
import utime as time

# ===== 사용자 설정 =====
WIFI_SSID = "Cos_iptime"         # ← 필요시 수정
WIFI_PASS = "16440110"      # ← 필요시 수정
MY_DIR    = "N"                # "N" | "E" | "S" | "W" (차량 방향)
UDP_PORT  = 5005               # 중앙 브로드캐스트 수신 포트

# 하트비트(대기 차량 보고)
HB_IP   = "255.255.255.255"
HB_PORT = 5006

# ===== OLED 초기화 =====
I2C_ID, PIN_SDA, PIN_SCL = 0, 0, 1   # 배선에 맞게 (대안: 4,5)
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

# ===== 작은 3x5 숫자글꼴(스케일) =====
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
}

def draw_char_scaled(x, y, ch, scale=3):
    g = GLYPH_3x5.get(ch)
    if not g:
        return (3 + 1) * scale
    for r, row in enumerate(g):
        for c, pix in enumerate(row):
            if pix == "#":
                for dy in range(scale):
                    for dx in range(scale):
                        oled.pixel(x + c*scale + dx, y + r*scale + dy, 1)
    return (3 + 1) * scale  # 문자폭(3)+간격1

def draw_big_number(value, y=26, scale=3):
    s = str(value)
    glyph_w = (3 + 1) * scale
    total_w = len(s) * glyph_w
    x = (OLED_W - total_w) // 2
    cx = x
    for ch in s:
        cx += draw_char_scaled(cx, y, ch, scale)

# ===== 표시 함수 =====
def draw_wait(trem, gdur):
    oled.fill(0)
    oled.text("WAIT", 0, 8)            # 1줄: 상태
    draw_big_number(trem, y=26)        # 2줄: 큰 숫자(가운데)
    oled.text(f"next g: {gdur}s", 0, 54)  # 3줄: 보조
    oled.show()

def draw_go(trem, gdur):
    oled.fill(0)
    oled.text("GO", 0, 8)              # 1줄: 상태
    draw_big_number(trem, y=26)        # 2줄: 큰 숫자(가운데)
    oled.text(f"slot g: {gdur}s", 0, 54)  # 3줄: 보조
    oled.show()

# ===== Wi-Fi 연결 =====
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

# ===== 하트비트 송신 =====
uid_suffix = None
hb_sock = None

def hb_init(my_ip):
    global uid_suffix, hb_sock
    uid_suffix = my_ip.split(".")[-1]  # 간단 UID
    hb_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hb_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

def hb_send():
    if not hb_sock:
        return
    msg = {"uid": f"{MY_DIR}-{uid_suffix}", "dir": MY_DIR}
    try:
        hb_sock.sendto(json.dumps(msg).encode(), (HB_IP, HB_PORT))
    except:
        pass

# ===== 브로드캐스트 수신 루프 =====
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
            my   = obj.get("directions", {}).get(MY_DIR)
            if not my:
                banner("NO DIR "+MY_DIR, "")
                continue

            phase = my.get("phase", "RED")
            trem  = int(my.get("t_rem", 0))
            gdur  = int(my.get("g_dur", 5))

            if phase == "GREEN":
                draw_go(trem, gdur)
            else:
                draw_wait(trem, gdur)
            hb_send()  # 대기 중일 때만 1초마다 보고
        except Exception as e:
            banner("RX ERROR", str(e)[:16])
            time.sleep(0.3)

# ===== 메인 =====
ip = wifi_connect()
hb_init(ip)
recv_loop()
