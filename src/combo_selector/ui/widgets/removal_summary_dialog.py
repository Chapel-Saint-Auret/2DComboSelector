from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class RemovalSummaryDialog(QDialog):
    def __init__(self, conditions: list[str], compounds: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Removal summary")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui(conditions, compounds)

    def _build_ui(self, conditions: list[str], compounds: list[str]):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._make_section(
            f"Conditions removed ({len(conditions)})", conditions
        ))
        layout.addWidget(self._make_section(
            f"Compounds removed ({len(compounds)})", compounds
        ))

    def _make_section(self, title: str, items: list[str]) -> QFrame:
        frame = QFrame()

        v = QVBoxLayout(frame)
        v.setSpacing(6)
        v.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(title)
        lbl.setStyleSheet("""                
                font-size: 14px;
                font-weight: bold;
                color: #154E9D;""")


        v.addWidget(lbl)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.NoSelection)
        list_widget.setFocusPolicy(Qt.NoFocus)
        list_widget.setFrameShape(QFrame.StyledPanel)

        if items:
            for item_text in items:
                QListWidgetItem(str(item_text), list_widget)

            # Auto-size height to content
            list_widget.setFixedHeight(
                list_widget.sizeHintForRow(0) * 5 + 8
            )
        else:
            QListWidgetItem('Nothing to remove', list_widget)

            # Auto-size height to content
            list_widget.setFixedHeight(
                list_widget.sizeHintForRow(0) * 1 + 8
            )
        v.addWidget(list_widget)
        return frame

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dlg = RemovalSummaryDialog(
        conditions=["pH > 7.5", "Temperature ≤ 25°C", "Gradient > 60% ACN"],
        compounds=["Caffeine", "Uracil", "Thiourea", "Naphthalene"],
    )
    result = dlg.exec()
    print("Accepted" if result == QDialog.Accepted else "Rejected")

    sys.exit(0)