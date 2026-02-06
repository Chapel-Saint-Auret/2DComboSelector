from functools import partial

from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QComboBox, QFrame, QPushButton, QGroupBox, QMessageBox,
    QSizePolicy, QSplitter, QSpinBox, QScrollArea,
    QGraphicsDropShadowEffect, QStackedLayout
)
from PySide6.QtCore import Qt, QModelIndex, QSize, Signal, QThreadPool, QTimer
from PySide6.QtGui import QColor, QIcon

import matplotlib as mpl
from matplotlib import collections
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas

from combo_selector.utils import resource_path
from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.core.plot_utils import PlotUtils
from combo_selector.core.orthogonality import Orthogonality
from combo_selector.core.workers import OMWorkerComputeOM, OMWorkerUpdateNumBin
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.circle_progress_bar import RoundProgressBar
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.ui.widgets.checkable_tree_list import CheckableTreeList
from combo_selector.ui.widgets.neumorphism import*

PLOT_SIZE = QSize(600, 400)
ICON_SIZE = QSize(28, 28)
drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")


METRIC_PLOT_MAP = {
    "Convex hull relative area": "Convex Hull",
    "Bin box counting": "Bin Box",
    "Pearson Correlation": "Linear regression",
    "Spearman Correlation": "Linear regression",
    "Kendall Correlation": "Linear regression",
    "Asterisk equations": "Asterisk",
    "%FIT": "%FIT yx",
    "%BIN": "%BIN",
    "Gilar-Watson method": None,
    "Modeling approach": "Modeling approach",
    "Geometric approach": "Geometric approach",
    "Conditional entropy": "Conditional entropy",
    "NND Arithm mean": None,
    "NND Geom mean": None,
    "NND Harm mean": None,
    "NND mean": None
}

