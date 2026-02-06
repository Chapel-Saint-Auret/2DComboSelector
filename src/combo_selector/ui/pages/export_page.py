import os

import matplotlib

matplotlib.use("Agg")  # make sure we’re using the non-GUI “Agg” backend

from functools import partial

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
)

from combo_selector.core.plot_utils import PlotUtils
from combo_selector.ui.widgets.checkable_combo_list import CheckableComboList
from combo_selector.ui.widgets.checkable_tree_list import CheckableTreeList
from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.neumorphism import *
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

PLOT_SIZE = QSize(600, 400)
drop_down_icon_path = resource_path("icons/drop_down_arrow.png").replace("\\", "/")


class ExportPage(QFrame):
    def __init__(self, model=None, title="Unnamed"):
        """
        Initialize the ExportPage.

        Layout:
          - Top row: left input panel (export options) + right figure visualization
          - (Optional) Table section is prepared but not added to splitter by default
        """
        super().__init__()

        # --- state ------------------------------------------------------------
        self.blink_timer = QTimer()
        self.blink_step = 0
        self.blink_ax = None
        self.animations = []
        self.highlighted_ax = None
        self.selected_scatter_collection = None
        self.selected_axe = None
        self.full_scatter_collection = None
        self.selected_set = "Set 1"
        self.orthogonality_dict = None
        self.model = model

        # --- plotting setup ---------------------------------------------------
        self.fig = Figure(figsize=(15, 15))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = CustomToolbar(self.canvas)

        self.axe = self.canvas.figure.add_subplot(1, 1, 1)
        self.axe.set_box_aspect(1)
        self.axe.set_xlim(0, 1)
        self.axe.set_ylim(0, 1)

        self.plot_utils = PlotUtils(fig=self.fig)
        self.plot_utils.set_axe(self.axe)

        self.plot_functions_map = {
            "Convex Hull": partial(self.plot_convex_hull),
            "Bin Box": partial(self.plot_bin_box),
            "Linear regression": partial(self.plot_linear_reg),
            "Modeling approach": partial(self.plot_modeling_approach),
            "Conditional entropy": partial(self.plot_conditional_entropy),
            "Asterisk": partial(self.plot_utils.plot_asterisk),
            "%FIT": partial(self.plot_utils.plot_percent_fit_xy),
            "%BIN": partial(self.plot_utils.plot_percent_bin),
        }

        self.table_functions_map = {
            "Normalized retention table": self.model.get_normalized_retention_time_df,
            "2D Combination table": self.model.get_combination_df,
            "OM result table": self.model.get_orthogonality_metric_df,
            "Orthogonality result correlation table": self.model.get_correlation_group_df,
            "Final result and ranking table": self.model.get_orthogonality_result_df,
        }

        # --- page frame & outer layout ---------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
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
        # user_input_frame.setStyleSheet("background-color: lightgrey; border-radius: 10px;")
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

        # Info group (stylesheet unchanged)
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

        # Export figure group (stylesheet unchanged)
        export_figure_grp = QGroupBox("Export data set figure")
        export_figure_grp.setStyleSheet(f"""
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
               QLabel {{
            background-color: transparent;
            color: #2C3E50;
            font-family: "Segoe UI";
            font-weight: bold;
            }}

            QComboBox::drop-down {{
            border: none;
            }}
            QComboBox::down-arrow {{
                image: url("{drop_down_icon_path}");
            }}
        """)

        form_layout = QVBoxLayout()

        # export directory
        self.figure_export_directory_lineEdit = QLineEdit()
        self.figure_export_directory_lineEdit.setText(os.getcwd())
        self.export_figure_directory_btn = QPushButton("...")
        self.export_figure_directory_btn.setFixedWidth(50)

        export_directory_hlayout = QHBoxLayout()
        export_directory_hlayout.addWidget(self.figure_export_directory_lineEdit)
        export_directory_hlayout.addWidget(self.export_figure_directory_btn)
        form_layout.addWidget(QLabel("Export directory:"))
        form_layout.addLayout(export_directory_hlayout)

        # folder name
        self.figure_folder_name_lineEdit = QLineEdit("Figure")
        form_layout.addWidget(QLabel("Folder name:"))
        form_layout.addWidget(self.figure_folder_name_lineEdit)

        # figure type + list
        self.figure_type_chklist = CheckableComboList()
        form_layout.addWidget(QLabel("Figure type:"))
        form_layout.addWidget(self.figure_type_chklist)

        self.figure_list_chklist = CheckableComboList()
        form_layout.addWidget(QLabel("Figure list:"))
        form_layout.addWidget(self.figure_list_chklist)

        self.save_figure_btn = QPushButton("Save figure(s)")
        form_layout.addWidget(self.save_figure_btn)

        export_figure_grp.setLayout(form_layout)

        # Export table group (stylesheet unchanged)
        export_table_grp = QGroupBox("Export table(s)")
        export_table_layout = QVBoxLayout()
        export_table_grp.setLayout(export_table_layout)
        export_table_grp.setStyleSheet("""
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
                color: #3f4c5a;
            }

            QComboBox::drop-down {
            border: none;
            }
            QComboBox::down-arrow {
                image: url(./drop_down_arrow.png);
            }
        """)

        table_list = [
            "Normalized retention table",
            "2D Combination table",
            "OM result table",
            "Orthogonality result correlation table",
            "Final result and ranking table",
        ]
        self.table_selection = CheckableTreeList(table_list)
        self.table_selection.setFixedHeight(175)

        self.table_export_directory_lineEdit = QLineEdit()
        self.table_export_directory_lineEdit.setText(os.getcwd())
        self.export_table_directory_btn = QPushButton("...")
        self.export_table_directory_btn.setFixedWidth(50)

        self.export_filename = QLineEdit()
        self.export_filename.setText("export_table.xlsx")

        export_table_directory_hlayout = QHBoxLayout()
        export_table_directory_hlayout.addWidget(self.table_export_directory_lineEdit)
        export_table_directory_hlayout.addWidget(self.export_table_directory_btn)

        self.export_table_btn = QPushButton("Export table(s)")

        export_table_layout.addWidget(QLabel("Select table to export:"))
        export_table_layout.addWidget(self.table_selection)
        export_table_layout.addWidget(QLabel("Export directory:"))
        export_table_layout.addLayout(export_table_directory_hlayout)
        export_table_layout.addWidget(QLabel("File name:"))
        export_table_layout.addWidget(self.export_filename)
        export_table_layout.addWidget(self.export_table_btn)

        # Assemble input column
        user_input_frame_layout.addWidget(export_figure_grp)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addWidget(export_table_grp)
        # user_input_frame_layout.addWidget(info_group)
        # user_input_frame_layout.addWidget(LineWidget('Horizontal'))
        user_input_frame_layout.addStretch()

        # ----- Right: Plot card (styles unchanged) ----------------------------
        plot_frame = QFrame()
        plot_frame.setStyleSheet("""
            background-color: #e7e7e7;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        plot_frame_layout = QVBoxLayout(plot_frame)
        plot_frame_layout.setContentsMargins(0, 0, 0, 0)

        plot_title = QLabel("Figure visualization")
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

        # Assemble top row
        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)
        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        # === (Optional) table section prepared, not added to splitter =========
        table_frame = QWidget()
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.styled_table = StyledTable("2D combination table")
        self.styled_table.set_header_label(
            ["Set #", "2D Combination", "Predicted 2D peak capacity"]
        )
        self.styled_table.set_default_row_count(10)
        table_frame_layout.addWidget(self.styled_table)

        self.table_frame_shadow = BoxShadow()
        self.styled_table.setGraphicsEffect(self.table_frame_shadow)

        # === Splitter & wiring ================================================
        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        # self.main_splitter.addWidget(table_frame)  # intentionally not shown by default
        self.main_layout.addWidget(self.main_splitter)

        # --- signals -----------------------------------------------------------
        self.export_figure_directory_btn.clicked.connect(self.create_figure_directory)
        self.export_table_directory_btn.clicked.connect(
            self.select_export_file_directory
        )
        self.save_figure_btn.clicked.connect(self.save_figure_list)
        self.export_table_btn.clicked.connect(self.export_tables)

    def init_page(self, om_list):
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        self.plot_utils.set_orthogonality_data(self.model.get_orthogonality_dict())
        data_sets_list = list(self.orthogonality_dict.keys())

        self.figure_list_chklist.add_items(data_sets_list)

        self.figure_type_chklist.clear()
        self.figure_type_chklist.add_items(om_list)

    def create_figure_directory(self):
        directory = QFileDialog.getExistingDirectory(self)
        if directory:
            self.figure_export_directory_lineEdit.setText(directory)

    def select_export_file_directory(self):
        directory = QFileDialog.getExistingDirectory(self)
        if directory:
            self.table_export_directory_lineEdit.setText(directory)

    def export_tables(self):
        select_directory = self.table_export_directory_lineEdit.text()
        file_path = f"{select_directory}/{self.export_filename.text()}"
        table_to_export_list = self.table_selection.get_checked_items()

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            for table_name in table_to_export_list:
                df = self.table_functions_map[table_name]()
                df.to_excel(writer, sheet_name=table_name, index=False)

    def save_figure_list(self):
        chosen_directory = self.figure_export_directory_lineEdit.text()
        chosen_folder_name = (
            f"{chosen_directory}/{self.figure_folder_name_lineEdit.text()}"
        )
        figure_type_list = self.figure_type_chklist.get_checked_item()
        figure_list_chklist = self.figure_list_chklist.get_checked_item()

        if os.path.exists(chosen_directory):
            if not os.path.exists(chosen_folder_name):
                os.mkdir(chosen_folder_name)

            for plot_type in figure_type_list:
                subdirectory_type_name = f"{chosen_folder_name}/{plot_type}"
                if not os.path.exists(subdirectory_type_name):
                    os.mkdir(subdirectory_type_name)
                # self.orthogonality_metric_combo.blockSignals(True)
                # self.orthogonality_metric_combo.setCurrentText(plot_type)
                # self.orthogonality_metric_combo.blockSignals(False)

                for figure_set_nb in figure_list_chklist:
                    self.save_figure(
                        plot_type=plot_type,
                        set_nb=figure_set_nb,
                        dirname=subdirectory_type_name,
                    )

    def save_figure(self, plot_type, set_nb, dirname):

        # 1) Grab the Figure from your persistent canvas

        # 2) Totally clear it, then re-add one Axes
        self.plot_utils.clean_figure()
        # ax = fig.add_subplot(111)
        #
        # self.plot_utils.set_axe(ax)

        if self.model.get_status() in ["loaded", "peak_capacity_loaded"]:
            self.plot_utils.plot_scatter(set_number=set_nb, dirname="")

        if plot_type in self.plot_functions_map:
            self.plot_functions_map[plot_type](
                set_number=set_nb
            )  # Call the corresponding function

        filename = f"{dirname}/{set_nb}.png"
        self.canvas.figure.savefig(
            filename, dpi=600, bbox_inches="tight", transparent=True
        )

    def plot_convex_hull(self, set_number):
        self.plot_utils.plot_convex_hull(set_number=set_number)

    def plot_percent_bin(self, set_number):
        self.plot_utils.plot_percent_bin(set_number=set_number)

    def plot_bin_box(self, set_number):
        self.plot_utils.plot_bin_box(set_number=set_number)

    # Plot methods
    def plot_asterisk(self, set_number):
        self.plot_utils.plot_asterisk(set_number=set_number)

    def plot_linear_reg(self, set_number):
        self.plot_utils.plot_linear_reg(set_number=set_number)

    def plot_percent_fit_xy(self, set_number):
        self.plot_utils.plot_percent_fit_xy(set_number=set_number)

    def plot_percent_fit_yx(self, set_number):
        self.plot_utils.plot_percent_fit_yx(set_number=set_number)

    def plot_conditional_entropy(self, set_number):
        self.plot_utils.plot_conditional_entropy(set_number=set_number)

    def plot_modeling_approach(self, set_number):
        self.plot_utils.plot_modeling_approach(set_number=set_number)
