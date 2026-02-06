import sys
from PySide6.QtWidgets import QGraphicsEffect, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsBlurEffect, QWidget, QGroupBox, QHBoxLayout, QApplication, QDialog, QFrame, QVBoxLayout

from PySide6.QtGui import QPixmap, QTransform, QPainter, QImage, QColor
from PySide6.QtCore import QRectF, QSize, Qt, QPoint


class BoxShadow(QGraphicsEffect):
    def __init__(self, shadow_list: list[dict] = None, border: int = 3, smooth: bool = True):
        QGraphicsEffect.__init__(self)

        light_outside = [{"outside": True, "offset": [8,8], "blur": 10, "color": "#ffffff"},
                   {"outside": True, "offset": [-8, -8], "blur": 10, "color": "#d0d0d0"}]
        light_inside = [{"inside": True, "offset": [6, 6], "blur": 8, "color": "#C1D5EE"},
                  {"inside": True, "offset": [-6, -6], "blur": 8, "color": "#FFFFFF"}]
        self._shadow_list = []
        self._max_x_offset = 0
        self._max_y_offset = 0
        self._border = 0
        self._smooth = smooth
        self.setShadowList(light_outside)
        self.setBorder(border)

    def setShadowList(self, shadow_list: list[dict] = None):
        if shadow_list is None:
            shadow_list = []
        self._shadow_list = shadow_list

        self._set_max_offset()

    def setBorder(self, border: int):
        if border > 0:
            self._border = border
        else:
            self._border = 0

    def necessary_indentation(self):
        return self._max_x_offset, self._max_y_offset

    def boundingRectFor(self, rect):
        return rect.adjusted(-self._max_x_offset, -self._max_y_offset, self._max_x_offset, self._max_y_offset)

    def _set_max_offset(self):
        for shadow in self._shadow_list:
            if "outside" in shadow.keys():
                if self._max_x_offset < abs(shadow["offset"][0]) + shadow["blur"] * 2:
                    self._max_x_offset = abs(shadow["offset"][0]) + shadow["blur"] * 2
                if self._max_y_offset < abs(shadow["offset"][1]) + shadow["blur"] * 2:
                    self._max_y_offset = abs(shadow["offset"][1]) + shadow["blur"] * 2

    @staticmethod
    def _blur_pixmap(src, blur_radius):
        w, h = src.width(), src.height()

        effect = QGraphicsBlurEffect(blurRadius=blur_radius)

        scene = QGraphicsScene()
        item = QGraphicsPixmapItem()
        item.setPixmap(QPixmap(src))
        item.setGraphicsEffect(effect)
        scene.addItem(item)

        res = QImage(QSize(w, h), QImage.Format_ARGB32)
        res.fill(Qt.transparent)

        ptr = QPainter(res)
        ptr.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        scene.render(ptr, QRectF(), QRectF(0, 0, w, h))
        ptr.end()

        return QPixmap(res)

    @staticmethod
    def _colored_pixmap(color: QColor, pixmap: QPixmap):
        new_pixmap = QPixmap(pixmap)
        new_pixmap.fill(color)
        painter = QPainter(new_pixmap)
        painter.setTransform(QTransform())
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return new_pixmap

    @staticmethod
    def _cut_shadow(pixmap: QPixmap, source: QPixmap, offset_x, offset_y):
        painter = QPainter(pixmap)
        painter.setTransform(QTransform())
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        painter.drawPixmap(offset_x, offset_y, source)
        painter.end()
        return pixmap

    def _outside_shadow(self):

        offset = QPoint()
        mask = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates,
                                 offset).createMaskFromColor(QColor(0, 0, 0, 0),
                                                             Qt.MaskMode.MaskInColor)

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "outside" in _shadow.keys():
                shadow = QPixmap(mask.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
                shadow_painter.setTransform(QTransform())
                shadow_painter.setPen(QColor(_shadow["color"]))
                shadow_painter.drawPixmap(_shadow["offset"][0], _shadow["offset"][1], mask)
                shadow_painter.end()

                _pixmap_shadow_list.append(shadow)

        outside_shadow = QPixmap(mask.size())
        outside_shadow.fill(Qt.transparent)

        outside_shadow_painter = QPainter(outside_shadow)
        outside_shadow_painter.setTransform(QTransform())
        outside_shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        for i, pixmap in enumerate(_pixmap_shadow_list):
            outside_shadow_painter.drawPixmap(0, 0, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"]))

        outside_shadow_painter.end()

        mask = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates,
                                 offset).createMaskFromColor(QColor(0, 0, 0, 0),
                                                             Qt.MaskMode.MaskOutColor)

        outside_shadow.setMask(mask)

        return outside_shadow

    def _inside_shadow(self):

        offset = QPoint()
        mask = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates,
                                 offset).createMaskFromColor(QColor(0, 0, 0, 0),
                                                             Qt.MaskMode.MaskInColor)

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "inside" in _shadow.keys():
                shadow = QPixmap(mask.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

                removed_color = "#000000"
                color = QColor(_shadow["color"])
                if removed_color == color.name():
                    removed_color = "#FFFFFF"

                shadow_painter.setTransform(QTransform())
                shadow_painter.setPen(color)
                shadow_painter.drawPixmap(0, 0, mask)
                shadow_painter.setPen(removed_color)
                shadow_painter.drawPixmap(_shadow["offset"][0], _shadow["offset"][1], mask)

                shadow_mask = shadow.createMaskFromColor(color, Qt.MaskMode.MaskOutColor)
                shadow_mask.save("mask.png")
                shadow.fill(Qt.transparent)
                shadow_painter.setPen(color)
                shadow_painter.drawPixmap(0, 0, shadow_mask)

                shadow_painter.end()

                shadow.scaled(mask.size())

                _pixmap_shadow_list.append(shadow)

        inside_shadow = QPixmap(mask.size())
        inside_shadow.fill(Qt.transparent)

        inside_shadow_painter = QPainter(inside_shadow)
        inside_shadow_painter.setTransform(QTransform())
        inside_shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        for i, pixmap in enumerate(_pixmap_shadow_list):
            inside_shadow_painter.drawPixmap(0, 0, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"]))

        inside_shadow_painter.end()

        inside_shadow.setMask(mask)

        return inside_shadow

    def _smooth_outside_shadow(self):

        offset = QPoint()
        source = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates, offset)
        w, h = source.width(), source.height()

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "outside" in _shadow.keys():
                shadow = QPixmap(source.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
                shadow_painter.setTransform(QTransform())
                shadow_painter.drawPixmap(_shadow["offset"][0], _shadow["offset"][1], w, h, self._colored_pixmap(_shadow["color"], source))
                shadow_painter.end()

                _pixmap_shadow_list.append(shadow)

        outside_shadow = QPixmap(source.size())
        outside_shadow.fill(Qt.transparent)

        outside_shadow_painter = QPainter(outside_shadow)
        outside_shadow_painter.setTransform(QTransform())
        outside_shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        for i, pixmap in enumerate(_pixmap_shadow_list):
            outside_shadow_painter.drawPixmap(0, 0, w, h, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"]))

        outside_shadow_painter.end()

        outside_shadow_painter = QPainter(outside_shadow)
        outside_shadow_painter.setTransform(QTransform())
        outside_shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        outside_shadow_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        outside_shadow_painter.drawPixmap(0, 0, w, h, source)

        outside_shadow_painter.end()

        return outside_shadow

    def _smooth_inside_shadow(self):

        offset = QPoint()
        source = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates, offset)
        w, h = source.width(), source.height()

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "inside" in _shadow.keys():
                shadow = QPixmap(source.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
                shadow_painter.setTransform(QTransform())
                new_source = self._colored_pixmap(_shadow["color"], source)
                shadow_painter.drawPixmap(0, 0, w, h, self._cut_shadow(new_source, source, _shadow["offset"][0] / 2, _shadow["offset"][1] / 2))
                shadow_painter.end()

                _pixmap_shadow_list.append(shadow)

        inside_shadow = QPixmap(source.size())
        inside_shadow.fill(Qt.transparent)

        inside_shadow_painter = QPainter(inside_shadow)
        inside_shadow_painter.setTransform(QTransform())
        inside_shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        for i, pixmap in enumerate(_pixmap_shadow_list):
            inside_shadow_painter.drawPixmap(0, 0, w, h, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"]))

        inside_shadow_painter.end()

        inside_shadow_painter = QPainter(inside_shadow)
        inside_shadow_painter.setTransform(QTransform())
        inside_shadow_painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        inside_shadow_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        inside_shadow_painter.drawPixmap(0, 0, w, h, source)

        inside_shadow_painter.end()

        return inside_shadow

    def draw(self, painter):

        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        restoreTransform = painter.worldTransform()

        source_rect = self.boundingRectFor(self.sourceBoundingRect(Qt.CoordinateSystem.DeviceCoordinates)).toRect()
        x, y, w, h = source_rect.getRect()

        offset = QPoint()
        source = self.sourcePixmap(Qt.CoordinateSystem.DeviceCoordinates, offset)

        painter.setTransform(QTransform())

        if self._smooth:
            outside_shadow = self._smooth_outside_shadow()
            inside_shadow = self._smooth_inside_shadow()
        else:
            outside_shadow = self._outside_shadow()
            inside_shadow = self._inside_shadow()

        painter.setPen(Qt.NoPen)

        painter.drawPixmap(x, y, w, h, outside_shadow)
        painter.drawPixmap(x, y, source)
        painter.drawPixmap(x + self._border, y + self._border, w - self._border * 2, h - self._border * 2, inside_shadow)
        painter.setWorldTransform(restoreTransform)

        painter.end()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    w = QFrame()

    main_layout = QHBoxLayout()
    main_layout.setContentsMargins(100,100,100,100)
    w.setLayout(main_layout)

    w.setStyleSheet("""background-color:#f7f9fc;""")

    groupbox = QWidget()
    groupbox.setStyleSheet("""background-color:white;
                              border-radius:10px""")
    groupbox.setFixedSize(500,500)

    shadow = BoxShadow()
    groupbox.setGraphicsEffect(shadow)

    main_layout.addWidget(groupbox)

    w.show()
    app.exec()

