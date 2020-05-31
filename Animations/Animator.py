class Animator:
    """Similar to a Visualizer object, but does not require Spotify data to render
    visualizations onto the strip. Useful for loading animations, for example.
    """

    def __init__(self, strip, num_pixels, frame_rate=0.03, pos=0):
        self.strip = strip
        self.num_pixels = num_pixels
        self.frame_rate = frame_rate
        self.pos = pos,
        self.start_pixel = 0

    def animate(self):
        raise NotImplementedError("All animations must have a custom 'animate' method.")
