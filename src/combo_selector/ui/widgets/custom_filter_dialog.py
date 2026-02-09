"""Custom filter dialog for chromatographic combination filtering.

This module provides a dialog for defining and selecting chromatographic
mode combinations (e.g., HILIC vs RPLC) to filter results tables.

Features:
- Tree view to define combination types (chromatographic mode, pH, etc.)
- Dynamic quantity adjustment for each condition
- Checkable list to select which combinations to filter by
- Regex pattern generation for table filtering
- Custom cell editors (spin boxes, combo boxes)
"""

import re
import sys

from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QTreeView,
    QSpinBox,
    QStyledItemDelegate,
    QLabel,
    QComboBox,
    QHeaderView,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QAbstractItemView,
    QListView,
    QDialogButtonBox,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel


class CustomComboBox(QComboBox):
    """Combo box that tracks its items list for index lookup.

    Attributes:
        mode_list (list): List of all items in the combo box.
    """

    def __init__(self, parent, items: list):
        """Initialize the custom combo box.

        Args:
            parent (QWidget): Parent widget.
            items (list): List of items to populate the combo box.
        """
        super().__init__(parent)
        self.mode_list = items
        self.addItems(self.mode_list)

    def get_item_index(self, item: str) -> int:
        """Get the index of an item in the list.

        Args:
            item (str): Item text to find.

        Returns:
            int: Index of the item, or 0 if not found.
        """
        try:
            return self.mode_list.index(item)
        except (ValueError, AttributeError):
            return 0


