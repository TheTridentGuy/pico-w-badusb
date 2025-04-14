import board
import digitalio
import storage
import time

button1 = digitalio.DigitalInOut(board.GP27)
button1.direction = digitalio.Direction.INPUT
button2 = digitalio.DigitalInOut(board.GP26)
button2.direction = digitalio.Direction.INPUT

if not button1.value and not button2.value:
    storage.disable_usb_drive()
else:
    time.sleep(3)
