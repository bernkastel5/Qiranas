# screen_capture.py

from PyQt5 import QtWidgets, QtGui, QtCore
import sys
from PIL import ImageGrab

class SnippingWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.setWindowOpacity(0.3)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.rect = None

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('red'), 2))
        if not self.begin.isNull() and not self.end.isNull():
            qp.drawRect(QtCore.QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        self.rect = QtCore.QRect(self.begin, self.end)
        self.close()

def capture_area_with_selection():
    app = QtWidgets.QApplication(sys.argv)
    snipper = SnippingWidget()
    snipper.show()
    app.exec_()
    if snipper.rect:
        x1 = min(snipper.rect.topLeft().x(), snipper.rect.bottomRight().x())
        y1 = min(snipper.rect.topLeft().y(), snipper.rect.bottomRight().y())
        x2 = max(snipper.rect.topLeft().x(), snipper.rect.bottomRight().x())
        y2 = max(snipper.rect.topLeft().y(), snipper.rect.bottomRight().y())
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        return img
    return None
