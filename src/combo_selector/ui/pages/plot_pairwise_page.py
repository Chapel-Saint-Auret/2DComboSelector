"""Pairwise 2D dataset visualization page.

This module provides the PlotPairWisePage class which handles:
- Side-by-side comparison of up to 4 dataset scatter plots
- Interactive subplot selection via clicking
- Table-plot synchronization for dataset selection
- Detachable table view dialog when splitter is collapsed
- Visual feedback (blinking) for selected subplots
"""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QItemSelectionModel, QModelIndex, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.neumorphism import BoxShadow
from combo_selector.ui.widgets.orthogonality_table import OrthogonalityTableView
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

# Dropdown arrow icon path
drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")


class PlotPairWisePage(QFrame):
    """Page for visualizing and comparing 1D LC condition datasets.

    Provides an interface for:
    - Displaying 1-4 datasets side-by-side in scatter plots
    - Selecting datasets via combo boxes or table selection
    - Clicking subplots to select them for new data display
    - Visual feedback (red blink) when clicking subplots
    - Detachable table view when bottom panel is collapsed
    - Synchronized sorting and selection between main and dialog tables

    The page uses matplotlib subplots with interactive selection, allowing
    users to click on a plot area and then select a dataset from the table
    to display there.

    Attributes:
        model: Reference to the Orthogonality data model.
        fig (Figure): Matplotlib figure for rendering plots.
        canvas (FigureCanvas): Qt canvas for displaying matplotlib figure.
        dataset_selector_map (dict): Maps indices to selectors, axes, and scatter collections.
        table_view_dialog (TableViewDialog): Detachable table view dialog.
        blink_timer (QTimer): Timer for smooth subplot highlight animation.
        selected_axe: Currently selected matplotlib axes.
        selected_set (str): Currently selected dataset name.
    """

    def __init__(self, model=None):
        """Initialize the PlotPairWisePage with interactive plots and table.

        Args:
            model: Orthogonality model instance containing dataset information.

        Layout Structure:
            - Top section (side-by-side):
                - Left: Input panel (dataset selection, info, tips)
                - Right: Plot area (1-4 subplots based on comparison number)
            - Bottom section:
                - Dataset table (can be collapsed to open in separate dialog)
        """
        super().__init__()

        # --- State & timers -----------------------------------------------
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.update_blink)
        self.blink_step = 0
        self.blink_ax = None
        self.highlighted_ax = None
        self.selected_scatter_collection = None
        self.selected_axe = None
        self.selected_set = "Set 1"
        self.orthogonality_dict = None
        self.model = model

        # --- Base frame setup ---------------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP SECTION ==================================================
        top_frame = self._create_top_section()

        # === BOTTOM SECTION: Table ========================================
        table_frame = self._create_table_section()

        # === Splitter & layout ============================================
        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)
        self.main_splitter.setSizes([486, 204])
        self.main_layout.addWidget(self.main_splitter)

        # --- Signal connections -------------------------------------------
        self.compare_number.currentTextChanged.connect(
            self.update_dataset_selector_state
        )

        for index, data in self.dataset_selector_map.items():
            data["selector"].currentTextChanged.connect(
                lambda _, k=index: self.on_selector_changed(k)
            )
            data["selector"].currentTextChanged.connect(
                self.data_set_selection_changed_from_combobox
            )

        self.canvas.figure.canvas.mpl_connect("button_press_event", self.on_click)
        self.main_splitter.splitterMoved.connect(self.table_collapsed)
        self.styled_table.selectionChanged.connect(
            self.data_set_selection_changed_from_table
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
        """Create the left input panel with dataset selectors and info.

        Returns:
            QFrame: Input section containing selectors, info, and tips.
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

        # Dataset selection group
        data_selection_group = self._create_dataset_selection_group()

        # Info group
        info_group = self._create_info_group()

        # Tips group
        page_tips_group = self._create_tips_group()

        user_input_frame_layout.addWidget(data_selection_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(info_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(page_tips_group)

        return input_section

    def _create_dataset_selection_group(self) -> QGroupBox:
        """Create dataset selection group with comparison number and selectors.

        Returns:
            QGroupBox: Group box containing dataset selectors.
        """
        data_selection_group = QGroupBox("Dataset selection")
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

        self.data_selection_layout = QVBoxLayout()
        self.data_selection_layout.setSpacing(6)

        self.data_selection_layout.addWidget(QLabel("Number of data set to compare:"))
        self.compare_number = QComboBox()
        self.compare_number.addItems(["1", "2"])
        self.data_selection_layout.addWidget(self.compare_number)
        self.data_selection_layout.addSpacing(20)

        # Create 4 dataset selectors
        self.dataset_selector1 = QComboBox()
        self.dataset_selector2 = QComboBox()
        self.dataset_selector3 = QComboBox()
        self.dataset_selector4 = QComboBox()

        self.dataset_selector2.setDisabled(True)
        self.dataset_selector3.setDisabled(True)
        self.dataset_selector4.setDisabled(True)

        self.add_dataset_selector("Select data set 1:", self.dataset_selector1)
        self.add_dataset_selector("Select data set 2:", self.dataset_selector2)
        # self.add_dataset_selector("Select data set 3:", self.dataset_selector3)
        # self.add_dataset_selector("Select data set 4:", self.dataset_selector4)

        self.dataset_selector_list = [
            self.dataset_selector1,
            self.dataset_selector2,
            self.dataset_selector3,
            self.dataset_selector4,
        ]

        # Map to track selectors, axes, and scatter collections
        self.dataset_selector_map = {
            str(i): {
                "selector": selector,
                "axe": None,
                "scatter_collection": None,
            }
            for i, selector in enumerate(self.dataset_selector_list)
        }

        data_selection_group.setLayout(self.data_selection_layout)
        return data_selection_group

    def _create_info_group(self) -> QGroupBox:
        """Create info group displaying dataset statistics.

        Returns:
            QGroupBox: Group box showing number of conditions and combinations.
        """
        info_group = QGroupBox("Info")
        info_group.setStyleSheet("""
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
            QLabel {
                background-color: transparent;
                color: #3f4c5a;
            }
        """)

        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Number of conditions:"))
        self.condition_label = QLabel("---")
        info_layout.addWidget(self.condition_label)
        info_layout.addWidget(QLabel("Number of combinations:"))
        self.combination_label = QLabel("---")
        info_layout.addWidget(self.combination_label)
        info_group.setLayout(info_layout)

        return info_group

    def _create_tips_group(self) -> QGroupBox:
        """Create tips group with usage instructions.

        Returns:
            QGroupBox: Group box containing helpful tips for using the page.
        """
        page_tips_group = QGroupBox("Tips")
        page_tips_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
                border-radius: 12px;
                margin-top: 25px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px;
                margin-top: -10px;
            }
            QLabel {
                background-color: transparent;
                color: #3f4c5a;
            }
        """)

        page_tips_layout = QVBoxLayout()
        page_tips_group.setLayout(page_tips_layout)

        self.textEdit = QLabel()
        self.textEdit.setTextFormat(Qt.RichText)
        self.textEdit.setWordWrap(True)
        self.textEdit.setText(
            '<p><strong><span style="text-decoration: underline;">Tip 1</span>:</strong><br>'
            "Click on a plot area to select it, then choose a dataset from the table to display it there.</p>"
            '<p><strong><span style="text-decoration: underline;">Tip 2</span>:</strong><br>'
            "Collapse the table section by moving the horizontal splitter down—this will open the table in a separate window.</p>"
        )
        page_tips_layout.addWidget(self.textEdit)

        return page_tips_group

    def _create_plot_panel(self) -> QFrame:
        """Create the right plot panel for dataset visualization.

        Returns:
            QFrame: Plot frame containing toolbar and canvas.
        """
        plot_frame = QFrame()
        plot_frame.setFrameShape(QFrame.StyledPanel)
        plot_frame.setFrameShadow(QFrame.Raised)
        plot_frame.setStyleSheet("""
            background-color: #e7e7e7;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)

        plot_frame_layout = QVBoxLayout(plot_frame)
        plot_frame_layout.setContentsMargins(0, 0, 0, 0)

        plot_title = QLabel("2D Dataset visualization")
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

        self.fig = Figure(figsize=(15, 15))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = CustomToolbar(self.canvas)

        self._ax = self.canvas.figure.add_subplot(1, 1, 1)
        self._ax.set_box_aspect(1)

        plot_frame_layout.addWidget(plot_title)
        plot_frame_layout.addWidget(self.toolbar)
        plot_frame_layout.addWidget(self.canvas)

        return plot_frame

    def _create_table_section(self) -> QWidget:
        """Create the bottom table section for dataset information.

        Returns:
            QWidget: Table frame containing styled dataset table.
        """
        table_frame = QWidget()
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.styled_table = StyledTable("2D combination table")
        self.styled_table.set_header_label(
            [
                "Set #",
                "2D Combination",
                "Number of peaks",
                "Hypothetical 2D peak capacity",
            ]
        )
        self.styled_table.set_default_row_count(10)

        self.table_view_dialog = TableViewDialog(
            self, self.styled_table.get_table_view(), self.styled_table.get_model()
        )

        table_frame_layout.addWidget(self.styled_table)

        self.table_frame_shadow = BoxShadow()
        self.styled_table.setGraphicsEffect(self.table_frame_shadow)

        return table_frame

    def add_dataset_selector(self, label_text: str, combobox: QComboBox) -> None:
        """Add a labeled combo box to the data selection layout.

        Args:
            label_text (str): Label text for the combo box.
            combobox (QComboBox): The combo box widget to add.
        """
        container = QVBoxLayout()
        container.setSpacing(2)
        container.addWidget(QLabel(label_text))
        container.addWidget(combobox)
        self.data_selection_layout.addLayout(container)

    # ==========================================================================
    # Page Initialization
    # ==========================================================================

    def init_page(self) -> None:
        """Initialize the page with data from the model.

        Side Effects:
            - Loads orthogonality dictionary
            - Updates table with dataset combinations
            - Populates dataset selectors
            - Updates condition and combination counts
            - Configures initial plot layout
        """
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        self.update_data_set_table()
        self.populate_data_set_selectors()

        self.condition_label.setText(str(self.model.get_number_of_condition()))
        self.combination_label.setText(str(self.model.get_number_of_combination()))

        self.update_dataset_selector_state()

    def populate_data_set_selectors(self) -> None:
        """Populate dataset selectors with available sets.

        Side Effects:
            - Updates all dataset selector combo boxes
            - Blocks signals during updates to prevent loops
        """
        if not self.orthogonality_dict:
            return

        data_sets_list = list(self.orthogonality_dict.keys())

        for selector_data in self.dataset_selector_map.values():
            selector = selector_data["selector"]
            selector.blockSignals(True)
            selector.clear()
            selector.addItems(data_sets_list)
            selector.blockSignals(False)

    def update_table_peak_data(self) -> None:
        """Update table with latest peak capacity data.

        Side Effects:
            - Refreshes orthogonality dictionary
            - Updates table display
        """
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        self.update_data_set_table()

    def update_data_set_table(self) -> None:
        """Update the table view with dataset combination data.

        Side Effects:
            - Fetches combination dataframe from model
            - Loads data asynchronously into table
            - Sets up sorting/filtering proxy
        """
        data = self.model.get_combination_df()
        self.styled_table.async_set_table_data(data)
        self.styled_table.set_table_proxy()

    # ==========================================================================
    # Plot Layout & Display Management
    # ==========================================================================

    def update_dataset_selector_state(self) -> None:
        """Enable/disable dataset selectors based on comparison number.

        Side Effects:
            - Enables/disables selector combo boxes
            - Updates plot layout
            - Refreshes all active plots
        """
        number_of_selectors = int(self.compare_number.currentText())

        for i, selector in enumerate(self.dataset_selector_list):
            selector.setDisabled(i >= number_of_selectors)

        self.update_plot_layout()
        [self.on_selector_changed(str(i)) for i in range(number_of_selectors)]

    def update_plot_layout(self) -> None:
        """Reconfigure plot layout based on number of comparisons.

        Creates 1-4 subplots depending on comparison number:
        - 1: Single plot (1x1)
        - 2: Side-by-side (1x2)
        - 3: Three plots (2x2 with one position empty for 4th)
        - 4: Four plots (2x2 grid)

        Side Effects:
            - Clears existing figure
            - Creates new subplots
            - Initializes scatter collections
            - Updates dataset_selector_map
        """
        number_of_selectors = self.compare_number.currentText()
        plot_key = number_of_selectors + "PLOT"

        plot_layout_map = {
            "1PLOT": [111],
            "2PLOT": [121, 122]
            # "3PLOT": [221, 222, 223],
            # "4PLOT": [221, 222, 223, 224],
        }

        layout_list = plot_layout_map[plot_key]
        self.fig.clear()

        for i, layout in enumerate(layout_list):
            index = str(i)
            axe = self.canvas.figure.add_subplot(layout)
            self.canvas.figure.subplots_adjust(wspace=0.5, hspace=0.5)
            axe.set_box_aspect(1)
            axe.set_xlim(0, 1)
            axe.set_ylim(0, 1)

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

            self.dataset_selector_map[index]["axe"] = axe
            self.dataset_selector_map[index]["scatter_collection"] = axe.scatter(
                [], [], s=20, c="k", marker="o", alpha=0.5
            )

    def on_selector_changed(self, index: str) -> None:
        """Handle dataset selector change.

        Args:
            index (str): Index of the changed selector ("0"-"3").

        Side Effects:
            - Updates selected set, axes, and scatter collection
            - Triggers figure update
        """
        selector = self.dataset_selector_map[index]["selector"]
        self.selected_set = selector.currentText()
        self.selected_axe = self.dataset_selector_map[index]["axe"]
        self.selected_scatter_collection = self.dataset_selector_map[index][
            "scatter_collection"
        ]
        self.update_figure()

    def update_figure(self) -> None:
        """Update the current visualization based on selected dataset.

        Side Effects:
            - Plots scatter if data is available
        """
        if self.model.get_status() in ["loaded", "peak_capacity_loaded"]:
            self.plot_scatter()

    def plot_scatter(self, set_nb: str = None, dirname: str = "") -> None:
        """Plot scatter points on the selected axes.

        Args:
            set_nb (str, optional): Dataset number to plot. Defaults to selected_set.
            dirname (str, optional): Directory name (unused, for compatibility).

        Side Effects:
            - Updates scatter plot offsets
            - Sets axes labels and title
            - Redraws canvas
        """
        if self.selected_axe is None:
            return

        set_number = set_nb if set_nb is not None else self.selected_set

        x = self.orthogonality_dict[set_number]["x_values"]
        y = self.orthogonality_dict[set_number]["y_values"]
        x_title = self.orthogonality_dict[set_number]["x_title"]
        y_title = self.orthogonality_dict[set_number]["y_title"]

        self.selected_axe.set_title(set_number, fontdict={"fontsize": 10}, pad=13)
        self.selected_axe.set_xlabel(x_title, fontsize=11)
        self.selected_axe.set_ylabel(y_title, fontsize=11)
        self.selected_scatter_collection.set_offsets(list(zip(x, y)))

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    # ==========================================================================
    # Interactive Subplot Selection
    # ==========================================================================

    def on_click(self, event) -> None:
        """Detect which subplot was clicked and highlight it.

        Args:
            event: Matplotlib button press event.

        Side Effects:
            - Updates selected_axe
            - Resets previous highlight
            - Starts blink animation for clicked subplot
        """
        if event.inaxes:
            self.selected_axe = event.inaxes

            if self.highlighted_ax:
                self.highlighted_ax.patch.set_edgecolor("black")

            self.selected_axe.patch.set_linewidth(1)
            self.blink_ax = self.selected_axe
            self.blink_step = 0
            self.blink_timer.start(25)

            self.highlighted_ax = self.selected_axe

    def update_blink(self) -> None:
        """Smoothly fade the subplot border in and out.

        Side Effects:
            - Updates subplot edge color with fading alpha
            - Stops after 10 steps and resets to black
        """
        if self.blink_ax:
            alpha = abs(np.sin(self.blink_step * np.pi / 10))
            self.blink_ax.patch.set_edgecolor((1, 0, 0, alpha))
            self.canvas.figure.canvas.draw_idle()

            self.blink_step += 1
            if self.blink_step >= 10:
                self.blink_timer.stop()
                self.blink_ax.patch.set_edgecolor("black")
                self.canvas.figure.canvas.draw_idle()

    # ==========================================================================
    # Table-Plot Synchronization
    # ==========================================================================

    def table_collapsed(self) -> None:
        """Handle splitter collapse to show/hide detached table dialog.

        Side Effects:
            - Shows table_view_dialog when splitter is fully collapsed
            - Closes dialog when splitter is expanded
        """
        if self.main_splitter.sizes()[1] == 0:
            self.table_view_dialog.show()
        else:
            self.table_view_dialog.close()

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

    def data_set_selection_changed_from_combobox(self) -> None:
        """Handle dataset selection from combo box.

        Side Effects:
            - Selects corresponding table row
            - Selects row in dialog table if visible
            - Refreshes figure
        """
        index_at_row = self.get_index_from()

        if index_at_row != -1:
            self.styled_table.select_row(index=index_at_row)
            self.table_view_dialog.get_table_view().selectRow(index_at_row)

        self.update_figure()

    def data_set_selection_changed_from_table(self) -> None:
        """Handle dataset selection from table view.

        Side Effects:
            - Finds which selector corresponds to selected axes
            - Updates that selector's combo box
            - Updates selected set and refreshes figure
        """
        model_index_list = self.styled_table.get_selected_rows()

        if not model_index_list:
            return

        proxy_model = self.styled_table.get_proxy_model()
        model_index = proxy_model.mapToSource(model_index_list[0])
        self.selected_set = f"Set {model_index.data()}"

        # Find selector index for current axes
        matching_indices = [
            index
            for index, val in self.dataset_selector_map.items()
            if val["axe"] == self.selected_axe
        ]

        if matching_indices:
            index = matching_indices[0]
            selector = self.dataset_selector_map[index]["selector"]
            self.selected_axe = self.dataset_selector_map[index]["axe"]
            self.selected_scatter_collection = self.dataset_selector_map[index][
                "scatter_collection"
            ]

            selector.blockSignals(True)
            selector.setCurrentText(self.selected_set)
            selector.blockSignals(False)

            self.update_figure()


class TableViewDialog(QDialog):
    """Detachable dialog window for viewing the dataset table.

    Provides a synchronized view of the main table that can be displayed
    when the bottom splitter is collapsed. Maintains sorting and selection
    synchronization with the main table view.

    Attributes:
        parent_table_view: Reference to the main table view.
        table_view (OrthogonalityTableView): Dialog's table view.
        table_model: Reference to the shared table model.
    """

    def __init__(self, parent, parent_table_view=None, model=None):
        """Initialize the table view dialog.

        Args:
            parent: Parent widget.
            parent_table_view: Main table view to synchronize with.
            model: Shared table model.
        """
        super().__init__(parent)

        self.setWindowTitle("Data set table")
        self.setGeometry(50, 50, 500, 400)
        self.parent_table_view = parent_table_view

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.table_model = model
        self.table_view = OrthogonalityTableView(self, model)

        self.table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )

        main_layout.addWidget(self.table_view)

        # Sync sorting between both tables
        self.table_view.horizontalHeader().sectionClicked.connect(self.sync_sorting)
        self.parent_table_view.horizontalHeader().sectionClicked.connect(
            self.sync_sorting
        )

        # Sync selection changes
        self.table_view.selectionModel().selectionChanged.connect(self.sync_selection)

    def get_table_view(self):
        """Get the dialog's table view.

        Returns:
            OrthogonalityTableView: The table view widget.
        """
        return self.table_view

    def sync_sorting(self, column: int) -> None:
        """Synchronize sorting between dialog and main layout.

        Args:
            column (int): Column index that was clicked for sorting.

        Side Effects:
            - Applies sorting to both table views
        """
        sender_table = self.sender().parent()
        current_order = sender_table.horizontalHeader().sortIndicatorOrder()

        self.parent_table_view.model().sort(column, current_order)
        self.table_view.model().sort(column, current_order)

    def sync_selection(self, selected, deselected) -> None:
        """Synchronize row selection from dialog to main layout.

        Args:
            selected: Selected items.
            deselected: Deselected items.

        Side Effects:
            - Updates selection in parent table view
        """
        parent_selection_model = self.parent_table_view.selectionModel()
        parent_selection_model.clearSelection()

        for index in selected.indexes():
            row = index.row()
            parent_index = self.parent_table_view.model().index(row, 0)
            parent_selection_model.select(
                parent_index, QItemSelectionModel.Select | QItemSelectionModel.Rows
            )