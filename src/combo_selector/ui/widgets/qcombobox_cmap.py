import os

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QComboBox

from combo_selector.utils import resource_path


class QComboBoxCmap(QComboBox):
    def __init__(self):
        super().__init__()

        # Get the directory with the colormap images
        colormap_directory = resource_path("colormaps")

        if os.path.isdir(colormap_directory):
            for filename in os.listdir(colormap_directory):
                if filename.endswith(".png"):
                    cmapIcon = QIcon(os.path.join(colormap_directory, filename))
                    self.addItem(cmapIcon, os.path.splitext(filename)[0])
        size = QSize(70, 20)
        self.setCurrentText("Spectral")
        self.setIconSize(size)
        self.adjustSize()


def main():
    import sys

    app = QApplication(sys.argv)
    cmap = QComboBoxCmap()
    cmap.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
