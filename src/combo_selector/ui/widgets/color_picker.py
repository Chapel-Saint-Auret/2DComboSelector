"""Color picker widget backed by predefined palette grids.

Provides :class:`ColorPicker`, a compact button that opens a pop-up grid of
palette colors, and supporting palette widget classes used internally.
"""

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
    """Small square push-button representing a single palette color.

    Attributes:
        color (str): Hex color string (e.g. ``"#ff0000"``) assigned to this button.
    """

    def __init__(self, color):
        """Initialize the palette button with the given color.

        Args:
            color (str): Hex color string used for the button background.
        """
        super().__init__()
        self.setFixedSize(QSize(20, 20))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)


class _PaletteBase(QWidget):
    """Abstract base class for palette widgets.

    Provides ``selected`` and ``selected_other`` signals for communicating
    color choices to parent widgets.

    Attributes:
        selected (Signal[object]): Emitted with the chosen hex color string.
        selected_other (Signal): Emitted when the user requests a custom color.
    """

    selected = Signal(object)
    selected_other = Signal()

    def _emit_color(self, color):
        """Emit the ``selected`` signal with the given color.

        Args:
            color (str): Hex color string chosen by the user.

        Side Effects:
            - Emits ``selected`` signal.
        """
        self.selected.emit(color)

    def emit_other_color(self):
        """Emit the ``selected_other`` signal to request a custom color dialog.

        Side Effects:
            - Emits ``selected_other`` signal.
        """
        self.selected_other.emit()


class _PaletteLinearBase(_PaletteBase):
    """Palette laid out linearly (horizontal or vertical).

    Subclasses set ``layoutvh`` to either :class:`QHBoxLayout` or
    :class:`QVBoxLayout` to control orientation.

    Attributes:
        layoutvh: Layout class used to arrange palette buttons.
    """

    def __init__(self, colors, *args, **kwargs):
        """Initialize a linear palette with the given colors.

        Args:
            colors (list[str] | str): List of hex color strings, or a palette
                name defined in :data:`PALETTES`.
            *args: Positional arguments forwarded to :class:`QWidget`.
            **kwargs: Keyword arguments forwarded to :class:`QWidget`.
        """
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
    """Palette laid out in a single horizontal row."""

    layoutvh = QHBoxLayout


class PaletteVertical(_PaletteLinearBase):
    """Palette laid out in a single vertical column."""

    layoutvh = QVBoxLayout


class ColorPicker(QWidget):
    """Compact color picker button with a pop-up palette grid.

    Displays a small square button whose background reflects the currently
    selected color.  Clicking opens a pop-up palette; selecting a color
    updates the button and emits ``selected``.

    Attributes:
        color (str | QColor): Currently selected color.
        colorPicketBtn (QPushButton): Main button showing the active color.
        palette (PaletteGrid): Pop-up palette grid widget.
        menu (QMenu): Menu used to host the pop-up palette.

    Signals:
        selected: Emitted when the user picks a color.
    """

    selected = Signal()

    def __init__(self, type='basic'):
        """Initialize the color picker with a palette of the given type.

        Args:
            type (str): Palette name from :data:`PALETTES`.
                Defaults to ``"basic"``.
        """
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
        """Show the palette pop-up when the main button is clicked.

        Side Effects:
            - Makes the palette visible.
            - Shows the menu.
            - Adjusts widget height to fit the palette.
        """
        self.palette.setVisible(True)
        self.menu.setVisible(True)
        self.setFixedHeight(self.palette.sizeHint().height())

    def color_picker_selected(self, color):
        """Handle palette color selection.

        Args:
            color (str): Hex color string selected by the user.

        Side Effects:
            - Hides the menu.
            - Updates button background to the selected color.
            - Updates ``color`` attribute.
            - Resets widget height.
            - Emits ``selected`` signal.
        """
        self.menu.setVisible(False)
        self.colorPicketBtn.setStyleSheet("background-color:{};".format(color))
        self.setFixedHeight(self.colorPicketBtn.sizeHint().height())
        self.color = color
        self.selected.emit()

    def color_picker_selected_other(self):
        """Open a system color dialog for custom color selection.

        Side Effects:
            - Hides the menu.
            - Opens :class:`QColorDialog`.
            - Updates button background and ``color`` attribute.
            - Resets widget height.
            - Emits ``selected`` signal.
        """
        self.menu.setVisible(False)
        self.setFixedHeight(self.colorPicketBtn.sizeHint().height())
        self.colorPicketBtn.setStyleSheet("background-color:{};".format(color.name()))
        self.color = color
        self.selected.emit()

    def get_color(self):
        """Return the currently selected color.

        Returns:
            str | QColor: Currently selected color value.
        """
        return self.color


class PaletteGrid(_PaletteBase):
    """Palette laid out as a fixed-column grid with an "Other…" button.

    Attributes:
        otherColorBtn (QPushButton): Button that triggers custom color selection.
    """

    def __init__(self, color_type, n_columns=5, *args, **kwargs):
        """Initialize the grid palette.

        Args:
            color_type (str): Palette name from :data:`PALETTES`, or any value
                that falls back to the ``"basic"`` palette if not found.
            n_columns (int): Number of color buttons per row. Defaults to ``5``.
            *args: Positional arguments forwarded to :class:`QWidget`.
            **kwargs: Keyword arguments forwarded to :class:`QWidget`.
        """
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