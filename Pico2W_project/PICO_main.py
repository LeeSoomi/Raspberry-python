# main.py  (Pico 2 W / MicroPython)
import network, usocket as socket, ujson as json
from machine import Pin, I2C
import utime as time

# ===== 사용자 설정 =====
WIFI_SSID = "COS_ROOM"
WIFI_PASS = "cos15511118"
MY_DIR    = "N"                 # "N" | "E" | "S" | "W"
UDP_PORT  = 5005                # 중앙 브로드캐스트 수신 포트

# 하트비트(대기 차량 보고)
HB_IP   = "255.255.255.255"
HB_PORT = 5006

# ===== OLED =====
I2C_ID, PIN_SDA, PIN_SCL = 0, 0, 1
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

# ===== 3x5 숫자 폰트 =====
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
    return (3 + 1) * scale

def draw_big_number(value, y=26, scale=3):
    s = str(value)
    glyph_w = (3 + 1) * scale
    total_w = len(s) * glyph_w
    x = (OLED_W - total_w) // 2
    cx = x
    for ch in s:
        cx += draw_char_scaled(cx, y, ch, scale)

def draw_wait(trem, gdur):
    oled.fill(0)
    oled.text("WAIT", 0, 8)
    draw_big_number(trem, y=26)
    oled.text("next g: %ss" % gdur, 0, 54)
    oled.show()

def draw_go(trem, gdur):
    oled.fill(0)
    oled.text("GO", 0, 8)
    draw_big_number(trem, y=26)
    oled.text("slot g: %ss" % gdur, 0, 54)
    oled.show()

# ===== Wi-Fi =====
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
    time.sleep(800)
    return ip

# ===== 하트비트 =====
uid_suffix = None
hb_sock = None
last_hb_ms = 0

def hb_init(my_ip):
    global uid_suffix, hb_sock
    uid_suffix = my_ip.split(".")[-1]  # 간단 UID
    hb_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hb_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

def hb_send_if_waiting(phase):
    global last_hb_ms
    if not hb_sock:
        return
    now = time.ticks_ms()
    if phase != "GREEN" and time.ticks_diff(now, last_hb_ms) >= 1000:
        msg = {"uid": "%s-%s" % (MY_DIR, uid_suffix), "dir": MY_DIR}
        try:
            hb_sock.sendto(json.dumps(msg).encode(), (HB_IP, HB_PORT))
        except:
            pass
        last_hb_ms = now

# ===== 수신 소켓 (논블로킹) =====
def make_rx_sock():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        pass
    s.bind(("0.0.0.0", UDP_PORT))
    s.setblocking(False)
    return s

def drain_latest(s):
    """버퍼 비우고 마지막 패킷만 반환"""
    latest = None
    while True:
        try:
            data, _ = s.recvfrom(2048)
            latest = data
        except OSError as e:
            # MicroPython: EAGAIN/WOULDBLOCK일 때 튕김
            break
    return latest

# ===== 메인 루프 =====
def recv_loop():
    s = make_rx_sock()
    banner("Listening %d" % UDP_PORT, "DIR:"+MY_DIR)

    # 표시 상태
    last_tuple = None      # 직전 (phase, trem)
    phase = "RED"
    trem  = None
    gdur  = 5
    total = 20

    last_draw_ms = time.ticks_ms()
    tick1s = time.ticks_ms()

    while True:
        # 1) 최신 패킷만 반영
        raw = drain_latest(s)
        if raw:
            try:
                obj = json.loads(raw)
                # 안전장치: 스키마가 있으면 체크
                if obj.get("src") == "central_hb_v1" and obj.get("schema", 1) != 1:
                    pass  # 다른 스키마는 무시
                d = obj.get("directions", {}).get(MY_DIR)
                if d:
                    p = d.get("phase", "RED")
                    t = int(d.get("t_rem", 0))
                    g = int(d.get("g_dur", 5))
                    tot = int(obj.get("total", 20))

                    # GREEN 마지막 1초는 로컬에서 YELLOW 처리
                    if p == "GREEN" and t == 1:
                        p_show = "YELLOW"
                    else:
                        p_show = p

                    if last_tuple != (p_show, t):
                        last_tuple = (p_show, t)
                        phase, trem, gdur, total = p_show, t, g, tot
            except Exception as e:
                banner("RX ERROR", str(e)[:16])
                time.sleep_ms(200)

        # 2) 1초 타이머로만 숫자 감소 (패킷 중복 와도 깔끔한 역카운트)
        now = time.ticks_ms()
        if trem is not None and time.ticks_diff(now, tick1s) >= 1000:
            tick1s = now
            if trem > 0:
                trem -= 1

            # GREEN 0이 되면 잠정 RED로 전환(다음 패킷 올 때까지 끊김 방지)
            if phase == "GREEN" and trem == 0:
                phase = "RED"
                trem  = total  # 다음 GREEN까지 대기 시작

        # 3) 화면 갱신(200ms 마다)
        if time.ticks_diff(now, last_draw_ms) >= 200:
            last_draw_ms = now
            if phase == "GREEN":
                draw_go(trem if trem is not None else 0, gdur)
            elif phase == "YELLOW":
                # 다음 GREEN까지 대기 남은 시간 표시
                draw_wait(trem if trem is not None else 0, gdur)
            else:
                draw_wait(trem if trem is not None else 0, gdur)

        # 4) 하트비트(대기 중일 때만 1Hz)
        hb_send_if_waiting(phase)

        time.sleep_ms(40)

# ===== 시작 =====
ip = wifi_connect()
hb_init(ip)
recv_loop()
