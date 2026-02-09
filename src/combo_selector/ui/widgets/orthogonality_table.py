"""Table model and view for displaying chromatographic orthogonality analysis results.

This module provides a complete table system for displaying 2D chromatography
orthogonality metrics including:
- Correlation coefficients (Pearson, Spearman, Kendall)
- Geometric measures (Convex Hull, Bin Box Counting)
- Orthogonality scores and factors
- 2D peak capacity calculations

Features:
- Custom formatting (3 decimal places for floats)
- NaN value highlighting (red background)
- Sortable columns with smart NaN handling
- Search/filter functionality
- Row selection support
"""

import math
import sys
from enum import Enum

import numpy as np
import pandas as pd
from PySide6.QtCore import (
    QAbstractTableModel,
    QItemSelectionModel,
    QModelIndex,
    QRegularExpression,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class COLUMN(Enum):
    """Column index enumeration for orthogonality table."""

    SET = 0
    TITLE = 1
    TWODPEAK = 2
    CNVX_HULL = 3
    BIN_BOX = 4
    LINEARR = 5
    PEARSON = 6
    SPEARMAN = 7
    KENDALL = 8
    ASTERIK = 9
    NNDAMEAN = 10
    NNDGMEAN = 11
    NNDHMEAN = 12
    ORTHOFACTOR = 13
    ORTHOSCORE = 14
    PRACTTWODPEAK = 15

class OrthogonalityTableSortProxy(QSortFilterProxyModel):
    """Sort proxy that handles NaN values intelligently.

    Ensures NaN values always sort to the end regardless of sort order,
    preventing them from appearing at the top of ascending sorts.

    Features:
    - NaN values always last
    - Numeric sorting when possible
    - String fallback for non-numeric data
    - Sequential vertical header numbering
    """

    def __init__(self):
        """Initialize the sort proxy."""
        super().__init__()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """Compare two values for sorting.

        Args:
            left (QModelIndex): Left value index.
            right (QModelIndex): Right value index.

        Returns:
            bool: True if left < right.

        Sorting rules:
            - NaN → +infinity (always last)
            - None → +infinity (always last)
            - Numeric values compared numerically
            - Non-numeric compared as strings
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        def norm(v):
            """Normalize value for comparison."""
            if v is None:
                return math.inf
            try:
                f = float(v)
                return f if not math.isnan(f) else math.inf
            except (ValueError, TypeError):
                # Not numeric, fallback to string comparison
                return v

        return norm(left_data) < norm(right_data)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Get header data with sequential vertical numbering.

        Args:
            section (int): Section index.
            orientation (Qt.Orientation): Header orientation.
            role (int): Data role.

        Returns:
            Header data or None.
        """
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)  # Sequential row numbers
        return super().headerData(section, orientation, role)

    def mapToSourceRow(self, proxy_row: int) -> int:
        """Map proxy row to source row.

        Args:
            proxy_row (int): Proxy row index.

        Returns:
            int: Source row index.
        """
        return self.mapToSource(self.index(proxy_row, 0)).row()


