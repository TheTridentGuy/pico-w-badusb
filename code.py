import wifi
import socketpool
import usb_hid
import pwmio
import digitalio
import board
import time
from adafruit_hid import keyboard, keycode, keyboard_layout_us
from adafruit_httpserver import Server, Request, Response, FileResponse


AP_SSID = ":3"
BRIGHTNESS = 0.5
RED = (1, 0, 0)
GREEN = (0, 1, 0)
BLUE = (0, 0, 1)
YELLOW = (1, 1, 0)
CYAN = (0, 1, 1)
MAGENTA = (1, 0, 1)


wifi.radio.start_ap(AP_SSID, authmode=(wifi.AuthMode.OPEN,))
print(f"SSID: {AP_SSID}, IP: {wifi.radio.ipv4_address_ap}")
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/html", debug=True)
keyboard = keyboard.Keyboard(usb_hid.devices)
layout = keyboard_layout_us.KeyboardLayoutUS(keyboard)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True


class RGBLed:
    def __init__(self, red_pin, green_pin, blue_pin):
        self.red = pwmio.PWMOut(red_pin, frequency=100, duty_cycle=65535)
        self.green = pwmio.PWMOut(green_pin, frequency=100, duty_cycle=65535)
        self.blue = pwmio.PWMOut(blue_pin, frequency=100, duty_cycle=65535)

    def set(self, r, g, b):
        self.red.duty_cycle = 65535 - int(r * 65535 * BRIGHTNESS)
        self.green.duty_cycle = 65535 - int(g * 65535 * BRIGHTNESS)
        self.blue.duty_cycle = 65535 - int(b * 65535 * BRIGHTNESS)

    def rainbow_next(self, cycle_time=10):
        h = (time.monotonic() % cycle_time) / cycle_time

        r = 1 - (self.red.duty_cycle / 65535 / BRIGHTNESS)
        g = 1 - (self.green.duty_cycle / 65535 / BRIGHTNESS)
        b = 1 - (self.blue.duty_cycle / 65535 / BRIGHTNESS)
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        s = 0 if mx == 0 else df / mx
        v = mx

        h *= 6
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)

        if i % 6 == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

        self.red.duty_cycle = int((1 - r) * 65535 * BRIGHTNESS)
        self.green.duty_cycle = int((1 - g) * 65535 * BRIGHTNESS)
        self.blue.duty_cycle = int((1 - b) * 65535 * BRIGHTNESS)

rgb1 = RGBLed(board.GP21, board.GP20, board.GP19)
rgb2 = RGBLed(board.GP18, board.GP17, board.GP16)
button1 = digitalio.DigitalInOut(board.GP27)
button1.direction = digitalio.Direction.INPUT
button2 = digitalio.DigitalInOut(board.GP26)
button2.direction = digitalio.Direction.INPUT


def string(text):
    layout.write(text)

def keydown(*keys):
    keyboard.press(*keys)

def keyup(*keys):
    keyboard.release(*keys)

def allup():
    keyboard.release_all()


@server.route("/")
def index(request: Request):
    return FileResponse(request, "index.html")

rgb1.set(1, 0, 0)
rgb2.set(1, 0, 0)
led.value = False
server.start(str(wifi.radio.ipv4_address_ap), 80)
while True:
    server.poll()
    rgb1.rainbow_next()
    rgb2.rainbow_next()
