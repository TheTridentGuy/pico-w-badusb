import wifi
import socketpool
import usb_hid
import pwmio
import digitalio
import board
import time
import asyncio
import os
import binascii
from adafruit_hid import keyboard, keyboard_layout_us
from adafruit_hid.keycode import Keycode
from adafruit_httpserver import Server, Request, Response, FileResponse
from adafruit_httpserver.status import *

from config import BRIGHTNESS, AP_SSID, SCRIPT_DIR, DEFAULT_RAINBOW_TIME


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
button1.pull = digitalio.Pull.DOWN
button2 = digitalio.DigitalInOut(board.GP26)
button2.direction = digitalio.Direction.INPUT
button2.pull = digitalio.Pull.DOWN


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
            <h1>USB Rubber Ducky</h1>
            <div class="flex-grow"></div>
            <span><input type="text" id="name" placeholder="awesome.script..."/></span>
            <a href="#" onclick="window.location.href='/edit/'+document.getElementById('name').value">[new script]</a>
            <a href="/keyboard">[go to keyboard]</a>
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
    if not filename:
        return Response(request, "filename is empty", content_type="text/plain", status=BAD_REQUEST_400)
    try:
        with open(SCRIPT_DIR+"/"+filename, "r") as f:
            content = f.read()
    except OSError:
        content = f"# {filename} (new script)"
    HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit Script</title>
    <style>
        * {
            font-family: sans-serif;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        html, body {
            height: 100%;
        }
        body {
            display: flex;
            flex-direction: column;
        }
        .flex-grow {
            flex-grow: 1;
        }
        textarea {
            flex-grow: 1;
            resize: none;
            border: none;
            padding: 10px;
        }
        textarea:focus {
            outline: none;
            border: none;
        }
        .flex-row {
            display: flex;
            flex-direction: row;
        }
        .flex-col {
            display: flex;
            flex-direction: column;
        }
    </style>
</head>"""+f"""
<body>
    <div class="flex-col flex-grow">
        <div class="flex-row">
            <h1>{filename}</h1>
        </div>
        <hr>
        <div class="flex-col flex-grow">
            <div class="flex-row">
                <div class="flex-grow"></div>
                <a href="#" onclick="save()">[save]</a>
                ---
                <a href="/run/{filename}">[run]</a>
            </div>
            <hr>
            <div class="flex-row flex-grow">
                <textarea name="" id="" class="flex-grow">{content}</textarea>
            </div>
            <span id="message"></span>
        </div>
    </div>"""+"""
    <script>
        message = "don't forget to save your changes!";
        document.getElementById("message").innerText = message;
        function save(){
            fetch("/save/"""+filename+"""", {
                method: "POST",
                body: document.querySelector("textarea").value
            }).then((response) => {
                if (response.ok) {
                    document.getElementById("message").innerText = "saved successfully!";
                    setTimeout(() => {
                        document.getElementById("message").innerText = message;
                    }, 5000);
                } else {
                    document.getElementById("message").innerText = "error saving file, http status: " + response.status +", see console for details.";
                    console.log(response);
                    setTimeout(() => {
                        document.getElementById("message").innerText = message;
                    }, 5000);
                }
            })
        }
    </script>
</body>
</html>"""
    return Response(request, HTML, content_type="text/html")

@server.route("/save/<filename>", methods=["POST"])
def save(request: Request, filename: str):
    try:
        with open(SCRIPT_DIR+"/"+filename, "w") as f:
            f.write(request.body.decode())
        return Response(request, "ok", content_type="text/plain")
    except OSError as e:
        print(e)
        return Response(request, "unable to save file", content_type="text/plain", status=INTERNAL_SERVER_ERROR_500)

@server.route("/run/<filename>")
def run(request: Request, filename: str):
    global run_flag, run_script
    run_flag = True
    run_script = filename
    return Response(request, f"running {filename}...", content_type="text/plain")

@server.route("/press/<key>")
def press_key(request: Request, key: str):
    keys = key.split("+")
    keys = [getattr(Keycode, k) for k in keys]
    keys = [k for k in keys if k is not None]
    if len(keys) > 0:
        press(*keys)
        return Response(request, "ok", content_type="text/plain")
    return Response(request, "no keys specified (they should be + seperated)", content_type="text/plain", status=BAD_REQUEST_400)

@server.route("/keydown/<key>")
def keydown_key(request: Request, key: str):
    keys = key.split("+")
    keys = [getattr(Keycode, k) for k in keys]
    keys = [k for k in keys if k is not None]
    if len(keys) > 0:
        keydown(*keys)
        return Response(request, "ok", content_type="text/plain")
    return Response(request, "no keys specified (they should be + seperated)", content_type="text/plain", status=BAD_REQUEST_400)

@server.route("/keyup/<key>")
def keyup_key(request: Request, key: str):
    keys = key.split("+")
    keys = [getattr(Keycode, k) for k in keys]
    keys = [k for k in keys if k is not None]
    if len(keys) > 0:
        keyup(*keys)
        return Response(request, "ok", content_type="text/plain")
    return Response(request, "no keys specified (they should be + seperated)", content_type="text/plain", status=BAD_REQUEST_400)

@server.route("/allup")
def allup_key(request: Request):
    allup()
    return Response(request, "ok", content_type="text/plain")

@server.route("/string", methods=["POST"])
def string_key(request: Request):
    if not request.body:
        return Response(request, "no string specified", content_type="text/plain", status=BAD_REQUEST_400)
    string(request.body.decode())
    return Response(request, "ok", content_type="text/plain")


@server.route("/keyboard")
def get_keyboard(request: Request):
    return FileResponse(request, "keyboard.html", content_type="text/html")

run_flag = False
run_script = None

def string(text):
    layout.write(text)

def press(*keys):
    keyboard.press(*keys)
    time.sleep(0.01)
    keyboard.release(*keys)

def keydown(*keys):
    keyboard.press(*keys)

def keyup(*keys):
    keyboard.release(*keys)

def allup():
    keyboard.release_all()

def sleep(seconds):
    time.sleep(seconds)

def wait_for_button1():
    while not button1.value:
        time.sleep(0.01)

def wait_for_button2():
    while not button2.value:
        time.sleep(0.01)

def set_rgb1(r, g, b, blink_time=0, rainbow_time=0):
    rgb1.blink_time = blink_time
    rgb1.rainbow_time = rainbow_time
    rgb1.set(r, g, b)

def set_rgb2(r, g, b, blink_time=0, rainbow_time=0):
    rgb2.blink_time = blink_time
    rgb2.rainbow_time = rainbow_time
    rgb2.set(r, g, b)


RUN_GLOBALS = {
    "string": string,
    "press": press,
    "keydown": keydown,
    "keyup": keyup,
    "allup": allup,
    "sleep": sleep,
    "wait_for_button1": wait_for_button1,
    "wait_for_button2": wait_for_button2,
    "set_rgb1": set_rgb1,
    "set_rgb2": set_rgb2,
}
all_keycodes = {key: getattr(Keycode, key) for key in dir(Keycode) if not key.startswith("_")}
for key in all_keycodes:
    RUN_GLOBALS[key] = all_keycodes[key]

async def run_event_loop():
    global run_flag, run_script
    while True:
        if run_flag and run_script:
            try:
                with open(SCRIPT_DIR+"/"+run_script, "r") as f:
                    code = f.read()
                exec(code, RUN_GLOBALS)
                rgb1.rainbow_time = DEFAULT_RAINBOW_TIME
                rgb2.rainbow_time = DEFAULT_RAINBOW_TIME
            except Exception as e:
                print(f"Error: {e}")
            finally:
                run_flag = False
        await asyncio.sleep(0.1)

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
    run_task = asyncio.create_task(run_event_loop())
    rgb1.rainbow_time = DEFAULT_RAINBOW_TIME
    rgb2.rainbow_time = DEFAULT_RAINBOW_TIME
    await asyncio.gather(rgb_task, server_task, run_task)
asyncio.run(main())
 # type: ignore