# USB Rubber Ducky written in CircuitPython for Raspberry Pi Pico W
## Hardware:
You technically don't need any hardware aside from the Pico W to run this. My hardware setup is viewable at https://wokwi.com/projects/428096216043299841.
## Usage:
- Install CircuitPython from https://circuitpython.org/board/raspberry_pi_pico_w/
- Make the root of your `CIRCUITPY` drive represent this repo. The easiest way to do this is to run `git clone https://github.com/TheTridentGuy/pico-w-badusb.git` from a folder you're ok with cloning a repo into (i.e, your home directory), and then running `cp -r pico-w-badusb/. /run/media/<user>/CIRCUITPY` to copy it over. If some unnecessary files (i.e. `/.git` are copied, you should delete them, as the Pico has very little storage.
- Your Pi Pico should now be set up. Note that on future boots, the `CIRCUITPY` drive won't show up. To re-enable USB mass storage mode, plug it in while shorting `GP26` or `GP27` to `3.3v`. If this fails, you may attempt to use the REPL to delete `boot.py`, which handles this behavior.
- Upon booting, the Pico will start an open wifi network, named `:3` by default (you can change this in `config.py`). Connect to it, and visit the Pico's IP, usually [`http://192.168.4.1/`](http://192.168.4.1/).
- You should now see a list of available scripts, and can run or edit them at your leisure.

## Scripts:
- Scripts (stored by default in `/srcipts` are python, with limited functions available.
### The following functions, every keycode provided by `adafruit_hid.keycode.Keycode`, and basic syntax are supported:
- `string(string)`: type the string `string`.
- `press(*keys)`: press and release `*keys`.
- `keydown(*keys)`: press `*keys` down.
- `keyup(*keys)`: release `*keys`.
- `allup()`: release all keys.
- `sleep(seconds)`: sleep for `seconds` seconds. `seconds` can be a float.
- `wait_for_button1()`: wait for button 1 to be pressed.
- `wait_for_button2()`: wait for button 2 to be pressed.
- `set_rgb1(r, g, b)`: set the first RGB LED to `r`, `g`, and `b` values. `r`, `g`, and `b` can be any value from 0 to 255. This is the LED closest to the Pico in the Wokwi diagram.
- `set_rgb2(r, g, b)`: set the second RGB LED to `r`, `g`, and `b` values. `r`, `g`, and `b` can be any value from 0 to 255. This is the LED furthest from the Pico in the Wokwi diagram.

### Example (`rickroll.script`):
```python
# set both RGB LEDs to red
set_rgb1(255, 0, 0)
set_rgb2(255, 0, 0)

# press the windows key
press(WINDOWS)
# wait a second
sleep(1)
# type a URL
string("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
# wait a second
sleep(1)
# press enter
press(ENTER)
# mischief managed
# RGB leds will automatically go back to rainbow cylcling.
```


## License:
> ### NOTE:
> The CircuitPython libraries in `/lib` are provided under their own license.

    pico-w-badusb - CircuitPython+Rapsberry Pi Pico W badusb.
    Copyright (C) 2025 Aiden Bohlander

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
