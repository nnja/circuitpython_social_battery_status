"""
The MIT License

Copyright (c) 2021 Nina Zakharenko and contributors

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import math
import random
import time

import board
import displayio
import neopixel
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
from adafruit_display_text import label
from adafruit_pyportal import PyPortal


class PeriodicTask:
    """Used to run a task every so often without needing to call
    time.sleep() and waste cycles.

    Sub-classes should implement `run`. You should call `update`
    every loop.
    """

    def __init__(self, frequency):
        self.frequency = frequency
        self._last_update_time = 0

    def update(self):
        now = time.monotonic_ns()
        next_update_time = self._last_update_time + int(
            1.0 / self.frequency * 1000000000
        )
        if now > next_update_time:
            self.run()
            self._last_update_time = time.monotonic_ns()

    def run(self):
        pass


class SparkleAnimation(PeriodicTask):
    def __init__(self, frequency, strip):
        super().__init__(frequency)
        self.strip = strip
        self._offset = 0
        self.color = 0

    def run(self):
        color = self.color
        strip = self.strip
        num_pixels = len(self.strip)

        # Normalize the color. It can come in as an integer (like 0xFFAABB) but
        # we want a tuple.
        if isinstance(color, int):
            color = tuple(color.to_bytes(3, "big"))

        base_color = tuple(color_value // 3 for color_value in color)
        strip.fill(base_color)

        num_sparkles = int((random.randint(25, 75) / 100) * num_pixels)

        if color != BLACK:
            positions = set()
            while len(positions) < num_sparkles:
                positions.add(random.randint(0, num_pixels - 1))

            color_multipliers = [
                random.randint(0, 90) / 100 for i in range(num_sparkles)
            ]

            for index, strip_position in enumerate(positions):
                strip[strip_position] = tuple(
                    int(color_value * color_multipliers[index]) for color_value in color
                )

        strip.show()


def create_buttons(width=320, height=40, offset=10):
    """
    Based on code from:
        https://learn.adafruit.com/pyportal-neopixel-color-oicker
    """
    buttons = []

    x = offset
    y = offset + int(height * 1.5)

    for text_label, color in color_labels.items():
        button = Button(
            x=x,
            y=y,
            width=width,
            height=height,
            style=Button.SHADOWROUNDRECT,
            fill_color=color,
            outline_color=0x222222,
            name=text_label,
            label=text_label,
            label_font=arial_font,
            label_color=0xFFFFFF,
        )
        buttons.append(button)
        y += 40
    return buttons


def create_initial_screen():
    pyportal.splash.append(social_status_label)

    for button in buttons:
        button_group.append(button.group)
    pyportal.splash.append(button_group)


def create_back_button():
    back_button = Button(
        x=10,
        y=200,
        width=80,
        height=40,
        style=Button.SHADOWROUNDRECT,
        fill_color=(0, 0, 0),
        outline_color=0x222222,
        name="back",
        label="back",
        label_font=arial_font,
        label_color=0xFFFFFF,
    )

    buttons.append(back_button)
    back_button_group.append(back_button.group)
    pyportal.splash.append(back_button_group)
    back_button_group.hidden = True


def init():
    strip.fill(BLACK)
    create_initial_screen()
    create_back_button()


BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 170, 0)
GREEN = (0, 180, 0)

GREEN_LABEL = "full"
YELLOW_LABEL = "low"
RED_LABEL = "empty"

color_labels = {
    RED_LABEL: RED,
    YELLOW_LABEL: YELLOW,
    GREEN_LABEL: GREEN,
}

status_backgrounds = {
    GREEN_LABEL: "images/full.bmp",
    YELLOW_LABEL: "images/low.bmp",
    RED_LABEL: "images/empty.bmp",
}

strip = neopixel.NeoPixel(
    board.D4,
    n=24,
    brightness=0.1,
    auto_write=False,  # Requires calling strip.show() to change neopixel values
)

arial_font = bitmap_font.load_font("/fonts/LeagueSpartan-Bold-16.bdf")
background_color = 0x0
pyportal = PyPortal(default_bg=background_color)
pixel_pattern = SparkleAnimation(strip=strip, frequency=12)
buttons = create_buttons()
button_group = displayio.Group()
back_button_group = displayio.Group()
social_status_label = label.Label(
    bitmap_font.load_font("/fonts/Junction-regular-24.bdf"),
    text="Social Battery",
    color=0xFFFFFF,
    x=30,
    y=30,
)

init()

while True:
    touch = pyportal.touchscreen.touch_point
    if touch:
        for button in buttons:
            if button.contains(touch):
                if button.name == "back":
                    back_button_group.hidden = True
                    button_group.hidden = False
                    social_status_label.hidden = False
                    pyportal.set_background(background_color)
                if button.name in status_backgrounds:
                    back_button_group.hidden = False
                    button_group.hidden = True
                    social_status_label.hidden = True
                    pyportal.set_background(status_backgrounds[button.name])
                    pixel_pattern.color = button.fill_color
                break

    pixel_pattern.update()