class OrthogonalityTableModel(QAbstractTableModel):
    """Table model for orthogonality analysis results.

    Manages tabular data with custom formatting:
    - Floats displayed with 3 decimal places
    - "Practical 2D peak capacity" column displayed as integers
    - NaN values highlighted with red background

    Attributes:
        _raw_data (list): Original unformatted data.
        _formatted_data (list): Cached formatted strings for display.
        header_label (list): Column header labels.
        _row_count (int): Number of rows.
        _column_count (int): Number of columns.

    Example:
        >>> model = OrthogonalityTableModel()
        >>> model.set_header_label(['Set', 'Pearson', 'Spearman', 'Score'])
        >>> df = pd.DataFrame({...})
        >>> model.set_data(df)
    """

    def __init__(self, data: pd.DataFrame = None):
        """Initialize the table model.

        Args:
            data (pd.DataFrame, optional): Initial data.
        """
        super().__init__()
        self._raw_data = None
        self._formatted_data = []
        self.default_row_count = 0
        self._data = data if data is not None else pd.DataFrame()
        self.header_label = []
        self.proxy_model = None
        self._row_count = 0
        self._column_count = 0

    def set_default_row_count(self, row_count: int) -> None:
        """Set default row count and emit model reset.

        Args:
            row_count (int): Number of rows.
        """
        self._row_count = row_count
        self.modelReset.emit()

    def set_header_label(self, header_label: list) -> None:
        """Set column headers and emit model reset.

        Args:
            header_label (list): List of column header strings.
        """
        self.header_label = header_label
        self._column_count = len(self.header_label)
        self.modelReset.emit()

    def get_header_label(self) -> list:
        """Get column headers.

        Returns:
            list: Column header strings.
        """
        return self.header_label

    def set_proxy(self, proxy: QSortFilterProxyModel) -> None:
        """Set associated proxy model.

        Args:
            proxy (QSortFilterProxyModel): Proxy model.
        """
        self.proxy_model = proxy

    def set_formated_data(self, data: list) -> None:
        """Set preformatted data directly.

        Args:
            data (list): 2D list of formatted strings.
        """
        self._formatted_data = data
        self.modelReset.emit()

    def set_data(self, data: pd.DataFrame) -> None:
        """Set data from pandas DataFrame with automatic formatting.

        Args:
            data (pd.DataFrame): Data to display.

        Side Effects:
            - Formats all values for display
            - Emits model reset signal
        """
        self.beginResetModel()
        data_cast = data.astype(object)
        data_list = data_cast.values.tolist()

        self._raw_data = data_list

        # Cache formatted values for display
        self._formatted_data = [
            [self._format_value(val, col_idx=j) for j, val in enumerate(row)]
            for row in data_list
        ]

        self._row_count = len(data_list)
        self._column_count = len(data_list[0]) if self._row_count > 0 else 0
        self.endResetModel()

    def _format_value(self, val, col_idx: int = None) -> str:
        """Format a value for display.

        Args:
            val: Value to format.
            col_idx (int, optional): Column index for special formatting.

        Returns:
            str: Formatted value.

        Formatting rules:
            - "Practical 2D peak capacity": Rounded to integer
            - Integers: As-is
            - Floats: 3 decimal places
            - Others: String representation
        """
        # Special case: "Practical 2D peak capacity" column
        if (
                col_idx is not None
                and self.header_label
                and col_idx < len(self.header_label)
                and self.header_label[col_idx] == "Practical 2D peak capacity"
        ):
            try:
                return str(int(round(float(val))))
            except Exception:
                return str(val)

        # Type-based formatting
        if isinstance(val, (int, np.integer)):
            return str(val)
        elif isinstance(val, (float, np.floating)):
            return f"{val:.3f}"
        elif isinstance(val, (str, tuple)):
            return str(val)
        else:
            return str(val)

    def apply_formatted_data(self, formatted_data: list, row_count: int, col_count: int) -> None:
        """Apply preformatted data with explicit dimensions.

        Args:
            formatted_data (list): 2D list of formatted values.
            row_count (int): Number of rows.
            col_count (int): Number of columns.
        """
        self.beginResetModel()
        self._formatted_data = formatted_data
        self._row_count = row_count
        self._column_count = col_count
        self.endResetModel()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Get data for a table cell.

        Args:
            index (QModelIndex): Cell index.
            role (int): Data role (DisplayRole, UserRole, BackgroundRole).

        Returns:
            Data appropriate for the role, or None.
        """
        if not index.isValid() or not self._formatted_data:
            return None

        r, c = index.row(), index.column()

        if role == Qt.DisplayRole:
            return self._formatted_data[r][c]

        if role == Qt.UserRole:
            return self._formatted_data[r][c]

        elif role == Qt.BackgroundRole:
            val = str(self._formatted_data[r][c]).strip().lower()
            if val == "nan":
                return QBrush(QColor("#ff9999"))  # Red background for NaN
            return None

        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of rows.

        Returns:
            int: Row count.
        """
        return self._row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of columns.

        Returns:
            int: Column count.
        """
        return self._column_count

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Get header data.

        Args:
            section (int): Section index.
            orientation (Qt.Orientation): Horizontal or vertical.
            role (int): Data role.

        Returns:
            Header label or None.
        """
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and section < len(self.header_label):
            return self.header_label[section]
        return None


