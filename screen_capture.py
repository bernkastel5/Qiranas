# screen_capture.py

import sys
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QCursor
from PIL import ImageGrab


class SnippingWidget(QWidget):
    # Сигнал, который вернет захваченное изображение (или None) и режим
    captured = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowOpacity(0.3)
        self.setCursor(QCursor(Qt.CrossCursor))

        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False

    def start_snip(self):
        """Сброс состояния и показ окна"""
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.show()
        # Важно: активируем окно, чтобы оно перехватило фокус мыши
        self.activateWindow()
        self.raise_()

    def paintEvent(self, event):
        if self.is_snipping:
            qp = QPainter(self)
            qp.setPen(QPen(QColor('red'), 2))
            qp.setBrush(Qt.NoBrush)
            qp.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_snipping = False
        self.close()

        # Вычисляем координаты
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        # Проверка на минимальный размер (защита от случайных кликов)
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            # Используем ImageGrab, так как он надежно работает с координатами экрана
            # (PySide grabWindow может путаться с DPI)
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.captured.emit(img)
        else:
            self.captured.emit(None)


# Глобальный экземпляр виджета, чтобы не создавать его каждый раз
_snipper_instance = None


def get_snipper():
    global _snipper_instance
    if _snipper_instance is None:
        _snipper_instance = SnippingWidget()
    return _snipper_instance