class OMCalculationPage(QFrame):
    metric_computed = Signal(list)
    gui_update_requested = Signal()

    def __init__(self, model: Orthogonality = None) -> None:
        """
        Initialize the OMCalculationPage.

        Layout:
          - Top: input (left) + OM visualization (right)
          - Bottom: OM result table
          - Overlay: circular progress bar during computations
        """
        super().__init__()

        # --- model & state ----------------------------------------------------
        self.model = model
        self.selected_metric_list = []
        self.threadpool = QThreadPool()
        self.selected_scatter_collection = None
        self.selected_metric = None  # First metric in the list
        self.artist_list = []
        self.arrow_list = []
        self.selected_set = "Set 1"
        self.orthogonality_dict = {}

        # --- plotting setup ---------------------------------------------------
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

        # --- base frame & main container -------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP AREA =========================================================
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        # ----- Left: Input card ----------------------------------------------
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

        # OM calculation group (stylesheet unchanged)
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
            QPushButton:hover {
                background-color: #bcc8f5;
            }
            QPushButton:pressed {
                background-color: #8fa3ef;
            }
            QPushButton:disabled {
                background-color: #E5E9F5;
                color: #FFFFFF;
            }
                           QLabel {
            background-color: transparent;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #154E9D;
                border-radius: 3px;
                background: white;
            }

            QCheckBox::indicator:checked {
                background: #154E9D;
                border: 1px solid #154E9D;
            }

            QCheckBox::indicator:unchecked {
                background: white;
                border: 1px solid #154E9D;
            }

            QCheckBox::indicator:disabled {
                background: #d0d0d0;
                border: 1px solid #b0b0b0;
            }

             QLabel#sub-title {
            background-color: transparent;
            color: #2C3E50;
            font-family: "Segoe UI";
            font-weight: bold;
            }
        """)

        metric_list = [
            "Convex hull relative area", "Bin box counting", "Gilar-Watson method",
            "Modeling approach", "Conditional entropy", "Pearson Correlation",
            "Spearman Correlation", "Kendall Correlation", "Asterisk equations",
            "NND Arithm mean", "NND Geom mean", "NND Harm mean", "%FIT", "%BIN"
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

        # OM selection group (stylesheet unchanged)
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


            QComboBox::drop-down {{
                border:none;
            }}

            QComboBox::down-arrow {{
                image: url("{drop_down_icon_path}");
            }}

        """)

        self.om_selection_layout = QVBoxLayout()
        self.om_selection_layout.setSpacing(6)
        self.om_selection_layout.addWidget(QLabel("Number of metric to compare:"))
        self.compare_number = QComboBox()
        self.compare_number.addItems(["1", "2", "3", "4"])
        self.om_selection_layout.addWidget(self.compare_number)
        self.om_selection_layout.addSpacing(20)

        self.om_selection_layout.addWidget(QLabel("Select data set:"))
        self.dataset_selector = QComboBox()
        self.om_selection_layout.addWidget(self.dataset_selector)

        self.om_selector1 = QComboBox()
        self.om_selector2 = QComboBox()
        self.om_selector3 = QComboBox()
        self.om_selector4 = QComboBox()
        self.om_selector2.setDisabled(True)
        self.om_selector3.setDisabled(True)
        self.om_selector4.setDisabled(True)

        self.add_dataset_selector("Select OM 1:", self.om_selector1)
        self.add_dataset_selector("Select OM 2:", self.om_selector2)
        self.add_dataset_selector("Select OM 3:", self.om_selector3)
        self.add_dataset_selector("Select OM 4:", self.om_selector4)

        self.om_selector_list = [self.om_selector1, self.om_selector2, self.om_selector3, self.om_selector4]
        self.om_selector_map = {
            "0": {"selector": self.om_selector1, "axe": None, "scatter_collection": None},
            "1": {"selector": self.om_selector2, "axe": None, "scatter_collection": None},
            "2": {"selector": self.om_selector3, "axe": None, "scatter_collection": None},
            "3": {"selector": self.om_selector4, "axe": None, "scatter_collection": None},
        }

        data_selection_group.setLayout(self.om_selection_layout)

        # (Optional) Tips group (stylesheet unchanged; currently not added to layout)
        page_tips_group = QGroupBox("Tips")
        page_tips_group.setStyleSheet("""
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
        """)
        page_tips_layout = QVBoxLayout()
        self.textEdit = QLabel()
        self.textEdit.setTextFormat(Qt.TextFormat.RichText)
        self.textEdit.setWordWrap(True)
        page_tips_layout.addWidget(self.textEdit)
        page_tips_group.setLayout(page_tips_layout)

        user_input_frame_layout.addWidget(om_computing_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(data_selection_group)
        # user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        # user_input_frame_layout.addWidget(page_tips_group)

        # ----- Right: Plot card (styles unchanged) ----------------------------
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
            font-weight: bold;
            padding: 6px 12px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        plot_frame_layout.addWidget(plot_title)
        plot_frame_layout.addWidget(self.toolbar)
        plot_frame_layout.addWidget(self.canvas)

        # Assemble top row
        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)
        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        # === BOTTOM AREA: table ===============================================
        table_frame = QWidget()
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.styled_table = StyledTable("OM result table")
        self.styled_table.set_header_label(["Set #", "2D Combination", "OM 1", "OM 2", "...", "OM n"])
        self.styled_table.set_default_row_count(10)
        table_frame_layout.addWidget(self.styled_table)

        self.table_frame_shadow = BoxShadow()
        self.styled_table.setGraphicsEffect(self.table_frame_shadow)

        # === Overlay (progress) ===============================================
        self.progress_bar = RoundProgressBar()
        self.progress_bar.rpb_setBarStyle("Pizza")

        self.progress_overlay = QWidget(self)
        self.progress_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.progress_overlay.setStyleSheet("background-color: transparent;")
        self.progress_overlay.hide()

        overlay_layout = QVBoxLayout(self.progress_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        overlay_layout.addStretch()

        # === Splitter + stacking ==============================================
        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)
        self.main_splitter.setSizes([486, 204])
        self.main_layout.addWidget(self.main_splitter)

        self.stack = QStackedLayout()
        self.stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.stack.addWidget(self.main_widget)
        self.stack.addWidget(self.progress_overlay)
        self.stack.setCurrentWidget(self.progress_overlay)  # default view

        self.base_layout = QVBoxLayout(self)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.addLayout(self.stack)

        self.progress_overlay.setGeometry(self.stack.geometry())
        self.progress_overlay.raise_()

        # --- signal wiring ----------------------------------------------------
        self.compare_number.currentTextChanged.connect(self.update_om_selector_state)
        for index, data in self.om_selector_map.items():
            data["selector"].currentTextChanged.connect(lambda _, k=index: self.on_selector_changed(k))
        self.om_calculate_btn.clicked.connect(self.compute_orthogonality_metric)
        self.nb_bin.editingFinished.connect(self.update_bin_box_number)
        self.dataset_selector.currentTextChanged.connect(self.data_set_selection_changed_from_combobox)
        # self.styled_table.selectionChanged.connect(self.data_set_selection_changed_from_table)

    def add_dataset_selector(self,label_text, combobox):
        container = QVBoxLayout()
        container.setSpacing(2)
        container.addWidget(QLabel(label_text))
        container.addWidget(combobox)
        self.om_selection_layout.addLayout(container)

    # Override resizeEvent to keep overlay in sync
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.progress_overlay.setGeometry(self.stack.geometry())

    def start_om_computation(self, metric_list):
        worker = OMWorkerComputeOM(metric_list, self.model)

        worker.signals.progress.connect(self.handle_progress_update)
        worker.signals.finished.connect(self.handle_finished)

        self.threadpool.start(worker)

    def start_update_bin_number(self,nb_bin):
        checked_metric_list = self.om_tree_list.get_checked_items()

        #TODO this was to only compute the metric if any of these metric were selected
        # remove the threading if not necessary

        if any(metric in checked_metric_list \
               for metric in ["Bin box counting", "Modeling approach", "Gilar-Watson method"]):

            worker = OMWorkerUpdateNumBin(nb_bin,checked_metric_list, self.model)

            worker.signals.progress.connect(self.handle_progress_update)

            #TODO find a better way to compute the metric once bin number has been updated
            # this is commented because this call this will update table and trigger computed_metric signal
            # the issue is that when bin number is updated, I should find a way to compute metric if they have at least
            # been computed once otherwise it means I compute the metric without clicking on compute metric button
            # worker.signals.finished.connect(self.handle_finished)


            self.threadpool.start(worker)
        else:
            return

    def handle_progress_update(self, value: int):
        if self.om_tree_list.get_checked_items():

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
        else:
            return

    def handle_finished(self):
        if self.om_tree_list.get_checked_items():
            self.progress_bar.rpb_setValue(100)  # Final visual update
            self.progress_bar.repaint()
            QTimer.singleShot(800, self.hide_progress_overlay)

            self.update_orthogonality_table()
            self.data_sets_change()
            self.metric_computed.emit([self.om_tree_list.get_checked_items(), self.selected_metric_list])
        else:
            return

    def hide_progress_overlay(self):
        self.progress_overlay.hide()
        self.stack.setCurrentWidget(self.main_widget)

    def init_page(self):
        self.om_tree_list.unchecked_all()
        self.styled_table.clean_table()
        self.styled_table.set_header_label(["Set #", "2D Combination", "OM 1", "OM 2", "...", "OM n"])
        # self.styled_table.set_table_data(pd.DataFrame())
        self.plot_utils.set_orthogonality_data(self.model.get_orthogonality_dict())
        self.model.reset_om_status_computation_state()
        self.populate_selector()
        self.update_om_selector_state()

    def clear_axis_except_pathcollections(self,ax):
        """Clear all elements from the axis except PathCollection objects (e.g., scatter plots)."""

        # Remove all lines
        for line in ax.get_lines():
            line.remove()

        for text in ax.texts:
            text.remove()

        # Remove all QuadMesh objects (used in pcolormesh, heatmaps)
        for quadmesh in ax.findobj(mpl.collections.QuadMesh):
            quadmesh.remove()

        # Remove all artists except PathCollection (scatter plots)
        for artist in ax.get_children():
            if isinstance(artist, mpl.legend.Legend):
                artist.remove()  # Remove legend
            elif isinstance(artist, mpl.axis.Axis):
                artist.set_visible(False)  # Hide ticks/labels

        # Refresh the figure
        # ax.figure.canvas.draw_idle()

    def update_om_selector_state(self):

        #TODO number_of_selector should be a class attribute (when compare_number currentTextChanged)
        number_of_selectors = int(self.compare_number.currentText())


        [self.om_selector_list[i].setDisabled(False) if i<number_of_selectors
         else self.om_selector_list[i].setDisabled(True) for i,selector in enumerate(self.om_selector_list)]

        self.update_plot_layout()

        self.refresh_displayed_plot()



    def update_plot_layout(self):
        #get the number of plot to compare
        number_of_selectors = self.compare_number.currentText()

        #create a key string based on the compare number value in order to know which ploy layout to select
        plot_key = number_of_selectors+'PLOT'


        # plot layout map that contains the list of plot layout to display based on the compare number
        plot_layout_map = {'1PLOT':[111,None,None,None],
                       '2PLOT':[121,122,None,None],
                       '3PLOT':[221,222,223,None],
                       '4PLOT':[221,222,223,224]}

        #get list of layout
        layout_list = plot_layout_map[plot_key]

        self.fig.clear()
        # self.remove_all_axes()

        for i,layout in enumerate(layout_list):
            index = str(i)
            #initialize selector axe and scatter point selection
            if layout is not None:
                axe = self.fig.add_subplot(layout)
                self.fig.subplots_adjust(wspace=.5, hspace=.5)
                axe.set_box_aspect(1)
                axe.set_xlim(0, 1)
                axe.set_ylim(0, 1)

                self.draw_figure()

                self.om_selector_map[index]['axe'] = axe
                self.om_selector_map[index]['scatter_collection'] = axe.scatter([], [],s=20, c='k', marker='o', alpha=0.5)
            else:
                self.om_selector_map[index]['axe'] = None
                self.om_selector_map[index]['scatter_collection'] = None

        # self.update_figure()

    def on_selector_changed(self, index):
        """Handle combobox text change and get the corresponding axe."""
        selector = self.om_selector_map[index]["selector"]
        self.selected_metric = selector.currentText()
        self.plot_utils.set_axe(self.om_selector_map[index]["axe"])
        self.plot_utils.set_scatter_collection(self.om_selector_map[index]["scatter_collection"])

        self.update_figure()

    def populate_selector(self):
        """
        Updates the dataset selection combo box and figure list with the available data sets.

        - Retrieves the list of available data sets from `self.orthogonality_dict`.
        - Updates `self.set_combo` with the new dataset options.
        - Ensures signals are blocked during updates to prevent unwanted UI triggers.

        Notes:
        - This method should be called after loading new data.
        - If no data sets are available, the combo boxes remain unchanged.
        """
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        if not self.orthogonality_dict:
            return  # No data available, prevent unnecessary UI updates

        data_sets_list = list(self.orthogonality_dict.keys())

        self.dataset_selector.blockSignals(True)  # Prevent UI signal loops

        self.dataset_selector.clear()

        self.dataset_selector.addItems(data_sets_list)

        self.dataset_selector.blockSignals(False)

        #clear selector list in case previous data were loaded
        for index, data in self.om_selector_map.items():
            om_selector = data['selector']

            om_selector.blockSignals(True)
            om_selector.clear()
            om_selector.blockSignals(False)

    def compute_orthogonality_metric(self) -> None:
        self.selected_metric_list = self.om_tree_list.get_checked_items()

        # self.model.compute_orthogonality_metric(self.selected_metric_list)
        self.stack.setCurrentWidget(self.progress_overlay)
        self.progress_overlay.show()
        self.progress_bar.rpb_setValue(0)
        self.progress_bar.repaint()
        QApplication.processEvents()

        self.start_om_computation(self.selected_metric_list)
        self.selected_metric_list = [METRIC_PLOT_MAP[metric] for metric in self.selected_metric_list]

        #remove None item
        self.selected_metric_list = [metric for metric in self.selected_metric_list if metric]

        #rermove doublon from list (when converting a list into dict it removes dupplicate keys)
        self.selected_metric_list = list(dict.fromkeys(self.selected_metric_list))

        for index, data in self.om_selector_map.items():
            om_selector = data['selector']

            om_selector.blockSignals(True)
            om_selector.clear()
            om_selector.addItems(self.selected_metric_list)
            om_selector.blockSignals(False)

        #
        # self.update_orthogonality_table()
        #
        # self.data_sets_change()

        # self.metric_computed.emit([self.om_tree_list.get_checked_items(),self.selected_metric_list])


    def _on_om_computed(self, original_metric_list: list):
        # now the model has filled its dataframes; we can continue
        # exactly the same as before, e.g.:

        # remap to plotting names
        plot_list = [METRIC_PLOT_MAP[m] for m in original_metric_list]
        plot_list = [m for m in plot_list if m]
        plot_list = list(dict.fromkeys(plot_list))

        for idx, data in self.om_selector_map.items():
            sel = data['selector']
            sel.blockSignals(True)
            sel.clear()
            sel.addItems(plot_list)
            sel.blockSignals(False)

        self.update_orthogonality_table()
        self.data_sets_change()
        self.metric_computed.emit([original_metric_list, plot_list])


    def update_bin_box_number(self):

        #simply update the number of bin and reset computed metric status for the metric that use bin number
        self.model.update_num_bins(self.nb_bin.value())

        # self.stack.setCurrentWidget(self.progress_overlay)
        # self.progress_overlay.show()
        # self.progress_bar.rpb_setValue(0)
        # self.progress_bar.repaint()
        # QApplication.processEvents()
        #
        # self.start_update_bin_number(self.nb_bin.value())
        #
        # self.refresh_displayed_plot()
        #
        # if self.selected_metric_list:
        #     self.metric_computed.emit([self.om_tree_list.get_checked_items(), self.selected_metric_list])

    def select_orthogonality(self):
        self.model.set_orthogonality_value('orthogonality_score')

    def update_orthogonality_table(self):
        data = self.model.get_orthogonality_metric_df()

        self.styled_table.set_header_label(list(data.columns))
        self.styled_table.async_set_table_data(data)
        self.styled_table.set_table_proxy()

    def data_sets_change(self, data_set: str = None) -> None:

        """
        Handles dataset selection from the dropdown menu and updates the UI accordingly.

        - Updates the current dataset based on the selection.
        - Highlights the corresponding row in the table view.
        - Refreshes the displayed figure to reflect the new dataset.

        Parameters:
            data_set (str, optional): The dataset name to switch to.
                                      If None, it is retrieved from `self.set_combo`.

        Notes:
        - If triggered by the dropdown, `data_set` is None, so the function retrieves the selected value.
        - Updates both the dropdown and table selection to stay synchronized.
        - Calls `update_figure()` to refresh the visualization.
        """
        if data_set is None:
            self.selected_set = self.dataset_selector.currentText()
            index_at_row = self.get_index_from()

            # Prevent unnecessary signal emissions while selecting the row
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

    def get_index_from(self) -> int:
        """
        Retrieves the row index corresponding to the currently selected dataset.

        - Iterates through the table model to find a match with `self.selected_set`.
        - Uses the proxy model to access the displayed data.

        Returns:g
            int: The row index of the selected dataset, or -1 if not found.

        Notes:
        - This function assumes that dataset names are stored in the first column.
        - If no match is found, returns -1 to indicate failure.
        """
        row_count = self.styled_table.get_row_count()

        for row in range(row_count):
            model_index = self.styled_table.get_proxy_model().index(row, 0)  # Column 0 assumed to contain dataset names
            if f"Set {model_index.data()}" == self.selected_set:
                return row

        return -1  # Explicitly return -1 if no match is found

    def table_item_clicked(self, index: QModelIndex) -> None:
        """
        Handles table row selection and updates the dataset accordingly.

        - Retrieves the dataset name from the selected row.
        - Calls `data_sets_change()` to synchronize the dropdown selection.

        Parameters:
            index (QModelIndex): The index of the clicked item (not used in current logic).

        Notes:
        - Only the first selected row is considered if multiple rows are selected.
        - Assumes dataset names are stored in the first column.
        """
        model_index_list = self.styled_table.get_selected_rows()

        if not model_index_list:
            return  # No selection, exit early

        self.data_sets_change(f"Set {model_index_list[0].data()}")

    def data_set_selection_changed_from_combobox(self) -> None:
        """
        Handles dataset selection changes from the combo box.

        - Updates the current dataset name.
        - Selects the corresponding row in the table view.
        - Refreshes the figure to display the selected dataset.

        Notes:
        - This function ensures synchronization between the combo box selection and the table view.
        - Calls `get_index_from()` to retrieve the correct row index.
        - If no matching row is found, no row selection is applied.
        """
        self.selected_set = self.dataset_selector.currentText()
        index_at_row = self.get_index_from()

        if index_at_row != -1:
            # signal is triggered by QItemSelectionModel not the QTableView when selecting a row
            self.styled_table.get_table_view().selectionModel().blockSignals(True)
            self.styled_table.select_row(index_at_row)
            self.styled_table.get_table_view().selectionModel().blockSignals(True)

        self.plot_utils.set_set_number(self.selected_set)

        self.refresh_displayed_plot()

    def data_set_selection_changed_from_table(self) -> None:
        """
        Handles dataset selection changes from the table view.

        - Retrieves the selected dataset from the table view.
        - Synchronizes the combo box with the selected dataset.
        - Updates the visualization based on the current tab.

        Notes:
        - Only the first selected row is considered if multiple rows are selected.
        - The combo box is blocked during updates to prevent signal loops.
        - If the "Calculations" tab is active, the selected dataset blinks on the orthogonality plot.
        - Otherwise, the standard figure update is triggered.
        """
        model_index_list = self.styled_table.get_selected_rows()

        if not model_index_list:
            return  # No selection, exit early

        proxy_model = self.styled_table.get_proxy_model()
        model_index = proxy_model.mapToSource(model_index_list[0])
        self.selected_set = f"Set {model_index.data()}"

        self.dataset_selector.blockSignals(True)
        self.dataset_selector.setCurrentText(self.selected_set)
        self.dataset_selector.blockSignals(False)

        self.refresh_displayed_plot()

    def refresh_displayed_plot(self):
        # Refresh the displayed figure
        number_of_selectors = int(self.compare_number.currentText())

        [self.on_selector_changed(str(i)) for i in range(number_of_selectors)]

    def draw_figure(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def  update_figure(self):

        #if no axe is selected no need to update figure
        if self.selected_axe is None:
            return

        self.plot_utils.clean_figure()

        if self.model.get_status() in ['loaded', 'peak_capacity_loaded']:
            # self.plot_scatter()
            self.plot_utils.plot_scatter()
        else:
            return

        # Execute the appropriate method based on combo box selection
        # current_metric = self.computed_metric.currentText()

        # if self.selected_metric in ['Bin Box']:
        #     self.bin_box_input_widget.setHidden(False)
        # else:
        #     self.bin_box_input_widget.setHidden(True)

        #No metric has been computed yet so no need to plot them
        if self.selected_metric is None:
            return

        if self.selected_metric in self.plot_functions_map:
            self.plot_functions_map[self.selected_metric]()  # Call the corresponding function

    def plot_percent_bin(self):
        self.plot_utils.plot_percent_bin()

    def plot_bin_box(self):
        self.plot_utils.plot_bin_box()

    # Plot methods
    def plot_asterisk(self):
        self.plot_utils.plot_asterisk()

    def plot_linear_reg(self):
        self.plot_utils.plot_linear_reg()

    def plot_percent_fit_xy(self):
        self.plot_utils.plot_percent_fit_xy()

    def plot_percent_fit_yx(self):
        self.plot_utils.plot_percent_fit_yx()

    def plot_convex_hull(self):
        self.plot_utils.plot_convex_hull()