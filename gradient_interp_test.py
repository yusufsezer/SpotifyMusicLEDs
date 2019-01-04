# import apa102
import numpy as np
from scipy.interpolate import interp1d

if __name__ == "__main__":
    # strip = apa102.APA102(num_led=num_pixels, global_brightness=20, mosi = 10, sclk = 11, order='rgb')
    x_vals = [_ for _ in range(11)]
    y_values = [
        0x0000FF,
        0x1900E5,
        0x3300CC,
        0x4C00B2,
        0x660099,
        0x7F007F,
        0x990066,
        0xB2004C,
        0xCC0032,
        0xE50019,
        0xFF0000
    ]
    gradient = interp1d(x_vals, y_values, kind="linear", assume_sorted=True)
    for _ in range(1):
        for i in range(101):
            perc = i / 100
            color = int(gradient(perc*10))
            r = (color & 0xFF0000) >> 16
            g = (color & 0x00FF00) >> 8
            b = (color & 0x0000FF)
            strip.fill(0, 239, r, g, b, 100)
            strip.show()
        for i in range(99, -1, -1):
            perc = i / 100
            color = int(gradient(perc * 10))
            r = (color & 0xFF0000) >> 16
            g = (color & 0x00FF00) >> 8
            b = (color & 0x0000FF)
            strip.fill(0, 239, r, g, b, 100)
            strip.show()