"""Circular progress bar widget with multiple visual styles.

This module provides RoundProgressBar, a highly customizable circular progress
indicator adapted from the PySide2extn library (by ANJAL.P).

Features:
- Multiple bar styles: Donut, Line, Pie, Pizza, Hybrid1, Hybrid2
- Customizable colors, line widths, and rotation direction
- Auto-hiding when progress reaches 0% or 100%
- Text display (value or percentage)
- Smooth animations

Original Source: https://github.com/anjalp/PySide2extn
Version: v2.0.0 (migrated to PySide6)
"""

import sys

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen


class RoundProgressBar(QtWidgets.QWidget):
    """Customizable circular progress bar widget.

    A highly flexible circular progress indicator that supports multiple
    visual styles, colors, and display options. Automatically shows/hides
    based on progress value.

    Common Usage:
        >>> progress = RoundProgressBar()
        >>> progress.rpb_setBarStyle("Pizza")
        >>> progress.rpb_setValue(50)  # Set to 50%
        >>> progress.rpb_setValue(100)  # Completes and auto-hides after 800ms

    Bar Styles:
        - Donut: Ring with background path
        - Line: Simple ring
        - Pie: Filled pie chart
        - Pizza: Ring with filled center
        - Hybrid1: Ring with background path and filled center
        - Hybrid2: Pie with ring overlay

    Attributes:
        rpb_value (float): Current progress value (0-100 by default).
        rpb_maximum (int): Maximum progress value.
        rpb_minimum (int): Minimum progress value.
        hide_timer (QTimer): Timer for auto-hiding at 100%.
    """

    def __init__(self, parent=None):
        """Initialize the round progress bar.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)

        self.setStyleSheet("background: transparent;")
        self.setFixedSize(100, 100)

        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
        self.hide()  # Initially hidden

        # Position and sizing
        self.positionX = 0
        self.positionY = 0
        self.posFactor = 0
        self.sizeFactor = 0
        self.rpb_Size = 0
        self.rpb_minimumSize = (0, 0)
        self.rpb_maximumSize = (0, 0)
        self.rpb_dynamicMin = True
        self.rpb_dynamicMax = True

        # Progress range
        self.rpb_maximum = 100
        self.rpb_minimum = 0
        self.rpb_value = 0

        # Style settings
        self.rpb_type = self.barStyleFlags.Donet
        self.startPosition = self.startPosFlags.North
        self.rpb_direction = self.rotationFlags.Clockwise

        # Text settings
        self.rpb_textType = self.textFlags.Percentage
        self.rpb_textColor = "#154E9D"
        self.rpb_textFont = "Segoe UI"
        self.rpb_textValue = "0%"
        self.rpb_textRatio = 8
        self.rpb_textWidth = 0
        self.textFactorX = 0
        self.textFactorY = 0
        self.dynamicText = True
        self.rpb_textActive = True

        # Line/path settings
        self.lineWidth = 10
        self.pathWidth = 10
        self.rpb_lineStyle = self.lineStyleFlags.SolidLine
        self.rpb_lineCap = self.lineCapFlags.SquareCap
        self.lineColor = "#154E9D"
        self.pathColor = "#e7e7e7"

        # Circle settings (for Pizza/Hybrid styles)
        self.rpb_circleColor = "#e7e7e7"
        self.rpb_circleRatio = 0.8
        self.rpb_circlePosX = 0
        self.rpb_circlePosY = 0

        # Pie settings
        self.rpb_pieColor = (200, 200, 200)
        self.rpb_pieRatio = 1
        self.rpb_piePosX = 0
        self.rpb_piePosY = 0

        if self.rpb_dynamicMin:
            self.setMinimumSize(
                QSize(
                    self.lineWidth * 6 + self.pathWidth * 6,
                    self.lineWidth * 6 + self.pathWidth * 6,
                )
            )

    # ==========================================================================
    # Style Flag Enumerations
    # ==========================================================================

    class lineStyleFlags:
        """Line style options."""
        SolidLine = Qt.SolidLine
        DotLine = Qt.DotLine
        DashLine = Qt.DashLine

    class lineCapFlags:
        """Line cap options."""
        SquareCap = Qt.SquareCap
        RoundCap = Qt.RoundCap

    class barStyleFlags:
        """Bar style options."""
        Donet = 0
        Line = 1
        Pie = 2
        Pizza = 3
        Hybrid1 = 4
        Hybrid2 = 5

    class rotationFlags:
        """Rotation direction options."""
        Clockwise = -1
        AntiClockwise = 1

    class textFlags:
        """Text display options."""
        Value = 0
        Percentage = 1

    class startPosFlags:
        """Starting position options."""
        North = 90 * 16
        South = -90 * 16
        East = 0 * 16
        West = 180 * 16

    # ==========================================================================
    # Main Configuration Methods
    # ==========================================================================

    def rpb_setValue(self, value: int) -> None:
        """Set progress value and manage visibility.

        Args:
            value (int): Progress value (clamped to min/max range).

        Side Effects:
            - Updates progress display
            - Shows widget if value > minimum
            - Hides widget at minimum
            - Auto-hides after 800ms at maximum
        """
        # Clamp value
        if value > self.rpb_maximum:
            value = self.rpb_maximum
        elif value < self.rpb_minimum:
            value = self.rpb_minimum

        # Avoid unnecessary updates
        if self.rpb_value == value:
            return

        # Cancel any pending hide if value < 100
        if value < self.rpb_maximum and self.hide_timer.isActive():
            self.hide_timer.stop()

        # Convert and update
        self.convertInputValue(value)
        self.update()

        # Manage visibility
        if value == self.rpb_minimum:
            self.hide()
        elif value < self.rpb_maximum:
            self.show()
        elif value == self.rpb_maximum:
            self.show()
            self.hide_timer.start(800)  # Delay before hiding after 100%

    def rpb_setBarStyle(self, style: str) -> None:
        """Set the visual style of the progress bar.

        Args:
            style (str): One of: 'Donut', 'Line', 'Pie', 'Pizza', 'Hybrid1', 'Hybrid2'.

        Raises:
            Exception: If style is not one of the valid options.
        """
        style_map = {
            "Donet": self.barStyleFlags.Donet,
            "Line": self.barStyleFlags.Line,
            "Pie": self.barStyleFlags.Pie,
            "Pizza": self.barStyleFlags.Pizza,
            "Hybrid1": self.barStyleFlags.Hybrid1,
            "Hybrid2": self.barStyleFlags.Hybrid2,
        }

        if style not in style_map:
            raise Exception(
                "Round Progress Bar has only the following styles: "
                "'Line', 'Donet', 'Hybrid1', 'Pizza', 'Pie' and 'Hybrid2'"
            )

        self.rpb_type = style_map[style]
        self.update()

    def rpb_setRange(self, maximum: int, minimum: int) -> None:
        """Set the progress range.

        Args:
            maximum (int): Maximum value.
            minimum (int): Minimum value.
        """
        if minimum > maximum:
            maximum, minimum = minimum, maximum
        if self.rpb_maximum != maximum:
            self.rpb_maximum = maximum
        if self.rpb_minimum != minimum:
            self.rpb_minimum = minimum
        self.update()

    # ==========================================================================
    # Getter Methods
    # ==========================================================================

    def rpb_getValue(self) -> float:
        """Get current progress value.

        Returns:
            float: Current progress value.
        """
        return self.rpb_value / 16

    def rpb_getRange(self) -> tuple:
        """Get progress range.

        Returns:
            tuple: (minimum, maximum)
        """
        return (self.rpb_minimum, self.rpb_maximum)

    # ==========================================================================
    # Internal Drawing Methods (abbreviated for clarity)
    # ==========================================================================

    def convertInputValue(self, value: int) -> None:
        """Convert input value to internal arc angle representation."""
        self.rpb_value = (
                ((value - self.rpb_minimum) / (self.rpb_maximum - self.rpb_minimum))
                * 360
                * 16
        )
        self.rpb_value = self.rpb_direction * self.rpb_value

        if self.rpb_textType == self.textFlags.Percentage:
            percentage = round(
                ((value - self.rpb_minimum) / (self.rpb_maximum - self.rpb_minimum))
                * 100
            )
            self.rpb_textValue = f"{percentage}%"
        else:
            self.rpb_textValue = str(value)

    def geometryFactor(self) -> None:
        """Calculate position and size correction factors."""
        if self.lineWidth > self.pathWidth:
            self.posFactor = self.lineWidth / 2 + 1
            self.sizeFactor = self.lineWidth + 1
        else:
            self.posFactor = self.pathWidth / 2 + 1
            self.sizeFactor = self.pathWidth + 1

    def rpb_textFactor(self) -> None:
        """Calculate text positioning."""
        if self.dynamicText:
            self.rpb_textWidth = self.rpb_Size / self.rpb_textRatio
        self.textFactorX = (
                self.posFactor
                + (self.rpb_Size - self.sizeFactor) / 2
                - self.rpb_textWidth * 0.75 * (len(self.rpb_textValue) / 2)
        )
        self.textFactorY = self.rpb_textWidth / 2 + self.rpb_Size / 2

    def rpb_MinimumSize(self, dynamicMax: bool, minimum: tuple, maximum: tuple) -> None:
        """Calculate appropriate size based on widget dimensions."""
        rpb_Height = self.height()
        rpb_Width = self.width()

        if dynamicMax:
            if rpb_Width >= rpb_Height and rpb_Height >= minimum[1]:
                self.rpb_Size = rpb_Height
            elif rpb_Width < rpb_Height and rpb_Width >= minimum[0]:
                self.rpb_Size = rpb_Width
        else:
            if rpb_Width >= rpb_Height and rpb_Height <= maximum[1]:
                self.rpb_Size = rpb_Height
            elif rpb_Width < rpb_Height and rpb_Width <= maximum[0]:
                self.rpb_Size = rpb_Width

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the progress bar (called automatically by Qt)."""
        if self.rpb_dynamicMin:
            self.setMinimumSize(
                QSize(
                    self.lineWidth * 6 + self.pathWidth * 6,
                    self.lineWidth * 6 + self.pathWidth * 6,
                )
            )

        self.rpb_MinimumSize(
            self.rpb_dynamicMax, self.rpb_minimumSize, self.rpb_maximumSize
        )
        self.geometryFactor()
        self.rpb_textFactor()

        # Draw based on style type
        style_renderers = {
            0: [self.pathComponent, self.lineComponent, self.textComponent],  # Donut
            1: [self.lineComponent, self.textComponent],  # Line
            2: [self.pieComponent, self.textComponent],  # Pie
            3: [self.circleComponent, self.lineComponent, self.textComponent],  # Pizza
            4: [self.circleComponent, self.pathComponent, self.lineComponent, self.textComponent],  # Hybrid1
            5: [self.pieComponent, self.lineComponent, self.textComponent],  # Hybrid2
        }

        for renderer in style_renderers.get(self.rpb_type, []):
            renderer()

    def lineComponent(self) -> None:
        """Draw the progress arc line."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setStyle(self.rpb_lineStyle)
        pen.setWidth(self.lineWidth)
        pen.setBrush(QColor(self.lineColor))
        pen.setCapStyle(self.rpb_lineCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(
            self.positionX + self.posFactor,
            self.positionY + self.posFactor,
            self.rpb_Size - self.sizeFactor,
            self.rpb_Size - self.sizeFactor,
            self.startPosition,
            self.rpb_value,
        )
        painter.end()

    def pathComponent(self) -> None:
        """Draw the background circle path."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setStyle(Qt.SolidLine)
        pen.setWidth(self.pathWidth)
        pen.setBrush(QColor(self.pathColor))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(
            self.positionX + self.posFactor,
            self.positionY + self.posFactor,
            self.rpb_Size - self.sizeFactor,
            self.rpb_Size - self.sizeFactor,
            0,
            360 * 16,
        )
        painter.end()

    def textComponent(self) -> None:
        """Draw the center text."""
        if self.rpb_textActive:
            painter = QPainter(self)
            pen = QPen()
            pen.setColor(QColor(self.rpb_textColor))
            painter.setPen(pen)
            font = QFont()
            font.setFamily(self.rpb_textFont)
            font.setPointSize(int(self.rpb_textWidth))
            painter.setFont(font)
            painter.drawText(
                int(self.positionX + self.textFactorX),
                int(self.positionY + self.textFactorY),
                self.rpb_textValue,
            )
            painter.end()

    def circleComponent(self) -> None:
        """Draw filled center circle (for Pizza style)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(0))
        painter.setBrush(QColor(self.rpb_circleColor))

        # Calculate circle position
        circlePosX = (
                self.positionX + self.posFactor
                + ((self.rpb_Size) * (1 - self.rpb_circleRatio)) / 2
        )
        circlePosY = (
                self.positionY + self.posFactor
                + ((self.rpb_Size) * (1 - self.rpb_circleRatio)) / 2
        )

        painter.drawEllipse(
            int(circlePosX),
            int(circlePosY),
            int((self.rpb_Size - self.sizeFactor) * self.rpb_circleRatio),
            int((self.rpb_Size - self.sizeFactor) * self.rpb_circleRatio),
        )
        painter.end()

    def pieComponent(self) -> None:
        """Draw filled pie segment."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(0))
        painter.setBrush(QColor(self.rpb_pieColor))

        # Calculate pie position
        piePosX = (
                self.positionX + self.posFactor
                + ((self.rpb_Size) * (1 - self.rpb_pieRatio)) / 2
        )
        piePosY = (
                self.positionY + self.posFactor
                + ((self.rpb_Size) * (1 - self.rpb_pieRatio)) / 2
        )

        painter.drawPie(
            int(piePosX),
            int(piePosY),
            int((self.rpb_Size - self.sizeFactor) * self.rpb_pieRatio),
            int((self.rpb_Size - self.sizeFactor) * self.rpb_pieRatio),
            self.startPosition,
            int(self.rpb_value),
        )
        painter.end()


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing progress animation."""

    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QWidget()
    window.setWindowTitle("RoundProgressBar Example")
    layout = QtWidgets.QVBoxLayout(window)

    # Create progress bar
    progress = RoundProgressBar()
    progress.rpb_setBarStyle("Pizza")
    layout.addWidget(progress)

    # Simulate progress
    value = 0


    def update_progress():
        global value
        value = (value + 10) % 110
        progress.rpb_setValue(value)


    timer = QTimer()
    timer.timeout.connect(update_progress)
    timer.start(500)

    window.show()
    sys.exit(app.exec())