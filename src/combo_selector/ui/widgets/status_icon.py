"""Status indicator widget with wait, valid, and error states.

This module provides a compact status icon widget that can display three states:
- Wait/Pending (default): Hourglass or waiting indicator
- Valid/OK: Green checkmark or success indicator
- Error/NOK: Red X or error indicator

Perfect for form validation, process status, or workflow step indicators.
"""

import sys

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from combo_selector.utils import resource_path


class Status(QWidget):
    """Status indicator widget with three states: wait, valid, and error.

    Displays a small icon indicating the current status state. Uses a
    QStackedWidget to switch between three icon states.

    States:
    - 0 (Wait): Default state, typically shown before validation
    - 1 (Valid): Success/OK state, shown when validation passes
    - 2 (Error): Error/NOK state, shown when validation fails

    Class Attributes:
        IconSize (QSize): Size of status icons (16x16 pixels).

    Attributes:
        qstack (QStackedWidget): Stacked widget containing icon states.

    Example:
        >>> status = Status()
        >>> status.set_valid()  # Show green checkmark
        >>> status.set_error()  # Show red X
    """

    IconSize = QSize(16, 16)

    def __init__(self, parent: QWidget = None):
        """Initialize the status indicator widget.

        Args:
            parent (QWidget, optional): Parent widget.

        Side Effects:
            - Loads wait, ok, and nok icons from resources
            - Sets default state to "wait" (index 0)
        """
        super().__init__(parent)
        self.setFixedSize(35, 40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.qstack = QStackedWidget()
        layout.addWidget(self.qstack)

        # Load and scale icons
        wait_icon = QPixmap(resource_path("icons/wait.png"))
        wait_icon = wait_icon.scaled(self.IconSize)

        ok_icon = QPixmap(resource_path("icons/ok.png"))
        ok_icon = ok_icon.scaled(self.IconSize)

        nok_icon = QPixmap(resource_path("icons/nok.png"))
        nok_icon = nok_icon.scaled(self.IconSize)

        # Create wait state widget
        wait_label = QLabel()
        wait_label.setPixmap(wait_icon)
        wait_widget = QWidget(self)
        wait_layout = QHBoxLayout(wait_widget)
        wait_layout.addWidget(wait_label)

        # Create valid/OK state widget
        ok_label = QLabel()
        ok_label.setPixmap(ok_icon)
        ok_widget = QWidget(self)
        ok_layout = QHBoxLayout(ok_widget)
        ok_layout.addWidget(ok_label)

        # Create error/NOK state widget
        nok_label = QLabel()
        nok_label.setPixmap(nok_icon)
        nok_widget = QWidget(self)
        nok_layout = QHBoxLayout(nok_widget)
        nok_layout.addWidget(nok_label)

        # Add states to stacked widget
        self.qstack.addWidget(wait_widget)  # Index 0
        self.qstack.addWidget(ok_widget)  # Index 1
        self.qstack.addWidget(nok_widget)  # Index 2

        # Set default state
        self.qstack.setCurrentIndex(0)

    def set_error(self) -> None:
        """Set status to error/NOK state (red X).

        Side Effects:
            - Switches to error icon (index 2)
        """
        self.qstack.setCurrentIndex(2)

    def set_valid(self) -> None:
        """Set status to valid/OK state (green checkmark).

        Side Effects:
            - Switches to valid icon (index 1)
        """
        self.qstack.setCurrentIndex(1)

    def set_wait(self) -> None:
        """Set status to wait/pending state (hourglass).

        Side Effects:
            - Switches to wait icon (index 0)
        """
        self.qstack.setCurrentIndex(0)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Example showing status indicator with state transitions."""

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Status Indicator Example")
    window.resize(300, 200)

    layout = QVBoxLayout(window)

    # Create status indicator
    status = Status()
    layout.addWidget(status)

    # Create buttons to change state
    btn_layout = QHBoxLayout()

    btn_wait = QPushButton("Set Wait")
    btn_wait.clicked.connect(status.set_wait)
    btn_layout.addWidget(btn_wait)

    btn_valid = QPushButton("Set Valid")
    btn_valid.clicked.connect(status.set_valid)
    btn_layout.addWidget(btn_valid)

    btn_error = QPushButton("Set Error")
    btn_error.clicked.connect(status.set_error)
    btn_layout.addWidget(btn_error)

    layout.addLayout(btn_layout)

    # Add description
    label = QLabel(
        "Click buttons to change status state:\n"
        "• Wait: Default/pending state\n"
        "• Valid: Success/OK state\n"
        "• Error: Failure/NOK state"
    )
    layout.addWidget(label)

    layout.addStretch()

    window.show()
    sys.exit(app.exec())