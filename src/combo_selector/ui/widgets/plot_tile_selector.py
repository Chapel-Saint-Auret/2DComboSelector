"""Tile-style plot type selector widget for PySide6 applications.

Provides a ``PlotTileSelector`` widget that presents available plot types as a
2-column grid of checkable, card-like tile buttons.  The selected tile is
highlighted with the application's standard blue header colour, making the
active choice immediately obvious to the user.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)

# ---------------------------------------------------------------------------
# Plot registry
# ---------------------------------------------------------------------------
# Each entry is (dispatch_key, tile_display_text).
# The dispatch_key must match the keys used in ResultsPage.plot_functions_map.
# Keep each display-text line short enough to fit inside a ~100 px-wide tile.
_PLOT_REGISTRY = [
    ("Multi Criteria Space",                "Multi Criteria\nSpace"),
    ("Reduced Criteria Space",              "Reduced\nCriteria Space"),
    ("Chromatographic Mode Performance HM", "Performance\nHeatmap"),
    ("Chromatographic Mode Performance BP", "Performance\nBar Plot"),
    ("Recommendation Distribution",         "Recommendation\nDistribution"),
    ("Feasibility Profile",                 "Feasibility\nProfile"),
]

# ---------------------------------------------------------------------------
# Tile stylesheet
# ---------------------------------------------------------------------------
_TILE_STYLE = """
    QPushButton {
        background-color: #eef2fc;
        color: #2C3E50;
        border: 2px solid #c8d2e8;
        border-radius: 8px;
        padding: 8px 8px;
        font-size: 10px;
        font-weight: 500;
        text-align: center;
    }
    QPushButton:hover {
        background-color: #dde6fc;
        border: 2px solid #4a7de8;
    }
    QPushButton:checked {
        background-color: #183881;
        color: #ffffff;
        border: 2px solid #6fa3f7;
        font-weight: bold;
    }
    QPushButton:checked:hover {
        background-color: #1e4a9c;
        border: 2px solid #8ab8ff;
    }
"""


class PlotTileSelector(QWidget):
    """Grid of checkable tile buttons for selecting the active result plot.

    Displays one tile per available plot type in a 2-column grid.  Exactly one
    tile is checked at a time (enforced by an exclusive ``QButtonGroup``).
    Clicking a tile emits :attr:`plot_selected` with the corresponding plot
    key so callers can dispatch to the correct plotting function.

    Attributes:
        plot_selected (Signal[str]): Emitted when the user selects a tile.
            Carries the dispatch key (e.g. ``"Multi Criteria Space"``).

    Example::

        selector = PlotTileSelector()
        selector.plot_selected.connect(lambda key: print("Selected:", key))
    """

    plot_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialise the selector and build the tile grid.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
        super().__init__(parent)

        self._id_to_key: dict[int, str] = {}
        self._selected_key: str | None = None

        grid = QGridLayout(self)
        grid.setSpacing(8)
        grid.setContentsMargins(4, 4, 4, 4)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        cols = 2
        for idx, (key, display_text) in enumerate(_PLOT_REGISTRY):
            btn = QPushButton(display_text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(56)
            btn.setStyleSheet(_TILE_STYLE)

            self._button_group.addButton(btn, idx)
            self._id_to_key[idx] = key
            grid.addWidget(btn, idx // cols, idx % cols)

        # Pre-select the first tile so the view always has an active plot.
        first_btn = self._button_group.button(0)
        if first_btn is not None:
            first_btn.setChecked(True)
            self._selected_key = self._id_to_key[0]

        self._button_group.idClicked.connect(self._on_id_clicked)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def selected_plot(self) -> Optional[str]:
        """Return the dispatch key of the currently selected tile.

        Returns:
            str | None: The plot key, or ``None`` if nothing is selected yet.
        """
        return self._selected_key

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _on_id_clicked(self, btn_id: int) -> None:
        """Handle tile button clicks and emit :attr:`plot_selected`.

        Args:
            btn_id (int): The button ID assigned by ``QButtonGroup``.
        """
        key = self._id_to_key.get(btn_id)
        if key is None:
            return
        self._selected_key = key
        self.plot_selected.emit(key)