class CustomFilterDialog(QDialog):
    """Dialog for defining and selecting chromatographic combination filters.

    Allows users to define condition types (e.g., chromatographic mode)
    with specific combinations (e.g., HILIC vs RPLC), then select which
    combinations to use for filtering the results table.

    Signals:
        filter_regexp_changed(str): Emitted when filter selection changes.
            Contains regex pattern for filtering.

    Example:
        >>> dialog = CustomFilterDialog(parent)
        >>> dialog.filter_regexp_changed.connect(table.set_filter)
        >>> dialog.exec()
    """

    filter_regexp_changed = Signal(object)

    def __init__(self, parent=None):
        """Initialize the filter dialog.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Custom Filter")

        main_layout = QVBoxLayout()
        self._apply_styles()

        # --- Title ---
        title_top = QLabel("<b>Define chromatographic mode combinations</b>")
        main_layout.addWidget(title_top)

        # --- Tree View for defining combinations ---
        self.data = {
            'Chromatographic mode': {
                '0': ['HILIC', 'HILIC'],
                '1': ['RPLC', 'RPLC'],
                '2': ['HILIC', 'RPLC'],
            }
        }

        self.filter_condition_tree_view = QTreeView()
        self.filter_condition_tree_view.setFixedWidth(310)
        self.filter_condition_tree_view.setMinimumHeight(220)

        self.delegate = CustomDelegate()
        self.filter_condition_tree_view.setItemDelegate(self.delegate)

        self.model = QStandardItemModel(0, 3)
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(['Condition', 'Qty', 'D1', '²D'])
        self.filter_condition_tree_view.setModel(self.model)

        self.build_tree_view_from_data()

        self.filter_condition_tree_view.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.filter_condition_tree_view.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.filter_condition_tree_view.header().setSectionResizeMode(3, QHeaderView.Stretch)
        self.filter_condition_tree_view.header().setStretchLastSection(False)

        main_layout.addWidget(self.filter_condition_tree_view)

        # --- Checkable list for selecting combinations ---
        filter_title = QLabel("<b>Select Combinations to filter</b>")
        main_layout.addWidget(filter_title)

        self.filtered_listview = FilteredListView()
        self.update_combination_group()
        main_layout.addWidget(self.filtered_listview)

        # --- OK / Cancel buttons ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            orientation=Qt.Horizontal,
            parent=self
        )
        button_box.accepted.connect(self.selected_filter_changed)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

        # --- Signal connections ---
        self.delegate.condition_changed.connect(self.update_condition_child_item)
        self.delegate.combination_changed.connect(self.update_combination_group)

    def _apply_styles(self) -> None:
        """Apply custom stylesheet to the dialog."""
        self.setStyleSheet("""
            QWidget {
                font-family: Segoe UI, Arial;
                font-size: 13px;
            }
            QLabel {
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #d1d9fc;
                color: #1859b4;
                font-size: 12px;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #d0d4da;
            }
            QTreeView {
                background-color: #F6F8FD;
                selection-background-color: #c9daf8;
                font-size: 11px;
            }
            QTreeView::item:selected {
                background-color: #d8e5fc;
                color: #000000;
            }
            QTreeView::item {
                background: transparent;
                border: none;
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
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #c5d0e6;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 14px;
            }
        """)

    def selected_filter_changed(self) -> None:
        """Build and emit regex pattern from selected filters.

        Generates a regex pattern that matches any of the selected
        combinations in either order (e.g., "HILIC vs RPLC" or "RPLC vs HILIC").

        Side Effects:
            - Emits filter_regexp_changed signal with regex pattern
            - Closes the dialog (accept)
        """
        selected_filter = self.filtered_listview.get_selected_filters()

        parts = []
        for s in selected_filter:
            # Extract word tokens (ignore "vs")
            toks = re.findall(r'\b[A-Za-z0-9-]+\b', s)
            toks = [t for t in toks if t.lower() != 'vs']

            if len(toks) >= 2:
                a, b = re.escape(toks[0]), re.escape(toks[-1])
                # Match both orders: A vs B or B vs A
                parts.append(rf'\b{a}\b.*?vs.*?\b{b}\b')
                parts.append(rf'\b{b}\b.*?vs.*?\b{a}\b')

        filter_regexp = re.compile('|'.join(parts), flags=re.IGNORECASE)
        self.filter_regexp_changed.emit(filter_regexp.pattern)
        self.accept()

    def insert_parent_item(self, text: str) -> None:
        """Add a parent item (condition type) to the tree.

        Args:
            text (str): Text for the parent item (e.g., "Chromatographic mode").
        """
        root_item = QStandardItem(text)
        self.model.appendRow(root_item)

    def insert_child_items(self, parent_row: int, child_items: list = None) -> None:
        """Add child items (D1 and D2 values) to a parent.

        Args:
            parent_row (int): Row index of the parent item.
            child_items (list, optional): List of [D1, D2] values.
                If None, adds placeholder "..." values.
        """
        parent_item = self.model.item(parent_row)
        row_count = parent_item.rowCount()

        if child_items:
            column = 2
            for child_text in child_items:
                item = QStandardItem(child_text)
                parent_item.setChild(row_count, column, item)
                column += 1
        else:
            parent_item.setChild(row_count, 2, QStandardItem('...'))
            parent_item.setChild(row_count, 3, QStandardItem('...'))

        self.filter_condition_tree_view.setExpanded(
            self.model.indexFromItem(parent_item), True
        )

    def set_data(self, row: int, column: int, text: str) -> None:
        """Set data for a specific cell in the tree.

        Args:
            row (int): Row index.
            column (int): Column index.
            text (str): Text to set.
        """
        index = self.model.index(row, column, QModelIndex())
        self.model.setData(index, text, Qt.EditRole)

    def build_tree_view_from_data(self) -> None:
        """Populate tree view from self.data dictionary.

        Side Effects:
            - Adds parent and child items to the model
            - Expands parent items
            - Resizes columns to content
        """
        for row, key in enumerate(self.data):
            condition = self.data[key]
            self.insert_parent_item(text=key)
            self.set_data(row, 1, len(condition))

            for cond_key in condition:
                index_row = condition[cond_key]
                self.insert_child_items(parent_row=row, child_items=index_row)

        self.filter_condition_tree_view.resizeColumnToContents(0)
        self.filter_condition_tree_view.resizeColumnToContents(1)

    def update_condition_child_item(self, row: int, previous_value: int, value: int) -> None:
        """Update the number of child items when quantity changes.

        Args:
            row (int): Parent row index.
            previous_value (int): Previous quantity.
            value (int): New quantity.

        Side Effects:
            - Adds or removes child items from parent
        """
        parent_item = self.model.item(row)

        if value > previous_value:
            for _ in range(value - previous_value):
                self.insert_child_items(parent_row=row)
        elif previous_value > value:
            for _ in range(previous_value - value):
                last_child_index = parent_item.rowCount() - 1
                parent_item.removeRow(last_child_index)

    def update_combination_group(self) -> None:
        """Update the filter list based on current tree combinations.

        Side Effects:
            - Extracts D1 vs D2 combinations from tree
            - Populates filtered_listview with combinations
        """
        combination_group = []
        combination_count = self.model.item(0).rowCount()

        for row in range(combination_count):
            text_1 = self.model.item(0).child(row, 2).text()
            text_2 = self.model.item(0).child(row, 3).text()
            combination_group.append(f"{text_1} vs {text_2}")

        self.filtered_listview.populate(combination_group)


class CustomDelegate(QStyledItemDelegate):
    """Custom item delegate for tree view cells.

    Provides custom editors:
    - Spin box for quantity column
    - Combo box for chromatographic modes (RPLC, HILIC, etc.)
    - Line edit for other fields

    Signals:
        condition_changed(int, int, int): Emitted when quantity changes.
            Args: (row, previous_value, new_value)
        combination_changed(): Emitted when D1/D2 values change.
    """

    condition_changed = Signal(object, object, object)
    combination_changed = Signal()

    def __init__(self):
        """Initialize the delegate."""
        super().__init__()
        self.previous_qty_value = 0

    def createEditor(self, parent, option, index):
        """Create appropriate editor widget for the cell.

        Args:
            parent (QWidget): Parent widget.
            option (QStyleOptionViewItem): Style options.
            index (QModelIndex): Cell index.

        Returns:
            QWidget: Editor widget (QSpinBox, QComboBox, or QLineEdit).
        """
        value = index.model().data(index, Qt.EditRole)
        isParent = index.parent().row() == -1
        isCondition = index.column() == 0
        isD1D2 = index.column() in [2, 3] and not isParent

        # Quantity column for parent items
        if index.column() == 1 and isParent:
            if index.model().data(index, Qt.EditRole) is not None:
                self.previous_qty_value = index.model().data(index, Qt.EditRole)
            return QSpinBox(parent)

        # D1/D2 columns or condition name
        elif (isCondition and isParent) or isD1D2:
            if index.parent().row() == 0:
                # Chromatographic modes
                combo = CustomComboBox(
                    parent, ['RPLC', 'HILIC', 'IEX', 'SEC', 'HIC', 'SFC']
                )
                combo.setCurrentIndex(combo.get_item_index(value))
                return combo
            elif index.parent().row() == 1:
                # Organic modifiers
                combo = CustomComboBox(parent, ['ACN', 'MeOH', 'EtOH', 'IpOH'])
                combo.setCurrentIndex(combo.get_item_index(value))
                return combo
            else:
                return QLineEdit(parent)

        return None

    def setEditorData(self, editor, index):
        """Populate editor with current cell value.

        Args:
            editor (QWidget): Editor widget.
            index (QModelIndex): Cell index.
        """
        value = index.model().data(index, Qt.EditRole)
        isParent = index.parent().row() == -1
        isCondition = index.column() == 0
        isD1D2 = index.column() in [2, 3] and not isParent

        if value:
            if index.column() == 1 and isParent:
                editor.setValue(value)
            elif (isCondition and isParent) or isD1D2:
                if index.parent().row() in [0, 1]:
                    editor.setEditText(value)
                else:
                    editor.setText(value)

    def setModelData(self, editor, model, index):
        """Save editor data back to model.

        Args:
            editor (QWidget): Editor widget.
            model (QAbstractItemModel): Data model.
            index (QModelIndex): Cell index.

        Side Effects:
            - Updates model with new value
            - Emits condition_changed or combination_changed signals
        """
        isParent = index.parent().row() == -1
        isCondition = index.column() == 0
        isD1D2 = index.column() in [2, 3] and not isParent

        if index.column() == 1 and isParent:
            model.setData(index, editor.value())
            self.condition_changed.emit(
                index.row(), int(self.previous_qty_value), editor.value()
            )
        elif (isCondition and isParent) or isD1D2:
            if index.parent().row() in [0, 1]:
                model.setData(index, editor.currentText())
                self.combination_changed.emit()
            else:
                model.setData(index, editor.text())

    def updateEditorGeometry(self, editor, option, index):
        """Set editor geometry to match cell.

        Args:
            editor (QWidget): Editor widget.
            option (QStyleOptionViewItem): Style options.
            index (QModelIndex): Cell index.
        """
        editor.setGeometry(option.rect)


class MultiListView(QListView):
    """List view with multi-select and space-to-toggle-checkbox support.

    Allows toggling check state of multiple selected items with spacebar.
    """

    def __init__(self, parent=None):
        """Initialize the multi-select list view."""
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def keyPressEvent(self, event):
        """Toggle checkbox state on spacebar press.

        Args:
            event (QKeyEvent): Key event.
        """
        if event.key() == Qt.Key_Space:
            selected = self.selectedIndexes()
            for idx in selected[:-1]:
                idx = self.model().mapToSource(idx)
                item = self.model().sourceModel().itemFromIndex(idx)
                newState = (
                    Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                )
                item.setCheckState(newState)
        return super().keyPressEvent(event)


class FilteredListView(QWidget):
    """Checkable list with text filter and regex support.

    Displays a list of items with checkboxes and provides a filter
    input to narrow down the list. Supports regex mode.

    Signals:
        filterChanged(list): Emitted when checked items change.

    Attributes:
        filters (list): List of currently checked item texts.
    """

    filterChanged = Signal(list)

    def __init__(self, parent=None):
        """Initialize the filtered list view."""
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Filter controls
        filterLayout = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter...")
        self.regexCheckbox = QCheckBox(".*")
        self.listView = MultiListView()
        filterLayout.addWidget(self.filter)
        filterLayout.addWidget(self.regexCheckbox)
        layout.addLayout(filterLayout)
        layout.addWidget(self.listView)

        self.filters = []
        self.__data = []

        # Inner proxy model for filtering
        class InnerProxyModel(QSortFilterProxyModel):
            """Proxy model that filters rows based on text input."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.__filterStr = ""
                self.__regexMode = False

            def filterAcceptsRow(self, sourceRow, sourceParent):
                """Check if row matches filter.

                Args:
                    sourceRow (int): Source row index.
                    sourceParent (QModelIndex): Parent index.

                Returns:
                    bool: True if row should be visible.
                """
                if not self.__filterStr:
                    return True

                index = self.sourceModel().index(sourceRow, 0, sourceParent)
                modelStr = self.sourceModel().data(index, Qt.DisplayRole)

                if not self.__regexMode:
                    # Simple text contains (case-insensitive)
                    regex = QtCore.QRegularExpression(
                        f".*{QtCore.QRegularExpression.escape(self.__filterStr)}.*",
                        QtCore.QRegularExpression.CaseInsensitiveOption,
                    )
                    return regex.match(modelStr).hasMatch()
                else:
                    # Regex mode
                    regex = QtCore.QRegularExpression(
                        self.__filterStr,
                        QtCore.QRegularExpression.CaseInsensitiveOption,
                    )
                    return regex.match(modelStr).hasMatch()

            def setRegexMode(self, mode: bool) -> None:
                """Enable/disable regex mode."""
                self.__regexMode = bool(mode)

            def updateFilterStr(self, string: str) -> None:
                """Update filter string and refresh."""
                self.__filterStr = string
                self.invalidateFilter()

        self.model = QStandardItemModel(self)
        self.proxy = InnerProxyModel()
        self.proxy.setSourceModel(self.model)
        self.listView.setModel(self.proxy)

        # Signal connections
        self.filter.textChanged.connect(self.proxy.updateFilterStr)
        self.regexCheckbox.toggled.connect(self.proxy.setRegexMode)
        self.model.dataChanged.connect(self.update_selected_filter_list)

    def populate(self, data: list) -> None:
        """Populate list with checkable items.

        Args:
            data (list): List of item texts.

        Side Effects:
            - Clears existing items
            - Adds new checkable items
            - Updates filter list
        """
        self.model.clear()
        self.__data = data
        for d in self.__data:
            item = QStandardItem(d)
            item.setCheckable(True)
            self.model.appendRow(item)

        self.update_selected_filter_list()

    def get_selected_filters(self) -> list:
        """Get list of checked item texts.

        Returns:
            list: List of checked item texts.
        """
        return self.filters

    def update_selected_filter_list(self) -> None:
        """Update internal filter list based on check states.

        Side Effects:
            - Updates self.filters
            - Emits filterChanged signal
        """
        self.filters = []

        for row in range(self.model.rowCount()):
            idx = self.model.index(row, 0)
            text = self.model.data(idx, Qt.DisplayRole)
            checked = self.model.data(idx, Qt.CheckStateRole)

            if checked:
                self.filters.append(text)

        self.filterChanged.emit(self.filters)

    def clearFilters(self) -> None:
        """Uncheck all items."""
        for r in range(self.model.rowCount()):
            self.model.item(r).setCheckState(Qt.Unchecked)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing the filter dialog."""

    app = QApplication(sys.argv)

    dialog = CustomFilterDialog()


    def on_filter_changed(pattern):
        print(f"Filter pattern: {pattern}")


    dialog.filter_regexp_changed.connect(on_filter_changed)
    dialog.show()

    sys.exit(app.exec())