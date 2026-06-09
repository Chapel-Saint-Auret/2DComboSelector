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
from PySide6.QtGui import QIcon, QFont, QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
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
from combo_selector.ui.widgets.section_help_button import SectionHelpButton
from combo_selector.utils import resource_path
from combo_selector.constants import ICON_SIZE


class ImportDataPage(QFrame):
    """Page for importing and normalizing chromatography retention time data."""

    retention_time_loaded = Signal()
    exp_peak_capacities_loaded = Signal()
    retention_time_normalized = Signal()

    def __init__(self, model=None) -> None:
        super().__init__()

        self.model = model
        self.nan_policy_dialog = NanPolicyDialog(model=self.model)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.label_font = QFont()
        self.label_font.setPointSize(20)

        # === TOP AREA (two cards) =============================================
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        data_import_frame = self._create_data_import_card()
        normalization_section = self._create_normalization_card()

        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        # === BOTTOM AREA (normalized table) ===================================
        table_frame = QWidget()
        table_frame.setMinimumHeight(100)
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.normalized_data_table = StyledTable("Normalized Retention Time Table")
        self.normalized_data_table.set_header_label(
            ["Compound #", "Condition 1", "Condition 2", "...", "Condition n"]
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
        self.browse_btn.clicked.connect(self._browse_file)
        self.load_all_btn.clicked.connect(self._load_all)
        self.clean_retention_time_btn.clicked.connect(self.show_nan_policy_dialog)

    # ==========================================================================
    # Card builders
    # ==========================================================================

    def _create_data_import_card(self) -> QFrame:
        """Create the left card with a single file picker and per-data-type sheet selectors."""

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
                color: #2C3E50;
                font-weight: bold; 
                font-size: 14px;
                
            }
            QLabel#section_title {
                color: #154E9D;
                font-size: 16px;
                font-weight: bold;

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
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #bcc8f5; }
            QPushButton:pressed { background-color: #8fa3ef; }
            QPushButton:disabled { background-color: #E5E9F5; color: #FFFFFF; }
            QComboBox {
                background-color: #f5f6f7;
                border: 1px solid #d1d6dd;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 12px;
                color: #3f4c5a;
            }
            QComboBox:disabled {
                color: #aaaaaa;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)

        # --- Title bar -------------------------------------------------------
        data_import_title_bar = QFrame()
        data_import_title_bar.setFixedHeight(40)
        data_import_title_bar.setStyleSheet("QFrame { background-color: #183881; }")
        title_bar_layout = QHBoxLayout(data_import_title_bar)
        title_bar_layout.setContentsMargins(10, 0, 6, 0)
        title_bar_layout.setSpacing(4)

        data_import_title = QLabel("A: Data Import")
        data_import_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        data_import_title.setStyleSheet(
            "background-color: transparent; color: #ffffff; font-weight: bold; font-size: 19px;"
        )

        data_import_help_btn = SectionHelpButton(
            title="Data import",
            markdown_path="markdown/data_import.md",
            parent=data_import_title_bar,
        )
        data_import_help_btn.setFixedSize(22, 22)
        data_import_help_btn.setIconSize(QSize(16, 16))
        data_import_help_btn.setStyleSheet("""
            QToolButton { border: none; background: transparent; color: #ffffff; font-size: 15px; }
            QToolButton:hover { color: #c5d0e6; }
        """)

        title_bar_layout.addWidget(data_import_title, 0, Qt.AlignVCenter)
        title_bar_layout.addWidget(data_import_help_btn, 0, Qt.AlignVCenter)
        title_bar_layout.addStretch(1)

        # --- Inner content ---------------------------------------------------
        data_import_input_frame = QFrame(data_import_frame)
        inner_layout = QVBoxLayout(data_import_input_frame)
        inner_layout.setSpacing(8)
        inner_layout.setContentsMargins(16, 16, 16, 16)

        # -- Source file row --------------------------------------------------
        source_label = QLabel("Source File")
        source_label.setObjectName("section_title")

        self.source_file_lineedit = QLineEdit()
        self.source_file_lineedit.setFixedHeight(35)
        self.source_file_lineedit.setReadOnly(True)
        self.source_file_lineedit.setPlaceholderText("No file selected…")

        self.browse_btn = QPushButton(
            QIcon(resource_path("icons/folder_icon.png")), "Browse"
        )
        self.browse_btn.setIconSize(ICON_SIZE)
        self.browse_btn.setFixedHeight(35)

        file_row = QHBoxLayout()
        file_row.addWidget(self.source_file_lineedit)
        file_row.addWidget(self.browse_btn)

        # -- Sheet assignment separator ---------------------------------------
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #d1d6dd;")

        sheet_section_label = QLabel("Sheet Assignment")
        sheet_section_label.setObjectName("section_title")

        # Grid layout: col 0 = fixed-width labels, col 1 = combos (stretch), col 2 = status icons
        # All five rows (RT, PC, EC, void, gradient) share the same grid so columns align perfectly.
        assignment_grid_widget = QWidget()
        assignment_grid = QGridLayout(assignment_grid_widget)
        assignment_grid.setContentsMargins(0, 0, 0, 0)
        assignment_grid.setHorizontalSpacing(8)
        assignment_grid.setVerticalSpacing(6)
        assignment_grid.setColumnStretch(1, 1)   # combo column stretches
        assignment_grid.setColumnMinimumWidth(0, 195)  # fixed label column

        def _make_combo() -> QComboBox:
            combo = QComboBox()
            combo.setFixedHeight(32)
            combo.setEnabled(False)
            combo.setPlaceholderText("— select a sheet —")
            return combo

        def _make_row_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            return lbl

        # Row 0 — Retention times
        self.ret_time_import_status = Status()
        self.rt_combo = _make_combo()
        assignment_grid.addWidget(_make_row_label("Retention Times:"),        0, 0, Qt.AlignVCenter)
        assignment_grid.addWidget(self.rt_combo,                               0, 1)
        assignment_grid.addWidget(self.ret_time_import_status,                 0, 2, Qt.AlignVCenter)

        # Row 1 — 1D Peak capacities
        self.twoD_peak_status = Status()
        self.pc_combo = _make_combo()
        assignment_grid.addWidget(_make_row_label("1D Peak Capacities:"),     1, 0, Qt.AlignVCenter)
        assignment_grid.addWidget(self.pc_combo,                               1, 1)
        assignment_grid.addWidget(self.twoD_peak_status,                       1, 2, Qt.AlignVCenter)

        # Row 2 — Elution-composition ranges
        self.delta_ce_status = Status()
        self.ec_combo = _make_combo()
        assignment_grid.addWidget(_make_row_label("Elution-Comp. Ranges:"),   2, 0, Qt.AlignVCenter)
        assignment_grid.addWidget(self.ec_combo,                               2, 1)
        assignment_grid.addWidget(self.delta_ce_status,                        2, 2, Qt.AlignVCenter)

        # Row 3 — Void time (hidden until Void-Max or WOSEL)
        self.void_time_import_status = Status()
        self.void_time_combo = _make_combo()
        self._void_time_label_widget = _make_row_label("Void Time:")
        self._void_time_label_widget.setVisible(False)
        self.void_time_combo.setVisible(False)
        self.void_time_import_status.setVisible(False)
        assignment_grid.addWidget(self._void_time_label_widget,                3, 0, Qt.AlignVCenter)
        assignment_grid.addWidget(self.void_time_combo,                        3, 1)
        assignment_grid.addWidget(self.void_time_import_status,                3, 2, Qt.AlignVCenter)

        # Row 4 — Gradient end time (hidden until WOSEL)
        self.gradient_end_time_import_status = Status()
        self.gradient_end_time_combo = _make_combo()
        self._gradient_end_time_label_widget = _make_row_label("Gradient End Time:")
        self._gradient_end_time_label_widget.setVisible(False)
        self.gradient_end_time_combo.setVisible(False)
        self.gradient_end_time_import_status.setVisible(False)
        assignment_grid.addWidget(self._gradient_end_time_label_widget,        4, 0, Qt.AlignVCenter)
        assignment_grid.addWidget(self.gradient_end_time_combo,                4, 1)
        assignment_grid.addWidget(self.gradient_end_time_import_status,        4, 2, Qt.AlignVCenter)

        # Keep legacy attribute names that change_norm_svg uses for setVisible()
        # We wrap the grid cells in thin QWidget containers so the existing
        # setVisible(True/False) calls on void_time_widget / gradient_end_time_widget still work.
        self.void_time_widget = self.void_time_combo          # same object, alias
        self.void_time_label = self._void_time_label_widget
        self.gradient_end_time_widget = self.gradient_end_time_combo
        self.gradient_end_time_label = self._gradient_end_time_label_widget

        # Stubs for legacy load handlers that set filename text (now unused, kept for compat)
        self.add_void_time_filename = QLineEdit()
        self.add_gradient_end_time_filename = QLineEdit()

        # -- Data Cleanup + Load All row --------------------------------------
        self.clean_retention_time_btn = QPushButton(
            QIcon(resource_path("icons/setting_icon.png")), "Data Cleanup"
        )
        self.clean_retention_time_btn.setLayoutDirection(Qt.RightToLeft)
        self.clean_retention_time_btn.setIconSize(QSize(19, 19))
        self.clean_retention_time_btn.setFixedHeight(35)

        self.load_all_btn = QPushButton(
            QIcon(resource_path("icons/folder_icon.png")), "Load All"
        )
        self.load_all_btn.setIconSize(ICON_SIZE)
        self.load_all_btn.setFixedHeight(35)
        self.load_all_btn.setEnabled(False)

        action_row = QHBoxLayout()
        action_row.addStretch()
        action_row.addWidget(self.load_all_btn)
        action_row.addWidget(self.clean_retention_time_btn)

        # -- Assemble inner layout --------------------------------------------
        inner_layout.addStretch()
        inner_layout.addWidget(source_label)
        inner_layout.addLayout(file_row)
        inner_layout.addWidget(separator)
        inner_layout.addWidget(sheet_section_label)
        inner_layout.addWidget(assignment_grid_widget)
        inner_layout.addLayout(action_row)
        inner_layout.addStretch()

        data_import_layout.addWidget(data_import_title_bar)
        data_import_layout.addWidget(data_import_input_frame)

        return data_import_frame

    # ==========================================================================
    # New unified import logic
    # ==========================================================================

    def _browse_file(self) -> None:
        """Open a file dialog, then populate all sheet combos."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            sheet_names = pd.ExcelFile(file_path, engine="openpyxl").sheet_names
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read file:\n{e}")
            return

        self.source_file_lineedit.setText(file_path)
        self._current_file_path = file_path
        self._current_sheet_names = sheet_names

        all_combos = (
            self.rt_combo,
            self.pc_combo,
            self.ec_combo,
            self.void_time_combo,
            self.gradient_end_time_combo,
        )
        for combo in all_combos:
            combo.clear()
            combo.setEnabled(True)
            combo.addItem("— select a sheet —", userData=None)
            for name in sheet_names:
                combo.addItem(name, userData=name)
            combo.setCurrentIndex(0)

        # Reset statuses
        self.ret_time_import_status.set_wait()
        self.twoD_peak_status.set_wait()
        self.delta_ce_status.set_wait()
        self.void_time_import_status.set_wait()
        self.gradient_end_time_import_status.set_wait()

        self.load_all_btn.setEnabled(True)

        self._auto_select_sheets(sheet_names)

    def _auto_select_sheets(self, sheet_names: list[str]) -> None:
        """Heuristic pre-selection based on sheet name keywords."""
        rt_keywords   = ("rt", "retention", "time")
        pc_keywords   = ("peak", "cap", "1d")
        ec_keywords   = ("elut", "compo", "range", "delta", "ce")
        void_keywords = ("void",)
        grad_keywords = ("gradient", "grad", "end")

        def _find(keywords):
            for i, name in enumerate(sheet_names):
                if any(k in name.lower() for k in keywords):
                    return i + 1  # +1 because index 0 is the placeholder
            return 0

        pairs = [
            (self.rt_combo,                 _find(rt_keywords)),
            (self.pc_combo,                 _find(pc_keywords)),
            (self.ec_combo,                 _find(ec_keywords)),
            (self.void_time_combo,          _find(void_keywords)),
            (self.gradient_end_time_combo,  _find(grad_keywords)),
        ]
        for combo, idx in pairs:
            if idx:
                combo.setCurrentIndex(idx)

    def _load_all(self) -> None:
        """Load all assigned data types from the selected sheets in one click."""
        file_path = getattr(self, "_current_file_path", None)
        if not file_path:
            return

        rt_sheet = self.rt_combo.currentData()
        pc_sheet = self.pc_combo.currentData()
        ec_sheet = self.ec_combo.currentData()

        missing = []
        if rt_sheet:
            self._load_retention_data(file_path, rt_sheet)
            # missing.append("Retention Times")
        if pc_sheet:
            self._load_peak_capacities(file_path, pc_sheet)
            # missing.append("Experimental 1D Peak Capacities")
        if ec_sheet:
            self._load_elution_composition(file_path, ec_sheet)
            # missing.append("Elution-Composition Ranges")

        if missing:
            QMessageBox.warning(
                self,
                "Missing sheet assignment",
                "Please assign a sheet for:\n• " + "\n• ".join(missing),
            )
            return





        # Optional: void time and gradient end time if their rows are visible
        if self.void_time_combo.isVisible():
            void_sheet = self.void_time_combo.currentData()
            if void_sheet:
                self._load_void_from_combo(file_path, void_sheet)

        if self.gradient_end_time_combo.isVisible():
            grad_sheet = self.gradient_end_time_combo.currentData()
            if grad_sheet:
                self._load_gradient_from_combo(file_path, grad_sheet)

    def _load_retention_data(self, file_path: str, sheet: str) -> None:
        try:
            self.model.load_retention_time(filepath=file_path, sheetname=sheet)

            if self.model.get_status() == "error":
                self.ret_time_import_status.set_error()
                QMessageBox.critical(
                    self, "Error", "Failed to load Retention Times. Check the file format."
                )
                return

            self.ret_time_import_status.set_valid()
            self.normalization_status.set_wait()

            data = self.model.get_retention_time_df()
            self.normalized_data_table.set_header_label(list(data.columns))
            self.normalized_data_table.async_set_table_data(data)

            self.retention_time_loaded.emit()

        except Exception as e:
            self.ret_time_import_status.set_error()
            QMessageBox.critical(self, "Error", f"Retention Times:\n{e}")

    def _load_peak_capacities(self, file_path: str, sheet: str) -> None:
        try:
            self.model.load_hypothetical_2d_peak_capacity(
                filepath=file_path, sheetname=sheet
            )

            if self.model.get_status() == "error":
                self.twoD_peak_status.set_error()
            else:
                self.twoD_peak_status.set_valid()
                self.exp_peak_capacities_loaded.emit()

        except Exception as e:
            self.twoD_peak_status.set_error()
            QMessageBox.critical(self, "Error", f"1D Peak Capacities:\n{e}")

    def _load_elution_composition(self, file_path: str, sheet: str) -> None:
        try:
            self.model.load_elution_composition_space_area_data(
                filepath=file_path, sheetname=sheet
            )

            if self.model.get_status() == "error":
                self.delta_ce_status.set_error()
            else:
                self.delta_ce_status.set_valid()
                self.exp_peak_capacities_loaded.emit()

        except Exception as e:
            self.delta_ce_status.set_error()
            QMessageBox.critical(self, "Error", f"Elution-Composition Ranges:\n{e}")

    def _load_void_from_combo(self, file_path: str, sheet: str) -> None:
        try:
            self.model.load_void_time(filepath=file_path, sheetname=sheet)
            if self.model.get_status() == "error":
                self.void_time_import_status.set_error()
            else:
                self.void_time_import_status.set_valid()
        except Exception as e:
            self.void_time_import_status.set_error()
            QMessageBox.critical(self, "Error", f"Void Time:\n{e}")

    def _load_gradient_from_combo(self, file_path: str, sheet: str) -> None:
        try:
            self.model.load_gradient_end_time(filepath=file_path, sheetname=sheet)
            if self.model.get_status() == "error":
                self.gradient_end_time_import_status.set_error()
            else:
                self.gradient_end_time_import_status.set_valid()
        except Exception as e:
            self.gradient_end_time_import_status.set_error()
            QMessageBox.critical(self, "Error", f"Gradient End Time:\n{e}")

    # ==========================================================================
    # Normalization card (unchanged from original)
    # ==========================================================================

    def _create_normalization_card(self) -> QFrame:
        """Create the right card containing normalization method selection."""

        separation_space_scaling_bar = QFrame()
        separation_space_scaling_bar.setFixedHeight(40)
        separation_space_scaling_bar.setStyleSheet(
            "QFrame { background-color: #183881; }"
        )

        title_bar_layout = QHBoxLayout(separation_space_scaling_bar)
        title_bar_layout.setContentsMargins(10, 0, 6, 0)
        title_bar_layout.setSpacing(4)

        separation_space_scaling_title = QLabel("B: Data Normalization")
        separation_space_scaling_title.setObjectName("TitleBar")
        separation_space_scaling_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        separation_space_scaling_title.setStyleSheet(
            "background-color: transparent; color: #ffffff; font-weight: bold; font-size: 19px;"
        )

        separation_space_scaling_help_btn = SectionHelpButton(
            title="Data Normalization",
            markdown_path="markdown/normalization.md",
            parent=separation_space_scaling_bar,
        )
        separation_space_scaling_help_btn.setFixedSize(22, 22)
        separation_space_scaling_help_btn.setIconSize(QSize(16, 16))
        separation_space_scaling_help_btn.setStyleSheet("""
            QToolButton { border: none; background: transparent; color: #ffffff; font-size: 15px; }
            QToolButton:hover { color: #c5d0e6; }
        """)

        title_bar_layout.addWidget(separation_space_scaling_title, 0, Qt.AlignVCenter)
        title_bar_layout.addWidget(separation_space_scaling_help_btn, 0, Qt.AlignVCenter)
        title_bar_layout.addStretch(1)

        select_scaling_input_frame = QFrame()
        select_scaling_input_frame_layout = QHBoxLayout(select_scaling_input_frame)
        select_scaling_input_frame_layout.setContentsMargins(40, 40, 40, 40)

        scaling_method_group = QGroupBox("Select Scaling Method")
        scaling_method_layout = QVBoxLayout()
        scaling_method_group.setLayout(scaling_method_layout)
        scaling_method_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px; font-weight: bold; background-color: #e7e7e7;
                color: #154E9D; border: 1px solid #d0d4da; border-radius: 12px; margin-top: 25px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0px; margin-top: -8px;
            }
            QRadioButton, QCheckBox {
                background-color: transparent; font-size: 14px; font-weight: bold; color: #2C3E50;
            }
            QPushButton {
                background-color: #d5dcf9; font-size: 15px; font-weight: bold;
                color: #2C3346; border: none; border-radius: 6px; padding: 8px 16px;
            }
            QPushButton:hover { background-color: #bcc8f5; }
            QPushButton:pressed { background-color: #8fa3ef; }
            QPushButton:disabled { background-color: #E5E9F5; color: #FFFFFF; }
        """)

        self.normalize_btn = QPushButton("Normalize Data")
        self.normalization_status = Status()

        self.min_max_scaling_btn = QRadioButton("min-max Scaling")
        self.min_max_scaling_btn.setObjectName("min_max")
        self.min_max_scaling_btn.setChecked(True)

        self.void_max_scaling_btn = QRadioButton("void–max Scaling")
        self.void_max_scaling_btn.setObjectName("void_max")

        self.wosel_btn = QRadioButton("WOSEL Scaling")
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

        scale_row = QHBoxLayout()
        scale_row.setAlignment(Qt.AlignVCenter)
        scale_row.addWidget(radio_widget)
        scale_row.addWidget(svg_container)

        scale_col = QVBoxLayout()
        scale_col.addStretch()
        scale_col.addLayout(scale_row)
        scale_col.addStretch()

        normalization_button_layout = QHBoxLayout()
        normalization_button_layout.addWidget(self.normalize_btn)
        normalization_button_layout.addWidget(self.normalization_status)

        scaling_method_layout.addLayout(scale_col)
        scaling_method_layout.addSpacing(10)
        scaling_method_layout.addLayout(normalization_button_layout)

        select_scaling_input_frame_layout.addWidget(scaling_method_group)

        normalization_section = QFrame()
        normalization_section.setStyleSheet(
            "background-color: #f3f3f3; border-top-left-radius: 10px; border-top-right-radius: 10px;"
        )
        normalization_layout = QVBoxLayout(normalization_section)
        normalization_layout.setSpacing(0)
        normalization_layout.setContentsMargins(0, 0, 0, 0)
        normalization_layout.addWidget(separation_space_scaling_bar)
        normalization_layout.addWidget(select_scaling_input_frame)

        return normalization_section

    # ==========================================================================
    # Event handlers
    # ==========================================================================

    def change_norm_svg(self) -> None:
        button_checked = self.radio_button_group.checkedButton()
        method = button_checked.objectName()

        def _set_void_visible(v: bool) -> None:
            self._void_time_label_widget.setVisible(v)
            self.void_time_combo.setVisible(v)
            self.void_time_import_status.setVisible(v)

        def _set_gradient_visible(v: bool) -> None:
            self._gradient_end_time_label_widget.setVisible(v)
            self.gradient_end_time_combo.setVisible(v)
            self.gradient_end_time_import_status.setVisible(v)

        if method == "min_max":
            self.scaling_method_svg_qstack.setCurrentIndex(0)
            _set_void_visible(False)
            _set_gradient_visible(False)

        elif method == "void_max":
            self.scaling_method_svg_qstack.setCurrentIndex(1)
            _set_void_visible(True)
            _set_gradient_visible(False)

        elif method == "wosel":
            self.scaling_method_svg_qstack.setCurrentIndex(2)
            _set_void_visible(False)
            _set_gradient_visible(True)

    def normalize_retention_time(self) -> None:
        button_checked = self.radio_button_group.checkedButton()
        method = button_checked.objectName()

        try:
            self.model.normalize_retention_time(method)
            self.normalization_status.set_valid()

            data = self.model.get_normalized_retention_time_df()
            self.normalized_data_table.async_set_table_data(data)

            self.retention_time_normalized.emit()

        except Exception as e:
            self.normalization_status.set_error()
            QMessageBox.critical(self, "Error", f"Cannot normalize data:\n{e}")

    def show_nan_policy_dialog(self) -> None:
        self.nan_policy_dialog.exec()

        data = self.model.get_retention_time_df()
        if not data.empty:
            self.normalized_data_table.async_set_table_data(data)
            self.retention_time_loaded.emit()
