import sys

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QHBoxLayout


class CheckableComboList(QComboBox):

    item_checked = Signal(list)

    def __init__(self, excluive=False, placeholder=""):
        super().__init__()
        self.item_list = []
        self.exclusive = excluive
        self.display_text = ""
        self.model = QStandardItemModel()
        self.checked_items = []
        self.setEditable(True)
        self.update_text()
        self.model.itemChanged.connect(self.update)
        self.lineEdit().setReadOnly(True)

        self.setEditable(True)
        self.setPlaceholderText(placeholder)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setCurrentIndex(-1)
        # self.lineEdit().textChanged.connect(self.emit_item_checked)

    # def emit_item_checked(self):
    #     # signal emited when linEdit edition is finished for the qcombobox
    #     self.item_checked.emit(self.get_checked_item())

    def _resize_item_rect(self):
        w = self.fontMetrics().boundingRect(max(self.item_list, key=len)).width()
        self.view().setFixedWidth(w + 10)

    def update_text(self):
        self.lineEdit().setText(self.display_text)

    def update(self, item=None):
        self.display_text = ""
        self.checked_items = []

        if self.exclusive and item:
            index_clicked = item.index().row()
            self.display_text += self.model.item(index_clicked, 0).text()
            for i in range(self.model.rowCount()):
                if i == index_clicked:
                    self.checked_items.append(self.model.item(i, 0).text())
                    continue
                else:
                    self.model.blockSignals(True)
                    self.model.item(i).setCheckState(Qt.Unchecked)
                    self.model.blockSignals(False)

        else:
            for i in range(self.model.rowCount()):
                if self.model.item(i, 0).checkState() == Qt.Checked:
                    self.display_text += self.model.item(i, 0).text() + "; "
                    self.checked_items.append(self.model.item(i, 0).text())
        toto = self.get_checked_item()
        toto = 0
        QTimer.singleShot(0, self.update_text)

    def add_item(self, text):
        row = self.model.rowCount()
        new_item = QStandardItem(text)
        new_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        new_item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.blockSignals(True)
        self.model.setItem(row, 0, new_item)
        self.blockSignals(False)
        self.setModel(self.model)

    def add_items(self, item_text_list):
        self.item_list = item_text_list
        for text in item_text_list:
            self.add_item(text)

        # self._resize_item_rect()

    def get_checked_item(self):
        return self.checked_items

    def get_items(self):
        return self.item_list

    def set_checked_items(self, item_text_list):
        nb_of_rows = self.model.rowCount()
        for item_text in item_text_list:
            index = self.findText(item_text)
            if index != -1:
                self.model.item(index).setCheckState(Qt.Checked)

        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = QDialog()

    main_layout = QHBoxLayout()
    w.setLayout(main_layout)

    checkablecomnbo = CheckableComboList(True)
    checkablecomnbo.add_items(["one", "two", "three"])
    checkablecomnbo.set_checked_items(["one", "two", "three"])

    main_layout.addWidget(checkablecomnbo)

    w.exec()
