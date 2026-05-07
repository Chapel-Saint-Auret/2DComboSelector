"""Styled table widget with title bar, footer, and custom header buttons.

This module provides:
- TablePanel  – self-contained table (model + view + async loading)
- StyledTable – card shell (title bar + TablePanel + footer)
"""

import sys

import pandas as pd
from PySide6.QtCore import QModelIndex, Qt, QThreadPool, Signal, QSize
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QSizePolicy,
    QTabWidget,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from combo_selector.core.workers import TableDataWorker
from combo_selector.ui.widgets.header_button import HeaderButton
from combo_selector.ui.widgets.section_help_button import SectionHelpButton
from combo_selector.ui.widgets.orthogonality_table import (
    OrthogonalityTableModel,
    OrthogonalityTableView,
    SquareBackgroundDelegate,
)


# =============================================================================
# TablePanel – pure table logic (model + view + async loading)
# =============================================================================

class TablePanel(QWidget):
    """Self-contained table widget: model, view, header, delegate and async loading.

    This class owns all table-related state and exposes every data/selection
    operation.  It has *no* knowledge of title bars, footers, or card frames –
    those belong to :class:`StyledTable`.

    Signals:
        selectionChanged(): Emitted when the table selection changes.

    Attributes:
        threadpool (QThreadPool): Thread pool for async data loading.
        model (OrthogonalityTableModel): Table data model.
        table (OrthogonalityTableView): Table view widget.
        header (HeaderButton): Custom header with filter-button support.
    """

    selectionChanged = Signal()

    def __init__(
        self,
        value_format: str = ".3f",
        enable_decoration: bool = False,
        color_config=None,
        bold_columns=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.threadpool = QThreadPool()

        self.value_format = value_format

        # Model + view
        self.model = OrthogonalityTableModel(color_config = color_config,
                                             bold_columns = bold_columns,
                                             enable_decoration=enable_decoration)
        self.table = OrthogonalityTableView(self, self.model)


        # Custom header with filter-button support
        self.header = HeaderButton(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(self.header)

        # Delegate for NaN highlighting
        self.table.setItemDelegate(SquareBackgroundDelegate(self.table))

        # Layout – the view fills all available space
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.table)


        # Selection forwarding
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        self.selectionChanged.emit()

    def get_selected_rows(self) -> list:
        """Return a list of selected :class:`QModelIndex` objects."""
        return self.table.selectionModel().selectedRows()

    def select_row(self, index: int) -> None:
        """Programmatically select *index*."""
        self.table.selectRow(index)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def async_set_table_data(self, df: pd.DataFrame) -> None:
        """Load *df* in a background thread; updates the view when done."""
        worker = TableDataWorker(df, self.model.get_header_label(), value_format=self.value_format)
        worker.signals.finished.connect(self._handle_data)
        self.threadpool.start(worker)

    def _handle_data(self, data: list, rows: int, cols: int) -> None:
        """Slot: receive formatted data from the async worker."""
        self.model.apply_formatted_data(data, rows, cols)

        header = self.table.horizontalHeader()
        header.setResizeContentsPrecision(50)
        self.table.resizeColumnsToContents()

        for i in range(cols):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            if i == cols - 1:
                self.table.setColumnWidth(i, 250)

    def clean_table(self) -> None:
        """Clear all data and reset to the default row count."""
        self.model.set_formated_data([])
        self.set_default_row_count(10)

    # ------------------------------------------------------------------
    # Header / columns
    # ------------------------------------------------------------------

    def add_header_button(self, column: int, tooltip: str, widget_to_show: QWidget) -> None:
        """Add a filter button to *column* in the header."""
        self.header.add_header_button(
            column=column, tooltip=tooltip, widget_to_show=widget_to_show
        )

    def add_help_button(self, column: int, title: str,markdown_path: str):
        """Add a help button to the specified column header (placeholder).

        Args:
            column (int): Column index to attach the help button to.
        """
        self.header.add_header_help_button(
            column=column, title=title, markdown_path=markdown_path
        )

    def get_header(self) -> HeaderButton:
        """Return the :class:`HeaderButton` instance."""
        return self.header

    def set_header_label(self, header_label: list) -> None:
        """Set the column header strings."""
        self.model.set_header_label(header_label)

    def set_default_row_count(self, value: int) -> None:
        """Set the number of placeholder rows shown in an empty table."""
        self.model.set_default_row_count(value)

    def get_row_count(self) -> int:
        """Return the current number of rows."""
        return self.model.rowCount(QModelIndex())

    def resize_column_width(self) -> None:
        """Stretch column 1 to fill available width."""
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def set_section_resize_mode(self) -> None:
        """Auto-size all columns; stretch column 1 (Combination)."""
        for col in range(self.model.columnCount(QModelIndex())):
            self.table.setColumnWidth(col, self.table.columnWidth(col) + 10)

        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.horizontalHeader().setStretchLastSection(True)

        for i in range(self.table.model().columnCount(QModelIndex())):
            mode = QHeaderView.Stretch if i == 1 else QHeaderView.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(i, mode)


    # ------------------------------------------------------------------
    # Filtering / proxy
    # ------------------------------------------------------------------

    def set_filter_key_column(self, column: int) -> None:
        """Set the column used for text-based proxy filtering."""
        self.table.setFilterKeyColumn(column)

    def set_proxy_filter_regexp(self, regexp: str) -> None:
        """Apply a regular-expression filter to the proxy model."""
        self.table.filterExpChanged(regexp)

    def set_table_proxy(self) -> None:
        """Wire the model to the view's proxy model."""
        self.model.set_proxy(self.table.getProxyModel())

    def get_proxy_model(self):
        """Return the :class:`QSortFilterProxyModel` used by the view."""
        return self.table.getProxyModel()

    # ------------------------------------------------------------------
    # Model / view accessors
    # ------------------------------------------------------------------

    def get_model(self) -> OrthogonalityTableModel:
        """Return the :class:`OrthogonalityTableModel`."""
        return self.model

    def get_table_view(self) -> OrthogonalityTableView:
        """Return the :class:`OrthogonalityTableView`."""
        return self.table


# =============================================================================
# StyledTable – card shell (title bar + TablePanel + footer)
# =============================================================================

class StyledTable(QWidget):
    """Card-style wrapper: blue title bar on top, :class:`TablePanel` in the
    middle, and a styled footer at the bottom.

    All data/model operations are forwarded to the internal
    :attr:`table_panel` so call sites remain unchanged.

    Signals:
        selectionChanged(): Forwarded from the inner :class:`TablePanel`.

    Attributes:
        title_bar (QLabel): The blue title label.
        table_panel (TablePanel): The embedded table widget.
        footer (QFrame): The footer frame (empty by default).

    Example:
        >>> t = StyledTable(title="Analysis Results")
        >>> t.set_header_label(['Set', 'Pearson', 'Spearman', 'Score'])
        >>> t.async_set_table_data(df)
        >>> t.selectionChanged.connect(lambda: print("changed"))
    """

    selectionChanged = Signal()

    def __init__(
        self,
        title: str = "",
        value_format: str = ".3f",
        has_tab:bool = False,
        color_config=None,
        bold_columns=None,
        enable_decoration: bool = False,
    ) -> None:
        super().__init__()

        self.sheet_index = {}
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Card frame ────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("CardFrame")
        card.setLayout(QVBoxLayout())
        card.layout().setContentsMargins(5, 5, 5, 5)
        card.layout().setSpacing(0)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        # --- Title bar: label + help button ----------------------------------
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setObjectName("TitleBarFrame")

        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(10, 0, 6, 0)
        self.title_layout.setSpacing(4)

        # Title bar
        self.title_label = QLabel(title)
        self.title_label.setFixedHeight(40)
        self.title_label.setObjectName("TitleBar")
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.title_label.setContentsMargins(10, 0, 0, 0)

        self.title_layout.addWidget(self.title_label, 0, Qt.AlignVCenter)

        # ── Table panel ───────────────────────────────────────────────
        self.table_panel = TablePanel(
            value_format=value_format,
            enable_decoration=enable_decoration,
            color_config=color_config,
            bold_columns=bold_columns,
            parent=self,
        )
        self.table_panel.selectionChanged.connect(self.selectionChanged)


        # ── Footer ────────────────────────────────────────────────────
        self.footer = QFrame()
        self.footer.setObjectName("Footer")
        self.footer.setLayout(QHBoxLayout())
        self.footer.layout().setContentsMargins(12, 6, 12, 6)
        self.footer.layout().setSpacing(8)

        # ── Assemble card ─────────────────────────────────────────────
        card.layout().addWidget(self.title_bar)

        if has_tab:
            self.tab_widget = QTabWidget(card)
            self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            card.layout().addWidget(self.tab_widget, 1)

        else:
            card.layout().addWidget(self.table_panel, 1)

        card.layout().addWidget(self.footer)
        outer.addWidget(card, 1)

        self._apply_styles()

    def add_title_bar_info_button(self, markdown_path:str) -> None:
        title_help_btn = SectionHelpButton(
            title="",
            markdown_path=markdown_path,
            parent=self.title_bar,
        )
        title_help_btn.setFixedSize(22, 22)           # ← explicit size, same as the close btn in HelpDialog
        title_help_btn.setIconSize(QSize(16, 16))     # ← keep icon smaller than the button box
        title_help_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                color: #ffffff;
                font-size: 15px;
            }
            QToolButton:hover {
                color: #c5d0e6;
            }
        """)

        self.title_layout.addWidget(title_help_btn, 0, Qt.AlignVCenter)  # ← per-item alignment flag
        self.title_layout.addStretch(1)

    def add_sheet(self,sheet_name='unnamed',value_format=".3f",color_config = None,bold_columns = None,enable_decoration= False) -> None:
        table_panel = TablePanel(
        value_format=value_format,
        color_config=color_config,
        bold_columns=bold_columns,
        enable_decoration = enable_decoration,
        parent=self,
        )

        table_panel.set_default_row_count(10)

        index = self.tab_widget.addTab(table_panel, sheet_name)
        self.sheet_index[sheet_name] = index

    def get_sheet_index_dict(self) -> dict:
        """get the table sheet index from the QTabWidget.

        Returns:
            dict: sheet index dictionary.
        """
        return self.sheet_index

    def get_table_from_sheet(self,sheet_name:str) -> TablePanel:
        """Get the TablePanel associated to the sheet name.
        Args: shee_name (str): sheet name.

        Returns:
            TablePanel: The TablePanel associated to the sheet name.
        """

        tab_index = self.sheet_index[sheet_name]
        return self.tab_widget.widget(tab_index)

    # ------------------------------------------------------------------
    # Public API – forwarded to TablePanel so call sites stay the same
    # ------------------------------------------------------------------

    def clean_table(self) -> None:
        self.table_panel.clean_table()

    def add_header_button(self, column: int, tooltip: str, widget_to_show: QWidget) -> None:
        self.table_panel.add_header_button(column, tooltip, widget_to_show)

    def add_help_button(self, column: int, title: str,markdown_path: str):
        self.table_panel.add_help_button(column, title, markdown_path)

    def get_header(self) -> HeaderButton:
        return self.table_panel.get_header()

    def set_header_label(self, header_label: list) -> None:
        self.table_panel.set_header_label(header_label)

    def set_default_row_count(self, value: int) -> None:
        self.table_panel.set_default_row_count(value)

    def get_row_count(self) -> int:
        return self.table_panel.get_row_count()

    def select_row(self, index: int) -> None:
        self.table_panel.select_row(index)

    def get_selected_rows(self) -> list:
        return self.table_panel.get_selected_rows()

    def async_set_table_data(self, df: pd.DataFrame) -> None:
        self.table_panel.async_set_table_data(df)

    def resize_column_width(self) -> None:
        self.table_panel.resize_column_width()

    def set_section_resize_mode(self) -> None:
        self.table_panel.set_section_resize_mode()

    def set_filter_key_column(self, column: int) -> None:
        self.table_panel.set_filter_key_column(column)

    def set_proxy_filter_regexp(self, regexp: str) -> None:
        self.table_panel.set_proxy_filter_regexp(regexp)

    def set_table_proxy(self) -> None:
        self.table_panel.set_table_proxy()

    def get_proxy_model(self):
        return self.table_panel.get_proxy_model()

    def get_model(self) -> OrthogonalityTableModel:
        return self.table_panel.get_model()

    def get_table_view(self) -> OrthogonalityTableView:
        return self.table_panel.get_table_view()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QWidget {
                font-family: Segoe UI, Arial;
                font-size: 13px;
            }

            QLabel#TitleBar {
                background-color: #183881;
                color: #ffffff;
                font-weight: bold;
                font-size: 19px;
            }
            
            QFrame#TitleBarFrame  {
                background-color: #183881;
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
    import numpy as np

    app = QApplication(sys.argv)

    data = pd.DataFrame({
        'Set': ['A', 'B', 'C', 'D'],
        'Combination': ['HILIC vs RPLC', 'RPLC vs IEX', 'IEX vs SEC', 'SEC vs HILIC'],
        'Pearson': [0.856, 0.723, 0.912, 0.678],
        'Spearman': [0.834, 0.701, 0.895, np.nan],
        'Orthogonality Score': [0.75, 0.82, 0.91, 0.73],
    })

    table = StyledTable(title="Orthogonality Analysis Results")
    table.set_header_label(list(data.columns))
    table.async_set_table_data(data)
    table.selectionChanged.connect(lambda: print(f"Selected {len(table.get_selected_rows())} row(s)"))

    table.resize(800, 400)
    table.show()

    sys.exit(app.exec())