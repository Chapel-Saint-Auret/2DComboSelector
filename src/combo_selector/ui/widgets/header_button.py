from functools import partial
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QHeaderView, QToolButton, QDialog, QStyle, QWidget
)

from combo_selector.utils import resource_path

class HeaderButton(QHeaderView):
    """
    Horizontal header that can show small filter buttons for specific sections.
    Use header.add_header_button(column_index, widget_to_show=yourDialog) to add a button for a column.
    """
    widgetRequested = Signal(int)  # emitted when a filter button is clicked (column index)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSectionsMovable(False)
        self.setSectionResizeMode(QHeaderView.Interactive)
        self.setCascadingSectionResizes(True)
        self.setStretchLastSection(True)
        # keep header height sensible for small buttons
        self.setFixedHeight(30)
        self.setHighlightSections(False)

        self._buttons = {}        # column_index -> QToolButton
        self._button_widget = {}  # column_index -> widget (dialog or widget to show)

        # Reposition when sections change size or move
        self.sectionResized.connect(self._reposition_buttons)
        self.sectionMoved.connect(self._reposition_buttons)
        if hasattr(self, "sectionCountChanged"):
            try:
                self.sectionCountChanged.connect(self._reposition_buttons)
            except Exception:
                pass
        self._reposition_buttons()

    def add_header_button(self, column: int, tooltip: str | None = None, widget_to_show: QWidget = None):
        """Create and attach a small header button to a header section."""
        if column in self._buttons:
            return  # already added

        # store the widget (dialog or other) to show later on click
        if widget_to_show is not None:
            self._button_widget[column] = widget_to_show

        btn = QToolButton(self)
        btn.setText("Filter")
        btn.setIcon(QIcon(resource_path("icons/filter.png")))
        btn.setIconSize(QSize(18, 18))
        btn.setToolTip(tooltip or f"Filter column {column}")
        btn.setAutoRaise(True)
        btn.setCursor(Qt.PointingHandCursor)

        # Connect the clicked signal properly so handler is called only on click.
        # Use a lambda to capture 'column' and ignore the 'checked' boolean the clicked signal may send.
        btn.clicked.connect(lambda checked=False, col=column: self._on_button_clicked(col))

        btn.show()
        self._buttons[column] = btn
        self._reposition_buttons()

    def remove_filter_button(self, column: int):
        btn = self._buttons.pop(column, None)
        if btn:
            btn.deleteLater()
        self._button_widget.pop(column, None)

    def _on_button_clicked(self, column: int):
        # Emit a signal for external handlers
        self.widgetRequested.emit(column)
        # Show the stored widget/dialog if provided
        self._open_widget_dialog(column)

    def _open_widget_dialog(self, column: int):
        widget = self._button_widget.get(column)
        if widget is None:
            return

        # If the stored widget is a QDialog, run it modally with exec()
        if isinstance(widget, QDialog):
            # ensure parent/owner is the top-level window so modality works as expected
            if widget.parent() is None:
                widget.setParent(self.window())
            widget.exec()
        else:
            # otherwise just show the widget (non-modal)
            widget.show()

    def _reposition_buttons(self, *args):
        """Position each button inside its section's rect (right-aligned)."""
        if not self._buttons:
            return

        # Robustly get number of sections
        try:
            section_count = self.count()
        except Exception:
            section_count = self.model().columnCount() if self.model() is not None else 0

        for col, btn in list(self._buttons.items()):
            if col < 0 or col >= section_count:
                btn.hide()
                continue

            try:
                hidden = self.isSectionHidden(col)
            except Exception:
                hidden = False
            if hidden:
                btn.hide()
                continue

            x = self.sectionViewportPosition(col)
            w = self.sectionSize(col)
            if w <= 0 or w < btn.width() + 4:
                btn.hide()
                continue

            rect = QRect(x, 0, w, self.height())
            x_pos = rect.right() - btn.width() - 4
            y = rect.top() + (rect.height() - btn.height()) // 2
            btn.move(x_pos, y)
            btn.show()