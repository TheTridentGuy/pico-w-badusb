import board
import digitalio
import pwmio
import storage
import time
from config import BRIGHTNESS

button1 = digitalio.DigitalInOut(board.GP27)
button1.direction = digitalio.Direction.INPUT
button2 = digitalio.DigitalInOut(board.GP26)
button2.direction = digitalio.Direction.INPUT

if not button1.value and not button2.value:
    storage.disable_usb_drive()
else:
    red_pwm1 = pwmio.PWMOut(board.GP21, frequency=100, duty_cycle=65535-(BRIGHTNESS * 65535))
    red_pwm2 = pwmio.PWMOut(board.GP18, frequency=100, duty_cycle=65535-(BRIGHTNESS * 65535))
    time.sleep(3)
