"""Orthogonality metric calculation and visualization page.

This module provides the OMCalculationPage class which handles:
- Selection and computation of orthogonality metrics
- Side-by-side comparison of up to 4 metrics
- Interactive visualization of metric results
- Progress tracking with circular progress bar overlay
- Results table display with sorting and filtering
"""

from functools import partial

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from combo_selector.core.orthogonality import Orthogonality
from combo_selector.core.plot_utils import PlotUtils
from combo_selector.core.workers import OMWorkerComputeOM, OMWorkerUpdateNumBin
from combo_selector.ui.widgets.checkable_tree_list import CheckableTreeList
from combo_selector.ui.widgets.circle_progress_bar import RoundProgressBar
from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.neumorphism import BoxShadow
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

# Dropdown arrow icon path
drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")

# Maps metric names (from model) to plot visualization names
METRIC_PLOT_MAP = {
    "Convex hull relative area": "Convex Hull",
    "Bin box counting": "Bin Box",
    "Pearson Correlation": "Linear regression",
    "Spearman Correlation": "Linear regression",
    "Kendall Correlation": "Linear regression",
    "Asterisk equations": "Asterisk",
    "%FIT": "%FIT yx",
    "%BIN": "%BIN",
    "Gilar-Watson method": None,  # No visualization
    "Modeling approach": "Modeling approach",
    "Geometric approach": "Geometric approach",
    "Conditional entropy": "Conditional entropy",
    "NND Arithm mean": None,  # No visualization
    "NND Geom mean": None,  # No visualization
    "NND Harm mean": None,  # No visualization
    "NND mean": None,  # No visualization
}


