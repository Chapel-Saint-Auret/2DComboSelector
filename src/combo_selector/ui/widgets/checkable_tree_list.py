"""Checkable tree widget with "Select All" parent item.

This module provides a tree widget with checkboxes where:
- A parent "Select All" item controls all children
- Individual children can be checked/unchecked
- Parent state automatically reflects children (checked/unchecked/partial)
- Custom checkbox icons can be used
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from combo_selector.utils import resource_path

# Custom checkbox icon paths
checked_icon_path = resource_path("icons/checkbox_checked.svg").replace("\\", "/")
unchecked_icon_path = resource_path("icons/checkbox_unchecked.svg").replace("\\", "/")


class CheckableTreeList(QWidget):
    """Tree widget with checkable items and "Select All" functionality.

    Displays a hierarchical list with:
    - Parent "Select All" item that controls all children
    - Child items with individual checkboxes
    - Auto-syncing between parent and children states
    - Partial check state when some (but not all) children are checked

    The parent checkbox has three states:
    - Checked: All children are checked
    - Unchecked: All children are unchecked
    - Partially checked: Some children are checked

    Attributes:
        tree (QTreeWidget): The tree widget containing all items.
        parent_item (QTreeWidgetItem): The "Select All" parent item.
        children (list): List of child items.

    Example:
        >>> tree = CheckableTreeList()
        >>> tree.add_items(["Option 1", "Option 2", "Option 3"])
        >>> checked = tree.get_checked_items()
        >>> print(checked)  # ["Option 1", "Option 2"]
    """

    def __init__(self, item_list: list = None):
        """Initialize the checkable tree list.

        Args:
            item_list (list, optional): Initial list of item names to add.
        """
        super().__init__()

        self.tree = QTreeWidget()
        self.tree.setStyleSheet(f"""
            QTreeWidget::indicator:unchecked {{
                image: url("{unchecked_icon_path}");
            }}
            QTreeWidget::indicator:checked {{
                image: url("{checked_icon_path}");
            }}
        """)
        self.tree.setHeaderHidden(True)

        # Initialize tree structure
        self.__init_tree()
        self.add_items(item_list)

        # Connect signals
        self.tree.itemChanged.connect(self.handle_item_changed)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def clear(self) -> None:
        """Clear all items and reinitialize the tree.

        Side Effects:
            - Removes all items from tree
            - Recreates "Select All" parent item
            - Clears children list
        """
        self.tree.clear()
        self.__init_tree()

    def __init_tree(self) -> None:
        """Initialize the tree with a "Select All" parent item.

        Side Effects:
            - Creates empty children list
            - Creates "Select All" parent item
            - Sets parent as unchecked and expanded
        """
        self.children = []
        self.parent_item = QTreeWidgetItem(self.tree, ["Select all"])
        self.parent_item.setFlags(self.parent_item.flags() | Qt.ItemIsUserCheckable)
        self.parent_item.setCheckState(0, Qt.Unchecked)
        self.parent_item.setExpanded(True)

    def add_items(self, item_list: list) -> None:
        """Add child items to the tree.

        Args:
            item_list (list): List of item names to add as children.

        Side Effects:
            - Creates checkable child items under parent
            - Adds children to internal children list
            - Expands parent item
        """
        if item_list:
            for item in item_list:
                child = QTreeWidgetItem(self.parent_item, [item])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
                self.children.append(child)

        self.parent_item.setExpanded(True)

    def handle_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle checkbox state changes.

        Synchronizes parent and children checkbox states:
        - If parent changes: update all children to match
        - If child changes: update parent to checked/unchecked/partial

        Args:
            item (QTreeWidgetItem): The item that changed.
            column (int): The column that changed (always 0 for checkboxes).

        Side Effects:
            - May update parent checkbox state
            - May update all children checkbox states
        """
        if item is self.parent_item and item.checkState(0) in (Qt.Checked, Qt.Unchecked):
            # Parent changed: sync all children
            state = item.checkState(0)
            self.tree.blockSignals(True)
            for child in self.children:
                child.setCheckState(0, state)
            self.tree.blockSignals(False)

        elif item in self.children:
            # Child changed: update parent state
            checked_count = sum(
                child.checkState(0) == Qt.Checked for child in self.children
            )
            unchecked_count = sum(
                child.checkState(0) == Qt.Unchecked for child in self.children
            )

            self.tree.blockSignals(True)
            if checked_count == len(self.children):
                self.parent_item.setCheckState(0, Qt.Checked)
            elif unchecked_count == len(self.children):
                self.parent_item.setCheckState(0, Qt.Unchecked)
            else:
                self.parent_item.setCheckState(0, Qt.PartiallyChecked)
            self.tree.blockSignals(False)

    def get_checked_items(self) -> list:
        """Get list of checked item names.

        Returns:
            list: List of text values for checked children.
        """
        return [
            child.text(0)
            for child in self.children
            if child.checkState(0) == Qt.Checked
        ]

    def get_items(self) -> list:
        """Get list of all item names (checked or not).

        Returns:
            list: List of text values for all children.
        """
        return [child.text(0) for child in self.children]

    def unchecked_all(self) -> None:
        """Uncheck all items (parent and children).

        Side Effects:
            - Sets parent to unchecked
            - Sets all children to unchecked
        """
        self.tree.blockSignals(True)
        self.parent_item.setCheckState(0, Qt.Unchecked)
        for child in self.children:
            child.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing the checkable tree list."""

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("CheckableTreeList Example")
    layout = QVBoxLayout(window)

    # Create checkable tree with sample items
    tree = CheckableTreeList()
    tree.add_items([
        "Pearson Correlation",
        "Spearman Correlation",
        "Kendall Correlation",
        "Convex Hull",
        "Bin Box Counting"
    ])
    layout.addWidget(tree)

    window.show()
    sys.exit(app.exec())