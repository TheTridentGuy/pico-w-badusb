import wifi
import socketpool
import usb_hid
import pwmio
import digitalio
import board
import time
import asyncio
from adafruit_hid import keyboard, keycode, keyboard_layout_us
from adafruit_httpserver import Server, Request, Response, FileResponse


AP_SSID = ":3"
BRIGHTNESS = 0.1
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
        self.color = (0, 0, 0)
        self.blink_time = 0
        self.rainbow_time = 10

    def set(self, r, g, b, end_rainbow=True, end_blink=True):
        if end_rainbow:
            self.rainbow_time = 0
        if end_blink:
            self.blink_time = 0
        self.color = (r, g, b)
        self.red.duty_cycle = 65535 - int((r / 255) * 65535 * BRIGHTNESS)
        self.green.duty_cycle = 65535 - int((g / 255) * 65535 * BRIGHTNESS)
        self.blue.duty_cycle = 65535 - int((b / 255) * 65535 * BRIGHTNESS)

    def blink_next(self):
        if self.blink_time == 0:
            return
        if int(time.monotonic() * (1 / self.blink_time)) % 2 == 0:
            self.set(*self.color, end_blink=False)
        else:
            self.set(0, 0, 0, end_rainbow=False, end_blink=False)
        
    def rainbow_next(self):
        if self.rainbow_time == 0:
            return
        h = (time.monotonic() % self.rainbow_time) / self.rainbow_time
        h *= 6
        i = int(h)
        f = h - i
        p = 0
        q = 1 - f
        t = f

        if i % 6 == 0:
            r, g, b = 1, t, p
        elif i == 1:
            r, g, b = q, 1, p
        elif i == 2:
            r, g, b = p, 1, t
        elif i == 3:
            r, g, b = p, q, 1
        elif i == 4:
            r, g, b = t, p, 1
        else:
            r, g, b = 1, p, q

        self.set(int(r * 255), int(g * 255), int(b * 255), end_rainbow=False, end_blink=False)

    def next(self):
        if self.blink_time > 0:
            self.blink_next()
        if self.rainbow_time > 0:
            self.rainbow_next()

rgb1 = RGBLed(board.GP21, board.GP20, board.GP19)
rgb2 = RGBLed(board.GP18, board.GP17, board.GP16)
rgb1.rainbow_time = 10
rgb2.rainbow_time = 10
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

async def rgb_event_loop():
    while True:
        rgb1.next()
        rgb2.next()
        await asyncio.sleep(0.05)

async def server_event_loop():
    while True:
        server.poll()
        await asyncio.sleep(0.01)

async def main():
    server.start(str(wifi.radio.ipv4_address_ap), 80)
    rgb_task = asyncio.create_task(rgb_event_loop())
    server_task = asyncio.create_task(server_event_loop())
    await asyncio.gather(rgb_task, server_task)

asyncio.run(main())
