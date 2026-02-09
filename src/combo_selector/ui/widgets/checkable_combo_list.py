"""Checkable combo box widget with multi-select support.

This module provides a custom QComboBox that displays checkboxes next to
each item, allowing users to select multiple items. The selected items are
displayed in the combo box's line edit, separated by semicolons.

The widget supports two modes:
- Exclusive: Only one item can be checked at a time (radio button behavior)
- Multi-select: Multiple items can be checked simultaneously (default)
"""

import sys

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QVBoxLayout


class CheckableComboList(QComboBox):
    """Custom combo box with checkable items for multi-selection.

    Displays a dropdown list where each item has a checkbox. Selected
    items are shown in the combo box's line edit, separated by semicolons.
    Supports both exclusive (single-select) and multi-select modes.

    Attributes:
        item_list (list): List of all item text values.
        exclusive (bool): If True, only one item can be checked at a time.
        display_text (str): Text shown in the line edit (checked items).
        model (QStandardItemModel): Model containing checkable items.
        checked_items (list): List of currently checked item texts.

    Signals:
        item_checked(list): Emitted when checked items change (currently unused).

    Example:
        >>> combo = CheckableComboList(placeholder="Select metrics...")
        >>> combo.add_items(["Metric 1", "Metric 2", "Metric 3"])
        >>> combo.set_checked_items(["Metric 1"])
        >>> checked = combo.get_checked_item()
        >>> print(checked)  # ["Metric 1"]
    """

    item_checked = Signal(list)

    def __init__(self, exclusive: bool = False, placeholder: str = ""):
        """Initialize the checkable combo box.

        Args:
            exclusive (bool): If True, allows only single selection.
                             If False, allows multiple selections. Default: False.
            placeholder (str): Placeholder text shown when no items are selected.
        """
        super().__init__()

        # --- State initialization ------------------------------------------
        self.item_list = []
        self.exclusive = exclusive
        self.display_text = ""
        self.checked_items = []

        # --- Model setup ---------------------------------------------------
        self.model = QStandardItemModel()
        self.model.itemChanged.connect(self.update)

        # --- Line edit setup -----------------------------------------------
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)  # Display only, not editable
        self.setPlaceholderText(placeholder)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setCurrentIndex(-1)

        self.update_text()

    def add_item(self, text: str) -> None:
        """Add a checkable item to the combo box.

        Args:
            text (str): Text to display for the item.

        Side Effects:
            - Creates new checkable item in model
            - Updates combo box model
        """
        row = self.model.rowCount()
        new_item = QStandardItem(text)
        new_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        new_item.setData(Qt.Unchecked, Qt.CheckStateRole)

        self.blockSignals(True)
        self.model.setItem(row, 0, new_item)
        self.blockSignals(False)
        self.setModel(self.model)

    def add_items(self, item_text_list: list[str]) -> None:
        """Add multiple checkable items to the combo box.

        Args:
            item_text_list (list[str]): List of item texts to add.

        Side Effects:
            - Stores item list
            - Adds each item to the model
        """
        self.item_list = item_text_list
        for text in item_text_list:
            self.add_item(text)

    def get_checked_item(self) -> list[str]:
        """Get list of currently checked item texts.

        Returns:
            list[str]: List of checked item texts.
        """
        return self.checked_items

    def get_items(self) -> list[str]:
        """Get list of all item texts (checked or not).

        Returns:
            list[str]: List of all item texts.
        """
        return self.item_list

    def set_checked_items(self, item_text_list: list[str]) -> None:
        """Programmatically check specific items.

        Args:
            item_text_list (list[str]): List of item texts to check.

        Side Effects:
            - Sets check state for matching items
            - Updates display text
        """
        for item_text in item_text_list:
            index = self.findText(item_text)
            if index != -1:
                self.model.item(index).setCheckState(Qt.Checked)

        self.update()

    def update(self, item: QStandardItem = None) -> None:
        """Update the display text and checked items list.

        Called when an item's check state changes. Handles both
        exclusive (single-select) and multi-select modes.

        Args:
            item (QStandardItem, optional): The item that was changed.

        Side Effects:
            - Updates display_text and checked_items
            - In exclusive mode, unchecks all other items
            - Schedules text update via QTimer
        """
        self.display_text = ""
        self.checked_items = []

        if self.exclusive and item:
            # Exclusive mode: uncheck all except the clicked item
            index_clicked = item.index().row()
            self.display_text = self.model.item(index_clicked, 0).text()

            for i in range(self.model.rowCount()):
                if i == index_clicked:
                    self.checked_items.append(self.model.item(i, 0).text())
                else:
                    self.model.blockSignals(True)
                    self.model.item(i).setCheckState(Qt.Unchecked)
                    self.model.blockSignals(False)
        else:
            # Multi-select mode: collect all checked items
            for i in range(self.model.rowCount()):
                if self.model.item(i, 0).checkState() == Qt.Checked:
                    self.display_text += self.model.item(i, 0).text() + "; "
                    self.checked_items.append(self.model.item(i, 0).text())

        # Schedule text update (deferred to avoid recursion issues)
        QTimer.singleShot(0, self.update_text)

    def update_text(self) -> None:
        """Update the line edit with the current display text.

        Side Effects:
            - Sets line edit text to display_text (checked items)
        """
        self.lineEdit().setText(self.display_text)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing multi-select and exclusive modes."""

    app = QApplication(sys.argv)

    window = QDialog()
    window.setWindowTitle("CheckableComboList Example")
    layout = QVBoxLayout(window)

    # Multi-select example
    combo = CheckableComboList(placeholder="Select items...")
    combo.add_items(["Option 1", "Option 2", "Option 3"])
    combo.set_checked_items(["Option 1", "Option 2"])
    layout.addWidget(combo)

    window.show()
    sys.exit(app.exec())