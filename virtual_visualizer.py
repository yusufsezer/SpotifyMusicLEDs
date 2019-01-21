from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor
import sys


class Visualization:
    def __init__(self):
        self.vw = None

    def start_visualization(self):
        app = QApplication(sys.argv)
        self.vw = VisualizationWidget()
        sys.exit(app.exec_())

    def show(self):
        if not self.vw:
            return
        self.vw.show()

    def set_pixel(self, i, r, g, b, brightness=0):
        if not self.vw:
            return
        self.vw.set_pixel(i, r, g, b, brightness)

    def fill(self, start, end, r, g, b, brightness=0):
        if not self.vw:
            return
        self.vw.fill(start, end, r, g, b, brightness)


class VisualizationWidget(QWidget):
    def __init__(self):
        self.num_pixels = 241
        self.pixels = [QColor(0, 0, 0) for _ in range(self.num_pixels)]
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setGeometry(10, 10, 5*self.num_pixels, 20)
        self.setWindowTitle('Spotify Virtual Visualizer')
        super().show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawPoints(qp)
        qp.end()

    def drawPoints(self, qp):
        for x in range(self.num_pixels):
            qp.setPen(self.pixels[x])
            for i in range(5):
                for j in range(20):
                    qp.drawPoint(5 * x + i, j)

    def show(self):
        self.update()

    def set_pixel(self, i, r, g, b, brightness=0):
        self.pixels[i] = QColor(r, g, b)

    def fill(self, start, end, r, g, b, brightness=0):
        for i in range(end-start+1):
            self.set_pixel(start+i, r, g, b, brightness)
