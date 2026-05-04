"""Plot tile selector widget with family and variant support.

This module provides the PlotTileSelector widget which allows users to:
- Select a plot family from a set of styled tile buttons
- Choose a plot variant when the selected family has multiple options
- Automatically emit the selection for single-variant families
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from combo_selector.utils import resource_path

# Dropdown arrow icon path
_drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")

# Plot families and their variants, in display order
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

_TILE_BASE = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 500;
        text-align: left;
    }}
    QPushButton:hover {{
        background-color: {hover};
        border: 1px solid #8fa3ef;
    }}
"""

_TILE_NORMAL = _TILE_BASE.format(
    bg="#d5dcf9",
    fg="#2C3346",
    border="#bcc8f5",
    hover="#bcc8f5",
)

_TILE_SELECTED = _TILE_BASE.format(
    bg="#183881",
    fg="#ffffff",
    border="#183881",
    hover="#1e4aad",
)

_VARIANT_COMBO_SS = f"""
    QComboBox {{
        background-color: #ffffff;
        color: #2C3346;
        border: 1px solid #bcc8f5;
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 11px;
    }}
    QComboBox:hover {{ border: 1px solid #8fa3ef; }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox::down-arrow {{ image: url("{_drop_down_icon_path}"); }}
"""


class PlotTileSelector(QWidget):
    """Hierarchical plot selector showing families with optional variant choice.

    Displays one clickable tile per plot family. When the selected family has
    multiple variants a labelled combo box appears below the tiles so the user
    can choose which variant to render. Single-variant families emit the
    selection immediately without requiring an extra click.

    Signals:
        plot_selected (str, str): Emitted whenever a complete (family, variant)
            pair has been chosen.  The first argument is the family name and
            the second is the variant name.

    Attributes:
        plot_groups (dict): Mapping of family names to variant name lists.
        current_family (str | None): The family whose tile is currently active.

    Example:
        >>> selector = PlotTileSelector()
        >>> selector.plot_selected.connect(lambda f, v: print(f, v))
    """

    plot_selected = Signal(str, str)

    def __init__(self, parent: QWidget = None) -> None:
        """Initialise the widget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        self.plot_groups: dict[str, list[str]] = PLOT_GROUPS
        self.current_family: str | None = None

        self._family_buttons: dict[str, QPushButton] = {}
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # --- Family tiles --------------------------------------------------
        for family in self.plot_groups:
            btn = QPushButton(family)
            btn.setCheckable(True)
            btn.setStyleSheet(_TILE_NORMAL)
            btn.clicked.connect(lambda checked, f=family: self._on_family_clicked(f))
            self._family_buttons[family] = btn
            self._button_group.addButton(btn)
            layout.addWidget(btn)

        # --- Variant selector (hidden until needed) -------------------------
        self._variant_label = QLabel("Variant:")
        self._variant_label.setVisible(False)
        self._variant_label.setStyleSheet(
            "color: #2C3E50; font-size: 11px; font-weight: bold;"
        )

        self._variant_combo = QComboBox()
        self._variant_combo.setStyleSheet(_VARIANT_COMBO_SS)
        self._variant_combo.setVisible(False)
        self._variant_combo.currentTextChanged.connect(self._on_variant_changed)

        layout.addWidget(self._variant_label)
        layout.addWidget(self._variant_combo)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_tile_style(self, family: str, selected: bool) -> None:
        """Apply the correct stylesheet to a family tile button.

        Args:
            family: The family name whose button should be styled.
            selected: ``True`` for the active (selected) style, ``False`` for normal.
        """
        btn = self._family_buttons[family]
        btn.setStyleSheet(_TILE_SELECTED if selected else _TILE_NORMAL)

    def _on_family_clicked(self, family: str) -> None:
        """Handle a family tile click.

        Updates tile styles, shows/hides the variant combo and emits
        ``plot_selected`` with the first variant (or the only variant for
        single-variant families).

        Args:
            family: The name of the clicked plot family.
        """
        # Update button styles
        for f in self._family_buttons:
            self._apply_tile_style(f, f == family)

        self.current_family = family
        variants = self.plot_groups[family]

        # Populate variant combo regardless (needed for multi-variant families)
        self._variant_combo.blockSignals(True)
        self._variant_combo.clear()
        self._variant_combo.addItems(variants)
        self._variant_combo.setCurrentIndex(0)
        self._variant_combo.blockSignals(False)

        has_variants = len(variants) > 1
        self._variant_label.setVisible(has_variants)
        self._variant_combo.setVisible(has_variants)

        # Always emit using the first (or only) variant
        self.plot_selected.emit(family, variants[0])

    def _on_variant_changed(self, variant: str) -> None:
        """Handle variant combo box change.

        Args:
            variant: The newly selected variant name.
        """
        if self.current_family and variant:
            self.plot_selected.emit(self.current_family, variant)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_family(self, family: str) -> None:
        """Programmatically select a family tile and emit the first variant.

        Args:
            family: The family name to activate.

        Raises:
            KeyError: If *family* is not in :attr:`plot_groups`.
        """
        if family not in self._family_buttons:
            raise KeyError(f"Unknown plot family: {family!r}")
        self._on_family_clicked(family)
