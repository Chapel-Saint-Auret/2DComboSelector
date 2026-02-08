"""Data import and normalization page for retention time data.

This module provides the ImportDataPage class which handles:
- Importing retention time data from Excel files
- Importing experimental 1D peak capacities
- Optional void time and gradient end time data
- Three normalization methods (Min-Max, Void-Max, WOSEL)
- NaN value cleaning
- Display of normalized retention timetable
"""

import pandas as pd
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from combo_selector.ui.widgets.nan_policy_widget import NanPolicyDialog
from combo_selector.ui.widgets.neumorphism import BoxShadow
from combo_selector.ui.widgets.status_icon import Status
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

# Icon size for folder buttons
ICON_SIZE = QSize(28, 28)


class ImportDataPage(QFrame):
    """Page for importing and normalizing chromatography retention time data.

    Provides a user interface for:
    - Loading retention time data from Excel files
    - Loading experimental 1D peak capacity data
    - Optionally loading void time and gradient end time
    - Selecting normalization method with visual formula display
    - Cleaning NaN values with customizable policies
    - Viewing normalized data in an interactive table

    The page is divided into three main sections:
    - Top-left: Data import controls
    - Top-right: Normalization method selection with SVG formulas
    - Bottom: Table displaying normalized retention times

    Attributes:
        model: Reference to the Orthogonality data model.
        nan_policy_dialog (NanPolicyDialog): Dialog for handling NaN values.
        normalized_data_table (StyledTable): Table displaying retention time data.
        radio_button_group (QButtonGroup): Exclusive radio buttons for scaling methods.
        scaling_method_svg_qstack (QStackedWidget): Stack of SVG formula displays.

    Signals:
        retention_time_loaded: Emitted when retention time data is successfully loaded.
        exp_peak_capacities_loaded: Emitted when peak capacity data is loaded.
        retention_time_normalized: Emitted when data normalization is complete.
    """

    retention_time_loaded = Signal()
    exp_peak_capacities_loaded = Signal()
    retention_time_normalized = Signal()

    def __init__(self, model=None) -> None:
        """Initialize the ImportDataPage with data import and normalization controls.

        Args:
            model: Orthogonality model instance for data management.

        Layout Structure:
            - Top section (side-by-side):
                - Left: Data import panel (retention times, peak capacities, optional data)
                - Right: Normalization method selection (Min-Max, Void-Max, WOSEL)
            - Bottom section:
                - Normalized retention timetable (resizable via splitter)
        """
        super().__init__()

        # --- Model & frame setup ----------------------------------------------
        self.model = model
        self.nan_policy_dialog = NanPolicyDialog(model=self.model)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP AREA (two cards) =============================================
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        # ----------------------------------------------------------------------
        # Left card: Data import
        # ----------------------------------------------------------------------
        data_import_frame = self._create_data_import_card()

        # ----------------------------------------------------------------------
        # Right card: Separation Space Scaling
        # ----------------------------------------------------------------------
        normalization_section = self._create_normalization_card()

        # Card shadow on the whole top row
        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        # === BOTTOM AREA (normalized table) ===================================
        table_frame = QWidget()
        table_frame.setMinimumHeight(100)
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.normalized_data_table = StyledTable("Normalized Retention time table")
        self.normalized_data_table.set_header_label(
            ["Peak #", "Condition 1", "Condition 2", "...", "Condition n"]
        )
        self.normalized_data_table.set_default_row_count(10)
        table_frame_layout.addWidget(self.normalized_data_table)

        self.table_frame_shadow = BoxShadow()
        self.normalized_data_table.setGraphicsEffect(self.table_frame_shadow)

        # === Final assembly ===================================================
        top_frame_layout.addWidget(data_import_frame, 50)
        top_frame_layout.addWidget(normalization_section, 50)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)
        self.main_splitter.setSizes([415, 293])

        self.main_layout.addWidget(self.main_splitter)

        # === Signal connections ===============================================
        self.radio_button_group.buttonClicked.connect(self.change_norm_svg)
        self.normalize_btn.clicked.connect(self.normalize_retention_time)
        self.add_ret_time_btn.clicked.connect(self.load_retention_data)
        self.add_2D_peak_data_btn.clicked.connect(
            self.load_experimental_peak_capacities
        )
        self.clean_retention_time_btn.clicked.connect(self.show_nan_policy_dialog)
        self.add_void_time_btn.clicked.connect(self.load_void_time_data)
        self.add_gradient_end_time_btn.clicked.connect(self.load_gradient_end_time_data)

    def _create_data_import_card(self) -> QFrame:
        """Create the left card containing data import controls.

        Returns:
            QFrame: Configured frame with import buttons and status indicators.
        """
        data_import_frame = QFrame()
        data_import_layout = QVBoxLayout(data_import_frame)
        data_import_layout.setSpacing(0)
        data_import_layout.setContentsMargins(0, 0, 0, 0)

        data_import_frame.setStyleSheet("""
            QFrame {
                background-color: #f3f3f3;
                border: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QLabel {
                color: #3f4c5a;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #f5f6f7;
                border: 1px solid #d1d6dd;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 12px;
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
            """)

        data_import_title = QLabel("Data import")
        data_import_title.setFixedHeight(30)
        data_import_title.setObjectName("TitleBar")
        data_import_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        data_import_title.setContentsMargins(10, 0, 0, 0)
        data_import_title.setStyleSheet("""
            background-color: #183881;
            color: #ffffff;
            font-weight: bold;
            font-size: 15px;
            margin-bottom: 0px;
            """)

        data_import_input_frame = QFrame(data_import_frame)
        data_import_inner_layout = QVBoxLayout(data_import_input_frame)

        # Retention times
        self.add_ret_time_btn = QPushButton(
            QIcon(resource_path("icons/folder_icon.png")), "Import"
        )
        self.clean_retention_time_btn = QPushButton("Clean NaN")
        self.add_ret_time_btn.setIconSize(ICON_SIZE)
        self.add_ret_time_btn.setFixedHeight(30)
        self.clean_retention_time_btn.setFixedHeight(30)
        self.add_ret_time_filename = QLineEdit()
        self.add_ret_time_filename.setFixedHeight(30)
        self.ret_time_import_status = Status()

        rt_layout = QHBoxLayout()
        rt_layout.addWidget(self.add_ret_time_filename)
        rt_layout.addWidget(self.add_ret_time_btn)
        rt_layout.addWidget(self.clean_retention_time_btn)
        rt_layout.addWidget(self.ret_time_import_status)

        # Experimental 1D peak capacities
        self.add_2D_peak_data_btn = QPushButton(
            QIcon(resource_path("icons/folder_icon.png")), "Import"
        )
        self.add_2D_peak_data_btn.setIconSize(ICON_SIZE)
        self.add_2D_peak_data_btn.setFixedHeight(30)
        self.add_2D_peak_data_linedit = QLineEdit()
        self.add_2D_peak_data_linedit.setFixedHeight(30)
        self.twoD_peak_status = Status()

        peak_layout = QHBoxLayout()
        peak_layout.addWidget(self.add_2D_peak_data_linedit)
        peak_layout.addWidget(self.add_2D_peak_data_btn)
        peak_layout.addWidget(self.twoD_peak_status)

        # Void time (hidden until Void-Max or WOSEL is selected)
        self.add_void_time_btn = QPushButton(
            QIcon(resource_path("icons/folder_icon.png")), "Import"
        )
        self.add_void_time_btn.setIconSize(ICON_SIZE)
        self.add_void_time_btn.setFixedHeight(30)
        self.add_void_time_filename = QLineEdit()
        self.add_void_time_filename.setFixedHeight(30)
        self.void_time_import_status = Status()

        self.void_time_widget = QWidget()
        self.void_time_widget.setVisible(False)
        void_time_layout = QHBoxLayout(self.void_time_widget)
        void_time_layout.setContentsMargins(0, 0, 0, 0)
        void_time_layout.addWidget(self.add_void_time_filename)
        void_time_layout.addWidget(self.add_void_time_btn)
        void_time_layout.addWidget(self.void_time_import_status)

        self.void_time_label = QLabel("Void time:")
        self.void_time_label.setVisible(False)

        # Gradient end time (hidden until WOSEL is selected)
        self.add_gradient_end_time_btn = QPushButton(
            QIcon(resource_path("icons/folder_icon.png")), "Import"
        )
        self.add_gradient_end_time_btn.setIconSize(ICON_SIZE)
        self.add_gradient_end_time_btn.setFixedHeight(30)
        self.add_gradient_end_time_filename = QLineEdit()
        self.add_gradient_end_time_filename.setFixedHeight(30)
        self.gradient_end_time_import_status = Status()

        self.gradient_end_time_widget = QWidget()
        self.gradient_end_time_widget.setVisible(False)
        gradient_end_time_layout = QHBoxLayout(self.gradient_end_time_widget)
        gradient_end_time_layout.setContentsMargins(0, 0, 0, 0)
        gradient_end_time_layout.addWidget(self.add_gradient_end_time_filename)
        gradient_end_time_layout.addWidget(self.add_gradient_end_time_btn)
        gradient_end_time_layout.addWidget(self.gradient_end_time_import_status)

        self.gradient_end_time_label = QLabel("Gradient end time:")
        self.gradient_end_time_label.setVisible(False)

        # Assemble left card content
        data_import_inner_layout.addStretch()
        data_import_inner_layout.addWidget(QLabel("Retention times:"))
        data_import_inner_layout.addLayout(rt_layout)
        data_import_inner_layout.addWidget(QLabel("Experimental 1D peak capacities:"))
        data_import_inner_layout.addLayout(peak_layout)
        data_import_inner_layout.addWidget(self.void_time_label)
        data_import_inner_layout.addWidget(self.void_time_widget)
        data_import_inner_layout.addWidget(self.gradient_end_time_label)
        data_import_inner_layout.addWidget(self.gradient_end_time_widget)
        data_import_inner_layout.addStretch()

        data_import_layout.addWidget(data_import_title)
        data_import_layout.addWidget(data_import_input_frame)

        return data_import_frame

    def _create_normalization_card(self) -> QFrame:
        """Create the right card containing normalization method selection.

        Returns:
            QFrame: Configured frame with radio buttons and SVG formula displays.
        """
        separation_space_scaling_title = QLabel("Separation Space Scaling")
        separation_space_scaling_title.setFixedHeight(30)
        separation_space_scaling_title.setObjectName("TitleBar")
        separation_space_scaling_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        separation_space_scaling_title.setContentsMargins(10, 0, 0, 0)
        separation_space_scaling_title.setStyleSheet("""
            background-color: #183881;
            color: #ffffff;
            font-weight: bold;
            font-size: 15px;
            margin-bottom: 0px;
            """)

        select_scaling_input_frame = QFrame()
        select_scaling_input_frame_layout = QHBoxLayout(select_scaling_input_frame)
        select_scaling_input_frame_layout.setContentsMargins(40, 40, 40, 40)

        scaling_method_group = QGroupBox("Select scaling method")
        scaling_method_layout = QVBoxLayout()
        scaling_method_group.setLayout(scaling_method_layout)
        scaling_method_group.setStyleSheet("""
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
                color: #2C3E50;
                font-family: "Segoe UI";
                font-size: 13px;
            }
            QRadioButton, QCheckBox {
                background-color: transparent;
                color: #2C3E50;
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
            """)

        self.normalize_btn = QPushButton("Normalize data")

        # Radio buttons (exclusive)
        self.min_max_scaling_btn = QRadioButton("Min-Max scaling")
        self.min_max_scaling_btn.setObjectName("min_max")
        self.min_max_scaling_btn.setChecked(True)

        self.void_max_scaling_btn = QRadioButton("Void – Max scaling")
        self.void_max_scaling_btn.setObjectName("void_max")

        self.wosel_btn = QRadioButton("WOSEL")
        self.wosel_btn.setObjectName("wosel")

        self.radio_button_group = QButtonGroup()
        self.radio_button_group.addButton(self.min_max_scaling_btn)
        self.radio_button_group.addButton(self.void_max_scaling_btn)
        self.radio_button_group.addButton(self.wosel_btn)
        self.radio_button_group.setExclusive(True)

        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.min_max_scaling_btn)
        radio_layout.addWidget(self.void_max_scaling_btn)
        radio_layout.addWidget(self.wosel_btn)

        radio_widget = QWidget()
        radio_widget.setStyleSheet("background-color: transparent;")
        radio_widget.setLayout(radio_layout)
        radio_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # SVG stack for formulas
        self.scaling_method_svg_qstack = QStackedWidget()

        self.norm_min_max_svg = QSvgWidget()
        self.norm_min_max_svg.load(resource_path("icons/norm_min_max.svg"))
        self.norm_min_max_svg.setAttribute(Qt.WA_TranslucentBackground)
        self.norm_min_max_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.norm_void_max_svg = QSvgWidget()
        self.norm_void_max_svg.setAttribute(Qt.WA_TranslucentBackground)
        self.norm_void_max_svg.setStyleSheet("background: transparent;")
        self.norm_void_max_svg.load(resource_path("icons/norm_void_max.svg"))
        self.norm_void_max_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.norm_wosel_svg = QSvgWidget()
        self.norm_wosel_svg.setAttribute(Qt.WA_TranslucentBackground)
        self.norm_wosel_svg.setStyleSheet("background: transparent;")
        self.norm_wosel_svg.load(resource_path("icons/norm_wosel.svg"))
        self.norm_wosel_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.scaling_method_svg_qstack.addWidget(self.norm_min_max_svg)
        self.scaling_method_svg_qstack.addWidget(self.norm_void_max_svg)
        self.scaling_method_svg_qstack.addWidget(self.norm_wosel_svg)

        svg_container = QFrame()
        svg_container.setStyleSheet("background-color: #e7e7e7;")
        svg_layout = QVBoxLayout(svg_container)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addStretch()
        svg_layout.addWidget(self.scaling_method_svg_qstack, alignment=Qt.AlignCenter)
        svg_layout.addStretch()
        svg_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Place radios (left) and svg (right) centered vertically
        scale_row = QHBoxLayout()
        scale_row.setAlignment(Qt.AlignVCenter)
        scale_row.addWidget(radio_widget)
        scale_row.addWidget(svg_container)

        scale_col = QVBoxLayout()
        scale_col.addStretch()
        scale_col.addLayout(scale_row)
        scale_col.addStretch()

        scaling_method_layout.addLayout(scale_col)
        scaling_method_layout.addSpacing(10)
        scaling_method_layout.addWidget(self.normalize_btn, alignment=Qt.AlignCenter)

        select_scaling_input_frame_layout.addWidget(scaling_method_group)

        normalization_section = QFrame()
        normalization_section.setStyleSheet(
            "background-color: #f3f3f3; border-top-left-radius: 10px; border-top-right-radius: 10px;"
        )
        normalization_layout = QVBoxLayout(normalization_section)
        normalization_layout.setSpacing(0)
        normalization_layout.setContentsMargins(0, 0, 0, 0)
        normalization_layout.addWidget(separation_space_scaling_title)
        normalization_layout.addWidget(select_scaling_input_frame)

        return normalization_section

    # ==========================================================================
    # Event Handlers & Data Operations
    # ==========================================================================

    def change_norm_svg(self) -> None:
        """Update the displayed normalization formula and show/hide optional inputs.

        Called when a different normalization radio button is selected.

        Side Effects:
            - Changes the displayed SVG formula
            - Shows/hides void time input for Void-Max and WOSEL
            - Shows/hides gradient end time input for WOSEL only
        """
        button_checked = self.radio_button_group.checkedButton()
        method = button_checked.objectName()

        if method == "min_max":
            self.scaling_method_svg_qstack.setCurrentIndex(0)
            self.void_time_widget.setVisible(False)
            self.gradient_end_time_widget.setVisible(False)
            self.void_time_label.setVisible(False)
            self.gradient_end_time_label.setVisible(False)

        elif method == "void_max":
            self.scaling_method_svg_qstack.setCurrentIndex(1)
            self.void_time_widget.setVisible(True)
            self.void_time_label.setVisible(True)
            self.gradient_end_time_widget.setVisible(False)
            self.gradient_end_time_label.setVisible(False)

        elif method == "wosel":
            self.scaling_method_svg_qstack.setCurrentIndex(2)
            self.void_time_widget.setVisible(True)
            self.void_time_label.setVisible(True)
            self.gradient_end_time_widget.setVisible(True)
            self.gradient_end_time_label.setVisible(True)

    def normalize_retention_time(self) -> None:
        """Normalize retention time data using the selected scaling method.

        Side Effects:
            - Normalizes data in the model
            - Updates the normalized data table display
            - Emits retention_time_normalized signal
        """
        button_checked = self.radio_button_group.checkedButton()
        method = button_checked.objectName()
        self.model.normalize_retention_time(method)

        data = self.model.get_normalized_retention_time_df()
        self.normalized_data_table.async_set_table_data(data)

        self.retention_time_normalized.emit()

    def show_nan_policy_dialog(self) -> None:
        """Open the NaN policy dialog for cleaning missing values.

        Side Effects:
            - Shows NaN policy dialog
            - Updates retention time data after cleaning
            - Updates the table display
            - Emits retention_time_loaded signal
        """
        self.nan_policy_dialog.exec()

        data = self.model.get_retention_time_df()
        self.normalized_data_table.async_set_table_data(data)

        self.retention_time_loaded.emit()

    def load_retention_data(self) -> None:
        """Load retention time data from an Excel file.

        Opens a file dialog for Excel file selection, prompts for sheet selection,
        and loads the data into the model. Handles NaN values if present.

        Side Effects:
            - Opens file and sheet selection dialogs
            - Loads data into model
            - Updates UI status indicators
            - Updates table display
            - May show NaN policy dialog if NaN values are present
            - Emits retention_time_loaded signal on success
            - Shows error messages on failure

        Raises:
            ValueError: If no sheet is selected.
            Exception: For unexpected file loading errors.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )

        if not file_path:
            return  # User canceled

        try:
            sheet_names = pd.ExcelFile(file_path, engine="openpyxl").sheet_names
            selected_sheet, ok = QInputDialog.getItem(
                self, "Select Sheet", "Choose a sheet:", sheet_names, editable=False
            )

            if not ok:
                raise ValueError("No sheet selected")

            self.model.load_retention_time(filepath=file_path, sheetname=selected_sheet)

            if self.model.get_status() == "error":
                self.ret_time_import_status.set_error()
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to load the data. Please check the file format.",
                )
                return

            # Successful load: update UI
            self.ret_time_import_status.set_valid()
            self.add_ret_time_filename.setText(file_path)

            data = self.model.get_retention_time_df()
            self.normalized_data_table.set_header_label(list(data.columns))
            self.normalized_data_table.async_set_table_data(data)

            # Show NaN policy dialog if needed
            if self.model.get_has_nan_value():
                self.nan_policy_dialog.exec_()
                data = self.model.get_retention_time_df()
                self.normalized_data_table.async_set_table_data(data)

            self.retention_time_loaded.emit()

        except ValueError as e:
            self.ret_time_import_status.set_error()
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            self.ret_time_import_status.set_error()
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred:\n{str(e)}"
            )

    def load_experimental_peak_capacities(self) -> None:
        """Load experimental 1D peak capacity data from an Excel file.

        Side Effects:
            - Opens file and sheet selection dialogs
            - Loads data into model
            - Updates UI status indicators
            - Emits exp_peak_capacities_loaded signal on success
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if fileName[0]:
            try:
                sheet_names_list = pd.ExcelFile(
                    fileName[0], engine="openpyxl"
                ).sheet_names
                sheet, ok = QInputDialog.getItem(
                    self, "Select excel sheet", "select sheet", sheet_names_list
                )
            except Exception:
                ok = False

            if ok:
                self.model.load_data_frame_2d_peak(
                    filepath=fileName[0], sheetname=sheet
                )

                status = self.model.get_status()

                if status == "error":
                    self.twoD_peak_status.set_error()
                else:
                    self.twoD_peak_status.set_valid()
                    self.add_2D_peak_data_linedit.setText(fileName[0])
                    self.exp_peak_capacities_loaded.emit()
            else:
                self.twoD_peak_status.set_error()

    def load_gradient_end_time_data(self) -> None:
        """Load gradient end time data from an Excel file.

        Required for WOSEL normalization method.

        Side Effects:
            - Opens file and sheet selection dialogs
            - Loads data into model
            - Updates UI status indicators
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if fileName[0]:
            try:
                sheet_names_list = pd.ExcelFile(
                    fileName[0], engine="openpyxl"
                ).sheet_names
                sheet, ok = QInputDialog.getItem(
                    self, "Select excel sheet", "select sheet", sheet_names_list
                )
            except Exception:
                ok = False

            if ok:
                self.model.load_gradient_end_time(filepath=fileName[0], sheetname=sheet)

                status = self.model.get_status()

                if status == "error":
                    self.gradient_end_time_import_status.set_error()
                else:
                    self.gradient_end_time_import_status.set_valid()
                    self.add_gradient_end_time_filename.setText(fileName[0])
            else:
                self.gradient_end_time_import_status.set_error()

    def load_void_time_data(self) -> None:
        """Load void time data from an Excel file.

        Required for Void-Max and WOSEL normalization methods.

        Side Effects:
            - Opens file and sheet selection dialogs
            - Loads data into model
            - Updates UI status indicators
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if fileName[0]:
            try:
                sheet_names_list = pd.ExcelFile(
                    fileName[0], engine="openpyxl"
                ).sheet_names
                sheet, ok = QInputDialog.getItem(
                    self, "Select excel sheet", "select sheet", sheet_names_list
                )
            except Exception:
                ok = False

            if ok:
                self.model.load_void_time(filepath=fileName[0], sheetname=sheet)

                status = self.model.get_status()

                if status == "error":
                    self.void_time_import_status.set_error()
                else:
                    self.void_time_import_status.set_valid()
                    self.add_void_time_filename.setText(fileName[0])
            else:
                self.void_time_import_status.set_error()