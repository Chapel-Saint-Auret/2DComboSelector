"""Animated segmented toggle button widget for PySide6 applications.

Provides a two-segment animated toggle button (similar to a segmented control)
with a sliding thumb animation.  The filename is intentionally kept as-is.
"""

import sys
from PySide6.QtCore import (
    Qt, Signal, QRect, QPropertyAnimation, QEasingCurve, Property, QAbstractAnimation
)
from PySide6.QtGui import QColor, QPainter, QFont, QFontMetrics
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout


class AnimatedSegmentedToggle(QWidget):
    """Two-segment animated toggle button with a sliding thumb.

    Displays two labeled segments side-by-side inside a rounded pill shape.
    Clicking a segment or using arrow keys moves the thumb to that segment
    with a smooth animation.

    Attributes:
        changed (Signal[int, str]): Emitted when the selected segment changes,
            with the new index and label text.
        labels (list[str]): Display labels for the two segments.

    Example::

        toggle = AnimatedSegmentedToggle(("Metrics", "Ranking"))
        toggle.changed.connect(lambda i, t: print(i, t))
    """

    changed = Signal(int, str)

    def __init__(self, labels=("Show metrics", "Show ranking"), parent=None):
        """Initialize the animated segmented toggle.

        Args:
            labels (tuple[str, str]): Display text for the left and right
                segments. Defaults to ``("Show metrics", "Show ranking")``.
            parent (QWidget | None): Optional parent widget.

        Raises:
            ValueError: If ``labels`` does not contain exactly two elements.
        """
        super().__init__(parent)

        if len(labels) != 2:
            raise ValueError("This version supports exactly 2 segments.")

        self.labels = list(labels)
        self._index = 0
        self._thumb_x = 0.0

        # ---- Compact height (standard control)
        self._height = 36
        self._inner_margin = 3
        self._outer_radius = self._height // 2
        self._thumb_radius = (self._height - 2 * self._inner_margin) // 2

        # ---- Colors matched to your app palette
        self._bg_color = QColor("#2A4FA3")        # blue pill
        self._thumb_color = QColor("#EAF0FF")     # soft blue-white selection
        self._text_selected = QColor("#1E459A")   # header blue
        self._text_unselected = QColor("#FFFFFF") # white text

        # ---- Font
        self._font = QFont()
        self._font.setPointSize(9)
        self._font.setWeight(QFont.DemiBold)

        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self._anim = QPropertyAnimation(self, b"thumbX", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # ---- Autosize width from text content
        self._recompute_size()

        self._thumb_x = self._target_x_for_index(self._index)

    # ---------- autosizing ----------
    def _recompute_size(self):
        """Recompute and set the fixed widget size based on label text widths.

        Measures each label using the current font and adds padding so both
        segments share the same width.  Updates ``_segment_width`` and calls
        ``setFixedSize``.
        """
        fm = QFontMetrics(self._font)

        # Width of each label text
        text_widths = [fm.horizontalAdvance(t) for t in self.labels]

        # Horizontal padding inside each segment around the text
        seg_text_padding = 14  # px left + right padding per segment around text

        seg_widths = [w + 2 * seg_text_padding for w in text_widths]

        # Make both segments same width for visual balance (segmented control style)
        self._segment_width = max(seg_widths)

        total_width = int(2 * self._segment_width + 2 * self._inner_margin)
        self.setFixedSize(total_width, self._height)

    # ---------- animated property ----------
    def getThumbX(self):
        """Return the current horizontal position of the sliding thumb.

        Returns:
            float: X-coordinate of the thumb's left edge.
        """
        return self._thumb_x

    def setThumbX(self, value):
        """Set the horizontal position of the sliding thumb and repaint.

        Args:
            value (float): New X-coordinate for the thumb's left edge.
        """
        self._thumb_x = float(value)
        self.update()

    thumbX = Property(float, getThumbX, setThumbX)

    # ---------- public API ----------
    def currentIndex(self):
        """Return the index of the currently selected segment.

        Returns:
            int: ``0`` for the left segment, ``1`` for the right segment.
        """
        return self._index

    def currentText(self):
        """Return the label text of the currently selected segment.

        Returns:
            str: Label of the active segment.
        """
        return self.labels[self._index]

    def setCurrentIndex(self, index: int, animated=True):
        """Select a segment by index, optionally with animation.

        Args:
            index (int): Target segment index (``0`` or ``1``).
            animated (bool): When ``True``, slides the thumb smoothly.
                Defaults to ``True``.

        Side Effects:
            - Updates ``_index`` to ``index``.
            - Starts or skips thumb animation.
            - Emits ``changed`` signal with the new index and label.
        """
        if index not in (0, 1):
            return
        if index == self._index and animated:
            return

        self._index = index
        target = self._target_x_for_index(index)

        if animated:
            self._anim.stop()
            self._anim.setStartValue(self._thumb_x)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._thumb_x = target
            self.update()

        self.changed.emit(index, self.labels[index])

    # ---------- geometry ----------
    def _content_rect(self):
        """Return the inner rectangle after applying the inner margin.

        Returns:
            QRect: Content rectangle inset by ``_inner_margin`` on all sides.
        """
        return self.rect().adjusted(
            self._inner_margin, self._inner_margin,
            -self._inner_margin, -self._inner_margin
        )

    def _segment_rects(self):
        """Return the bounding rectangles of both segments.

        Returns:
            tuple[QRect, QRect]: ``(left_rect, right_rect)`` for the two
            segments inside the content area.
        """
        c = self._content_rect()
        # use explicit equal widths based on autosized segment width
        left = QRect(int(c.x()), int(c.y()), int(self._segment_width), int(c.height()))
        right = QRect(int(c.x() + self._segment_width), int(c.y()),
                      int(self._segment_width), int(c.height()))
        return left, right

    def _target_x_for_index(self, index):
        """Compute the target thumb X-coordinate for a given segment index.

        Args:
            index (int): Segment index (``0`` or ``1``).

        Returns:
            float: The X-coordinate the thumb left edge should reach.
        """
        c = self._content_rect()
        return c.x() + self._segment_width * index

    def _thumb_rect(self):
        """Return the current bounding rectangle of the sliding thumb.

        Returns:
            QRect: Rectangle describing the thumb position and size.
        """
        c = self._content_rect()
        pad = 1
        return QRect(
            int(self._thumb_x + pad),
            int(c.y() + pad),
            int(self._segment_width - 2 * pad),
            int(c.height() - 2 * pad)
        )

    # ---------- events ----------
    def resizeEvent(self, event):
        """Snap the thumb to its target position when the widget is resized.

        Args:
            event (QResizeEvent): The resize event.
        """
        super().resizeEvent(event)
        if self._anim.state() != QAbstractAnimation.Running:
            self._thumb_x = self._target_x_for_index(self._index)

    def mousePressEvent(self, event):
        """Handle mouse press to switch the active segment.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)

        left_rect, right_rect = self._segment_rects()
        pos = event.position().toPoint()

        if left_rect.contains(pos):
            self.setCurrentIndex(0, animated=True)
        elif right_rect.contains(pos):
            self.setCurrentIndex(1, animated=True)

        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard navigation between segments.

        Left/Up arrow moves to the left segment; Right/Down arrow moves to
        the right segment.

        Args:
            event (QKeyEvent): The key press event.
        """
        if event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.setCurrentIndex(0, animated=True)
            event.accept()
            return
        if event.key() in (Qt.Key_Right, Qt.Key_Down):
            self.setCurrentIndex(1, animated=True)
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------- optional: change labels dynamically ----------
    def setLabels(self, left: str, right: str):
        """Update segment labels and resize the widget accordingly.

        Args:
            left (str): New label for the left segment.
            right (str): New label for the right segment.

        Side Effects:
            - Updates ``labels`` list.
            - Recomputes widget size.
            - Repaints the widget.
        """
        self.labels = [left, right]
        self._recompute_size()
        self._thumb_x = self._target_x_for_index(self._index)
        self.update()

    # ---------- painting ----------
    def paintEvent(self, event):
        """Paint the toggle button: background pill, thumb, and labels.

        Args:
            event (QPaintEvent): The paint event.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(self._font)
        p.setPen(Qt.NoPen)

        # Background pill
        p.setBrush(self._bg_color)
        p.drawRoundedRect(self.rect(), self._outer_radius, self._outer_radius)

        # Sliding thumb
        p.setBrush(self._thumb_color)
        p.drawRoundedRect(self._thumb_rect(), self._thumb_radius, self._thumb_radius)

        # Labels
        left_rect, right_rect = self._segment_rects()

        p.setPen(self._text_selected if self._index == 0 else self._text_unselected)
        p.drawText(left_rect, Qt.AlignCenter, self.labels[0])

        p.setPen(self._text_selected if self._index == 1 else self._text_unselected)
        p.drawText(right_rect, Qt.AlignCenter, self.labels[1])


if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = QWidget()
    w.setStyleSheet("background:#F1F3F8;")
    layout = QVBoxLayout(w)
    layout.setContentsMargins(20, 20, 20, 20)

    toggle = AnimatedSegmentedToggle(("Show metrics", "Show ranking"))
    toggle.changed.connect(lambda i, t: print("Selected:", i, t))

    layout.addWidget(toggle, alignment=Qt.AlignLeft)

    w.resize(420, 100)
    w.show()
    sys.exit(app.exec())