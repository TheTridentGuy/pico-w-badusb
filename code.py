import wifi
import socketpool
import usb_hid
import pwmio
import digitalio
import board
import time
import asyncio
import os
from adafruit_hid import keyboard, keycode, keyboard_layout_us
from adafruit_httpserver import Server, Request, Response


AP_SSID = ":3"
SCRIPT_DIR = "/scripts"
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
server = Server(pool, "/", debug=True)
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

    def _set(self, r, g, b):
        self.red.duty_cycle = 65535 - int((r / 255) * 65535 * BRIGHTNESS)
        self.green.duty_cycle = 65535 - int((g / 255) * 65535 * BRIGHTNESS)
        self.blue.duty_cycle = 65535 - int((b / 255) * 65535 * BRIGHTNESS)
    
    def set(self, r, g, b):
        self.color = (r, g, b)
        self._set(*self.color)
        
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

        self.color = (int(r * 255), int(g * 255), int(b * 255))

    def next(self):
        if self.blink_time > 0:
            if time.monotonic() % (self.blink_time * 2) < self.blink_time:
                self.rainbow_next()
                self._set(*self.color)
            else:
                self._set(0, 0, 0)
        else:
            self.rainbow_next()
            self._set(*self.color)

rgb1 = RGBLed(board.GP21, board.GP20, board.GP19)
rgb2 = RGBLed(board.GP18, board.GP17, board.GP16)
rgb1.set(255, 0, 0)
rgb2.set(255, 0, 0)
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
    files = os.listdir(SCRIPT_DIR)
    HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USB Rubber Ducky</title>
    <style>
        * {
            font-family: sans-serif;
        }
        body {
            display: flex;
        }
        .flex-row {
            display: flex;
            flex-direction: row;
        }
        .flex-grow {
            flex-grow: 1;
        }
    </style>
</head>
<body>
    <div class="flex-col flex-grow">
        <div class="flex-row">
            <h1>Scripts:</h1>
            <div class="flex-grow"></div>
            <a href="/console">[go to console]</a>
        </div>
        <hr>
        <div class="flex-col flex-grow">"""+"".join([f"""
            <div class="flex-row">
                <span>{file}</span>
                <div class="flex-grow"></div>
                <a href="/edit/{file}">[edit]</a>
                ---
                <a href="/run/{file}">[quick run]</a>
            </div>
            <hr>
            """ for file in files])+"""
        </div>
    </div>
</body>
</html>"""
    return Response(request, HTML, content_type="text/html")

@server.route("/edit/<filename>")
def edit(request: Request, filename: str):
    try:
        with open(SCRIPT_DIR+"/"+filename, "r") as f:
            content = f.read()
    except OSError:
        content = None
    HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USB Rubber Ducky</title>
    <style>
        * {
            font-family: sans-serif;
        }
        body {
            display: flex;
        }
        .flex-row {
            display: flex;
            flex-direction: row;
        }
        .flex-grow {
            flex-grow: 1;
        }
        textarea {
            height: 100%;
        }
    </style>
</head>"""+f"""
<body>
    <div class="flex-col flex-grow">
        <div class="flex-row">
            <h1>{filename}</h1>
            <div class="flex-grow"></div>
            <a href="/console">[go to console]</a>
        </div>
        <hr>
        <div class="flex-col flex-grow">
            <div class="flex-row">
                <div class="flex-grow"></div>
                <a href="/run/{filename}">[run]</a>
            </div>
            <hr>
            <div class="flex-row flex-grow">
                <textarea name="" id="" class="flex-col flex-grow">{content}</textarea>
            </div>
        </div>
    </div>
</body>
</html>"""
    return Response(request, HTML, content_type="text/html")

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
    rgb1.rainbow_time = 10
    rgb2.rainbow_time = 10
    await asyncio.gather(rgb_task, server_task)
asyncio.run(main())
