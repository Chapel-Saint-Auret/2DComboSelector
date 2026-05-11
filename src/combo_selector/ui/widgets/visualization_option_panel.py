"""
visualization_options_panel.py

A QGroupBox-based widget for the "Visualization Options" panel in 2DComboSelector.
Dynamically shows/hides sub-option panels depending on the selected plot type.
"""

from PySide6.QtWidgets import (
    QApplication, QGroupBox, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QWidget, QButtonGroup, QRadioButton,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt,Signal
from PySide6.QtGui import QFont


from dataclasses import dataclass

from combo_selector.ui.widgets.flat_radio_grouped_button import FlatRadioGroupedButton

import sys


# ---------------------------------------------------------------------------
# Plot metadata
# ---------------------------------------------------------------------------

PLOT_TYPES = [
    "Orthogonality Space",
    "Metric Removal Impact On Orthogonality Rank",
    "Multi-Criteria Space",
    "Chromatographic Mode Performance",
    "Recommendation Distribution",
    "Feasibility Profile",
    "Final Rank vs Recommendation",
]

PLOT_DESCRIPTIONS = {
    "Orthogonality Space":
        "Scatter plot of chromatographic condition pairs in orthogonality space.",
    "Metric Removal Impact On Orthogonality Rank":
        "Shows the median orthogonality rank obtained after removing each metric from its correlation group.",
    "Multi-Criteria Space":
        "Scatter plot of solutions in criteria space to explore trade-offs between objectives.",
    "Chromatographic Mode Performance":
        "Compares chromatographic modes across selected criteria.",
    "Recommendation Distribution":
        "Shows the distribution of recommended condition pairs.",
    "Feasibility Profile":
        "Displays feasibility scores across the evaluated condition space.",
    "Final Rank vs Recommendation":
        "Cross-plots the final consensus rank against recommendation scores.",
}

CRITERIA_ITEMS = [
    "All criteria",
    "Orthogonality",
    "Elution Domain",
    "Peak Capacity",
    "Final consensus",
    "Peak rate",
]


# ---------------------------------------------------------------------------
# Helper: thin horizontal separator
# ---------------------------------------------------------------------------

def _make_separator():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color: #d0d5dd;")
    return line


# ---------------------------------------------------------------------------
# Helper: styled radio-button row inside a light rounded container
# ---------------------------------------------------------------------------

class RadioPanel(QWidget):
    """A row of radio buttons in a light rounded container."""

    def __init__(self, label: str, options: list[str], parent=None):
        super().__init__(parent)
        self._group = QButtonGroup(self)
        self._buttons: dict[str, QRadioButton] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: 600; color: #1d2939; font-size: 13px;")
        outer.addWidget(lbl)

        container = QWidget()
        container.setObjectName("RadioContainer")
        container.setStyleSheet("""
            QWidget#RadioContainer {
                background: #f9fafb;
                border: 1px solid #e4e7ec;
                border-radius: 8px;
            }
        """)
        row = QHBoxLayout(container)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(2)

        for i, opt in enumerate(options):
            rb = QRadioButton(opt)
            rb.setStyleSheet("""
                QRadioButton {
                    font-size: 13px;
                    color: #344054;
                    padding: 5px 10px;
                    border-radius: 6px;
                }
                QRadioButton::indicator { width: 0; height: 0; }
                QRadioButton:checked {
                    background: #ffffff;
                    color: #1d2939;
                    font-weight: 600;
                    border: 1px solid #d0d5dd;
                }
            """)
            self._group.addButton(rb, i)
            self._buttons[opt] = rb
            row.addWidget(rb)
            if i == 0:
                rb.setChecked(True)

        outer.addWidget(container)

    def checked_text(self) -> str:
        btn = self._group.checkedButton()
        return btn.text() if btn else ""

    def connect_toggled(self, slot):
        self._group.buttonToggled.connect(slot)


# ---------------------------------------------------------------------------
# Helper: labelled combo box
# ---------------------------------------------------------------------------

class LabelledCombo(QWidget):
    def __init__(self, label: str, items: list[str], parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        layout.addWidget(lbl)

        title_font = QFont(self.font())
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        lbl.setFont(title_font)
        lbl.setStyleSheet("color: #333333;")
        lbl.setContentsMargins(0, 0, 0, 0)

        self.combo = QComboBox()
        self.combo.addItems(items)
        layout.addWidget(self.combo)


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------
@dataclass
class PlotState:
    plot_type: str  = 'Orthogonality Space'        # always set
    subset:     str = 'All'   # "All" | "Top 50%" | "Top 20%" | "Top 10%"
    axis_scale: str = 'Auto'  # "Auto" | "Linear" | "Log"
    view:       str = 'Heatmap'  # "Heatmap" | "Boxplot"
    criteria:   str = 'All criteria'  # only when view == "Boxplot"
    grouping:   str = 'Global' # "Global" | "By mode"


class VisualizationOptionsPanel(QGroupBox):
    """
    Visualization Options group box with dynamic sub-panels.

    Sub-panels shown per plot type:
      - Orthogonality Space          → Subset (All / Top 50% / Top 20% / Top 10%)
      - Multi-Criteria Space         → Subset + Axis scale (auto / linear / log)
      - Chromatographic Mode Perf.   → View (Heatmap / Boxplot)
                                       + Criteria combo (only when Boxplot selected)
      - Recommendation Distribution  → Grouping (Global / By mode)
      - Feasibility Profile          → Grouping + Axis scale
      - Final Rank vs Recommendation → (no extra options)
    """
    plotTypeChanged = Signal(str)
    stateChanged = Signal(object)  # emits a PlotState

    def __init__(self, parent=None):
        super().__init__("Visualization Options", parent)

        self._build_ui()
        self._on_plot_changed(0)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 18, 14, 14)
        root.setSpacing(10)

        # --- Plot type label + combo ---
        plot_label = QLabel("Plot type")
        plot_label.setStyleSheet("font-weight: 600; color: #1d2939; font-size: 13px;")
        root.addWidget(plot_label)

        title_font = QFont(self.font())
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        plot_label.setFont(title_font)
        plot_label.setStyleSheet("color: #333333;")
        plot_label.setContentsMargins(0, 0, 0, 0)

        self._plot_combo = QComboBox()
        self._plot_combo.addItems(PLOT_TYPES)
        root.addWidget(self._plot_combo)

        # --- Description label ---
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet(
            "color: #667085; font-size: 12px; padding: 0 2px;"
        )
        root.addWidget(self._desc_label)

        root.addWidget(_make_separator())

        # ------------------------------------------------------------------
        # Sub-panels (created once, shown/hidden dynamically)
        # ------------------------------------------------------------------

        # Subset panel (Orthogonality + Multi-Criteria)
        self._percentile_panel = FlatRadioGroupedButton(title='Subset',
            items=["All", "Top 50%", "Top 20%", "Top 10%"]
        )

        root.addWidget(self._percentile_panel)

        # Axis scale panel (Multi-Criteria + Feasibility)

        self._axis_panel = FlatRadioGroupedButton(title='Axis scale',
                               items=["Auto", "Linear", "Log"]
                               )
        root.addWidget(self._axis_panel)

        # View panel (Chromatographic Mode Performance)
        self._view_panel = FlatRadioGroupedButton(title='View',
                               items=["Heatmap", "Boxplot"]
                               )
        self._view_panel.buttonClicked.connect(self._on_view_toggled)
        root.addWidget(self._view_panel)

        # Criteria combo (Chromatographic Mode Performance — Boxplot only)
        self._criteria_combo_widget = LabelledCombo("Criteria", CRITERIA_ITEMS)
        root.addWidget(self._criteria_combo_widget)

        # Grouping panel (Recommendation + Feasibility)
        self._grouping_panel = FlatRadioGroupedButton(title='Grouping',
                               items=["Global", "By mode"]
                               )
        root.addWidget(self._grouping_panel)

        # Stretch at bottom
        root.addStretch()

        # Wire plot combo
        self._plot_combo.currentIndexChanged.connect(self._on_plot_changed)

        self._plot_combo.currentIndexChanged.connect(lambda _: self._emit_state())
        self._percentile_panel.buttonClicked.connect(lambda _: self._emit_state())
        self._axis_panel.buttonClicked.connect(lambda _: self._emit_state())
        self._view_panel.buttonClicked.connect(lambda _: self._emit_state())
        self._grouping_panel.buttonClicked.connect(lambda _: self._emit_state())
        self._criteria_combo_widget.combo.currentTextChanged.connect(lambda _: self._emit_state())

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _emit_state(self):
        plot = self._plot_combo.currentText()

        show_subset = plot in ("Orthogonality Space", "Multi-Criteria Space")
        show_axis = plot in ("Multi-Criteria Space", "Feasibility Profile")
        show_view = plot == "Chromatographic Mode Performance"
        show_grouping = plot in ("Recommendation Distribution", "Feasibility Profile")
        is_boxplot = show_view and self._view_panel.currentText() == "Boxplot"

        state = PlotState(
            plot_type=plot,
            subset=self._percentile_panel.currentText() if show_subset else None,
            axis_scale=self._axis_panel.currentText() if show_axis else None,
            view=self._view_panel.currentText() if show_view else None,
            criteria=self._criteria_combo_widget.combo.currentText() if is_boxplot else None,
            grouping=self._grouping_panel.currentText() if show_grouping else None,
        )
        self.stateChanged.emit(state)

    def _on_plot_changed(self, index: int):
        plot = PLOT_TYPES[index]

        # Update description
        self._desc_label.setText(PLOT_DESCRIPTIONS.get(plot, ""))

        # Determine visibility of each panel
        show_subset = plot in ("Orthogonality Space", "Multi-Criteria Space")
        show_axis = plot in ("Multi-Criteria Space", "Feasibility Profile")
        show_view = plot == "Chromatographic Mode Performance"
        show_grouping = plot in ("Recommendation Distribution", "Feasibility Profile")

        self._percentile_panel.setVisible(show_subset)
        self._axis_panel.setVisible(show_axis)
        self._view_panel.setVisible(show_view)
        self._grouping_panel.setVisible(show_grouping)

        # Criteria combo visibility depends on view panel state
        if show_view:
            text = self._view_panel.currentText()
            self._update_criteria_visibility(text)
        else:
            self._criteria_combo_widget.setVisible(False)

        self.plotTypeChanged.emit(plot)

    def _on_view_toggled(self, text):
        self._update_criteria_visibility(text)

    def _update_criteria_visibility(self,text):
        is_boxplot = text == "Boxplot"
        self._criteria_combo_widget.setVisible(is_boxplot)

    def _percentile_toggled(self, button, checked):
        button.text()




# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    panel = VisualizationOptionsPanel()
    panel.setMinimumWidth(340)
    panel.setMaximumWidth(400)
    panel.show()

    sys.exit(app.exec())