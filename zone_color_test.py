"""A module to help experiment with different color combinations for 12-zone pitch visuazization
"""
import apa102
import time

def _apply_gradient_fade(r, g, b, strength):
    """Fade the passed RGB value towards the gradient start color based on strength

    Note that a strength value of 0.0 results in the start color of the gradient, and a strength value of 1.0
    results in the same RGB color that was passed (no fade is applied)

    Args:
         r (int): represents the red value (in range [0, 255]) of the RGB color to fade
         b (int): represents the blue value (in range [0, 255]) of the RGB color to fade
         g (int): represents the green value (in range [0, 255]) of the RGB color to fade
         strength (float): a strength value representing how strong the RGB color should be (in range [0.0, 1.0])

    Returns:
        a 3-tuple of ints representing the RGB value with fade applied
    """
    start_r, start_g, start_b = start_color
    r_diff, g_diff, b_diff = r - start_r, g - start_g, b - start_b

    faded_r = start_r + int(strength * r_diff)
    faded_g = start_g + int(strength * g_diff)
    faded_b = start_b + int(strength * b_diff)

    return faded_r, faded_g, faded_b

# Initialize strip
num_pixels = 240
strip = apa102.APA102(num_led=num_pixels, global_brightness=20, mosi=10, sclk=11, order='rgb')

# Initialize colors for visualization
start_color = (0, 0, 0xFF)
end_colors = {
            0: (0xFF, 0xFF, 0xFF),
            1: (0xF5, 0xE7, 0xE7),
            2: (0xEC, 0xD0, 0xD0),
            3: (0xE3, 0xB9, 0xB9),
            4: (0xD9, 0xA2, 0xA2),
            5: (0xD0, 0x8B, 0x8B),
            6: (0xC7, 0x73, 0x73),
            7: (0xBE, 0x5C, 0x5C),
            8: (0xB4, 0x45, 0x45),
            9: (0xAB, 0x2E, 0x2E),
            10: (0xA2, 0x17, 0x17),
            11: (0x99, 0, 0)
        }

brightness = 100

# Fill strip with start color
start_r, start_g, start_b = start_color
strip.fill(0, num_pixels, start_r, start_g, start_b, brightness)
strip.show()

# Segment strip into 12 zones (1 zone for each of the 12 pitch keys)
for i in range(0, 12):
    if i in range(6):
        start = i * num_pixels // 12
        end = (i + 1) * num_pixels // 12
    else:
        start = num_pixels - ((11 - i + 1) * num_pixels // 12)
        end = num_pixels - ((11 - i) * num_pixels // 12)
    segment_len = end - start
    segment_mid = start + (segment_len // 2)

    r, g, b = end_colors[i]

    # Fade zone to full strength and back
    for j in range(201):
        strength = j / 100
        if strength > 1.0:
            strength = 2.0 - strength
        faded_r, faded_g, faded_b = _apply_gradient_fade(r, g, b, strength)
        strip.fill(start, end, faded_r, faded_g, faded_b, brightness)
        strip.show()
        time.sleep(0.02)