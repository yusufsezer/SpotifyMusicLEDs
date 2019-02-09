class Visualizer:
    @staticmethod
    def visualize():
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
