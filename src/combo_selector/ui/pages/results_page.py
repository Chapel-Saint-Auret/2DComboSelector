import logging

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
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
from combo_selector.ui.widgets.neumorphism import *
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

PLOT_SIZE = QSize(600, 400)
drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")

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
    def __init__(self, model=None, title="Unnamed"):
        """
        Initialize the ResultsPage.

        Layout:
          - Top: input panel (left) + result visualization (right)
          - Bottom: final result & ranking table
          - Overlay: circular progress bar during computations
        """
        super().__init__()

        # --- state ------------------------------------------------------------
        self.threadpool = QThreadPool()
        self.orthogonality_filter_marker = None
        self.orthogonality_scatter_default = None
        self.selected_score = None
        self.selected_metric = None
        self.scatter_collection = None
        self.blink_step = 0
        self.blink_ax = None
        self.animations = []
        self.highlighted_ax = None
        self.selected_scatter_collection = None
        self.selected_filtered_scatter_point = {}
        self.selected_axe = None
        self.full_scatter_collection = None
        self.selected_set = "Set 1"
        self.orthogonality_dict = None
        self.scatter_point_group = {}
        self.model = model

        # --- base frame & outer layout ---------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP AREA (input + plot) ==========================================
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        # ----- Left: Input column ---------------------------------------------
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

        # --- Score Calculation group (stylesheet UNCHANGED) -------------------
        ranking_selection_group = QGroupBox("Ranking")
        ranking_selection_group.setStyleSheet(f"""
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
                    QPushButton:hover {{
                        background-color: #bcc8f5;
                    }}
                    QPushButton:pressed {{
                        background-color: #8fa3ef;
                    }}
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
                    color: #2C3E50;              /* dark slate navy */
                        font-family: "Segoe UI";
        			    font-weight: bold;
                    }}
                    QComboBox:hover {{
                        border: 1px solid #a6b2c0;
                    }}
                    QComboBox::drop-down {{
                        border:none;
                    }}

                    QComboBox::down-arrow {{
                        image: url("{drop_down_icon_path}");
                    }}
                """)

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

        # --- Score Calculation group (stylesheet UNCHANGED) -------------------
        orthogonality_score_group = QGroupBox("Orthogonality score calculation")
        orthogonality_score_group.setStyleSheet(f"""
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
            QPushButton:hover {{
                background-color: #bcc8f5;
            }}
            QPushButton:pressed {{
                background-color: #8fa3ef;
            }}
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
            color: #2C3E50;              /* dark slate navy */
                font-family: "Segoe UI";
			    font-weight: bold;
            }}
            QComboBox:hover {{
                border: 1px solid #a6b2c0;
            }}
            QComboBox::drop-down {{
                border:none;
            }}

            QComboBox::down-arrow {{
                image: url("{drop_down_icon_path}");
            }}
        """)
        orthogonality_score_layout = QVBoxLayout()
        orthogonality_score_layout.setContentsMargins(5, 5, 5, 5)

        self.om_list = CheckableTreeList()
        self.om_list.setFixedHeight(175)
        self.compute_score_btn = QPushButton("Compute score")

        self.use_suggested_btn = QRadioButton("Use suggested core")
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

        # --- Score Comparison group (stylesheet UNCHANGED) --------------------
        orthogonality_compare_score_group = QGroupBox("Orthogonality score comparison")
        orthogonality_compare_score_group.setStyleSheet(
            orthogonality_score_group.styleSheet()
        )

        self.om_selection_layout = QVBoxLayout()
        self.om_selection_layout.addWidget(QLabel("Number of score to compare:"))
        self.compare_number = QComboBox()
        self.compare_number.addItems(["1", "2", "3", "4"])
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
        self.add_dataset_selector("Select Score 3:", self.om_selector3)
        self.add_dataset_selector("Select Score 4:", self.om_selector4)

        self.om_selector_list = [
            self.om_selector1,
            self.om_selector2,
            self.om_selector3,
            self.om_selector4,
        ]
        self.om_selector_map = {
            "0": {
                "selector": self.om_selector1,
                "axe": None,
                "scatter_collection": None,
                "filtered_scatter_point": {},
            },
            "1": {
                "selector": self.om_selector2,
                "axe": None,
                "scatter_collection": None,
                "filtered_scatter_point": {},
            },
            "2": {
                "selector": self.om_selector3,
                "axe": None,
                "scatter_collection": None,
                "filtered_scatter_point": {},
            },
            "3": {
                "selector": self.om_selector4,
                "axe": None,
                "scatter_collection": None,
                "filtered_scatter_point": {},
            },
        }
        orthogonality_compare_score_group.setLayout(self.om_selection_layout)

        # --- Info group (stylesheet UNCHANGED) --------------------------------
        info_page_group = QGroupBox("Info")
        info_page_group.setStyleSheet("""
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
        info_page_layout = QVBoxLayout()
        self.textEdit = QLabel()
        self.textEdit.setTextFormat(Qt.TextFormat.RichText)
        self.textEdit.setWordWrap(True)
        self.textEdit.setText("""
            <p><strong><u>Info 1</u>:</strong><br>
            The table groups metrics that are correlated based on the selected threshold.
            Metrics in the same group have a correlation value <strong>equal to or above</strong> the threshold.</p>
            <p><strong><u>Info 2</u>:</strong><br>
            The <strong>correlation threshold tolerance</strong> allows flexibility in detecting correlated metrics.</p>
        """)
        self.om_score_formula = QSvgWidget()
        self.om_score_formula.load("om_suggested_score_infos.svg")
        info_page_layout.addWidget(self.om_score_formula)
        info_page_group.setLayout(info_page_layout)

        # Assemble input column
        user_input_frame_layout.addWidget(ranking_selection_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(orthogonality_score_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(orthogonality_compare_score_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        # user_input_frame_layout.addWidget(info_page_group)

        # ----- Right: Plot card (styles UNCHANGED) ----------------------------
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
            font-weight: bold;
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

        # Assemble top row
        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)
        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        # === BOTTOM AREA (table) ==============================================
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

        # === Splitter & stacked layout ========================================
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

        # --- signals -----------------------------------------------------------
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

    def filter_table(self, regexp):
        self.styled_table.set_proxy_filter_regexp(regexp)

    def add_dataset_selector(self, label_text, combobox):
        container = QVBoxLayout()
        container.setSpacing(2)
        container.addWidget(QLabel(label_text))
        container.addWidget(combobox)
        self.om_selection_layout.addLayout(container)

    def create_filter_groupbox(self):

        grid_layout = QGridLayout()

        # Add widgets to grid_layout
        self.filter_button_group = QButtonGroup()
        self.filter_button_group.setExclusive(False)

        self.hilic_vs_hilic = QCheckBox("HILIC x HILIC")
        self.rplc_vs_rplc = QCheckBox("RPLC x RPLC")
        self.rplc_vs_hilic = QCheckBox("HILIC x RPLC")

        self.hilic_vs_hilic.setCheckState(Qt.CheckState.Checked)
        self.rplc_vs_rplc.setCheckState(Qt.CheckState.Checked)
        self.rplc_vs_hilic.setCheckState(Qt.CheckState.Checked)

        self.hilic_vs_hilic.setObjectName("HILIC x HILIC")
        self.rplc_vs_rplc.setObjectName("RPLC x RPLC")
        self.rplc_vs_hilic.setObjectName("HILIC x RPLC")

        self.filter_button_group.addButton(self.hilic_vs_hilic)
        self.filter_button_group.addButton(self.rplc_vs_rplc)
        self.filter_button_group.addButton(self.rplc_vs_hilic)

        grid_layout.addWidget(QLabel("Filters:"), 0, 0)
        grid_layout.addWidget(self.hilic_vs_hilic, 1, 0)
        grid_layout.addWidget(self.rplc_vs_rplc, 2, 0)
        grid_layout.addWidget(self.rplc_vs_hilic, 3, 0)

        return grid_layout

    def init_page(self, om_list):

        logging.debug("Running ResultsWorker: update_orthogonality_metric_list")
        self.update_orthogonality_metric_list(om_list)

        logging.debug("Running ResultsWorker: populate_om_score_selector")
        self.populate_om_score_selector()

        # logging.debug("Running ResultsWorker: build_filtered_point")
        # self.build_filtered_point()

        logging.debug("Running ResultsWorker: update_om_selector_state")
        self.update_om_selector_state()

        logging.debug("Running ResultsWorker: update_results_table")
        self.update_results_table()

        number_of_selectors = int(self.compare_number.currentText())
        for i in range(number_of_selectors):
            self.handle_selector_change(str(i), emit_plot=True)

    def update_om_selector_state(self):
        number_of_selectors = int(self.compare_number.currentText())

        [
            (
                self.om_selector_list[i].setDisabled(False)
                if i < number_of_selectors
                else self.om_selector_list[i].setDisabled(True)
            )
            for i, selector in enumerate(self.om_selector_list)
        ]

        self.update_plot_layout()

        # [self.on_selector_changed(str(i)) for i in range(number_of_selectors)]

        for i in range(number_of_selectors):
            self.handle_selector_change(str(i), emit_plot=False)

    def handle_selector_change(self, index: str, emit_plot: bool = True):
        """
        Handles logic for selector change.
        This can be reused without triggering signals during initialization.
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

    def on_selector_changed(self, index: str):
        """Slot triggered by QComboBox.currentTextChanged"""
        self.handle_selector_change(index)

    def populate_om_score_selector(self):

        om_list = self.om_list.get_items()

        om_score_list = ["Suggested score", "Computed score"] + om_list

        for index, data in self.om_selector_map.items():
            om_score_selector = data["selector"]
            om_score_selector.blockSignals(True)
            om_score_selector.clear()
            om_score_selector.addItems(om_score_list)
            om_score_selector.blockSignals(False)

    def update_plot_layout(self):
        # get the number of plot to compare
        number_of_selectors = self.compare_number.currentText()

        # create a key string based on the compare number value in order to know which ploy layout to select
        plot_key = number_of_selectors + "PLOT"

        # plot layout map that contains the list of plot layout to display based on the compare number
        plot_layout_map = {
            "1PLOT": [111, None, None, None],
            "2PLOT": [121, 122, None, None],
            "3PLOT": [221, 222, 223, None],
            "4PLOT": [221, 222, 223, 224],
        }

        # get list of layout
        layout_list = plot_layout_map[plot_key]

        self.fig.clear()
        # self.remove_all_axes()

        for i, layout in enumerate(layout_list):
            index = str(i)
            # initialize selector axe and scatter point selection
            if layout is not None:
                axe = self.fig.add_subplot(layout)
                self.fig.subplots_adjust(wspace=0.5, hspace=0.5)
                axe.set_box_aspect(1)

                self.draw_figure()

                # since the figure has been cleares, all the previous axes and scatter collection need to be reinitialized
                # if it's not done the filtered_scatter_point won be attached to any axe because it has been deleted
                self.om_selector_map[index]["axe"] = axe
                self.om_selector_map[index]["filtered_scatter_point"] = {}

                # self.om_selector_map[index]['scatter_collection'] = axe.scatter([], [], s=15, color='silver', edgecolor='black', linewidths=0.8)
            else:
                self.om_selector_map[index]["axe"] = None
                self.om_selector_map[index]["filtered_scatter_point"] = None
                # self.om_selector_map[index]['scatter_collection'] = None

    def filter_button_clicked(self):
        number_of_selectors = int(self.compare_number.currentText())

        # [self.on_selector_changed1(str(i)) for i in range(number_of_selectors)]

        for i in range(number_of_selectors):
            self.handle_selector_change(str(i), emit_plot=True)

    def draw_figure(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def on_selector_changed1(self, index):
        selector = self.om_selector_map[index]["selector"]
        self.selected_score = selector.currentText()
        self.selected_axe = self.om_selector_map[index]["axe"]
        self.selected_filtered_scatter_point = self.om_selector_map[index][
            "filtered_scatter_point"
        ]

        if self.selected_axe and self.selected_score:
            print("PLot OM vs 2D")
            self.plot_orthogonality_vs_2d_peaks()

    def set_ranking_argument(self):
        ranking_argument = self.select_ranking_type.currentText()
        self.model.set_orthogonality_ranking_argument(ranking_argument)
        self.update_results_table()

    def set_use_suggested_om_score_flag(self):

        if self.use_suggested_btn.isChecked():
            flag = True
            # self.compute_score_btn.setDisabled(True)
        else:
            flag = False
            # self.compute_score_btn.setDisabled(False)

        self.model.suggested_om_score_flag(flag)
        # self.model.compute_suggested_score()
        self.model.compute_practical_2d_peak_capacity()
        self.model.create_results_table()
        self.update_results_table()

    def update_orthogonality_metric_list(self, om_list):
        self.om_list.blockSignals(True)
        self.om_list.clear()
        self.om_list.add_items(om_list)
        self.om_list.blockSignals(False)

    def update_suggested_score_data(self):
        self.model.compute_suggested_score()
        self.model.compute_practical_2d_peak_capacity()

        self.model.create_results_table()
        self.update_results_table()

    def compute_custom_orthogonality_metric_score(self):
        metric_list = self.om_list.get_checked_items()
        self.model.compute_custom_orthogonality_score(metric_list)
        self.model.compute_practical_2d_peak_capacity()
        self.model.create_results_table()

    def start_om_computation(self, metric_list):
        worker = ResultsWorkerComputeCustomOMScore(self)

        worker.signals.progress.connect(self.handle_progress_update)
        worker.signals.finished.connect(self.handle_finished)

        self.threadpool.start(worker)

        # self.populate_om_score_selector()
        self.update_results_table()
        # this is just to update self.filter_subset_dict with the new computed value (maybe there is a mor optimize way to do it)
        # it a lazy option
        self.build_filtered_point()
        self.plot_orthogonality_vs_2d_peaks()

    def handle_progress_update(self, value: int):
        print(f"[RECEIVED] Progress update: {value}")

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

    def handle_finished(self):
        print("Computation done")
        self.progress_bar.rpb_setValue(100)  # Final visual update
        self.progress_bar.repaint()
        QTimer.singleShot(800, self.hide_progress_overlay)

        # self.populate_om_score_selector()
        self.update_results_table()
        # this is just to update self.filter_subset_dict with the new computed value (maybe there is a mor optimize way to do it)
        # it a lazy option
        # self.build_filtered_point()
        self.plot_orthogonality_vs_2d_peaks()

    def hide_progress_overlay(self):
        self.progress_overlay.hide()
        self.stack.setCurrentWidget(self.main_widget)

    def update_results_table(self):
        data = self.model.get_orthogonality_result_df()
        self.styled_table.async_set_table_data(data)
        self.styled_table.set_table_proxy()

    def plot_orthogonality_vs_2d_peaks(self):
        if self.model.get_status() not in ["peak_capacity_loaded"]:
            return

        if not self.selected_score:
            return

        # will be used when filtered are implemented
        # if not hasattr(self, "orthogonality_score"):
        #     print("[plot_orthogonality_vs_2d_peaks] Missing orthogonality_score")
        #     return

        orthogonality_score_dict = self.model.get_orthogonality_score_df()
        orthogonality_score_df = pd.DataFrame.from_dict(
            orthogonality_score_dict, orient="index"
        )

        score = UI_TO_MODEL_MAPPING[self.selected_score]

        x = orthogonality_score_df[score]
        y = orthogonality_score_df["2d_peak_capacity"]

        # Set axes titles
        self.selected_axe.set_xlabel(self.selected_score, fontsize=12)
        self.selected_axe.set_ylabel("Hypothetical 2D peak capacity", fontsize=12)

        # self.display_filtered_point()
        if self.selected_scatter_collection in self.selected_axe.collections:
            self.selected_scatter_collection.remove()
            self.selected_scatter_collection = None

        self.selected_scatter_collection = self.selected_axe.scatter(
            x, y, s=20, color="silver", edgecolor="black", linewidths=0.9
        )

        # Hide the legend and update the figure
        self.fig.legend().set_visible(False)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def build_filtered_point(self):
        # for group in self.selected_filtered_scatter_point:
        #     scatter = self.selected_filtered_scatter_point[group]
        #
        #     if scatter in self.selected_axe.collections:
        #         scatter.remove()
        #         scatter = None

        self.orthogonality_score = self.model.get_orthogonality_score_df()
        data_frame = pd.DataFrame.from_dict(self.orthogonality_score, orient="index")

        self.filter_subset_dict = {}
        button_list = self.filter_button_group.buttons()
        button_name_list = [button.objectName() for button in button_list]

        def get_filter_column_nb(filter):
            # Iterate over columns
            for col in self.filter_df.columns:
                if filter in self.filter_df[col].values:
                    column_number = col
                    break
            # return the column number of the filter name
            return column_number

        regular_expresion_map = {
            "HILIC x HILIC": r"HILIC.*vs.*HILIC",
            "RPLC x RPLC": r"RPLC.*vs.*RPLC",
            "HILIC x RPLC": r"HILIC.*vs.*RPLC",
            "pH3 x pH8": r"pH\s?3(?!\.\d).*vs.*pH\s?8(?!\.\d)",
            "pH3 x pH5.5": r"pH\s?3(?!\.\d).*vs.*pH\s?5.5(?!\.\d)",
            "pH5.5 x pH8": r"pH\s?5.5(?!\.\d).*vs.*pH\s?8(?!\.\d)",
            "MeOH x ACN": r"MeOH.*vs.*ACN",
        }

        data_frame_mask2 = pd.Series(False, index=range(len(data_frame)))

        for button_name in button_name_list:
            reg_exp1 = regular_expresion_map[button_name]
            data_frame_mask1 = data_frame["title"].str.contains(reg_exp1)

            # Split the original string into words
            words = reg_exp1.split(".*")
            # Reverse the order of the words
            swapped_words = words[::-1]
            # Combine the reversed words with separators
            reg_exp2 = ".*".join(swapped_words)
            data_frame_mask2.index = data_frame_mask1.index
            # if swapped word is the same we don't want to double the mask which would lead to have double scatter point of same subset of datas
            if reg_exp1 != reg_exp2:
                data_frame_mask2 = data_frame["title"].str.contains(reg_exp2)
            else:
                # that's a workaround, proper way would be to just set a dataframe mask of False, same size of data_frame

                data_frame_mask2.index = data_frame_mask1.index

            self.filter_subset_dict[button_name] = [
                {"mask": data_frame_mask1, "data_frame1": data_frame[data_frame_mask1]},
                {"mask": data_frame_mask2, "data_frame2": data_frame[data_frame_mask2]},
            ]

    def display_filtered_point(self):
        # self.orthogonality_dict = self.model.get_orthogonality_dict()
        if self.orthogonality_scatter_default in self.selected_axe.collections:
            self.orthogonality_scatter_default.remove()
            self.orthogonality_scatter_default = None

        score = UI_TO_MODEL_MAPPING[self.selected_score]

        button_list = self.filter_button_group.buttons()
        checked_button_list = [
            button.objectName() for button in button_list if button.isChecked()
        ]
        button_name_list = [button.objectName() for button in button_list]

        def get_filter_column_nb(filter):
            # Iterate over columns
            for col in self.filter_df.columns:
                if filter in self.filter_df[col].values:
                    column_number = col
                    break
            # return the column number of the filter name
            return column_number

        def check_if_filter_exclusively_in_same_column():
            # check if all checked filter button are exclusively in the same column (in GUI it means same row)
            if button_name_list:
                filter_column_list = np.array(
                    [get_filter_column_nb(checked) for checked in button_name_list]
                )

                return np.all(filter_column_list == filter_column_list[0])
            else:
                return False

        def set_scatter_visibility():
            for button in self.selected_filtered_scatter_point:
                scatter_point = self.selected_filtered_scatter_point[button]
                # edge, face = scatter_point
                face = scatter_point

                if button in checked_button_list:
                    # edge.set_visible(True)
                    face.set_visible(True)
                else:
                    # edge.set_visible(False)
                    face.set_visible(False)

        filter_marker_map = {
            "HILIC x HILIC": {
                "MARKER": "s",
                "COLOR": "lightgray",
                "FACECOLOR": "k",
                "EDGECOLOR": "k",
                "LABEL": "HILIC x HILIC",
            },
            "RPLC x RPLC": {
                "MARKER": "o",
                "COLOR": "lightgray",
                "FACECOLOR": "k",
                "EDGECOLOR": "k",
                "LABEL": "RPLC x RPLC",
            },
            "HILIC x RPLC": {
                "MARKER": "^",
                "COLOR": "lightgray",
                "FACECOLOR": "k",
                "EDGECOLOR": "k",
                "LABEL": "HILIC x RPLC",
            },
            "pH3 x pH8": {
                "MARKER": None,
                "COLOR": "red",
                "FACECOLOR": None,
                "EDGECOLOR": "red",
            },
            "pH3 x pH5.5": {
                "MARKER": None,
                "COLOR": "green",
                "FACECOLOR": None,
                "EDGECOLOR": "green",
            },
            "pH5.5 x pH8": {
                "MARKER": None,
                "COLOR": "blue",
                "FACECOLOR": None,
                "EDGECOLOR": "blue",
            },
            "MeOH x ACN": {
                "MARKER": None,
                "COLOR": "brown",
                "FACECOLOR": None,
                "EDGECOLOR": "brown",
            },
        }

        data_frame_mask = False
        if self.filter_subset_dict:
            for checked_filter in self.filter_subset_dict:
                data_frame_mask1 = self.filter_subset_dict[checked_filter][0]["mask"]
                data_frame_mask2 = self.filter_subset_dict[checked_filter][1]["mask"]
                data_frame_mask = (data_frame_mask | data_frame_mask1) | (
                    data_frame_mask | data_frame_mask2
                )

        if button_name_list:
            # for key in self.displayed_filter_keys:

            # Initialize a set to keep track of displayed keys

            # self.orthoganality_scatter = self._ax.scatter(x_full, y_full,s=20, color='k',facecolor='None', alpha=0.05)
            final_dataframe = pd.DataFrame()
            # if check_if_filter_exclusively_in_same_column():
            # if checked_button_list:
            # self.orthogonality_filter_marker = None
            for button_name in self.filter_subset_dict:

                # Skip if already plotted
                subset1 = self.filter_subset_dict[button_name][0]["data_frame1"]
                subset2 = self.filter_subset_dict[button_name][1]["data_frame2"]

                # Concatenate the two DataFrames vertically
                subset = pd.concat([subset1, subset2], axis=0)
                final_dataframe = pd.concat([final_dataframe, subset], axis=1)
                # Reset the index of the merged DataFrame
                subset = subset.reset_index(drop=True)

                x = subset[score]
                y = subset["2d_peak_capacity"]

                if button_name not in list(self.selected_filtered_scatter_point.keys()):

                    scatter = self.selected_axe.scatter(
                        x,
                        y,
                        s=20,
                        marker=filter_marker_map[button_name]["MARKER"],
                        color=filter_marker_map[button_name]["COLOR"],
                        label=filter_marker_map[button_name]["LABEL"],
                        # color=None,
                        # facecolor=filter_marker_map[button_name]['FACECOLOR'],
                        # facecolor='None',
                        # edgecolor=filter_marker_map[button_name]['EDGECOLOR'],
                        # edgecolor=filter_marker_map[button_name]['EDGECOLOR'],
                        edgecolor="black",
                        # alpha=0.5,
                        linewidths=0.8,
                    )

                    # scatter_face = self.orthogonality_axes.scatter(x, y,
                    #                                  s=20,
                    #                                  marker=filter_marker_map[button_name]['MARKER'],
                    #                                  # color=filter_marker_map[button_name]['COLOR'],
                    #                                  facecolor=filter_marker_map[button_name]['FACECOLOR'],
                    #                                  # edgecolor=filter_marker_map[button_name]['EDGECOLOR'],
                    #                                  edgecolor='None')
                    #                                  # alpha=0.3,
                    #                                 # linewidths=0)

                    # self.scatter_point_group[button_name] = (scatter_edge, scatter_face)
                    self.selected_filtered_scatter_point[button_name] = scatter
                else:
                    # if they are present in group just update their value with scatter plot offset
                    # means that selected score has been changes so scatter point needs to be updated
                    # accordingly
                    scatter = self.selected_filtered_scatter_point[button_name]
                    scatter.set_offsets(list(zip(x, y)))
                # Add the key to the set to mark it as displayed
            # else:
            #     x = [self.orthogonality_score[key][score] for key in self.orthogonality_score]
            #     y = [self.orthogonality_score[key]['2d_peak_capacity'] for key in self.orthogonality_score]
            #     self.orthogonality_scatter_default = self.selected_axe.scatter(x, y, s=15, color='silver',
            #                                                                          edgecolor='black',
            #                                                                          linewidths=0.8)
            #     self.selected_scatter_collection.set_offsets(list(zip(x, y)))
            #     # self.orthogonality_scatter_default = self.orthogonality_axes.scatter(x, y, s=20, color='k', alpha=0.4,linewidths=2)

            set_scatter_visibility()

        # self.fig.legend().set_visible(False)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
