class Visualizer:

    def __init__(self, strip, num_pixels, primary_color=(0, 0, 255), secondary_color=(255, 211, 62)):
        self.strip = strip
        self.num_pixels = num_pixels
        self.primary_color = primary_color
        self.secondary_color = secondary_color

    def visualize(self):
        raise NotImplementedError("All visualizations must have a custom 'visualize' method.")

    @staticmethod
    def normalize_loudness(loudness, range_min=-54.0, range_max=-4.0):
        """Normalize a loudness value to the range specified.

                Args:
                    loudness (float): the loudness value to normalize.
                    range_min (float): the lower bound of the range.
                    range_max (float): the upper bound of the range.

                Returns:
                    the normalized loudness value (float between 0.0 and 1.0) for the specified range.
                """
        if loudness > range_max:
            return 1.0
        if loudness < range_min:
            return 0.0
        range_size = range_max - range_min
        return (loudness - range_min) / range_size

    @staticmethod
    def apply_gradient_fade(goal_color, strength, start_color):
        """Fade the passed RGB value towards start_color based on strength

        Note that a strength value of 0.0 results in the start color of the gradient, and a strength value of 1.0
        results in the same RGB color that was passed (no fade is applied).

        Args:
             goal_color (int tuple): Represents an RGB value representing the color to fade to.
             strength (float): a strength value representing how strong the RGB color should be (in range [0.0, 1.0]).
             start_color (int tuple): Represents an RGB value representing the background color of the strip.

        Returns:
            a 3-tuple of ints representing the new faded RGB value.
        """
        start_r, start_g, start_b = start_color
        r_diff, g_diff, b_diff = goal_color[0] - start_r, goal_color[1] - start_g, goal_color[2] - start_b

        faded_r = start_r + int(strength * r_diff)
        faded_g = start_g + int(strength * g_diff)
        faded_b = start_b + int(strength * b_diff)

        return faded_r, faded_g, faded_b

    def get_visualization_device(self):
        return self.strip

    def reset(self):
        self.strip.fill(0, self.num_pixels, 0, 0, 0, 0)
        self.strip.show()

    def set_primary_color(self, color):
        self.primary_color = color

    def set_secondary_color(self, color):
        self.secondary_color = color
