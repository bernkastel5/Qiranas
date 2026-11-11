# screen_capture.py

import sys
import io
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QBuffer, QIODevice
from PySide6.QtGui import QPainter, QPen, QColor, QCursor
from PIL import Image


class SnippingWidget(QWidget):
    # Сигнал, который вернет захваченное изображение (PIL Image)
    captured = Signal(object)

    def __init__(self):
        super().__init__()
        # Окно на весь экран, поверх всех, без рамок
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(QCursor(Qt.CrossCursor))

        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False

        # Затемняем фон
        self.overlay_color = QColor(0, 0, 0, 100)

    def start_snip(self):
        """Сброс состояния и показ окна"""
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False

        # Получаем экран, где сейчас мышь
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)

        if not screen:
            screen = QApplication.primaryScreen()

        # Устанавливаем геометрию на весь этот экран
        self.setGeometry(screen.geometry())

        self.show()
        self.activateWindow()
        self.raise_()

    def paintEvent(self, event):
        qp = QPainter(self)
        # Заливаем весь экран полупрозрачным черным
        qp.fillRect(self.rect(), self.overlay_color)

        if self.is_snipping:
            # Вырезаем "дырку" (прозрачную область) там, где выделение
            r = QRect(self.begin, self.end).normalized()
            qp.setCompositionMode(QPainter.CompositionMode_Clear)
            qp.fillRect(r, Qt.transparent)

            # Рисуем красную рамку вокруг
            qp.setCompositionMode(QPainter.CompositionMode_SourceOver)
            qp.setPen(QPen(QColor('red'), 2))
            qp.setBrush(Qt.NoBrush)
            qp.drawRect(r)

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

        # Нормализуем координаты
        r = QRect(self.begin, self.end).normalized()

        # Защита от случайных кликов
        if r.width() > 5 and r.height() > 5:
            # Получаем экран и его параметры
            screen = self.screen()
            full_pixmap = screen.grabWindow(0)
            dpr = screen.devicePixelRatio()

            # Пересчитываем логические координаты окна в физические пиксели скриншота
            x = int(r.x() * dpr)
            y = int(r.y() * dpr)
            w = int(r.width() * dpr)
            h = int(r.height() * dpr)

            # Вырезаем
            cropped = full_pixmap.copy(x, y, w, h)

            # Конвертируем
            img = self._pixmap_to_pil(cropped)
            self.captured.emit(img)
        else:
            self.captured.emit(None)

    def _pixmap_to_pil(self, pixmap):
        """Конвертирует QPixmap (PySide6) в PIL Image"""
        # 1. Создаем Qt буфер
        qbuffer = QBuffer()
        qbuffer.open(QIODevice.WriteOnly)

        # 2. Сохраняем туда картинку
        pixmap.save(qbuffer, "PNG")

        # 3. Достаем байты и скармливаем их PIL
        pil_data = io.BytesIO(qbuffer.data().data())
        return Image.open(pil_data)


# Глобальный экземпляр
_snipper_instance = None


def get_snipper():
    global _snipper_instance
    if _snipper_instance is None:
        _snipper_instance = SnippingWidget()
    return _snipper_instance