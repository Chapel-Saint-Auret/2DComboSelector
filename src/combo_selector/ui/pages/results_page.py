"""Results page for ranking and visualizing orthogonality scores.

This module provides the ResultsPage class which handles:
- Computing custom orthogonality scores from selected metrics
- Ranking 2D combinations based on different criteria
- Visualizing score vs. peak capacity correlations
- Side-by-side comparison of up to 4 scores
- Custom filtering of results by combination type
- Progress tracking with circular progress bar overlay
"""

import logging

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QThreadPool, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from combo_selector.core.workers import ResultsWorkerComputeCustomOMScore
from combo_selector.ui.widgets.checkable_tree_list import CheckableTreeList
from combo_selector.ui.widgets.circle_progress_bar import RoundProgressBar
from combo_selector.ui.widgets.custom_filter_dialog import CustomFilterDialog
from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.neumorphism import BoxShadow
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

# Dropdown arrow icon path
drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")

# Maps UI metric names to model data frame column names
UI_TO_MODEL_MAPPING = {
    "Suggested score": "suggested_score",
    "Computed score": "computed_score",
    "Convex hull relative area": "convex_hull",
    "Bin box counting": "bin_box_ratio",
    "Pearson Correlation": "pearson_r",
    "Spearman Correlation": "spearman_rho",
    "Kendall Correlation": "kendall_tau",
    "Asterisk equations": "asterisk_metrics",
    "NND Arithm mean": "nnd_arithmetic_mean",
    "NND Geom mean": "nnd_geom_mean",
    "NND Harm mean": "nnd_harm_mean",
    "NND mean": "nnd_mean",
    "%FIT": "percent_fit",
    "%BIN": "percent_bin",
    "Gilar-Watson method": "gilar-watson",
    "Modeling approach": "modeling_approach",
    "Conditional entropy": "conditional_entropy",
}