class OMCalculationPage(QFrame):
    """Page for computing and visualizing orthogonality metrics.

    Provides a comprehensive interface for:
    - Selecting metrics to compute from a checklist
    - Computing metrics in background threads with progress tracking
    - Comparing 1-4 metrics side-by-side
    - Interactive selection of data sets
    - Adjusting bin numbers for grid-based metrics
    - Viewing computed results in a sortable table

    The page uses a stacked layout to overlay a progress indicator during
    long-running computations, keeping the UI responsive.

    Attributes:
        model (Orthogonality): Data model containing chromatography data.
        thread pool (QThreadPool): Thread pool for background computations.
        plot_utils (PlotUtils): Utility for generating metric visualizations.
        om_selector_map (dict): Maps plot indices to selectors and axes.
        selected_metric_list (list): Currently computed metric names.
        progress_overlay (QWidget): Transparent overlay showing progress bar.

    Signals:
        metric_computed (list): Emitted when metrics finish computing.
                               Carries [metric_names, plot_names].
        gui_update_requested: Emitted when GUI update is needed (unused).
    """

    metric_computed = Signal(list)
    gui_update_requested = Signal()

    def __init__(self, model: Orthogonality = None) -> None:
        """Initialize the OMCalculationPage with controls and visualizations.

        Args:
            model (Orthogonality, optional): Data model instance.

        Layout Structure:
            - Top section (side-by-side):
                - Left: Input panel (metric selection, bin number, display options)
                - Right: Plot area (1-4 subplots based on comparison number)
            - Bottom section:
                - Results table showing computed metric values
            - Overlay:
                - Circular progress bar during computations
        """
        super().__init__()

        # --- Model & state ------------------------------------------------
        self.model = model
        self.selected_metric_list = []
        self.threadpool = QThreadPool()
        self.selected_metric = None
        self.selected_set = "Set 1"
        self.orthogonality_dict = {}

        # --- Plotting setup -----------------------------------------------
        self.fig = Figure(figsize=(15, 15))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = CustomToolbar(self.canvas)

        self.selected_axe = self.canvas.figure.add_subplot(1, 1, 1)
        self.selected_axe.set_box_aspect(1)
        self.selected_axe.set_xlim(0, 1)
        self.selected_axe.set_ylim(0, 1)

        self.plot_utils = PlotUtils(fig=self.fig)
        self.plot_functions_map = {
            "Convex Hull": partial(self.plot_convex_hull),
            "Bin Box": partial(self.plot_bin_box),
            "Linear regression": partial(self.plot_linear_reg),
            "Asterisk": partial(self.plot_utils.plot_asterisk),
            "%FIT xy": partial(self.plot_utils.plot_percent_fit_xy),
            "%FIT yx": partial(self.plot_utils.plot_percent_fit_yx),
            "%BIN": partial(self.plot_utils.plot_percent_bin),
            "Modeling approach": partial(self.plot_utils.plot_modeling_approach),
            "Conditional entropy": partial(self.plot_utils.plot_conditional_entropy),
        }

        # --- Base frame & main container ----------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP AREA =====================================================
        top_frame = self._create_top_section()

        # === BOTTOM AREA: table ===========================================
        table_frame = self._create_table_section()

        # === Overlay (progress) ===========================================
        self.progress_overlay = self._create_progress_overlay()

        # === Splitter + stacking ==========================================
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

        # --- Signal wiring ------------------------------------------------
        self.compare_number.currentTextChanged.connect(self.update_om_selector_state)
        for index, data in self.om_selector_map.items():
            data["selector"].currentTextChanged.connect(
                lambda _, k=index: self.on_selector_changed(k)
            )
        self.om_calculate_btn.clicked.connect(self.compute_orthogonality_metric)
        self.nb_bin.editingFinished.connect(self.update_bin_box_number)
        self.dataset_selector.currentTextChanged.connect(
            self.data_set_selection_changed_from_combobox
        )

    def _create_top_section(self) -> QFrame:
        """Create the top section with input panel and plot area.

        Returns:
            QFrame: Configured top frame with input and plot sections.
        """
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        # Left: Input card
        input_section = self._create_input_panel()

        # Right: Plot card
        plot_frame = self._create_plot_panel()

        # Assemble
        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)

        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        return top_frame

    def _create_input_panel(self) -> QFrame:
        """Create the left input panel with metric selection and options.

        Returns:
            QFrame: Input section containing metric checklist and selectors.
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

        # OM calculation group
        om_computing_group = self._create_om_calculation_group()

        # OM selection group
        data_selection_group = self._create_om_selection_group()

        user_input_frame_layout.addWidget(om_computing_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(data_selection_group)

        return input_section

    def _create_om_calculation_group(self) -> QGroupBox:
        """Create the OM calculation group with metric checklist.

        Returns:
            QGroupBox: Group box containing metric checklist and compute button.
        """
        om_computing_group = QGroupBox("OM calculation")
        om_calculation_layout = QVBoxLayout()
        om_computing_group.setLayout(om_calculation_layout)
        om_computing_group.setStyleSheet("""
             QGroupBox {
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
                border: 1px solid #d0d4da;
                border-radius: 12px;
                margin-top: 25px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px;
                margin-top: -8px;
            }
            QPushButton {
                background-color: #d5dcf9;
                color: #2C3346;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #bcc8f5; }
            QPushButton:pressed { background-color: #8fa3ef; }
            QPushButton:disabled { background-color: #E5E9F5; color: #FFFFFF; }
            QLabel { background-color: transparent; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #154E9D;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #154E9D;
                border: 1px solid #154E9D;
            }
            QLabel#sub-title {
                background-color: transparent;
                color: #2C3E50;
                font-family: "Segoe UI";
                font-weight: bold;
            }
        """)

        metric_list = [
            "Convex hull relative area",
            "Bin box counting",
            "Gilar-Watson method",
            "Modeling approach",
            "Conditional entropy",
            "Pearson Correlation",
            "Spearman Correlation",
            "Kendall Correlation",
            "Asterisk equations",
            "NND Arithm mean",
            "NND Geom mean",
            "NND Harm mean",
            "%FIT",
            "%BIN",
        ]
        self.om_tree_list = CheckableTreeList(metric_list)
        self.om_tree_list.setFixedHeight(175)
        self.om_calculate_btn = QPushButton("Compute metrics")

        self.footnote = QLabel()
        self.footnote.setTextFormat(Qt.TextFormat.RichText)
        self.footnote.setWordWrap(True)
        self.footnote.setText("<strong>NND</strong>: Nearest Neighbor Distance")
        self.footnote.setStyleSheet("font-size: 8pt;")

        number_of_bin_layout = QHBoxLayout()
        self.nb_bin = QSpinBox()
        self.nb_bin.setFixedWidth(100)
        self.nb_bin.setValue(14)
        self.nb_bin_label = QLabel("Number of bin box:")
        self.nb_bin_label.setObjectName("sub-title")
        number_of_bin_layout.addWidget(self.nb_bin_label)
        number_of_bin_layout.addWidget(self.nb_bin)

        select_metric_title = QLabel("Select metrics to compute:")
        select_metric_title.setObjectName("sub-title")

        om_calculation_layout.addWidget(select_metric_title)
        om_calculation_layout.addWidget(self.om_tree_list)
        om_calculation_layout.addWidget(self.footnote)
        om_calculation_layout.addSpacing(15)
        om_calculation_layout.addLayout(number_of_bin_layout)
        om_calculation_layout.addSpacing(15)
        om_calculation_layout.addWidget(self.om_calculate_btn)

        return om_computing_group

    def _create_om_selection_group(self) -> QGroupBox:
        """Create the OM selection group for comparing metrics.

        Returns:
            QGroupBox: Group box with dataset and metric selectors.
        """
        data_selection_group = QGroupBox("OM selection")
        data_selection_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
                border: 1px solid #d0d4da;
                border-radius: 12px;
                margin-top: 25px;
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
            QComboBox::drop-down {{ border:none; }}
            QComboBox::down-arrow {{
                image: url("{drop_down_icon_path}");
            }}
        """)

        self.om_selection_layout = QVBoxLayout()
        self.om_selection_layout.setSpacing(6)

        self.om_selection_layout.addWidget(QLabel("Number of metric to compare:"))
        self.compare_number = QComboBox()
        self.compare_number.addItems(["1", "2"])
        self.om_selection_layout.addWidget(self.compare_number)
        self.om_selection_layout.addSpacing(20)

        self.om_selection_layout.addWidget(QLabel("Select data set:"))
        self.dataset_selector = QComboBox()
        self.om_selection_layout.addWidget(self.dataset_selector)

        # Create 4 metric selectors
        self.om_selector1 = QComboBox()
        self.om_selector2 = QComboBox()
        self.om_selector3 = QComboBox()
        self.om_selector4 = QComboBox()
        self.om_selector2.setDisabled(True)
        self.om_selector3.setDisabled(True)
        self.om_selector4.setDisabled(True)

        self.add_dataset_selector("Select OM 1:", self.om_selector1)
        self.add_dataset_selector("Select OM 2:", self.om_selector2)
        # self.add_dataset_selector("Select OM 3:", self.om_selector3)
        # self.add_dataset_selector("Select OM 4:", self.om_selector4)

        self.om_selector_list = [
            self.om_selector1,
            self.om_selector2
            # self.om_selector3,
            # self.om_selector4,
        ]

        # Map to track selector, axes, and scatter collections
        self.om_selector_map = {
            str(i): {
                "selector": selector,
                "axe": None,
                "scatter_collection": None,
            }
            for i, selector in enumerate(self.om_selector_list)
        }

        data_selection_group.setLayout(self.om_selection_layout)
        return data_selection_group

    def _create_plot_panel(self) -> QFrame:
        """Create the right plot panel for metric visualization.

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

        plot_title = QLabel("OM visualization")
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

        self.styled_table = StyledTable("OM result table")
        self.styled_table.set_header_label(
            ["Set #", "2D Combination", "OM 1", "OM 2", "...", "OM n"]
        )
        self.styled_table.set_default_row_count(10)
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

    def add_dataset_selector(self, label_text: str, combobox: QComboBox) -> None:
        """Add a labeled combo box to the OM selection layout.

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
    # Worker Thread Management
    # ==========================================================================

    def start_om_computation(self, metric_list: list) -> None:
        """Start orthogonality metric computation in background thread.

        Args:
            metric_list (list): List of metric names to compute.

        Side Effects:
            - Creates worker thread
            - Connects progress and finished signals
            - Starts computation in thread pool
        """
        worker = OMWorkerComputeOM(metric_list, self.model)
        worker.signals.progress.connect(self.handle_progress_update)
        worker.signals.finished.connect(self.handle_finished)
        self.threadpool.start(worker)

    def handle_progress_update(self, value: int) -> None:
        """Update progress bar during computation.

        Args:
            value (int): Progress percentage (0-100).

        Side Effects:
            - Shows/hides progress overlay
            - Updates progress bar value
            - Forces UI repaint
        """
        if not self.om_tree_list.get_checked_items():
            return

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
            - Refreshes plot displays
            - Emits metric_computed signal
        """
        if not self.om_tree_list.get_checked_items():
            return

        self.progress_bar.rpb_setValue(100)
        self.progress_bar.repaint()
        QTimer.singleShot(800, self.hide_progress_overlay)

        self.update_orthogonality_table()
        self.data_sets_change()
        self.metric_computed.emit(
            [self.om_tree_list.get_checked_items(), self.selected_metric_list]
        )

    def hide_progress_overlay(self) -> None:
        """Hide the progress overlay and return to main view."""
        self.progress_overlay.hide()
        self.stack.setCurrentWidget(self.main_widget)

    # ==========================================================================
    # Page Initialization & Updates
    # ==========================================================================

    def init_page(self) -> None:
        """Initialize the page with fresh data.

        Side Effects:
            - Clears metric selections
            - Resets table
            - Loads orthogonality data
            - Resets computation state
            - Populates selectors
        """
        self.om_tree_list.unchecked_all()
        self.styled_table.clean_table()
        self.styled_table.set_header_label(
            ["Set #", "2D Combination", "OM 1", "OM 2", "...", "OM n"]
        )
        self.plot_utils.set_orthogonality_data(self.model.get_orthogonality_dict())
        self.model.reset_om_status_computation_state()
        self.populate_selector()
        self.update_om_selector_state()

    def populate_selector(self) -> None:
        """Populate dataset selector with available sets.

        Side Effects:
            - Updates dataset_selector combo box
            - Clears metric selectors
            - Blocks signals during updates
        """
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        if not self.orthogonality_dict:
            return

        data_sets_list = list(self.orthogonality_dict.keys())

        self.dataset_selector.blockSignals(True)
        self.dataset_selector.clear()
        self.dataset_selector.addItems(data_sets_list)
        self.dataset_selector.blockSignals(False)

        # Clear metric selectors
        for data in self.om_selector_map.values():
            om_selector = data["selector"]
            om_selector.blockSignals(True)
            om_selector.clear()
            om_selector.blockSignals(False)

    def compute_orthogonality_metric(self) -> None:
        """Begin orthogonality metric computation.

        Side Effects:
            - Shows progress overlay
            - Starts worker thread
            - Updates metric selectors with plot names
            - Filters and deduplicates metric list
        """
        self.selected_metric_list = self.om_tree_list.get_checked_items()

        self.stack.setCurrentWidget(self.progress_overlay)
        self.progress_overlay.show()
        self.progress_bar.rpb_setValue(0)
        self.progress_bar.repaint()
        QApplication.processEvents()

        self.start_om_computation(self.selected_metric_list)

        # Convert to plot names
        self.selected_metric_list = [
            METRIC_PLOT_MAP[metric] for metric in self.selected_metric_list
        ]

        # Remove None and duplicates
        self.selected_metric_list = [
            metric for metric in self.selected_metric_list if metric
        ]
        self.selected_metric_list = list(dict.fromkeys(self.selected_metric_list))

        # Update selectors
        for data in self.om_selector_map.values():
            om_selector = data["selector"]
            om_selector.blockSignals(True)
            om_selector.clear()
            om_selector.addItems(self.selected_metric_list)
            om_selector.blockSignals(False)

    def update_bin_box_number(self) -> None:
        """Update the number of bins for grid-based metrics.

        Side Effects:
            - Updates model's bin_number
            - Invalidates bin-dependent metrics
        """
        self.model.update_num_bins(self.nb_bin.value())

    def update_orthogonality_table(self) -> None:
        """Update the results table with computed metric values.

        Side Effects:
            - Fetches data from model
            - Updates table headers
            - Loads data asynchronously
            - Sets up filtering proxy
        """
        data = self.model.get_orthogonality_metric_df()
        self.styled_table.set_header_label(list(data.columns))
        self.styled_table.async_set_table_data(data)
        self.styled_table.set_table_proxy()

    # ==========================================================================
    # Plot Layout & Display Management
    # ==========================================================================

    def update_om_selector_state(self) -> None:
        """Enable/disable metric selectors based on comparison number.

        Side Effects:
            - Enables/disables selector combo boxes
            - Updates plot layout
            - Refreshes displayed plots
        """
        number_of_selectors = int(self.compare_number.currentText())

        for i, selector in enumerate(self.om_selector_list):
            selector.setDisabled(i >= number_of_selectors)

        self.update_plot_layout()
        self.refresh_displayed_plot()

    def update_plot_layout(self) -> None:
        """Reconfigure plot layout based on number of comparisons.

        Creates 1-4 subplots depending on comparison number:
        - 1: Single plot (1x1)
        - 2: Side-by-side (1x2)
        - 3: Three plots (2x2 with one empty)
        - 4: Four plots (2x2 grid)

        Side Effects:
            - Clears existing figure
            - Creates new subplots
            - Initializes scatter collections
            - Updates om_selector_map
        """
        number_of_selectors = self.compare_number.currentText()
        plot_key = number_of_selectors + "PLOT"

        plot_layout_map = {
            "1PLOT": [111, None, None, None],
            "2PLOT": [121, 122, None, None]
            # "3PLOT": [221, 222, 223, None],
            # "4PLOT": [221, 222, 223, 224],
        }

        layout_list = plot_layout_map[plot_key]
        self.fig.clear()

        for i, layout in enumerate(layout_list):
            index = str(i)
            if layout is not None:
                axe = self.fig.add_subplot(layout)
                self.fig.subplots_adjust(wspace=0.5, hspace=0.5)
                axe.set_box_aspect(1)
                axe.set_xlim(0, 1)
                axe.set_ylim(0, 1)

                self.draw_figure()

                self.om_selector_map[index]["axe"] = axe
                self.om_selector_map[index]["scatter_collection"] = axe.scatter(
                    [], [], s=20, c="k", marker="o", alpha=0.5
                )
            else:
                self.om_selector_map[index]["axe"] = None
                self.om_selector_map[index]["scatter_collection"] = None

    def on_selector_changed(self, index: str) -> None:
        """Handle metric selector change.

        Args:
            index (str): Index of the changed selector ("0"-"3").

        Side Effects:
            - Updates selected metric
            - Configures plot_utils for correct axes
            - Triggers figure update
        """
        selector = self.om_selector_map[index]["selector"]
        self.selected_metric = selector.currentText()
        self.plot_utils.set_axe(self.om_selector_map[index]["axe"])
        self.plot_utils.set_scatter_collection(
            self.om_selector_map[index]["scatter_collection"]
        )
        self.update_figure()

    def refresh_displayed_plot(self) -> None:
        """Refresh all displayed plots based on current selections.

        Side Effects:
            - Calls on_selector_changed for each active selector
        """
        number_of_selectors = int(self.compare_number.currentText())
        [self.on_selector_changed(str(i)) for i in range(number_of_selectors)]

    def draw_figure(self) -> None:
        """Redraw the matplotlib figure canvas."""
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update_figure(self) -> None:
        """Update the figure with scatter plot and selected metric overlay.

        Side Effects:
            - Cleans current axes
            - Plots base scatter
            - Overlays selected metric visualization
        """
        if self.selected_axe is None:
            return

        self.plot_utils.clean_figure()

        if self.model.get_status() in ["loaded", "peak_capacity_loaded"]:
            self.plot_utils.plot_scatter()
        else:
            return

        if self.selected_metric is None:
            return

        if self.selected_metric in self.plot_functions_map:
            self.plot_functions_map[self.selected_metric]()

    # ==========================================================================
    # Dataset Selection Handlers
    # ==========================================================================

    def data_sets_change(self, data_set: str = None) -> None:
        """Handle dataset selection change.

        Args:
            data_set (str, optional): Dataset name to switch to.
                                     If None, uses dataset_selector value.

        Side Effects:
            - Updates selected_set
            - Synchronizes table and combo box selections
            - Refreshes plot display
        """
        if data_set is None:
            self.selected_set = self.dataset_selector.currentText()
            index_at_row = self.get_index_from()

            self.styled_table.get_table_view().blockSignals(True)
            self.styled_table.get_table_view().selectionModel().blockSignals(True)
            self.styled_table.get_table_view().selectRow(index_at_row)
            self.styled_table.get_table_view().blockSignals(False)
            self.styled_table.get_table_view().selectionModel().blockSignals(False)
        else:
            self.selected_set = data_set
            self.dataset_selector.blockSignals(True)
            self.dataset_selector.setCurrentText(self.selected_set)
            self.dataset_selector.blockSignals(False)

        self.plot_utils.set_set_number(self.selected_set)
        self.refresh_displayed_plot()

    def data_set_selection_changed_from_combobox(self) -> None:
        """Handle dataset selection from combo box.

        Side Effects:
            - Updates selected_set
            - Selects corresponding table row
            - Refreshes plot display
        """
        self.selected_set = self.dataset_selector.currentText()
        index_at_row = self.get_index_from()

        if index_at_row != -1:
            self.styled_table.get_table_view().selectionModel().blockSignals(True)
            self.styled_table.select_row(index_at_row)
            self.styled_table.get_table_view().selectionModel().blockSignals(True)

        self.plot_utils.set_set_number(self.selected_set)
        self.refresh_displayed_plot()

    def get_index_from(self) -> int:
        """Get table row index for currently selected dataset.

        Returns:
            int: Row index, or -1 if not found.
        """
        row_count = self.styled_table.get_row_count()

        for row in range(row_count):
            model_index = self.styled_table.get_proxy_model().index(row, 0)
            if f"Set {model_index.data()}" == self.selected_set:
                return row

        return -1

    # ==========================================================================
    # Plot Wrapper Methods
    # ==========================================================================

    def plot_convex_hull(self) -> None:
        """Plot convex hull visualization."""
        self.plot_utils.plot_convex_hull()

    def plot_bin_box(self) -> None:
        """Plot bin box counting visualization."""
        self.plot_utils.plot_bin_box()

    def plot_linear_reg(self) -> None:
        """Plot linear regression with correlations."""
        self.plot_utils.plot_linear_reg()