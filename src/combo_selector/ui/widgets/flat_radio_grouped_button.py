from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel


class _FlatRadioItem(QWidget):
    clicked = Signal(str)

    def __init__(self, text: str, is_first: bool = False, is_last: bool = False, parent=None):
        super().__init__(parent)
        self._text = text
        self._checked = False
        self._is_first = is_first
        self._is_last = is_last

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(42)

    def text(self) -> str:
        return self._text

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked == checked:
            return
        self._checked = checked
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._text)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        rectf = QRectF(rect)
        radius = 12.0

        path = QPainterPath()

        if self._is_first and self._is_last:
            path.addRoundedRect(rectf, radius, radius)
        elif self._is_first:
            path.moveTo(rectf.topRight())
            path.lineTo(rectf.topLeft() + QPointF(radius, 0))
            path.quadTo(rectf.topLeft(), rectf.topLeft() + QPointF(0, radius))
            path.lineTo(rectf.bottomLeft() + QPointF(0, -radius))
            path.quadTo(rectf.bottomLeft(), rectf.bottomLeft() + QPointF(radius, 0))
            path.lineTo(rectf.bottomRight())
            path.closeSubpath()
        elif self._is_last:
            path.moveTo(rectf.topLeft())
            path.lineTo(rectf.topRight() + QPointF(-radius, 0))
            path.quadTo(rectf.topRight(), rectf.topRight() + QPointF(0, radius))
            path.lineTo(rectf.bottomRight() + QPointF(0, -radius))
            path.quadTo(rectf.bottomRight(), rectf.bottomRight() + QPointF(-radius, 0))
            path.lineTo(rectf.bottomLeft())
            path.closeSubpath()
        else:
            path.addRect(rectf)

        bg = QColor("#d1d9fc") if self._checked else QColor("white")
        painter.fillPath(path, bg)

        cx = 22
        cy = self.height() // 2

        painter.setPen(QPen(QColor("#bfc7d5"), 2))
        painter.setBrush(QColor("white"))
        painter.drawEllipse(cx - 8, cy - 8, 16, 16)

        if self._checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#183881"))
            painter.drawEllipse(cx - 4, cy - 4, 8, 8)

        painter.setPen(QColor("#333333"))
        text_rect = self.rect().adjusted(36, 0, -12, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._text,
        )

        if not self._is_last:
            painter.setPen(QColor("#e6e6e6"))
            painter.drawLine(self.rect().topRight(), self.rect().bottomRight())


class _FlatRadioGroupPanel(QWidget):
    buttonClicked = Signal(str)

    def __init__(self, items: list[str], parent=None):
        super().__init__(parent)

        self._items: list[_FlatRadioItem] = []
        self._current_index = -1
        self._radius = 12

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(42)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        for i, text in enumerate(items):
            item = _FlatRadioItem(
                text=text,
                is_first=(i == 0),
                is_last=(i == len(items) - 1),
                parent=self,
            )
            item.clicked.connect(self._on_item_clicked)
            layout.addWidget(item)
            self._items.append(item)

        if self._items:
            self.setCurrentIndex(0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(0, 0, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self._radius, self._radius)

        painter.setPen(QPen(QColor("#d9d9d9"), 1))
        painter.setBrush(QColor("white"))
        painter.drawPath(path)

    def _on_item_clicked(self, text: str):
        for i, item in enumerate(self._items):
            checked = item.text() == text
            item.setChecked(checked)
            if checked:
                self._current_index = i
        self.buttonClicked.emit(text)

    def currentText(self) -> str:
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index].text()
        return ""

    def currentIndex(self) -> int:
        return self._current_index

    def setCurrentIndex(self, index: int):
        if not (0 <= index < len(self._items)):
            return
        self._current_index = index
        for i, item in enumerate(self._items):
            item.setChecked(i == index)


class FlatRadioGroupedButton(QWidget):
    buttonClicked = Signal(str)

    def __init__(self, items: list[str], title: str = "", parent=None):
        super().__init__(parent)

        self._title_label = QLabel(title, self)
        self._title_label.setVisible(bool(title))

        title_font = QFont(self.font())
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        self._title_label.setFont(title_font)
        self._title_label.setStyleSheet("color: #333333;")
        self._title_label.setContentsMargins(0, 0, 0, 0)

        self._panel = _FlatRadioGroupPanel(items, self)
        self._panel.buttonClicked.connect(self.buttonClicked)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._title_label)
        layout.addWidget(self._panel)

    def setTitle(self, title: str):
        self._title_label.setText(title)
        self._title_label.setVisible(bool(title))

    def title(self) -> str:
        return self._title_label.text()

    def currentText(self) -> str:
        return self._panel.currentText()

    def currentIndex(self) -> int:
        return self._panel.currentIndex()

    def setCurrentIndex(self, index: int):
        self._panel.setCurrentIndex(index)