class ResultsPage(QFrame):
    """Page for computing, ranking, and visualizing final results.

    Provides a comprehensive interface for:
    - Computing custom orthogonality scores from selected metrics
    - Choosing between suggested score vs. computed score
    - Ranking combinations by score or peak capacity
    - Comparing 1-4 scores side-by-side in scatter plots
    - Filtering results by combination type (custom filters)
    - Viewing final results in sortable/filterable table

    The page uses background threads to compute custom scores without
    freezing the UI, and displays progress with an animated circular bar.

    Attributes:
        model: Reference to the Orthogonality data model.
        thread pool (QThreadPool): Thread pool for background computations.
        om_selector_map (dict): Maps plot indices to selectors and axes.
        selected_score (str): Currently selected score name.
        selected_axe: Currently selected matplotlib axes.
        progress_overlay (QWidget): Transparent overlay showing progress bar.
    """

    def __init__(self, model=None):
        """Initialize the Results Page with controls and visualizations.

        Args:
            model: Orthogonality model instance containing computed metrics.

        Layout Structure:
            - Top section (side-by-side):
                - Left: Input panel (ranking, score calculation, comparison)
                - Right: Plot area (1-4 subplots for score comparisons)
            - Bottom section:
                - Results table with rankings
            - Overlay:
                - Circular progress bar during computations
        """
        super().__init__()

        # --- State & threading ---------------------------------------------
        self.threadpool = QThreadPool()
        self.selected_score = None
        self.selected_axe = None
        self.selected_scatter_collection = None
        self.selected_filtered_scatter_point = {}
        self.model = model

        # --- Base frame & layout -------------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP AREA ======================================================
        top_frame = self._create_top_section()

        # === BOTTOM AREA: table ============================================
        table_frame = self._create_table_section()

        # === Progress overlay ==============================================
        self.progress_overlay = self._create_progress_overlay()

        # === Splitter & stacked layout =====================================
        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)
        self.main_splitter.setSizes([486, 204])
        self.main_layout.addWidget(self.main_splitter)

        self.stack = QStackedLayout()
        self.stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.stack.addWidget(self.main_widget)
        self.stack.addWidget(self.progress_overlay)
        self.stack.setCurrentWidget(self.progress_overlay)

        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.addLayout(self.stack)

        self.progress_overlay.setGeometry(self.stack.geometry())
        self.progress_overlay.raise_()

        # --- Signal connections --------------------------------------------
        self.custom_filter_widget.filter_regexp_changed.connect(self.filter_table)
        self.select_ranking_type.currentTextChanged.connect(self.set_ranking_argument)
        self.radio_button_group.buttonClicked.connect(
            self.set_use_suggested_om_score_flag
        )
        self.compute_score_btn.clicked.connect(self.start_om_computation)
        self.compare_number.currentTextChanged.connect(self.update_om_selector_state)

        for index, data in self.om_selector_map.items():
            data["selector"].currentTextChanged.connect(
                lambda _, k=index: self.on_selector_changed(k)
            )

    def get_model(self):
        return self.model

    def _create_top_section(self) -> QFrame:
        """Create the top section with input panel and plot area.

        Returns:
            QFrame: Configured top frame with input and plot sections.
        """
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        # Left: Input section
        input_section = self._create_input_panel()

        # Right: Plot section
        plot_frame = self._create_plot_panel()

        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)

        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        return top_frame

    def _create_input_panel(self) -> QFrame:
        """Create the left input panel with all controls.

        Returns:
            QFrame: Input section containing all control groups.
        """
        input_title = QLabel("Input")
        input_title.setFixedHeight(30)
        input_title.setObjectName("TitleBar")
        input_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        input_title.setContentsMargins(10, 0, 0, 0)
        input_title.setStyleSheet("""
            background-color: #183881;
            color: white;
            font-weight:bold;
            font-size: 16px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)

        user_input_scroll_area = QScrollArea()
        user_input_scroll_area.setFixedWidth(290)
        user_input_scroll_area.setWidgetResizable(True)
        user_input_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        user_input_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        user_input_frame = QFrame()
        user_input_frame.setFixedWidth(290)
        user_input_frame_layout = QVBoxLayout(user_input_frame)
        user_input_frame_layout.setContentsMargins(20, 20, 20, 20)
        user_input_scroll_area.setWidget(user_input_frame)

        input_section = QFrame()
        input_section.setFixedWidth(290)
        input_layout = QVBoxLayout(input_section)
        input_layout.setSpacing(0)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(input_title)
        input_layout.addWidget(user_input_scroll_area)

        # Create control groups
        ranking_selection_group = self._create_ranking_group()
        orthogonality_score_group = self._create_score_calculation_group()
        orthogonality_compare_score_group = self._create_score_comparison_group()

        user_input_frame_layout.addWidget(ranking_selection_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(orthogonality_score_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(orthogonality_compare_score_group)

        return input_section

    def _create_ranking_group(self) -> QGroupBox:
        """Create ranking selection group.

        Returns:
            QGroupBox: Group box with ranking type selector.
        """
        ranking_selection_group = QGroupBox("Ranking")
        ranking_selection_group.setStyleSheet(self._get_group_stylesheet())

        ranking_layout = QVBoxLayout()
        ranking_layout.setContentsMargins(5, 5, 5, 5)
        ranking_selection_group.setLayout(ranking_layout)

        ranking_layout.addWidget(QLabel("Ranking based on:"))
        self.select_ranking_type = QComboBox()
        self.select_ranking_type.addItems(
            ["Suggested score", "Computed score", "Practical 2D peak capacity"]
        )
        ranking_layout.addWidget(self.select_ranking_type)
        ranking_layout.addSpacing(20)

        return ranking_selection_group

    def _create_score_calculation_group(self) -> QGroupBox:
        """Create orthogonality score calculation group.

        Returns:
            QGroupBox: Group box with metric selection and compute button.
        """
        orthogonality_score_group = QGroupBox("Orthogonality score calculation")
        orthogonality_score_group.setStyleSheet(self._get_group_stylesheet())

        orthogonality_score_layout = QVBoxLayout()
        orthogonality_score_layout.setContentsMargins(5, 5, 5, 5)

        self.om_list = CheckableTreeList()
        self.om_list.setFixedHeight(175)
        self.compute_score_btn = QPushButton("Compute score")

        self.use_suggested_btn = QRadioButton("Use suggested score")
        self.use_suggested_btn.setChecked(True)
        self.use_computed_btn = QRadioButton("Use computed score")

        self.radio_button_group = QButtonGroup()
        self.radio_button_group.addButton(self.use_suggested_btn)
        self.radio_button_group.addButton(self.use_computed_btn)
        self.radio_button_group.setExclusive(True)

        orthogonality_score_layout.addWidget(
            QLabel("Practical 2D peak capacity Calculation:")
        )
        orthogonality_score_layout.addWidget(self.use_suggested_btn)
        orthogonality_score_layout.addWidget(self.use_computed_btn)
        orthogonality_score_layout.addWidget(QLabel("Computed OM list:"))
        orthogonality_score_layout.addWidget(self.om_list)
        orthogonality_score_layout.addWidget(self.compute_score_btn)
        orthogonality_score_group.setLayout(orthogonality_score_layout)

        return orthogonality_score_group

    def _create_score_comparison_group(self) -> QGroupBox:
        """Create score comparison group for side-by-side plots.

        Returns:
            QGroupBox: Group box with score selectors.
        """
        orthogonality_compare_score_group = QGroupBox("Orthogonality score comparison")
        orthogonality_compare_score_group.setStyleSheet(self._get_group_stylesheet())

        self.om_selection_layout = QVBoxLayout()
        self.om_selection_layout.addWidget(QLabel("Number of score to compare:"))
        self.compare_number = QComboBox()
        self.compare_number.addItems(["1", "2"])
        self.om_selection_layout.addWidget(self.compare_number)
        self.om_selection_layout.addSpacing(20)

        self.om_selector1 = QComboBox()
        self.om_selector2 = QComboBox()
        self.om_selector3 = QComboBox()
        self.om_selector4 = QComboBox()
        self.om_selector2.setDisabled(True)
        self.om_selector3.setDisabled(True)
        self.om_selector4.setDisabled(True)

        self.add_dataset_selector("Select Score 1:", self.om_selector1)
        self.add_dataset_selector("Select Score 2:", self.om_selector2)
        # self.add_dataset_selector("Select Score 3:", self.om_selector3)
        # self.add_dataset_selector("Select Score 4:", self.om_selector4)

        self.om_selector_list = [
            self.om_selector1,
            self.om_selector2,
            self.om_selector3,
            self.om_selector4,
        ]

        self.om_selector_map = {
            str(i): {
                "selector": selector,
                "axe": None,
                "scatter_collection": None,
                "filtered_scatter_point": {},
            }
            for i, selector in enumerate(self.om_selector_list)
        }

        orthogonality_compare_score_group.setLayout(self.om_selection_layout)

        return orthogonality_compare_score_group

    def _create_plot_panel(self) -> QFrame:
        """Create the right plot panel for result visualization.

        Returns:
            QFrame: Plot frame containing toolbar and canvas.
        """
        plot_frame = QFrame()
        plot_frame.setStyleSheet("""
            background-color: #e7e7e7;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        plot_frame_layout = QVBoxLayout(plot_frame)
        plot_frame_layout.setContentsMargins(0, 0, 0, 0)

        plot_title = QLabel("Result visualization")
        plot_title.setFixedHeight(30)
        plot_title.setObjectName("TitleBar")
        plot_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        plot_title.setContentsMargins(10, 0, 0, 0)
        plot_title.setStyleSheet("""
            background-color: #183881;
            color: white;
            font-weight:bold;
            font-size: 16px;
            padding: 6px 12px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)

        self.fig = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = CustomToolbar(self.canvas)

        self._ax = self.canvas.figure.add_subplot(1, 1, 1)
        self._ax.set_box_aspect(1)

        plot_frame_layout.addWidget(plot_title)
        plot_frame_layout.addWidget(self.toolbar)
        plot_frame_layout.addWidget(self.canvas)

        return plot_frame

    def _create_table_section(self) -> QWidget:
        """Create the bottom table section for results display.

        Returns:
            QWidget: Table frame containing styled results table.
        """
        table_frame = QWidget()
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.styled_table = StyledTable("Final result and ranking table")
        self.styled_table.set_header_label(
            [
                "Set #",
                "2D Combination",
                "Suggested score",
                "Computed score",
                "Practical 2D peak capacity",
                "Ranking",
            ]
        )
        self.styled_table.get_header().setSectionResizeMode(0, QHeaderView.Fixed)
        self.styled_table.get_header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.styled_table.get_header().setSectionResizeMode(5, QHeaderView.Fixed)
        self.styled_table.set_default_row_count(10)

        self.custom_filter_widget = CustomFilterDialog(self)
        self.styled_table.add_header_button(
            column=1, tooltip="Custom filter", widget_to_show=self.custom_filter_widget
        )

        table_frame_layout.addWidget(self.styled_table)

        self.table_frame_shadow = BoxShadow()
        self.styled_table.setGraphicsEffect(self.table_frame_shadow)

        return table_frame

    def _create_progress_overlay(self) -> QWidget:
        """Create the progress bar overlay widget.

        Returns:
            QWidget: Transparent overlay with circular progress bar.
        """
        self.progress_bar = RoundProgressBar()
        self.progress_bar.rpb_setBarStyle("Pizza")

        progress_overlay = QWidget(self)
        progress_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        progress_overlay.setStyleSheet("background-color: transparent;")
        progress_overlay.hide()

        overlay_layout = QVBoxLayout(progress_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        overlay_layout.addStretch()

        return progress_overlay

    def _get_group_stylesheet(self) -> str:
        """Get the standard group box stylesheet.

        Returns:
            str: QSS stylesheet string for group boxes.
        """
        return f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
                border: 1px solid #d0d4da;
                border-radius: 12px;
                margin-top: 25px;
            }}
            QPushButton {{
                background-color: #d5dcf9;
                color: #2C3346;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: #bcc8f5; }}
            QPushButton:pressed {{ background-color: #8fa3ef; }}
            QPushButton:disabled {{ 
                background-color: #E5E9F5;
                color: #FFFFFF;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px;
                margin-top: -8px;
            }}
            QLabel {{
                background-color: transparent;
                color: #2C3E50;
                font-family: "Segoe UI";
                font-weight: bold;
            }}
            QRadioButton, QCheckBox {{
                background-color: transparent;
                color: #2C3E50;
                font-family: "Segoe UI";
                font-weight: bold;
            }}
            QComboBox:hover {{ border: 1px solid #a6b2c0; }}
            QComboBox::drop-down {{ border:none; }}
            QComboBox::down-arrow {{ image: url("{drop_down_icon_path}"); }}
        """

    def add_dataset_selector(self, label_text: str, combobox: QComboBox) -> None:
        """Add a labeled combo box to the score selection layout.

        Args:
            label_text (str): Label text for the combo box.
            combobox (QComboBox): The combo box widget to add.
        """
        container = QVBoxLayout()
        container.setSpacing(2)
        container.addWidget(QLabel(label_text))
        container.addWidget(combobox)
        self.om_selection_layout.addLayout(container)

    def resizeEvent(self, event) -> None:
        """Keep progress overlay synchronized with window size.

        Args:
            event: Resize event from Qt.
        """
        super().resizeEvent(event)
        self.progress_overlay.setGeometry(self.stack.geometry())

    # ==========================================================================
    # Page Initialization
    # ==========================================================================

    def init_page(self, om_list: list) -> None:
        """Initialize the page with computed metrics.

        Args:
            om_list (list): List of computed orthogonality metric names.

        Side Effects:
            - Updates metric list in checklist
            - Populates score selectors
            - Updates plot layout
            - Loads results table
            - Triggers initial plots
        """
        logging.debug("Running ResultsPage: update_orthogonality_metric_list")
        self.update_orthogonality_metric_list(om_list)

        logging.debug("Running ResultsPage: populate_om_score_selector")
        self.populate_om_score_selector()

        logging.debug("Running ResultsPage: update_om_selector_state")
        self.update_om_selector_state()

        logging.debug("Running ResultsPage: update_results_table")
        self.update_results_table()

        number_of_selectors = int(self.compare_number.currentText())
        for i in range(number_of_selectors):
            self.handle_selector_change(str(i), emit_plot=True)

    def update_orthogonality_metric_list(self, om_list: list) -> None:
        """Update the metric checklist with available metrics.

        Args:
            om_list (list): List of metric names to display.

        Side Effects:
            - Clears and repopulates om_list widget
            - Blocks signals during update
        """
        self.om_list.blockSignals(True)
        self.om_list.clear()
        self.om_list.add_items(om_list)
        self.om_list.blockSignals(False)

    def populate_om_score_selector(self) -> None:
        """Populate score selectors with available scores.

        Side Effects:
            - Updates all score selector combo boxes
            - Includes suggested, computed, and individual metric scores
        """
        om_list = self.om_list.get_items()
        om_score_list = ["Suggested score", "Computed score"] + om_list

        for data in self.om_selector_map.values():
            om_score_selector = data["selector"]
            om_score_selector.blockSignals(True)
            om_score_selector.clear()
            om_score_selector.addItems(om_score_list)
            om_score_selector.blockSignals(False)

    # ==========================================================================
    # Score Computation
    # ==========================================================================

    def start_om_computation(self) -> None:
        """Start custom orthogonality score computation in background thread.

        Side Effects:
            - Creates worker thread
            - Connects progress and finished signals
            - Starts computation in thread pool
            - Updates results when complete
        """
        worker = ResultsWorkerComputeCustomOMScore(self)
        worker.signals.progress.connect(self.handle_progress_update)
        worker.signals.finished.connect(self.handle_finished)
        self.threadpool.start(worker)

    def compute_custom_orthogonality_metric_score(self) -> None:
        """Compute custom score from checked metrics.

        Side Effects:
            - Computes weighted score from selected metrics
            - Updates practical 2D peak capacity
            - Recreates results table
        """
        metric_list = self.om_list.get_checked_items()
        self.model.compute_custom_orthogonality_score(metric_list)
        self.model.compute_practical_2d_peak_capacity()
        self.model.create_results_table()

    def handle_progress_update(self, value: int) -> None:
        """Update progress bar during computation.

        Args:
            value (int): Progress percentage (0-100).

        Side Effects:
            - Shows/hides progress overlay
            - Updates progress bar value
            - Forces UI repaint
        """
        if value == 0:
            self.progress_overlay.hide()
        else:
            self.stack.setCurrentWidget(self.progress_overlay)
            self.progress_overlay.show()
            self.progress_bar.rpb_setValue(value)
            self.progress_bar.repaint()

        if value == 100:
            self.progress_bar.repaint()

        QApplication.processEvents()

    def handle_finished(self) -> None:
        """Handle computation completion.

        Side Effects:
            - Sets progress to 100%
            - Schedules overlay hide after 800ms
            - Updates results table
            - Refreshes plots
        """
        logging.info("Computation done")
        self.progress_bar.rpb_setValue(100)
        self.progress_bar.repaint()
        QTimer.singleShot(800, self.hide_progress_overlay)

        self.update_results_table()
        self.plot_orthogonality_vs_2d_peaks()

    def hide_progress_overlay(self) -> None:
        """Hide the progress overlay and return to main view."""
        self.progress_overlay.hide()
        self.stack.setCurrentWidget(self.main_widget)

    # ==========================================================================
    # Plot Layout & Visualization
    # ==========================================================================

    def update_om_selector_state(self) -> None:
        """Enable/disable score selectors based on comparison number.

        Side Effects:
            - Enables/disables selector combo boxes
            - Updates plot layout
            - Triggers plot updates for active selectors
        """
        number_of_selectors = int(self.compare_number.currentText())

        for i, selector in enumerate(self.om_selector_list):
            selector.setDisabled(i >= number_of_selectors)

        self.update_plot_layout()

        for i in range(number_of_selectors):
            self.handle_selector_change(str(i), emit_plot=False)

    def update_plot_layout(self) -> None:
        """Reconfigure plot layout based on number of comparisons.

        Creates 1-4 subplots depending on comparison number.

        Side Effects:
            - Clears existing figure
            - Creates new subplots
            - Resets scatter collections
            - Updates om_selector_map
        """
        number_of_selectors = self.compare_number.currentText()
        plot_key = number_of_selectors + "PLOT"

        plot_layout_map = {
            "1PLOT": [111, None, None, None],
            "2PLOT": [121, 122, None, None],
            # "3PLOT": [221, 222, 223, None],
            # "4PLOT": [221, 222, 223, 224],
        }

        layout_list = plot_layout_map[plot_key]
        self.fig.clear()

        for i, layout in enumerate(layout_list):
            index = str(i)
            print('index')
            print(index)
            print('layout')
            print(layout)
            if layout is not None:
                axe = self.fig.add_subplot(layout)
                self.fig.subplots_adjust(wspace=0.5, hspace=0.5)
                axe.set_box_aspect(1)
                self.draw_figure()

                self.om_selector_map[index]["axe"] = axe
                self.om_selector_map[index]["filtered_scatter_point"] = {}
            else:
                self.om_selector_map[index]["axe"] = None
                self.om_selector_map[index]["filtered_scatter_point"] = None

    def handle_selector_change(self, index: str, emit_plot: bool = True) -> None:
        """Handle score selector change.

        Args:
            index (str): Index of the changed selector ("0"-"3").
            emit_plot (bool): Whether to trigger plot update.

        Side Effects:
            - Updates selected score and axes
            - Plots if emit_plot is True
        """
        selector = self.om_selector_map[index]["selector"]
        self.selected_score = selector.currentText()
        self.selected_axe = self.om_selector_map[index]["axe"]
        self.selected_filtered_scatter_point = self.om_selector_map[index][
            "filtered_scatter_point"
        ]

        if self.selected_axe and self.selected_score and emit_plot:
            logging.debug(
                f"Plot OM vs 2D for index {index} with score {self.selected_score}"
            )
            self.plot_orthogonality_vs_2d_peaks()

    def on_selector_changed(self, index: str) -> None:
        """Slot triggered by QComboBox.currentTextChanged.

        Args:
            index (str): Index of the changed selector.
        """
        self.handle_selector_change(index)

    def draw_figure(self) -> None:
        """Redraw the matplotlib figure canvas."""
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_orthogonality_vs_2d_peaks(self) -> None:
        """Plot selected score vs. 2D peak capacity scatter plot.

        Side Effects:
            - Removes old scatter collection if exists
            - Creates new scatter plot
            - Sets axes labels
            - Redraws canvas
        """
        if self.model.get_status() not in ["peak_capacity_loaded"]:
            return

        if not self.selected_score:
            return

        orthogonality_score_dict = self.model.get_orthogonality_score_df()
        orthogonality_score_df = pd.DataFrame.from_dict(
            orthogonality_score_dict, orient="index"
        )

        score = UI_TO_MODEL_MAPPING[self.selected_score]

        x = orthogonality_score_df[score]
        y = orthogonality_score_df["2d_peak_capacity"]

        self.selected_axe.set_xlabel(self.selected_score, fontsize=12)
        self.selected_axe.set_ylabel("Hypothetical 2D peak capacity", fontsize=12)

        if self.selected_scatter_collection in self.selected_axe.collections:
            self.selected_scatter_collection.remove()
            self.selected_scatter_collection = None

        self.selected_scatter_collection = self.selected_axe.scatter(
            x, y, s=20, color="silver", edgecolor="black", linewidths=0.9
        )

        self.fig.legend().set_visible(False)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    # ==========================================================================
    # Ranking & Filtering
    # ==========================================================================

    def set_ranking_argument(self) -> None:
        """Update ranking criterion and refresh table.

        Side Effects:
            - Sets ranking argument in model
            - Updates results table
        """
        ranking_argument = self.select_ranking_type.currentText()
        self.model.set_orthogonality_ranking_argument(ranking_argument)
        self.update_results_table()

    def set_use_suggested_om_score_flag(self) -> None:
        """Toggle between suggested and computed score.

        Side Effects:
            - Sets suggested score flag in model
            - Recomputes practical 2D peak capacity
            - Recreates results table
            - Updates table display
        """
        flag = self.use_suggested_btn.isChecked()
        self.model.suggested_om_score_flag(flag)
        self.model.compute_practical_2d_peak_capacity()
        self.model.create_results_table()
        self.update_results_table()

    def update_results_table(self) -> None:
        """Update the results table with latest data.

        Side Effects:
            - Fetches results dataframe from model
            - Loads data asynchronously into table
            - Sets up sorting/filtering proxy
        """
        data = self.model.get_orthogonality_result_df()
        self.styled_table.async_set_table_data(data)
        self.styled_table.set_table_proxy()

    def filter_table(self, regexp: str) -> None:
        """Apply custom filter to results table.

        Args:
            regexp (str): Regular expression filter pattern.

        Side Effects:
            - Applies filter to table proxy model
        """
        self.styled_table.set_proxy_filter_regexp(regexp)