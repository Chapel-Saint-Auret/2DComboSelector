"""Custom table header with filter buttons in column headers.

This module provides a QHeaderView subclass that can display small
filter buttons inside specific column headers. The buttons automatically
reposition themselves when columns are resized or moved.

Features:
- Add filter buttons to any column
- Buttons auto-reposition on resize/move
- Associate dialogs or widgets with buttons
- Emits signal when button clicked
"""

import sys

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from combo_selector.utils import resource_path


class HeaderButton(QHeaderView):
    """Custom header view with filter buttons in column headers.

    Extends QHeaderView to support small tool buttons positioned inside
    column header sections. Buttons automatically reposition when columns
    are resized or moved.

    Typical use case: Add filter buttons to table columns that open filter
    dialogs when clicked.

    Signals:
        widgetRequested(int): Emitted when a filter button is clicked.
            Args: column index.

    Attributes:
        _buttons (dict): Maps column index to QToolButton.
        _button_widget (dict): Maps column index to associated widget/dialog.

    Example:
        >>> header = HeaderButton(Qt.Horizontal, table)
        >>> table.setHorizontalHeader(header)
        >>> filter_dialog = MyFilterDialog()
        >>> header.add_header_button(2, "Filter column", filter_dialog)
    """

    widgetRequested = Signal(int)

    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal, parent=None):
        """Initialize the header with button support.

        Args:
            orientation (Qt.Orientation): Header orientation (horizontal/vertical).
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(orientation, parent)

        # Header configuration
        self.setSectionsClickable(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSectionsMovable(False)
        self.setSectionResizeMode(QHeaderView.Interactive)
        self.setCascadingSectionResizes(True)
        self.setStretchLastSection(True)
        self.setFixedHeight(30)  # Keep height sensible for small buttons
        self.setHighlightSections(False)

        # Button storage
        self._buttons = {}  # column_index -> QToolButton
        self._button_widget = {}  # column_index -> widget (dialog or widget)

        # Auto-reposition buttons when sections change
        self.sectionResized.connect(self._reposition_buttons)
        self.sectionMoved.connect(self._reposition_buttons)

        # Connect sectionCountChanged if available (not in all Qt versions)
        if hasattr(self, "sectionCountChanged"):
            try:
                self.sectionCountChanged.connect(self._reposition_buttons)
            except Exception:
                pass

        self._reposition_buttons()

    def add_header_button(
            self,
            column: int,
            tooltip: str = None,
            widget_to_show: QWidget = None
    ) -> None:
        """Add a filter button to a column header.

        Creates a small tool button positioned in the right side of the
        column header. Optionally associates a widget/dialog to show when
        the button is clicked.

        Args:
            column (int): Column index to add button to.
            tooltip (str, optional): Button tooltip. Defaults to "Filter column {n}".
            widget_to_show (QWidget, optional): Widget or dialog to show on click.
                If QDialog, it will be shown modally with exec().
                Otherwise shown with show().

        Side Effects:
            - Creates QToolButton in header
            - Stores widget association
            - Repositions all buttons
        """
        if column in self._buttons:
            return  # Already added

        # Store the widget (dialog or other) to show later on click
        if widget_to_show is not None:
            self._button_widget[column] = widget_to_show

        # Create button
        btn = QToolButton(self)
        btn.setText("Filter")
        btn.setIcon(QIcon(resource_path("icons/filter.png")))
        btn.setIconSize(QSize(18, 18))
        btn.setToolTip(tooltip or f"Filter column {column}")
        btn.setAutoRaise(True)
        btn.setCursor(Qt.PointingHandCursor)

        # Connect click handler (lambda captures column, ignores checked parameter)
        btn.clicked.connect(
            lambda checked=False, col=column: self._on_button_clicked(col)
        )

        btn.show()
        self._buttons[column] = btn
        self._reposition_buttons()

    def remove_filter_button(self, column: int) -> None:
        """Remove a filter button from a column header.

        Args:
            column (int): Column index to remove button from.

        Side Effects:
            - Deletes button widget
            - Removes widget association
        """
        btn = self._buttons.pop(column, None)
        if btn:
            btn.deleteLater()
        self._button_widget.pop(column, None)

    def _on_button_clicked(self, column: int) -> None:
        """Handle button click event.

        Args:
            column (int): Column index of clicked button.

        Side Effects:
            - Emits widgetRequested signal
            - Opens associated widget/dialog if present
        """
        self.widgetRequested.emit(column)
        self._open_widget_dialog(column)

    def _open_widget_dialog(self, column: int) -> None:
        """Open the widget/dialog associated with a column button.

        Args:
            column (int): Column index.

        Side Effects:
            - If QDialog: shows modally with exec()
            - If other widget: shows non-modally with show()
        """
        widget = self._button_widget.get(column)
        if widget is None:
            return

        if isinstance(widget, QDialog):
            # Ensure proper parent for modality
            if widget.parent() is None:
                widget.setParent(self.window())
            widget.exec()
        else:
            # Show non-modal
            widget.show()

    def _reposition_buttons(self, *args) -> None:
        """Reposition all buttons inside their column headers.

        Buttons are right-aligned within their column section.
        Buttons are hidden if:
        - Column is hidden
        - Column is too narrow
        - Column index is out of range

        Args:
            *args: Ignored arguments from signal connections.

        Side Effects:
            - Moves and shows/hides buttons as needed
        """
        if not self._buttons:
            return

        # Robustly get section count
        try:
            section_count = self.count()
        except Exception:
            section_count = (
                self.model().columnCount() if self.model() is not None else 0
            )

        for col, btn in list(self._buttons.items()):
            # Hide if column out of range
            if col < 0 or col >= section_count:
                btn.hide()
                continue

            # Hide if section is hidden
            try:
                hidden = self.isSectionHidden(col)
            except Exception:
                hidden = False
            if hidden:
                btn.hide()
                continue

            # Get section geometry
            x = self.sectionViewportPosition(col)
            w = self.sectionSize(col)

            # Hide if column too narrow for button
            if w <= 0 or w < btn.width() + 4:
                btn.hide()
                continue

            # Position button (right-aligned with 4px margin)
            rect = QRect(x, 0, w, self.height())
            x_pos = rect.right() - btn.width() - 4
            y = rect.top() + (rect.height() - btn.height()) // 2
            btn.move(x_pos, y)
            btn.show()


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing header with filter buttons."""

    app = QApplication(sys.argv)


    # Create sample dialog for filtering
    class SimpleFilterDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Filter Options")
            layout = QVBoxLayout(self)
            from PySide6.QtWidgets import QLabel
            layout.addWidget(QLabel("Filter settings would go here..."))


    # Create table with custom header
    table = QTableWidget(5, 4)
    table.setWindowTitle("HeaderButton Example")
    table.resize(600, 300)

    # Set up header with buttons
    header = HeaderButton(Qt.Horizontal, table)
    table.setHorizontalHeader(header)

    # Set column headers
    table.setHorizontalHeaderLabels(["Name", "Age", "City", "Score"])

    # Add sample data
    data = [
        ["Alice", "25", "Paris", "95"],
        ["Bob", "30", "London", "87"],
        ["Charlie", "22", "Berlin", "92"],
        ["Diana", "28", "Madrid", "89"],
        ["Eve", "26", "Rome", "94"],
    ]

    for row, row_data in enumerate(data):
        for col, value in enumerate(row_data):
            table.setItem(row, col, QTableWidgetItem(value))

    # Add filter buttons to columns 0, 2, and 3
    filter_dialog = SimpleFilterDialog()

    header.add_header_button(0, "Filter names", filter_dialog)
    header.add_header_button(2, "Filter cities")
    header.add_header_button(3, "Filter scores")


    # Connect signal to show which column was clicked
    def on_filter_requested(column):
        print(f"Filter button clicked for column {column}")


    header.widgetRequested.connect(on_filter_requested)

    table.show()
    sys.exit(app.exec())