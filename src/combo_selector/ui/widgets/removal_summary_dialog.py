"""Dialog widget that summarizes removed compounds and conditions."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt


class RemovalSummaryDialog(QDialog):
    """Modal dialog displaying removed compounds and conditions in two lists."""

    def __init__(self, compounds: list[str], conditions: list[str], parent=None):
        """Initialize the removal summary dialog.

        Args:
            compounds (list[str]): Removed compounds to display.
            conditions (list[str]): Removed conditions to display.
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Removal summary")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui(compounds, conditions)

    def _build_ui(self, compounds: list[str], conditions: list[str]):
        """Build and attach the dialog content sections."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._make_section(
            f"Compounds removed ({len(compounds)})", compounds
        ))
        layout.addWidget(self._make_section(
            f"Conditions removed ({len(conditions)})", conditions
        ))


    def _make_section(self, title: str, items: list[str]) -> QFrame:
        """Create one titled list section for removed items."""
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

            # Show a compact preview window even when many items are removed.
            list_widget.setFixedHeight(
                list_widget.sizeHintForRow(0) * 5 + 8
            )
        else:
            QListWidgetItem('Nothing to remove', list_widget)

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
        compounds=["Caffeine", "Uracil", "Thiourea", "Naphthalene"],
        conditions=["pH > 7.5", "Temperature ≤ 25°C", "Gradient > 60% ACN"],
    )
    dlg.exec()

    sys.exit(0)
