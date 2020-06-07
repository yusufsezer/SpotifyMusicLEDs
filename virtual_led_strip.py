from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor
import sys


class _VirtualLEDStrip:
    """A class for launching/controlling a virtual LED strip visualizer

    This class is intended for use with spotify_visualizer.py in developer mode.
    """

    def __init__(self):
        self.visualization_widget = None

    def start_visualization(self):
        """Start the visualization app.
        """
        app = QApplication(sys.argv)
        self.visualization_widget = VisualizationWidget()
        sys.exit(app.exec_())

    def show(self):
        """Show (update) the visualization widget.
        """
        if not self.visualization_widget:
            return
        self.visualization_widget.show()

    def set_pixel(self, i, r, g, b, _=0):
        """Set pixel at index i to the specified RGB value. Wraps the set_pixel method of the visualization widget.

        Optional parameter is included to conform to the LED strip behaviors expected by SpotifyVisualizer. Its
        value is ignored.

        Args:
            i (int): the index of the pixel to set.
            r (int): an int in range [0, 255] describing the red value to set.
            g (int): an int in range [0, 255] describing the green value to set.
            b (int): an int in range [0, 255] describing the blue value to set.
            _ (int): a brightness value in range [0, 100]; this value is ignored.
        """
        if not self.visualization_widget:
            return
        self.visualization_widget.set_pixel(i, r, g, b)

    def fill(self, start, end, r, g, b, _=0):
        """Set all pixels between indices start and end (inclusive) to the specified RGB value. Wraps the fill method
        of the visualization widget

        Optional parameter is included to conform to the LED strip behaviors expected by SpotifyVisualizer. Its
        value is ignored.

        Args:
            start (int): the start index of the pixel range to fill (inclusive).
            end (int): the end index of the pixel range to fill (inclusive).
            r (int): an int in range [0, 255] describing the red value to set.
            g (int): an int in range [0, 255] describing the green value to set.
            b (int): an int in range [0, 255] describing the blue value to set.
            _ (int): a brightness value in range [0, 100]; this value is ignored.
        """
        if not self.visualization_widget:
            return
        self.visualization_widget.fill(start, end, r, g, b)


_virtual_led_strip = _VirtualLEDStrip()
def VirtualLEDStrip():
    """A method to effectively make VirtualLEDStrip a singleton class.

    We want VirtualLEDStrip to be a singleton because no matter how many times
    we restart the visualization, the window created should stay the same.
    """
    return _virtual_led_strip


class VisualizationWidget(QWidget):
    """A QWidget to handle initializing a UI and drawing.

    This class is intended for use with VirtualLEDStrip and spotify_visualizer.py in developer mode.
    """

    def __init__(self):
        self.num_pixels = 241
        self.pixels = [QColor(0, 0, 0) for _ in range(self.num_pixels)]
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize and show the window representing the virtual LED strip.
        """
        self.setGeometry(10, 10, 5*self.num_pixels, 20)
        self.setWindowTitle('Spotify Virtual Visualizer')
        super().show()

    def paintEvent(self, e):
        """Invokes self.draw_points whenever a paint event occurs. (Overridden method of QWidget).

        Args:
            e (Exception): any exception that may have occurred.
        """
        qp = QPainter()
        qp.begin(self)
        self.draw_points(qp)
        qp.end()

    def draw_points(self, qp):
        """Paints the current state of the virtual LED strip.

        Args:
            qp (QPainter): the QPainter object to facilitate painting of the virtual LED strip.
        """
        for x in range(self.num_pixels):
            qp.setPen(self.pixels[x])
            for i in range(5):
                for j in range(20):
                    qp.drawPoint(5 * x + i, j)

    def show(self):
        """Update the virtual LED strip.
        """
        self.update()

    def set_pixel(self, i, r, g, b):
        """Set pixel at index i to the specified RGB value.

        Args:
            i (int): the index of the pixel to set.
            r (int): an int in range [0, 255] describing the red value to set.
            g (int): an int in range [0, 255] describing the green value to set.
            b (int): an int in range [0, 255] describing the blue value to set.
            _ (int): a brightness value in range [0, 100]; this value is ignored.
        """
        self.pixels[i] = QColor(r, g, b)

    def fill(self, start, end, r, g, b):
        """Set all pixels between indices start and end (inclusive) to the specified RGB value.

        Args:
            start (int): the start index of the pixel range to fill (inclusive).
            end (int): the end index of the pixel range to fill (inclusive).
            r (int): an int in range [0, 255] describing the red value to set.
            g (int): an int in range [0, 255] describing the green value to set.
            b (int): an int in range [0, 255] describing the blue value to set.
        """
        for i in range(end-start+1):
            self.set_pixel(start+i, r, g, b)
