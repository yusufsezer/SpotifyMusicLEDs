from Visualizations.Visualizer import Visualizer


class LoudnessLengthEdgeFadeVisualizer(Visualizer):

    def visualize(self, loudness_func, pitch_funcs, pos):
        """Displays a visual on the LED strip based on the loudness and pitch data at current playback position.

        Args:
            strip (strip obj): light strip or visualization including 'set_pixel' and 'fill'.
            num_pixels (int): the number of LEDs on the strip.
            loudness_func (interp1d): interpolated loudness function.
            pitch_funcs (list): a list of interpolated pitch functions (one pitch function for each major musical key).
            pos (float): the current playback position (offset into the track in seconds).
        """

        # Get normalized loudness value for current playback position
        norm_loudness = Visualizer.normalize_loudness(loudness_func(pos))


        #Full strip fill threshold
        color_threshold = 0.75
        length_threshold = 0.85
        # Fading background color to (RED, hardcoded) if over 0.75
        start_color = self.primary_color # (0, 0, 255)
        if norm_loudness > color_threshold:
            start_color = LoudnessLengthEdgeFadeVisualizer\
                .apply_gradient_fade((120, 0, 0), (norm_loudness-color_threshold)/(1-color_threshold), start_color)

        # print("%f: %f" % (pos, norm_loudness))

        # Determine how many pixels to light (growing from the center of the strip) based on normalized loudness
        mid = self.num_pixels // 2
        length = int(self.num_pixels * min(1, norm_loudness/length_threshold))
        lower = mid - round(length / 2)
        upper = mid + round(length / 2)
        brightness = 100

        # Set middle pixel to start_color (when an odd number of pixels are lit, segments don't cover the middle pixel)
        start_r, start_g, start_b = start_color
        self.strip.set_pixel(mid, start_r, start_g, start_b, brightness)

        # Segment strip into 12 zones (1 for each of the pitch keys) and set color based on corresponding pitch strength
        for i in range(0, 12):
            pitch_strength = pitch_funcs[i](pos)
            start = lower + (i * length // 12) if i in range(6) else upper - ((11 - i + 1) * length // 12)
            end = lower + ((i + 1) * length // 12) if i in range(6) else upper - ((11 - i) * length // 12)
            segment_len = end - start
            segment_mid = start + (segment_len // 2)

            # Get the appropriate color based on the current pitch zone and pitch strength
            zone_r, zone_g, zone_b = self._calculate_zone_color(pitch_strength, start_color, self.secondary_color)

            # Fade the strength of the RGB values near the ends of the zone to produce a nice gradient effect
            for j in range(start, end + 1):
                color_strength = (1.0 + (j - start)) / (1.0 + (segment_mid - start))
                if color_strength > 1.0:
                    color_strength = 2.0 - color_strength
                faded_r, faded_g, faded_b = LoudnessLengthEdgeFadeVisualizer\
                    .apply_gradient_fade((zone_r, zone_g, zone_b), color_strength, start_color)
                self.strip.set_pixel(j, faded_r, faded_g, faded_b, brightness)

        # Make sure to turn off pixels that are not in use and push visualization to the strip
        self.strip.fill(0, lower, 0, 0, 0, 0)
        self.strip.fill(upper, self.num_pixels, 0, 0, 0, 0)
        self.strip.show()

    def _calculate_zone_color(self, pitch_strength, start_color, end_color):
        """Calculate the color to visualize based on the pitch/zone index and corresponding pitch strength.

        The visualizer divides the lit portion of the strip into 12 equal-length zones, one for each of the 12 major
        pitch keys. This function calculates what color should be displayed in the zone specified by zone_index if the
        corresponding pitch has strength pitch_strength (0.0 corresponds to lowest strength, 1.0 corresponds to maximum
        strength).

        Args:
            pitch_strength (float): a value representing how strong or present the pitch is (normalized to [0.0, 1.0]).

        Returns:
            a 3-tuple of ints representing the RGB value that should be displayed in the zone specified by zone_index.
        """
        if pitch_strength < 0.0:
            pitch_strength = 0.0
        elif pitch_strength > 1.0:
            pitch_strength = 1.0

        start_r, start_g, start_b = start_color
        end_r, end_g, end_b = end_color
        r_diff, g_diff, b_diff = end_r - start_r, end_g - start_g, end_b - start_b

        r = start_r + int(pitch_strength * r_diff)
        g = start_g + int(pitch_strength * g_diff)
        b = start_b + int(pitch_strength * b_diff)

        return r, g, b
