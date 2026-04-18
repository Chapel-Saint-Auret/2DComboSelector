import sys

from PySide6.QtWidgets import (QComboBox, QLineEdit, QVBoxLayout,
                                QWidget, QCompleter,QApplication)
from PySide6.QtCore import Qt,QSortFilterProxyModel

class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)

        self.filter_model = QSortFilterProxyModel(self)
        self.filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter_model.setSourceModel(self.model())

        completer = QCompleter(self.filter_model, self)
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(completer)

        self.lineEdit().textEdited.connect(self.filter_model.setFilterFixedString)

if __name__ == "__main__":
    """Simple usage example showing horizontal and vertical separators."""

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("LineWidget Example")
    window.resize(300, 200)

    layout = QVBoxLayout(window)

    combo = SearchableComboBox()
    combo.addItems(["Set 1", "Set 2", "Set 32", "Set 421", "Set 51", "Set 6"])

    layout.addWidget(combo)

    window.show()
    sys.exit(app.exec())

