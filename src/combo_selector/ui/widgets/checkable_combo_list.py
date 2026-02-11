"""Custom combo box widget with checkable items for multi-selection.

Provides a dropdown list where each item has a checkbox, allowing
users to select multiple items from a list. Selected items are
displayed in the combo box's line edit, separated by semicolons.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox


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
        """Add a single checkable item to the combo box.

        Args:
            text (str): Text to display for the item.

        Side Effects:
            - Creates new checkable item in model
            - Updates combo box model

        Note:
            For adding multiple items, use add_items() for better performance.
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
        """Add multiple checkable items to the combo box efficiently.

        Optimized for bulk operations - sets the model only once after
        all items are added, rather than after each individual item.

        Args:
            item_text_list (list[str]): List of item texts to add.

        Side Effects:
            - Stores item list
            - Adds all items to the model in batch
            - Sets model only once for performance
        """
        if not item_text_list:
            return

        self.item_list = item_text_list

        # Block signals and model updates during bulk operation
        self.blockSignals(True)
        self.model.blockSignals(True)

        try:
            # Add all items to model without updating view each time
            for text in item_text_list:
                row = self.model.rowCount()
                new_item = QStandardItem(text)
                new_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                new_item.setData(Qt.Unchecked, Qt.CheckStateRole)
                self.model.setItem(row, 0, new_item)

            # Set the model only ONCE after all items are added
            self.setModel(self.model)

        finally:
            # Re-enable signals
            self.model.blockSignals(False)
            self.blockSignals(False)

    def clear(self) -> None:
        """Clear all items from the combo box efficiently.

        Side Effects:
            - Clears the model
            - Resets item list
            - Clears checked items
            - Updates display text
        """
        # Block signals during clear operation
        self.blockSignals(True)
        self.model.blockSignals(True)

        try:
            # Clear model
            self.model.clear()

            # Reset state
            self.item_list = []
            self.checked_items = []
            self.display_text = ""

            # Update line edit
            self.lineEdit().clear()

        finally:
            # Re-enable signals
            self.model.blockSignals(False)
            self.blockSignals(False)

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

    def set_checked_items(self, checked_items: list[str]) -> None:
        """Set which items should be checked.

        Args:
            checked_items (list[str]): List of item texts to check.

        Side Effects:
            - Updates check state for matching items
            - Updates display text
        """
        self.blockSignals(True)
        self.model.blockSignals(True)

        try:
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                if item.text() in checked_items:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

            self.update_text()

        finally:
            self.model.blockSignals(False)
            self.blockSignals(False)

    def update(self, item: QStandardItem) -> None:
        """Handle item check state changes.

        Args:
            item (QStandardItem): Item whose check state changed.

        Side Effects:
            - In exclusive mode, unchecks other items
            - Updates checked items list
            - Updates display text
            - Emits item_checked signal
        """
        if self.exclusive:
            # Uncheck all other items in exclusive mode
            if item.checkState() == Qt.Checked:
                self.blockSignals(True)
                for i in range(self.model.rowCount()):
                    other_item = self.model.item(i, 0)
                    if other_item != item:
                        other_item.setCheckState(Qt.Unchecked)
                self.blockSignals(False)

        self.update_text()
        self.item_checked.emit(self.checked_items)

    def update_text(self) -> None:
        """Update the display text with currently checked items.

        Side Effects:
            - Collects checked items
            - Updates line edit text (semicolon-separated)
        """
        checked = []
        for i in range(self.model.rowCount()):
            item = self.model.item(i, 0)
            if item and item.checkState() == Qt.Checked:
                checked.append(item.text())

        self.checked_items = checked
        self.display_text = "; ".join(checked) if checked else ""
        self.lineEdit().setText(self.display_text)

    def showPopup(self) -> None:
        """Show the dropdown popup.

        Overridden to ensure first item is not auto-selected.
        """
        super().showPopup()
        self.setCurrentIndex(-1)