class SquareBackgroundDelegate(QStyledItemDelegate):
    """Delegate that paints rectangular (non-rounded) cell backgrounds.

    Ensures NaN highlighting appears as square rectangles rather than
    rounded corners, which can look odd in tables.
    """

    def paint(self, painter, option, index) -> None:
        """Paint cell with square background.

        Args:
            painter (QPainter): Painter to draw with.
            option (QStyleOptionViewItem): Style options.
            index (QModelIndex): Cell index.
        """
        # Paint square background if model provides one
        brush = index.data(Qt.BackgroundRole)
        if isinstance(brush, QColor):
            brush = QBrush(brush)
        if isinstance(brush, QBrush):
            painter.save()
            painter.fillRect(option.rect, brush)  # Square, no rounded corners
            painter.restore()

        # Let Qt draw text, focus, etc.
        super().paint(painter, option, index)


class OrthogonalityTableView(QTableView):
    """Custom table view for orthogonality data with sorting and filtering.

    Features:
    - Automatic proxy model setup for sorting/filtering
    - Row selection mode
    - Smooth pixel scrolling
    - Optional title label and action buttons
    - Search integration

    Attributes:
        _proxyModel (OrthogonalityTableSortProxy): Proxy for sorting/filtering.
        _mainWidget (QWidget): Optional container with title/actions.

    Example:
        >>> model = OrthogonalityTableModel()
        >>> view = OrthogonalityTableView(model=model)
        >>> view.setTitle("Orthogonality Results")
        >>> widget = view.getWidget(parent)
    """

    def __init__(self, parent=None, model=None, default_column_width: int = 100):
        """Initialize the table view.

        Args:
            parent (QWidget, optional): Parent widget.
            model (OrthogonalityTableModel, optional): Data model.
            default_column_width (int): Default column width (unused currently).
        """
        super().__init__(parent)

        self._default_column_width = default_column_width
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Internal widgets & state
        self._proxyModel = None
        self._mainWidget = None
        self._titleLabel = None
        self._actionLayout = None
        self._toolButtonMap = {}

        if model:
            self.setModel(model)

        # Table appearance
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)

        # Horizontal header config
        header = self.horizontalHeader()
        header.setFocusPolicy(Qt.NoFocus)
        header.setSectionsMovable(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setSortIndicatorShown(True)
        header.setDefaultAlignment(Qt.AlignBottom)
        header.setFixedHeight(30)
        header.setHighlightSections(False)

        # Vertical header config
        v_header = self.verticalHeader()
        v_header.setDefaultSectionSize(22)
        v_header.setMinimumSectionSize(18)
        v_header.hide()

        # Smooth scrolling
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    def setModel(self, model: OrthogonalityTableModel) -> None:
        """Set model with automatic proxy model setup.

        Args:
            model (OrthogonalityTableModel): Source model.

        Side Effects:
            - Creates OrthogonalityTableSortProxy
            - Enables sorting and filtering
        """
        self._proxyModel = OrthogonalityTableSortProxy()
        self._proxyModel.setSortRole(Qt.UserRole)
        self._proxyModel.setDynamicSortFilter(True)
        self._proxyModel.setSourceModel(model)
        self._proxyModel.invalidate()
        self._proxyModel.setFilterKeyColumn(-1)

        super().setModel(self._proxyModel)

    def getSelectedIndexes(self) -> list:
        """Get selected indexes mapped to source model.

        Returns:
            list: List of QModelIndex from source model.
        """
        return [self._proxyModel.mapToSource(index) for index in self.selectedIndexes()]

    def selectedRows(self, column: int = 0) -> list:
        """Get selected rows mapped to source model.

        Args:
            column (int): Column to use for row selection.

        Returns:
            list: List of QModelIndex from source model.
        """
        return [
            self._proxyModel.mapToSource(index)
            for index in self.selectionModel().selectedRows(column)
        ]

    def getSourceModel(self) -> OrthogonalityTableModel:
        """Get the underlying source model.

        Returns:
            OrthogonalityTableModel: Source model.
        """
        return self._proxyModel.sourceModel()

    def setSearcher(self, filterLineEdit) -> None:
        """Connect a QLineEdit for table filtering.

        Args:
            filterLineEdit (QLineEdit): Line edit widget for search input.
        """
        filterLineEdit.textChanged.connect(self.filterExpChanged)

    def filterExpChanged(self, text: str) -> None:
        """Update filter based on search text.

        Args:
            text (str): Filter text (supports regex).
        """
        self._proxyModel.setFilterRegularExpression(QRegularExpression(text))
        self._proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def getProxyModel(self) -> OrthogonalityTableSortProxy:
        """Get the proxy model.

        Returns:
            OrthogonalityTableSortProxy: Proxy model.
        """
        return self._proxyModel

    def getIndex(self, proxyIndex: QModelIndex) -> QModelIndex:
        """Map proxy index to source index.

        Args:
            proxyIndex (QModelIndex): Proxy model index.

        Returns:
            QModelIndex: Source model index.
        """
        return self._proxyModel.mapToSource(proxyIndex)

    def setWidget(self) -> None:
        """Create container widget with title and action layout.

        Side Effects:
            - Creates _mainWidget with title label
            - Sets up action button layout
        """
        if self._mainWidget is not None:
            return

        self._mainWidget = QWidget(None)
        self._mainWidget.setObjectName("WhiteBackground")

        headerWidget = QWidget(self._mainWidget)
        headerWidget.setObjectName("WhiteBackground")

        self._titleLabel = QLabel(headerWidget)
        self._titleLabel.setObjectName("Bold_14")
        self._titleLabel.setScaledContents(True)

        self._actionLayout = QHBoxLayout(headerWidget)
        self._actionLayout.setContentsMargins(10, 0, 10, 0)
        self._actionLayout.addWidget(self._titleLabel)
        self._actionLayout.addStretch(100)
        self._actionLayout.setSpacing(10)
        headerWidget.setLayout(self._actionLayout)

        mainLayout = QVBoxLayout(self._mainWidget)
        mainLayout.setContentsMargins(10, 0, 10, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(headerWidget)
        mainLayout.addWidget(self)
        self.setParent(self._mainWidget)
        self._mainWidget.setLayout(mainLayout)
        headerWidget.setFixedHeight(30)

    def getWidget(self, parentWidget: QWidget) -> QWidget:
        """Get container widget with title/actions.

        Args:
            parentWidget (QWidget): Parent to set for container.

        Returns:
            QWidget: Container widget with table view.
        """
        self.setWidget()
        self._mainWidget.setParent(parentWidget)
        return self._mainWidget

    def setTitle(self, title: str) -> None:
        """Set table title.

        Args:
            title (str): Title text.
        """
        self.setWidget()
        self._titleLabel.setText(title)

# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Example showing orthogonality table with sample data."""

    app = QApplication(sys.argv)

    # Create sample data
    data = pd.DataFrame({
        'Set': ['A', 'B', 'C', 'D', 'E'],
        'Pearson': [0.856, 0.723, np.nan, 0.912, 0.678],
        'Spearman': [0.834, 0.701, 0.889, 0.895, np.nan],
        'Kendall': [0.712, 0.623, 0.801, 0.823, 0.567],
        'Orthogonality Score': [0.75, 0.82, 0.68, 0.91, 0.73],
        'Practical 2D peak capacity': [345.7, 423.2, 312.8, 567.4, 401.9]
    })

    # Create model and set data
    model = OrthogonalityTableModel()
    model.set_header_label(list(data.columns))
    model.set_data(data)

    # Create view
    view = OrthogonalityTableView(model=model)
    view.setTitle("Orthogonality Analysis Results")
    view.setItemDelegate(SquareBackgroundDelegate())  # Use square backgrounds

    # Get widget with title
    widget = view.getWidget(None)
    widget.setWindowTitle("Orthogonality Table Example")
    widget.resize(800, 400)

    widget.show()
    sys.exit(app.exec())