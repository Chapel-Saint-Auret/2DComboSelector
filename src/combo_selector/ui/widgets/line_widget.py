"""Simple horizontal or vertical separator line widget.

This module provides a lightweight widget for drawing separator lines
in layouts, commonly used to visually divide sections of a UI.
"""

import sys

from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QWidget, QLabel


class LineWidget(QFrame):
    """Simple separator line widget (horizontal or vertical).

    Creates a thin sunken line that can be used as a visual separator
    between UI elements. Typically used in layouts to divide sections.

    Attributes:
        orientation (str): "Horizontal" or "Vertical".

    Example:
        >>> layout = QVBoxLayout()
        >>> layout.addWidget(QLabel("Section 1"))
        >>> layout.addWidget(LineWidget("Horizontal"))
        >>> layout.addWidget(QLabel("Section 2"))
    """

    def __init__(self, orientation: str = "Horizontal"):
        """Initialize the line widget.

        Args:
            orientation (str): Line orientation. Either "Horizontal" or "Vertical".
                Defaults to "Horizontal".
        """
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create line frame
        line = QFrame()

        if orientation == "Horizontal":
            line.setFrameShape(QFrame.HLine)
        elif orientation == "Vertical":
            line.setFrameShape(QFrame.VLine)
        else:
            # Default to horizontal if invalid orientation
            line.setFrameShape(QFrame.HLine)

        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing horizontal and vertical separators."""

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("LineWidget Example")
    window.resize(300, 200)

    layout = QVBoxLayout(window)

    # Section 1
    layout.addWidget(QLabel("Section 1: Welcome"))
    layout.addWidget(QLabel("This is the first section."))

    # Horizontal separator
    layout.addWidget(LineWidget("Horizontal"))

    # Section 2
    layout.addWidget(QLabel("Section 2: Details"))
    layout.addWidget(QLabel("This is the second section."))

    # Horizontal separator
    layout.addWidget(LineWidget("Horizontal"))

    # Section 3
    layout.addWidget(QLabel("Section 3: Summary"))
    layout.addWidget(QLabel("This is the third section."))

    layout.addStretch()

    window.show()
    sys.exit(app.exec())