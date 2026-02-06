from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from combo_selector.utils import resource_path

checked_icon_path = resource_path("icons/checkbox_checked.svg").replace("\\", "/")
unchecked_icon_path = resource_path("icons/checkbox_unchecked.svg").replace("\\", "/")


class CheckableTreeList(QWidget):
    def __init__(self, item_list=None):
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

        # Create "Select all" parent item
        self.__init_tree()

        self.add_items(item_list)

        self.tree.itemChanged.connect(self.handle_item_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def clear(self):
        self.tree.clear()
        self.__init_tree()

    def __init_tree(self):
        # List of child items
        self.children = []
        # Create "Select all" parent item
        self.parent_item = QTreeWidgetItem(self.tree, ["Select all"])
        self.parent_item.setFlags(self.parent_item.flags() | Qt.ItemIsUserCheckable)
        self.parent_item.setCheckState(0, Qt.Unchecked)
        self.parent_item.setExpanded(True)  # Set expanded by default

    def add_items(self, item_list):
        if item_list:
            for item in item_list:
                child = QTreeWidgetItem(self.parent_item, [item])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
                self.children.append(child)

        self.parent_item.setExpanded(True)

    def handle_item_changed(self, item, column):
        if item is self.parent_item and item.checkState(0) in (
            Qt.Checked,
            Qt.Unchecked,
        ):
            state = item.checkState(0)
            self.tree.blockSignals(True)  # Prevent recursive triggers
            for child in self.children:
                child.setCheckState(0, state)
            self.tree.blockSignals(False)
        elif item in self.children:
            checked_count = sum(
                child.checkState(0) == Qt.Checked for child in self.children
            )
            unchecked_count = sum(
                child.checkState(0) == Qt.Unchecked for child in self.children
            )
            partially_checked = any(
                child.checkState(0) == Qt.PartiallyChecked for child in self.children
            )
            self.tree.blockSignals(True)
            if checked_count == len(self.children):
                self.parent_item.setCheckState(0, Qt.Checked)
            elif unchecked_count == len(self.children):
                self.parent_item.setCheckState(0, Qt.Unchecked)
            else:
                self.parent_item.setCheckState(0, Qt.PartiallyChecked)
            self.tree.blockSignals(False)

    def get_checked_items(self):
        return [
            child.text(0)
            for child in self.children
            if child.checkState(0) == Qt.Checked
        ]

    def get_items(self):
        return [child.text(0) for child in self.children]

    def unchecked_all(self):
        self.tree.blockSignals(True)
        self.parent_item.setCheckState(0, Qt.Unchecked)

        for child in self.children:
            child.setCheckState(0, Qt.Unchecked)

        self.tree.blockSignals(False)
