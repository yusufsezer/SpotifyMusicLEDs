from Animations.Animator import Animator

_author_ = "Yusuf Sezer"


class LoadingAnimator(Animator):

    def animate(self):
        """Displays a visual loading animation on the LED strip. Each call to this method
        pushes one frame of the loading animation onto the strip.
        """

        # Move loading bar based on frame rate
        self.start_pixel = self.start_pixel + max(1, int(self.frame_rate * self.num_pixels))
        end_pixel = self.start_pixel + (self.num_pixels // 10)

        self.strip.fill(0, self.num_pixels, 0, 0, 0, 0) # Clear strip
        for idx in range(self.start_pixel, end_pixel):
            self.strip.set_pixel(idx % self.num_pixels, 255, 255, 255, 100)
        self.strip.show()
