import sys

from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout


class LineWidget(QFrame):
    def __init__(self, orientation='Horizontal'):
        super().__init__()

        layout = QVBoxLayout()
        # Add horizontal line
        line = QFrame()
        if orientation == 'Horizontal':
            line.setFrameShape(QFrame.HLine)

        if orientation == 'Vertical':
            line.setFrameShape(QFrame.VLine)

        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LineWidget(Orientation='Vertical')
    window.show()
    sys.exit(app.exec())