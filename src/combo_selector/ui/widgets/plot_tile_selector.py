"""Plot tile selector widget displaying individual plot tiles in a 2-column grid.

This module provides the PlotTileSelector widget which allows users to:
- Select a plot from a set of styled tile buttons arranged in a 2-column grid
- Emit a (family, variant) pair used by ResultsPage to route to the correct plot function
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Ordered list of (tile label, family, variant) for the 2-column grid.
# The tile label uses newlines so the text wraps neatly inside fixed-height tiles.
PLOT_TILES: list[tuple[str, str, str]] = [
    ("Multi Criteria\nSpace",         "Criteria Space",            "Multi Criteria Space"),
    ("Reduced\nCriteria Space",       "Criteria Space",            "Reduced Criteria Space"),
    ("Performance\nHeatmap",          "Performance",               "Performance Heatmap"),
    ("Performance\nBar Plot",         "Performance",               "Performance Bar Plot"),
    ("Recommendation\nDistribution",  "Recommendation Distribution","Recommendation Distribution"),
    ("Feasibility\nProfile",          "Feasibility Profile",       "Overall Feasibility Profile"),
]

# Keep PLOT_GROUPS for consumers that need the family→variant mapping
PLOT_GROUPS: dict[str, list[str]] = {
    "Criteria Space": [
        "Multi Criteria Space",
        "Reduced Criteria Space",
    ],
    "Performance": [
        "Performance Heatmap",
        "Performance Bar Plot",
    ],
    "Recommendation Distribution": [
        "Recommendation Distribution",
    ],
    "Feasibility Profile": [
        "Overall Feasibility Profile",
        "Feasibility Profile by Mode",
    ],
}

_TILE_NORMAL = """
    QPushButton {
        background-color: #dce8f8;
        color: #154E9D;
        border: none;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
        text-align: center;
    }
    QPushButton:hover {
        background-color: #c8d9f5;
    }
"""

_TILE_SELECTED = """
    QPushButton {
        background-color: #183881;
        color: #ffffff;
        border: none;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
        text-align: center;
    }
    QPushButton:hover {
        background-color: #1e4aad;
    }
"""

_TITLE_SS = """
    QLabel {
        color: #154E9D;
        font-size: 13px;
        font-weight: bold;
        background-color: transparent;
    }
"""


class PlotTileSelector(QWidget):
    """Plot selector showing individual plot tiles in a 2-column grid.

    Renders each plot as an equal-sized tile button.  Clicking a tile
    immediately emits ``plot_selected`` with the corresponding
    (family, variant) pair.

    Signals:
        plot_selected (str, str): Emitted when a tile is clicked.
            First argument is the plot family, second is the variant name.

    Attributes:
        current_variant (str | None): The variant name of the active tile.

    Example:
        >>> selector = PlotTileSelector()
        >>> selector.plot_selected.connect(lambda f, v: print(f, v))
    """

    plot_selected = Signal(str, str)

    # Height (px) for every tile button
    _TILE_HEIGHT = 56
    # Number of columns in the grid
    _COLUMNS = 2

    def __init__(self, parent: "QWidget | None" = None) -> None:
        """Initialise the widget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        self.current_variant: str | None = None

        self._tile_buttons: dict[str, QPushButton] = {}  # keyed by variant name
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # Title label
        title = QLabel("Select Result Plot")
        title.setStyleSheet(_TITLE_SS)
        outer.addWidget(title)

        # 2-column grid of tiles
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        for idx, (label, family, variant) in enumerate(PLOT_TILES):
            row, col = divmod(idx, self._COLUMNS)
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(self._TILE_HEIGHT)
            btn.setStyleSheet(_TILE_NORMAL)
            btn.clicked.connect(
                lambda checked, f=family, v=variant: self._on_tile_clicked(f, v)
            )
            self._tile_buttons[variant] = btn
            self._button_group.addButton(btn)
            grid.addWidget(btn, row, col)

        outer.addLayout(grid)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _on_tile_clicked(self, family: str, variant: str) -> None:
        """Handle a tile click: update styles and emit the selection.

        Args:
            family: The plot family name for the clicked tile.
            variant: The plot variant name for the clicked tile.
        """
        for v, btn in self._tile_buttons.items():
            btn.setStyleSheet(_TILE_SELECTED if v == variant else _TILE_NORMAL)

        self.current_variant = variant
        self.plot_selected.emit(family, variant)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_variant(self, variant: str) -> None:
        """Programmatically activate a tile by its variant name.

        Args:
            variant: The variant name of the tile to activate.

        Raises:
            KeyError: If *variant* is not a known tile variant.
        """
        for label, family, v in PLOT_TILES:
            if v == variant:
                self._on_tile_clicked(family, variant)
                return
        raise KeyError(f"Unknown plot variant: {variant!r}")
