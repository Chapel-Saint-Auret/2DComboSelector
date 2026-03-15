import sys

from PySide6.QtCore import QSize,Signal

from PySide6.QtWidgets import QApplication, QPushButton, QHBoxLayout, QVBoxLayout,QWidget,QWidgetAction,QGridLayout, QColorDialog, QDialog,QMenu,QToolButton

PALETTES = {
    # bokeh paired 12
    'paired12':['#000000', '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928', '#ffffff'],
    # d3 category 10
    'category10':['#000000', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#ffffff'],
    # 17 undertones https://lospec.com/palette-list/17undertones
    '17undertones': ['#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970', '#5ebb49', '#458352','#dcd37b', '#fffee5', '#ffd035', '#cc9245', '#a15c3e', '#a42f3b', '#f45b7a', '#c24998', '#81588d', '#bcb0c2', '#ffffff'],
    'basic': ['#FFFFFF', '#C8D2D7', '#969682', '#323C46', '#000000', '#FFE178', '#FAA50A', '#FA780A','#ED0B00','#870A00', '#F5C8DC', '#EB78A5', '#AF23A5', '#641946', '#4B0500', '#CDE6EB', '#8CC3D2', '#55A0B9', '#006487', '#00374B','#8CD2B4','#55D2B4','#1EA028','#96B419','#556E28']
}


class _PaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QSize(20, 20))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)


class _PaletteBase(QWidget):

    selected = Signal(object)
    selected_other = Signal()

    def _emit_color(self, color):
        print('color')
        print(color)
        self.selected.emit(color)

    def emit_other_color(self):
        print('_emit_other_color')
        self.selected_other.emit()


class _PaletteLinearBase(_PaletteBase):
    def __init__(self, colors, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(colors, str):
            if colors in PALETTES:
                colors = PALETTES[colors]

        palette = self.layoutvh()

        for c in colors:
            b = _PaletteButton(c)
            b.pressed.connect(
                lambda c=c: self._emit_color(c)
            )
            palette.addWidget(b)

        self.setLayout(palette)


class PaletteHorizontal(_PaletteLinearBase):
    layoutvh = QHBoxLayout


class PaletteVertical(_PaletteLinearBase):
    layoutvh = QVBoxLayout


class ColorPicker(QWidget):
    selected = Signal()

    def __init__(self,type='basic'):
        super().__init__()
        self.setFixedWidth(25)
        self.vLayout = QVBoxLayout()
        self.setLayout(self.vLayout)

        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.vLayout.setSpacing(0)
        self.colorPicketBtn = QPushButton()
        # self.colorPicketBtn = QToolButton()
        # self.colorPicketBtn.setPopupMode(QToolButton.MenuButtonPopup)
        self.menu = QMenu()
        self.colorPicketBtn.setMenu(self.menu)
        self.colorPicketBtn.setStyleSheet("background-color:#000000;")
        self.color = '#000000'
        self.palette = PaletteGrid(type)

        action = QWidgetAction(self.colorPicketBtn)
        action.setDefaultWidget(self.palette)
        self.colorPicketBtn.menu().addAction(action)

        self.vLayout.addWidget(self.colorPicketBtn)

        self.colorPicketBtn.clicked.connect(self.color_picker_btn_clicked)
        self.palette.selected.connect(self.color_picker_selected)
        self.palette.selected_other.connect(self.color_picker_selected_other)

    def color_picker_btn_clicked(self):
        self.palette.setVisible(True)
        self.menu.setVisible(True)
        self.setFixedHeight(self.palette.sizeHint().height())

    def color_picker_selected(self, color):
        self.menu.setVisible(False)
        self.colorPicketBtn.setStyleSheet("background-color:{};".format(color))
        self.setFixedHeight(self.colorPicketBtn.sizeHint().height())
        self.color = color
        self.selected.emit()

    def color_picker_selected_other(self):
        self.menu.setVisible(False)
        self.setFixedHeight(self.colorPicketBtn.sizeHint().height())
        color = QColorDialog.getColor()
        self.colorPicketBtn.setStyleSheet("background-color:{};".format(color.name()))
        self.color = color
        self.selected.emit()

    def get_color(self):
        return self.color


class PaletteGrid(_PaletteBase):

    def __init__(self, color_type, n_columns=5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(color_type, str):
            if color_type in PALETTES:
                colors = PALETTES[color_type]
        else:
            colors = PALETTES['basic']

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        palette = QGridLayout()
        palette.setContentsMargins(0, 0, 0, 0)
        palette.setSpacing(0)
        row, col = 0, 0

        for c in colors:
            b = _PaletteButton(c)
            b.pressed.connect(
                lambda c=c: self._emit_color(c)
            )
            palette.addWidget(b, row, col)
            col += 1
            if col == n_columns:
                col = 0
                row += 1
        self.otherColorBtn = QPushButton('Other...')
        vlayout.addLayout(palette)
        vlayout.addWidget(self.otherColorBtn)

        self.otherColorBtn.pressed.connect(
                lambda c=c: self.emit_other_color()
            )

        self.setLayout(vlayout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = QDialog()

    main_layout = QHBoxLayout()
    w.setLayout(main_layout)

    color_picker = ColorPicker('basic')

    main_layout.addWidget(color_picker)

    w.exec()