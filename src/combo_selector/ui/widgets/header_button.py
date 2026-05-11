"""Custom table header with filter buttons in column headers.

This module provides a QHeaderView subclass that can display small
filter buttons inside specific column headers. The buttons automatically
reposition themselves when columns are resized, moved, or horizontally
scrolled.

Features:
- Add filter buttons to any column
- Buttons auto-reposition on resize/move/scroll
- Associate dialogs or widgets with buttons
- Emits signal when button clicked
"""

import sys

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QAbstractScrollArea,
    QDialog,
    QHeaderView,
    QStyle,
    QStyleOptionHeader,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from combo_selector.ui.widgets.section_help_button import SectionHelpButton
from combo_selector.utils import resource_path


class HeaderButton(QHeaderView):
    """Custom header view with filter buttons in column headers.

    Extends QHeaderView to support small tool buttons positioned inside
    column header sections. Buttons automatically reposition when columns
    are resized, moved, or horizontally scrolled.

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

        # Reposition buttons on horizontal scroll as well
        if isinstance(parent, QAbstractScrollArea):
            try:
                parent.horizontalScrollBar().valueChanged.connect(
                    self._reposition_buttons
                )
            except Exception:
                pass

        # Connect sectionCountChanged if available (not in all Qt versions)
        if hasattr(self, "sectionCountChanged"):
            try:
                self.sectionCountChanged.connect(self._reposition_buttons)
            except Exception:
                pass

        self._reposition_buttons()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_label_text(self, logical_index: int) -> str:
        """Return the display text for a header section.

        Args:
            logical_index (int): Logical column index.

        Returns:
            str: Header label text, or empty string on failure.
        """
        try:
            label = self.model().headerData(
                logical_index, self.orientation(), Qt.DisplayRole
            )
            return str(label) if label is not None else ""
        except Exception:
            return ""

    def _make_style_option(self, logical_index: int, rect: QRect) -> QStyleOptionHeader:
        """Build a QStyleOptionHeader for the given section.

        Mirrors what QHeaderView uses internally so that subElementRect
        returns an accurate label rect.

        Args:
            logical_index (int): Logical column index.
            rect (QRect): Bounding rect of the section in viewport coordinates.

        Returns:
            QStyleOptionHeader: Populated style option.
        """
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.section = logical_index
        opt.rect = rect
        opt.text = self._get_label_text(logical_index)
        opt.position = QStyleOptionHeader.Middle
        opt.selectedPosition = QStyleOptionHeader.NotAdjacent
        return opt

    def _text_end_x(self, logical_index: int) -> int:
        """Return the viewport x-coordinate of the right edge of the header
        text for *logical_index*.

        Uses QStyle.SE_HeaderLabel to find the rect Qt paints into, then
        measures the actual text width with fontMetrics so the button always
        sits flush against the last character — even when the column is wider
        than the text.

        Args:
            logical_index (int): Logical column index.

        Returns:
            int: x pixel position of text right edge in viewport coordinates.
        """
        sec_x = self.sectionViewportPosition(logical_index)
        sec_w = self.sectionSize(logical_index)
        sec_rect = QRect(sec_x, 0, sec_w, self.height())

        opt = self._make_style_option(logical_index, sec_rect)

        # The rect Qt uses for the label (accounts for margins, sort arrow, etc.)
        label_rect = self.style().subElementRect(QStyle.SE_HeaderLabel, opt, self)

        # Actual pixel width of the text string
        fm = self.fontMetrics()
        text_w = min(fm.horizontalAdvance(opt.text), label_rect.width())

        return label_rect.left() + text_w

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintSection(self, painter, rect: QRect, logical_index: int) -> None:
        """Paint a header section.

        For sections that have a button the label text is clipped to a
        narrowed rect so it can never overlap the button, regardless of
        column width. Sections without a button are painted normally.

        Args:
            painter (QPainter): Active painter for the viewport.
            rect (QRect): Bounding rect of the section in viewport coordinates.
            logical_index (int): Logical index of the section being painted.
        """
        if logical_index not in self._buttons:
            super().paintSection(painter, rect, logical_index)
            return

        btn = self._buttons[logical_index]
        btn_w = btn.sizeHint().width()
        gap = 4  # px between text right edge and button left edge

        painter.save()

        opt = self._make_style_option(logical_index, rect)

        # 1. Draw background (frame, highlight, etc.) without any text
        opt_bg = QStyleOptionHeader(opt)
        opt_bg.text = ""
        self.style().drawControl(QStyle.CE_Header, opt_bg, painter, self)

        # 2. Draw the label text clipped to the area left of the button
        text_rect = rect.adjusted(0, 0, -(btn_w + gap), 0)
        opt_text = QStyleOptionHeader(opt)
        opt_text.rect = text_rect
        self.style().drawControl(QStyle.CE_Header, opt_text, painter, self)

        painter.restore()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_header_button(
        self,
        column: int,
        tooltip: str = None,
        widget_to_show: QWidget = None,
    ) -> None:
        """Add a filter button to a column header.

        Creates a small tool button placed immediately after the header text.
        The text area is automatically constrained via paintSection so it
        never overlaps the button. Optionally associates a widget/dialog to
        show when the button is clicked.

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
        btn.adjustSize()  # Ensure sizeHint is valid before first reposition

        # Connect click handler (lambda captures column, ignores checked parameter)
        btn.clicked.connect(
            lambda checked=False, col=column: self._on_button_clicked(col)
        )

        btn.show()
        self._buttons[column] = btn
        self._reposition_buttons()

    def add_header_help_button(
        self,
        column: int,
        title: str,
        markdown_path: str,
    ) -> None:
        """Add a help button to a column header.

        Attaches a :class:`~combo_selector.ui.widgets.section_help_button.SectionHelpButton`
        to the given column that opens a help pop-up when clicked. The button
        is placed immediately after the header text.

        Args:
            column (int): Column index to attach the help button to.
            title (str): Title shown in the help pop-up dialog.
            markdown_path (str): Path to the Markdown file displayed in the
                help pop-up.

        Side Effects:
            - Creates and shows a :class:`SectionHelpButton`.
            - Stores the button in ``_buttons[column]``.
            - Repositions all header buttons.
        """
        if column in self._buttons:
            return  # Already added

        btn = SectionHelpButton(
            title=title,
            markdown_path=markdown_path,
            parent=self,
        )
        btn.adjustSize()  # Ensure sizeHint is valid before first reposition

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
        self.viewport().update()

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
        """Reposition all buttons immediately after their column header text.

        The button x position is derived from _text_end_x() which uses
        QStyle.SE_HeaderLabel + fontMetrics to find exactly where the text
        ends, so the button tracks the text even as the column is resized
        or horizontally scrolled.

        The section is widened automatically if it is too narrow to show
        both the text and the button.

        Buttons are hidden if:
        - Column is hidden
        - Column index is out of range

        Args:
            *args: Ignored arguments from signal connections.

        Side Effects:
            - Moves and shows/hides buttons as needed
            - May resize sections to ensure text + button fit
        """
        if not self._buttons:
            return

        if self.model() is None:
            return

        # Robustly get section count
        try:
            section_count = self.count()
        except Exception:
            section_count = (
                self.model().columnCount() if self.model() is not None else 0
            )

        gap = 4  # px between text right edge and button left edge

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

            btn_size = btn.sizeHint()
            btn_w = btn_size.width()
            btn_h = btn_size.height()

            sec_x = self.sectionViewportPosition(col)
            sec_w = self.sectionSize(col)

            # Ensure section is wide enough: text label rect + gap + button + gap
            sec_rect = QRect(sec_x, 0, sec_w, self.height())
            opt = self._make_style_option(col, sec_rect)
            label_rect = self.style().subElementRect(QStyle.SE_HeaderLabel, opt, self)
            fm = self.fontMetrics()
            text_w = fm.horizontalAdvance(opt.text)

            # Minimum width: left margin + text + gap + button + right margin
            left_margin = label_rect.left() - sec_x
            right_margin = gap
            min_w = left_margin + text_w + gap + btn_w + right_margin
            if sec_w < min_w:
                self.blockSignals(True)
                self.resizeSection(col, min_w)
                self.blockSignals(False)
                sec_w = min_w

            # Place button right after the text, vertically centred
            x_pos = self._text_end_x(col) + gap
            y_pos = (self.height() - btn_h) // 2
            btn.move(x_pos, y_pos)
            btn.show()

    def resizeEvent(self, event) -> None:
        """Ensure buttons stay aligned when the header itself resizes."""
        super().resizeEvent(event)
        self._reposition_buttons()

    def showEvent(self, event) -> None:
        """Ensure buttons are correctly positioned when the header is shown."""
        super().showEvent(event)
        self._reposition_buttons()


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing header with filter buttons."""

    app = QApplication(sys.argv)

    # Create sample dialog for filtering
    class SimpleFilterDialog(QDialog):
        """Sample filter dialog for demonstration purposes."""

        def __init__(self, parent=None):
            """Initialize the demo filter dialog.

            Args:
                parent (QWidget | None): Optional parent widget.
            """
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
    header.add_header_help_button(3, "Filter scores", "no_help_found.md")

    # Connect signal to show which column was clicked
    def on_filter_requested(column):
        """Print the column index when a filter button is clicked.

        Args:
            column (int): Index of the column whose filter button was clicked.
        """
        print(f"Filter button clicked for column {column}")

    header.widgetRequested.connect(on_filter_requested)

    table.show()
    sys.exit(app.exec())