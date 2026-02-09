"""Styled table widget with title bar, footer, and custom header buttons.

This module provides a complete styled table widget designed for displaying
orthogonality analysis results with:
- Card-style frame with rounded corners
- Title bar with blue background
- Custom header with filter button support
- Footer area for controls
- Async data loading support
- Selection change signals
- Modern blue color scheme
"""

import sys

import pandas as pd
from PySide6.QtCore import QModelIndex, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from combo_selector.core.workers import TableDataWorker
from combo_selector.ui.widgets.header_button import HeaderButton
from combo_selector.ui.widgets.orthogonality_table import (
    OrthogonalityTableModel,
    OrthogonalityTableView,
    SquareBackgroundDelegate,
)


class StyledTable(QWidget):
    """Complete styled table with title, content, and footer.

    Provides a card-style table widget with:
    - Blue title bar with rounded top corners
    - Orthogonality table with custom formatting
    - Filter buttons in column headers
    - Footer area for additional controls
    - Async data loading with thread pool
    - Selection change notifications

    Signals:
        selectionChanged(): Emitted when table selection changes.

    Attributes:
        threadpool (QThreadPool): Thread pool for async data loading.
        model (OrthogonalityTableModel): Table data model.
        table (OrthogonalityTableView): Table view widget.
        header (HeaderButton): Custom header with filter buttons.

    Example:
        >>> table = StyledTable(title="Analysis Results")
        >>> table.set_header_label(['Set', 'Pearson', 'Spearman', 'Score'])
        >>> table.set_table_data(df)
        >>> table.selectionChanged.connect(lambda: print("Selection changed"))
    """

    selectionChanged = Signal()

    def __init__(self, title: str = ""):
        """Initialize the styled table widget.

        Args:
            title (str): Title text for the title bar.
        """
        super().__init__()

        self.threadpool = QThreadPool()

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        # Card frame
        card = QFrame()
        card.setObjectName("CardFrame")
        card.setLayout(QVBoxLayout())
        card.layout().setContentsMargins(5, 5, 5, 5)
        card.layout().setSpacing(0)

        # Title bar
        title_label = QLabel(title)
        title_label.setFixedHeight(30)
        title_label.setObjectName("TitleBar")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_label.setContentsMargins(10, 0, 0, 0)

        # Table with custom model and view
        self.model = OrthogonalityTableModel()
        self.table = OrthogonalityTableView(self, self.model)

        # Custom header with filter button support
        self.header = HeaderButton(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(self.header)

        # Square background delegate for NaN highlighting
        self.table.setItemDelegate(SquareBackgroundDelegate(self.table))

        # Footer (currently empty, but styled)
        footer = QFrame()
        footer.setObjectName("Footer")
        footer.setLayout(QHBoxLayout())
        footer.layout().setContentsMargins(12, 6, 12, 6)
        footer.layout().setSpacing(8)

        # Assemble components
        card.layout().addWidget(title_label)
        card.layout().addWidget(self.table)
        card.layout().addWidget(footer)
        outer.addWidget(card)

        # Apply stylesheet
        self._apply_styles()

        # Connect selection signal
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)

    def clean_table(self) -> None:
        """Clear table data and reset to default row count.

        Side Effects:
            - Clears all formatted data
            - Sets row count to 10
        """
        self.model.set_formated_data([])
        self.set_default_row_count(10)

    def add_header_button(self, column: int, tooltip: str, widget_to_show: QWidget) -> None:
        """Add a filter button to a column header.

        Args:
            column (int): Column index for button.
            tooltip (str): Tooltip text for button.
            widget_to_show (QWidget): Widget/dialog to show when clicked.
        """
        self.header.add_header_button(
            column=column, tooltip=tooltip, widget_to_show=widget_to_show
        )

    def selection_changed(self) -> None:
        """Handle selection changes and emit signal.

        Side Effects:
            - Emits selectionChanged signal
        """
        self.selectionChanged.emit()

    def async_set_table_data(self, df: pd.DataFrame) -> None:
        """Load table data asynchronously using thread pool.

        Args:
            df (pd.DataFrame): Data to load.

        Side Effects:
            - Starts worker thread for data formatting
            - Calls handle_data() when complete
        """
        worker = TableDataWorker(df, self.model.get_header_label())
        worker.signals.finished.connect(self.handle_data)
        self.threadpool.start(worker)

    def handle_data(self, data: list, rows: int, cols: int) -> None:
        """Handle formatted data from async worker.

        Args:
            data (list): Formatted data.
            rows (int): Number of rows.
            cols (int): Number of columns.

        Side Effects:
            - Applies formatted data to model
        """
        self.model.apply_formatted_data(data, rows, cols)

    def set_table_data(self, data: pd.DataFrame) -> None:
        """Set table data synchronously with auto-sizing.

        Args:
            data (pd.DataFrame): Data to display.

        Side Effects:
            - Sets model data
            - Adjusts column widths
            - Configures column resize modes
            - Stretches column 1 (Combination column)
        """
        self.model.set_data(data)

        # Add padding to columns
        for col in range(self.model.columnCount(QModelIndex())):
            current_width = self.table.columnWidth(col)
            self.table.setColumnWidth(col, current_width + 10)

        # Configure header alignment
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )
        self.table.horizontalHeader().setStretchLastSection(True)

        # Set column resize modes
        for i in range(self.table.model().columnCount(QModelIndex())):
            if i == 1:  # 'Combination' column - stretch to fill space
                self.table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.Stretch
                )
            else:
                self.table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeToContents
                )

    def get_header(self) -> HeaderButton:
        """Get the custom header widget.

        Returns:
            HeaderButton: Header widget with filter button support.
        """
        return self.header

    def set_proxy_filter_regexp(self, regexp: str) -> None:
        """Set filter regular expression on proxy model.

        Args:
            regexp (str): Regular expression pattern.
        """
        self.table.filterExpChanged(regexp)

    def set_table_proxy(self) -> None:
        """Configure model to use table's proxy model."""
        self.model.set_proxy(self.table.getProxyModel())

    def get_proxy_model(self):
        """Get the table's proxy model.

        Returns:
            QSortFilterProxyModel: Proxy model for sorting/filtering.
        """
        return self.table.getProxyModel()

    def get_selected_rows(self) -> list:
        """Get currently selected rows.

        Returns:
            list: List of selected QModelIndex objects.
        """
        return self.table.selectionModel().selectedRows()

    def get_model(self) -> OrthogonalityTableModel:
        """Get the table model.

        Returns:
            OrthogonalityTableModel: Data model.
        """
        return self.model

    def get_table_view(self) -> OrthogonalityTableView:
        """Get the table view widget.

        Returns:
            OrthogonalityTableView: Table view.
        """
        return self.table

    def get_row_count(self) -> int:
        """Get number of rows in model.

        Returns:
            int: Row count.
        """
        return self.model.rowCount(QModelIndex())

    def select_row(self, index: int) -> None:
        """Select a specific row.

        Args:
            index (int): Row index to select.
        """
        self.table.selectRow(index)

    def set_header_label(self, header_label: list) -> None:
        """Set column header labels.

        Args:
            header_label (list): List of column header strings.
        """
        self.model.set_header_label(header_label)

    def set_default_row_count(self, value: int) -> None:
        """Set default row count for empty table.

        Args:
            value (int): Number of rows.
        """
        self.model.set_default_row_count(value)

    def _apply_styles(self) -> None:
        """Apply stylesheet to the widget.

        Side Effects:
            - Sets modern blue color scheme
            - Styles title bar, table, scrollbars, and footer
        """
        self.setStyleSheet("""
            QWidget {
                font-family: Segoe UI, Arial;
                font-size: 13px;
            }

            QLabel#TitleBar {
                background-color: #183881;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }

            QHeaderView::section {
                background-color: #d1d9fc;
                color: #1859b4;
                font-size: 12px;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #d0d4da;
            }

            QTableView {
                background-color: #F6F8FD;
                gridline-color: #D4D6EC;
                selection-background-color: #c9daf8;
                selection-color: #000000;
                font-size: 11px;
            }

            QTableView::item:selected {
                background-color: #d8e5fc;
                color: #000000;
            }

            QTableView::item {
                background: transparent;
                border: none;
                border-radius: 0px;
            }

            QScrollBar:vertical {
                border: none;
                background: #bdcaf6;
                width: 10px;
                margin: 4px 0 4px 0;
            }

            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
                border-radius: 5px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }

            QFrame#Footer {
                background-color: #f1f3f6;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Example showing the styled table with sample data."""

    # Note: This example requires TableDataWorker which may not be available
    # in standalone context. For full functionality, run within the application.

    app = QApplication(sys.argv)

    # Create sample data
    import numpy as np

    data = pd.DataFrame({
        'Set': ['A', 'B', 'C', 'D'],
        'Combination': ['HILIC vs RPLC', 'RPLC vs IEX', 'IEX vs SEC', 'SEC vs HILIC'],
        'Pearson': [0.856, 0.723, 0.912, 0.678],
        'Spearman': [0.834, 0.701, 0.895, np.nan],
        'Orthogonality Score': [0.75, 0.82, 0.91, 0.73],
    })

    # Create styled table
    table = StyledTable(title="Orthogonality Analysis Results")
    table.set_header_label(list(data.columns))
    table.set_table_data(data)


    # Connect selection signal
    def on_selection():
        rows = table.get_selected_rows()
        print(f"Selected {len(rows)} row(s)")


    table.selectionChanged.connect(on_selection)

    table.resize(800, 400)
    table.show()

    sys.exit(app.exec())