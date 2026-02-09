"""Neumorphism box shadow graphics effect for Qt widgets.

This module provides a sophisticated neumorphism (soft UI) graphics effect
that creates soft, raised or pressed appearances using layered shadows.

Neumorphism combines:
- Outside shadows: Light and dark shadows cast outside the widget
- Inside shadows: Inset shadows creating depth within the widget
- Blur effects: Soft, organic shadow edges
- Border control: Inner shadow border width

Perfect for creating modern, soft UI designs with depth and tactility.
"""

import sys

from PySide6.QtCore import QPoint, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsBlurEffect,
    QGraphicsEffect,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QHBoxLayout,
    QWidget,
)


class BoxShadow(QGraphicsEffect):
    """Neumorphism-style box shadow effect with inner and outer shadows.

    Creates a soft, raised or pressed appearance using configurable shadow layers.
    Each shadow can be positioned inside or outside the widget with custom
    offset, blur, and color.

    Default Configuration:
        - Light outside shadows (white + gray) for raised appearance
        - Configurable border for inside shadow offset
        - Smooth rendering mode enabled by default

    Shadow Format:
        Each shadow is a dict with keys:
        - "outside" (bool) or "inside" (bool): Shadow type
        - "offset" ([x, y]): Shadow offset in pixels
        - "blur" (int): Blur radius in pixels
        - "color" (str): Hex color code (e.g., "#ffffff")

    Attributes:
        _shadow_list (list): List of shadow configurations.
        _max_x_offset (int): Maximum X offset (for bounding rect).
        _max_y_offset (int): Maximum Y offset (for bounding rect).
        _border (int): Border width for inside shadows.
        _smooth (bool): Use smooth rendering algorithm.

    Example:
        >>> shadow = BoxShadow()
        >>> widget.setGraphicsEffect(shadow)
        >>> 
        >>> # Custom shadows
        >>> custom_shadows = [
        ...     {"outside": True, "offset": [10, 10], "blur": 15, "color": "#ffffff"},
        ...     {"outside": True, "offset": [-10, -10], "blur": 15, "color": "#cccccc"}
        ... ]
        >>> shadow.setShadowList(custom_shadows)
    """

    def __init__(
            self,
            shadow_list: list[dict] = None,
            border: int = 3,
            smooth: bool = True
    ):
        """Initialize the box shadow effect.

        Args:
            shadow_list (list[dict], optional): List of shadow configurations.
                If None, uses default light outside shadows.
            border (int): Inside shadow border width in pixels. Default 3.
            smooth (bool): Use smooth rendering algorithm. Default True.
        """
        super().__init__()

        # Default shadow configurations
        light_outside = [
            {"outside": True, "offset": [8, 8], "blur": 10, "color": "#ffffff"},
            {"outside": True, "offset": [-8, -8], "blur": 10, "color": "#d0d0d0"},
        ]
        # Unused but kept for reference
        light_inside = [
            {"inside": True, "offset": [6, 6], "blur": 8, "color": "#C1D5EE"},
            {"inside": True, "offset": [-6, -6], "blur": 8, "color": "#FFFFFF"},
        ]

        self._shadow_list = []
        self._max_x_offset = 0
        self._max_y_offset = 0
        self._border = 0
        self._smooth = smooth

        self.setShadowList(shadow_list or light_outside)
        self.setBorder(border)

    def setShadowList(self, shadow_list: list[dict] = None) -> None:
        """Set the list of shadow configurations.

        Args:
            shadow_list (list[dict], optional): Shadow configurations.

        Side Effects:
            - Updates shadow list
            - Recalculates max offset for bounding rect
        """
        if shadow_list is None:
            shadow_list = []
        self._shadow_list = shadow_list
        self._set_max_offset()

    def setBorder(self, border: int) -> None:
        """Set the border width for inside shadows.

        Args:
            border (int): Border width in pixels (>= 0).
        """
        self._border = max(0, border)

    def necessary_indentation(self) -> tuple:
        """Get necessary indentation for shadows.

        Returns:
            tuple: (max_x_offset, max_y_offset) in pixels.
        """
        return self._max_x_offset, self._max_y_offset

    def boundingRectFor(self, rect: QRectF) -> QRectF:
        """Calculate bounding rect including shadow space.

        Args:
            rect (QRectF): Source rect.

        Returns:
            QRectF: Expanded rect including shadows.
        """
        return rect.adjusted(
            -self._max_x_offset,
            -self._max_y_offset,
            self._max_x_offset,
            self._max_y_offset,
        )

    def _set_max_offset(self) -> None:
        """Calculate maximum shadow offset for bounding rect.

        Side Effects:
            - Updates _max_x_offset and _max_y_offset
        """
        self._max_x_offset = 0
        self._max_y_offset = 0

        for shadow in self._shadow_list:
            if "outside" in shadow:
                x_offset = abs(shadow["offset"][0]) + shadow["blur"] * 2
                y_offset = abs(shadow["offset"][1]) + shadow["blur"] * 2
                self._max_x_offset = max(self._max_x_offset, x_offset)
                self._max_y_offset = max(self._max_y_offset, y_offset)

    @staticmethod
    def _blur_pixmap(src: QPixmap, blur_radius: int) -> QPixmap:
        """Apply Gaussian blur to a pixmap.

        Args:
            src (QPixmap): Source pixmap.
            blur_radius (int): Blur radius in pixels.

        Returns:
            QPixmap: Blurred pixmap.
        """
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
    def _colored_pixmap(color: QColor, pixmap: QPixmap) -> QPixmap:
        """Create a colored version of a pixmap.

        Args:
            color (QColor): Target color.
            pixmap (QPixmap): Source pixmap.

        Returns:
            QPixmap: Colored pixmap with original alpha channel.
        """
        new_pixmap = QPixmap(pixmap)
        new_pixmap.fill(color)
        painter = QPainter(new_pixmap)
        painter.setTransform(QTransform())
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return new_pixmap

    @staticmethod
    def _cut_shadow(pixmap: QPixmap, source: QPixmap, offset_x: float, offset_y: float) -> QPixmap:
        """Cut out source from pixmap at offset (for inside shadows).

        Args:
            pixmap (QPixmap): Target pixmap.
            source (QPixmap): Source to cut out.
            offset_x (float): X offset.
            offset_y (float): Y offset.

        Returns:
            QPixmap: Result pixmap with cutout.
        """
        painter = QPainter(pixmap)
        painter.setTransform(QTransform())
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        painter.drawPixmap(offset_x, offset_y, source)
        painter.end()
        return pixmap

    def _outside_shadow(self) -> QPixmap:
        """Generate outside shadows (basic algorithm).

        Returns:
            QPixmap: Combined outside shadows.
        """
        offset = QPoint()
        mask = self.sourcePixmap(
            Qt.DeviceCoordinates, offset
        ).createMaskFromColor(QColor(0, 0, 0, 0), Qt.MaskInColor)

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "outside" in _shadow:
                shadow = QPixmap(mask.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(
                    QPainter.Antialiasing | QPainter.SmoothPixmapTransform
                )
                shadow_painter.setTransform(QTransform())
                shadow_painter.setPen(QColor(_shadow["color"]))
                shadow_painter.drawPixmap(
                    _shadow["offset"][0], _shadow["offset"][1], mask
                )
                shadow_painter.end()

                _pixmap_shadow_list.append(shadow)

        outside_shadow = QPixmap(mask.size())
        outside_shadow.fill(Qt.transparent)

        outside_shadow_painter = QPainter(outside_shadow)
        outside_shadow_painter.setTransform(QTransform())
        outside_shadow_painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )

        for i, pixmap in enumerate(_pixmap_shadow_list):
            outside_shadow_painter.drawPixmap(
                0, 0, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"])
            )

        outside_shadow_painter.end()

        # Apply mask to clip shadow to outside only
        mask = self.sourcePixmap(
            Qt.DeviceCoordinates, offset
        ).createMaskFromColor(QColor(0, 0, 0, 0), Qt.MaskOutColor)

        outside_shadow.setMask(mask)

        return outside_shadow

    def _inside_shadow(self) -> QPixmap:
        """Generate inside shadows (basic algorithm).

        Returns:
            QPixmap: Combined inside shadows.
        """
        offset = QPoint()
        mask = self.sourcePixmap(
            Qt.DeviceCoordinates, offset
        ).createMaskFromColor(QColor(0, 0, 0, 0), Qt.MaskInColor)

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "inside" in _shadow:
                shadow = QPixmap(mask.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(
                    QPainter.Antialiasing | QPainter.SmoothPixmapTransform
                )

                removed_color = "#000000"
                color = QColor(_shadow["color"])
                if removed_color == color.name():
                    removed_color = "#FFFFFF"

                shadow_painter.setTransform(QTransform())
                shadow_painter.setPen(color)
                shadow_painter.drawPixmap(0, 0, mask)
                shadow_painter.setPen(removed_color)
                shadow_painter.drawPixmap(
                    _shadow["offset"][0], _shadow["offset"][1], mask
                )

                shadow_mask = shadow.createMaskFromColor(
                    color, Qt.MaskOutColor
                )
                # DEBUG: Uncomment to save mask
                # shadow_mask.save("mask.png")
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
        inside_shadow_painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )

        for i, pixmap in enumerate(_pixmap_shadow_list):
            inside_shadow_painter.drawPixmap(
                0, 0, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"])
            )

        inside_shadow_painter.end()

        inside_shadow.setMask(mask)

        return inside_shadow

    def _smooth_outside_shadow(self) -> QPixmap:
        """Generate outside shadows (smooth algorithm).

        Returns:
            QPixmap: Combined outside shadows with smooth edges.
        """
        offset = QPoint()
        source = self.sourcePixmap(Qt.DeviceCoordinates, offset)
        w, h = source.width(), source.height()

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "outside" in _shadow:
                shadow = QPixmap(source.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(
                    QPainter.Antialiasing | QPainter.SmoothPixmapTransform
                )
                shadow_painter.setTransform(QTransform())
                shadow_painter.drawPixmap(
                    _shadow["offset"][0],
                    _shadow["offset"][1],
                    w,
                    h,
                    self._colored_pixmap(_shadow["color"], source),
                )
                shadow_painter.end()

                _pixmap_shadow_list.append(shadow)

        outside_shadow = QPixmap(source.size())
        outside_shadow.fill(Qt.transparent)

        outside_shadow_painter = QPainter(outside_shadow)
        outside_shadow_painter.setTransform(QTransform())
        outside_shadow_painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )

        for i, pixmap in enumerate(_pixmap_shadow_list):
            outside_shadow_painter.drawPixmap(
                0, 0, w, h, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"])
            )

        outside_shadow_painter.end()

        # Cut out the source widget to leave only outside shadow
        outside_shadow_painter = QPainter(outside_shadow)
        outside_shadow_painter.setTransform(QTransform())
        outside_shadow_painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        outside_shadow_painter.setCompositionMode(
            QPainter.CompositionMode_DestinationOut
        )
        outside_shadow_painter.drawPixmap(0, 0, w, h, source)

        outside_shadow_painter.end()

        return outside_shadow

    def _smooth_inside_shadow(self) -> QPixmap:
        """Generate inside shadows (smooth algorithm).

        Returns:
            QPixmap: Combined inside shadows with smooth edges.
        """
        offset = QPoint()
        source = self.sourcePixmap(Qt.DeviceCoordinates, offset)
        w, h = source.width(), source.height()

        _pixmap_shadow_list = []

        for _shadow in self._shadow_list:
            if "inside" in _shadow:
                shadow = QPixmap(source.size())
                shadow.fill(Qt.transparent)
                shadow_painter = QPainter(shadow)
                shadow_painter.setRenderHints(
                    QPainter.Antialiasing | QPainter.SmoothPixmapTransform
                )
                shadow_painter.setTransform(QTransform())
                new_source = self._colored_pixmap(_shadow["color"], source)
                shadow_painter.drawPixmap(
                    0,
                    0,
                    w,
                    h,
                    self._cut_shadow(
                        new_source,
                        source,
                        _shadow["offset"][0] / 2,
                        _shadow["offset"][1] / 2,
                    ),
                )
                shadow_painter.end()

                _pixmap_shadow_list.append(shadow)

        inside_shadow = QPixmap(source.size())
        inside_shadow.fill(Qt.transparent)

        inside_shadow_painter = QPainter(inside_shadow)
        inside_shadow_painter.setTransform(QTransform())
        inside_shadow_painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )

        for i, pixmap in enumerate(_pixmap_shadow_list):
            inside_shadow_painter.drawPixmap(
                0, 0, w, h, self._blur_pixmap(pixmap, self._shadow_list[i]["blur"])
            )

        inside_shadow_painter.end()

        # Clip to widget bounds
        inside_shadow_painter = QPainter(inside_shadow)
        inside_shadow_painter.setTransform(QTransform())
        inside_shadow_painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        inside_shadow_painter.setCompositionMode(
            QPainter.CompositionMode_DestinationIn
        )
        inside_shadow_painter.drawPixmap(0, 0, w, h, source)

        inside_shadow_painter.end()

        return inside_shadow

    def draw(self, painter: QPainter) -> None:
        """Draw the neumorphism effect.

        Args:
            painter (QPainter): Painter to draw with.

        Side Effects:
            - Draws outside shadows
            - Draws source widget
            - Draws inside shadows with border offset
        """
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        restoreTransform = painter.worldTransform()

        source_rect = self.boundingRectFor(
            self.sourceBoundingRect(Qt.DeviceCoordinates)
        ).toRect()
        x, y, w, h = source_rect.getRect()

        offset = QPoint()
        source = self.sourcePixmap(Qt.DeviceCoordinates, offset)

        painter.setTransform(QTransform())

        # Generate shadows based on smooth mode
        if self._smooth:
            outside_shadow = self._smooth_outside_shadow()
            inside_shadow = self._smooth_inside_shadow()
        else:
            outside_shadow = self._outside_shadow()
            inside_shadow = self._inside_shadow()

        painter.setPen(Qt.NoPen)

        # Draw layers: outside shadow -> source -> inside shadow
        painter.drawPixmap(x, y, w, h, outside_shadow)
        painter.drawPixmap(x, y, source)
        painter.drawPixmap(
            x + self._border,
            y + self._border,
            w - self._border * 2,
            h - self._border * 2,
            inside_shadow,
        )
        painter.setWorldTransform(restoreTransform)

        painter.end()


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Example showing neumorphism effect on a white box."""

    app = QApplication(sys.argv)

    window = QFrame()
    window.resize(800, 600)

    main_layout = QHBoxLayout()
    main_layout.setContentsMargins(100, 100, 100, 100)
    window.setLayout(main_layout)

    window.setStyleSheet("background-color: #f7f9fc;")

    # Create widget with neumorphism effect
    box = QWidget()
    box.setStyleSheet("""
        background-color: white;
        border-radius: 10px;
    """)
    box.setFixedSize(500, 500)

    # Apply neumorphism shadow
    shadow = BoxShadow()
    box.setGraphicsEffect(shadow)

    main_layout.addWidget(box)

    window.show()
    sys.exit(app.exec())