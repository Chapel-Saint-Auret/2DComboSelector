"""Combo box widget for selecting matplotlib colormaps with visual previews.

This module provides a specialized QComboBox that displays colormap options
with preview images, making it easy for users to select visualization colormaps.

The widget automatically loads all PNG images from the 'colormaps' resource
directory and displays them as icons in the dropdown.
"""

import os
import sys

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QComboBox

from combo_selector.utils import resource_path


class QComboBoxCmap(QComboBox):
    """Combo box for selecting colormaps with visual preview icons.

    Automatically populates itself with colormap options by loading PNG
    images from the 'colormaps' resource directory. Each colormap is
    displayed with its preview image as an icon.

    Features:
    - Auto-loads colormap images from resources
    - Visual preview of each colormap
    - Default selection: "Spectral"
    - Icon size: 70x20 pixels

    Attributes:
        Inherits all QComboBox attributes.

    Example:
        >>> cmap_selector = QComboBoxCmap()
        >>> cmap_selector.currentTextChanged.connect(lambda name: print(f"Selected: {name}"))
        >>> selected_cmap = cmap_selector.currentText()
    """

    def __init__(self):
        """Initialize the colormap combo box.

        Side Effects:
            - Loads all PNG files from 'colormaps' resource directory
            - Adds each as a combo box item with icon
            - Sets default selection to "Spectral"
            - Adjusts size to fit content
        """
        super().__init__()

        # Get the directory with the colormap images
        colormap_directory = resource_path("colormaps")

        # Load all PNG colormaps from the resource directory
        if os.path.isdir(colormap_directory):
            for filename in sorted(os.listdir(colormap_directory)):
                if filename.endswith(".png"):
                    cmap_path = os.path.join(colormap_directory, filename)
                    cmap_icon = QIcon(cmap_path)
                    # Use filename without extension as colormap name
                    cmap_name = os.path.splitext(filename)[0]
                    self.addItem(cmap_icon, cmap_name)

        # Configure appearance
        icon_size = QSize(70, 20)
        self.setIconSize(icon_size)

        # Set default colormap
        self.setCurrentText("Spectral")

        self.adjustSize()


# =============================================================================
# Usage Example
# =============================================================================

def main():
    """Example showing the colormap combo box."""

    app = QApplication(sys.argv)

    # Create colormap selector
    cmap_selector = QComboBoxCmap()
    cmap_selector.setWindowTitle("Colormap Selector")

    # Connect signal to print selection
    def on_colormap_changed(cmap_name):
        print(f"Selected colormap: {cmap_name}")

    cmap_selector.currentTextChanged.connect(on_colormap_changed)

    # Show and select initial value
    cmap_selector.show()
    print(f"Initial colormap: {cmap_selector.currentText()}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()