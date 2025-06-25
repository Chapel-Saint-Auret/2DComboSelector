import sys
from PySide6.QtWidgets import QFrame,QVBoxLayout,QApplication


class LineWidget(QFrame):
    def __init__(self, Orientation):
        super().__init__()

        layout = QVBoxLayout()
        # Add horizontal line
        line = QFrame()
        if Orientation == 'Horizontal':
            line.setFrameShape(QFrame.HLine)

        if Orientation == 'Vertical':
            line.setFrameShape(QFrame.VLine)

        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LineWidget(Orientation='Vertical')
    window.show()
    sys.exit(app.exec())