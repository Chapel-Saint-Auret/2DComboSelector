import openpyxl
import pandas as pd
from PySide6.QtGui import QIcon, QColor
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QInputDialog,
    QLabel, QLineEdit, QFrame, QPushButton, QGroupBox, QMessageBox,
    QSizePolicy, QSplitter, QStackedWidget,
    QGraphicsDropShadowEffect, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QSize, Signal

from combo_selector.utils import resource_path
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.ui.widgets.status_icon import Status

PLOT_SIZE = QSize(600, 400)

class ImportDataPage(QFrame):

    retention_time_loaded = Signal()
    exp_peak_capacities_loaded = Signal()
    retention_time_normalized = Signal()

    def __init__(self, model=None, title='Unnamed'):
        super().__init__()

        self.model = model

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 100))

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.NoFrame)
        top_frame.setGraphicsEffect(self.shadow)
        top_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(25, 25, 25, 25)
        top_frame_layout.setSpacing(25)

        # ====== INFORMATION SECTION ======
        separation_space_scaling_title = QLabel("Separation Space Scaling")
        separation_space_scaling_title.setFixedHeight(30)
        separation_space_scaling_title.setObjectName("TitleBar")
        separation_space_scaling_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        separation_space_scaling_title.setContentsMargins(10, 0, 0, 0)
        separation_space_scaling_title.setStyleSheet("""
            background-color: #154E9D;
            color: white;
            font-weight:bold;
            font-size: 15px;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            margin-bottom: 0px;
        """)


        user_input_frame = QFrame()
        user_input_frame.setStyleSheet("background-color: white; border-radius: 0px;")
        user_input_frame_layout = QHBoxLayout(user_input_frame)
        user_input_frame_layout.setContentsMargins(40, 40, 40, 40)

        # --- GROUP BOX ---
        scaling_method_group = QGroupBox("Select scaling method")
        scaling_method_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                background-color: white;
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
            color: #2C3E50;              /* dark slate navy */
            
            }

            QPushButton {
                background-color: #d5dcf9;
                color: #2C3346;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: 600;
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
        """)

        # --- MAIN LAYOUT ---
        scaling_method_layout = QVBoxLayout()

        # --- Normalize Button ---
        self.normalize_btn = QPushButton("Normalize data")

        # --- RADIO BUTTONS ---
        self.min_max_scaling_btn = QRadioButton("Min-Max scaling")
        self.min_max_scaling_btn.setObjectName('min_max')
        self.min_max_scaling_btn.setChecked(True)

        self.void_max_scaling_btn = QRadioButton("Void – Max scaling")
        self.void_max_scaling_btn.setObjectName('void_max')

        self.wosel_btn = QRadioButton("WOSEL")
        self.wosel_btn.setObjectName('wosel')

        # --- GROUP RADIO BUTTONS ---
        self.radio_button_group = QButtonGroup()
        self.radio_button_group.addButton(self.min_max_scaling_btn)
        self.radio_button_group.addButton(self.void_max_scaling_btn)
        self.radio_button_group.addButton(self.wosel_btn)
        self.radio_button_group.setExclusive(True)

        # --- RADIO LAYOUT ---
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.min_max_scaling_btn)
        radio_layout.addWidget(self.void_max_scaling_btn)
        radio_layout.addWidget(self.wosel_btn)
        # radio_layout.addStretch()

        radio_widget = QWidget()
        radio_widget.setStyleSheet("background-color: transparent;")
        radio_widget.setLayout(radio_layout)
        radio_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        radio_widget.setMaximumWidth(200)

        # --- SVG STACK ---
        self.scaling_method_svg_qstack = QStackedWidget()
        # self.scaling_method_svg_qstack.setFixedHeight(100)

        self.norm_min_max_svg = QSvgWidget()

        self.norm_min_max_svg.load(resource_path('icons/norm_min_max.svg'))
        self.norm_min_max_svg.setAttribute(Qt.WA_TranslucentBackground)
        self.norm_min_max_svg.setStyleSheet("background: transparent;")
        self.norm_min_max_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.norm_void_max_svg = QSvgWidget()
        self.norm_void_max_svg.setAttribute(Qt.WA_TranslucentBackground)
        self.norm_void_max_svg.setStyleSheet("background: transparent;")
        self.norm_void_max_svg.load(resource_path('icons/norm_void_max.svg'))
        self.norm_void_max_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.norm_wosel_svg = QSvgWidget()
        self.norm_wosel_svg.setAttribute(Qt.WA_TranslucentBackground)
        self.norm_wosel_svg.setStyleSheet("background: transparent;")
        self.norm_wosel_svg.load(resource_path('icons/norm_wosel.svg'))
        self.norm_wosel_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.scaling_method_svg_qstack.addWidget(self.norm_min_max_svg)
        self.scaling_method_svg_qstack.addWidget(self.norm_void_max_svg)
        self.scaling_method_svg_qstack.addWidget(self.norm_wosel_svg)

        # --- SVG CONTAINER ---
        svg_container = QWidget()
        # svg_container.setFixedSize(QSize(218*1.2, 93*1.2))
        svg_layout = QVBoxLayout()
        svg_layout.addStretch()  # Top stretch
        svg_layout.addWidget(self.scaling_method_svg_qstack, alignment=Qt.AlignCenter)  # Center SVG horizontally
        svg_layout.addStretch()  # Bottom stretch
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_container.setLayout(svg_layout)
        svg_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow vertical growth

        # --- HORIZONTAL LAYOUT (Left + Right) ---
        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignVCenter)  # Ensure row is vertically centered in parent
        hlayout.addWidget(radio_widget)
        hlayout.addWidget(svg_container)

        # --- VERTICAL CENTERING ---
        centered_layout = QVBoxLayout()
        centered_layout.addStretch()
        centered_layout.addLayout(hlayout)
        centered_layout.addStretch()

        # --- FINAL ASSEMBLY ---
        scaling_method_layout.addLayout(centered_layout)
        scaling_method_layout.addSpacing(10)
        scaling_method_layout.addWidget(self.normalize_btn, alignment=Qt.AlignCenter)

        scaling_method_group.setLayout(scaling_method_layout)

        user_input_frame_layout.addWidget(scaling_method_group)

        normalization_section = QFrame()
        normalization_layout = QVBoxLayout(normalization_section)
        normalization_layout.setSpacing(0)
        normalization_layout.setContentsMargins(0, 0, 0, 0)
        normalization_layout.addWidget(separation_space_scaling_title)
        normalization_layout.addWidget(user_input_frame)

        # ====== DATA FILES SECTION (clean and squared) ======
        import_data_inner_frame = QFrame()

        import_data_inner_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
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
                background-color: #f1f3f6;
                border: none;
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #e1e6ec;
            }
        """)

        import_data_inner_layout = QVBoxLayout(import_data_inner_frame)
        # import_data_inner_layout.setSpacing(10)
        # import_data_inner_layout.setContentsMargins(20, 20, 20, 20)

        # Retention time
        self.add_ret_time_btn = QPushButton(QIcon("Circle-icons-folder.png"), 'Import')
        self.add_ret_time_btn.setFixedHeight(24)
        self.add_ret_time_filename = QLineEdit()
        self.add_ret_time_filename.setFixedHeight(24)
        self.ret_time_import_status = Status()
        norm_layout = QHBoxLayout()
        norm_layout.addWidget(self.add_ret_time_filename)
        norm_layout.addWidget(self.add_ret_time_btn)
        norm_layout.addWidget(self.ret_time_import_status)

        # 1D peak capacity
        self.add_2D_peak_data_btn = QPushButton(QIcon("Circle-icons-folder.png"), 'Import')
        self.add_2D_peak_data_btn.setFixedHeight(24)
        self.add_2D_peak_data_linedit = QLineEdit()
        self.add_2D_peak_data_linedit.setFixedHeight(24)
        self.twoD_peak_status = Status()
        peak_layout = QHBoxLayout()
        peak_layout.addWidget(self.add_2D_peak_data_linedit)
        peak_layout.addWidget(self.add_2D_peak_data_btn)
        peak_layout.addWidget(self.twoD_peak_status)



        # Retention time
        self.add_void_time_btn = QPushButton(QIcon("Circle-icons-folder.png"), 'Import')
        self.add_void_time_btn.setFixedHeight(24)
        self.add_void_time_filename = QLineEdit()
        self.add_void_time_filename.setFixedHeight(24)
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


        # Retention time
        self.add_gradient_end_time_btn = QPushButton(QIcon("Circle-icons-folder.png"), 'Import')

        self.add_gradient_end_time_btn.setFixedHeight(24)
        self.add_gradient_end_time_filename = QLineEdit()
        self.add_gradient_end_time_filename.setFixedHeight(24)
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

        # Add widgets to layout
        import_data_inner_layout.addStretch()
        import_data_inner_layout.addWidget(QLabel("Retention times:"))
        import_data_inner_layout.addLayout(norm_layout)
        import_data_inner_layout.addWidget(QLabel("Experimental 1D peak capacities:"))
        import_data_inner_layout.addLayout(peak_layout)
        import_data_inner_layout.addWidget(self.void_time_label)
        import_data_inner_layout.addWidget(self.void_time_widget)
        import_data_inner_layout.addWidget(self.gradient_end_time_label)
        import_data_inner_layout.addWidget(self.gradient_end_time_widget)
        import_data_inner_layout.addStretch()

        # === Title Bar + Wrapping Frame ===
        data_file_title = QLabel("Data import")
        data_file_title.setFixedHeight(30)
        data_file_title.setObjectName("TitleBar")
        data_file_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        data_file_title.setContentsMargins(10, 0, 0, 0)
        data_file_title.setStyleSheet("""
            background-color: #154E9D;
            color: white;
            font-weight:bold;
            font-size: 15px;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            margin-bottom: 0px;
        """)

        import_data_frame = QFrame()
        import_data_layout = QVBoxLayout(import_data_frame)
        import_data_layout.setSpacing(0)
        import_data_layout.setContentsMargins(0, 0, 0, 0)
        import_data_layout.addWidget(data_file_title)
        import_data_layout.addWidget(import_data_inner_frame)

        # ====== NORMALIZED TABLE SECTION (optional below) ======
        table_frame = QFrame()
        self.shadow1 = QGraphicsDropShadowEffect(self)
        self.shadow1.setBlurRadius(20)
        self.shadow1.setXOffset(0)
        self.shadow1.setYOffset(0)
        self.shadow1.setColor(QColor(0, 0, 0, 100))
        table_frame.setGraphicsEffect(self.shadow1)
        table_frame.setStyleSheet("QFrame { background-color: transparent; }")
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.normalized_data_table = StyledTable("Normalized Retention time table")
        self.normalized_data_table.set_header_label(["Peak #", "Condition 1", "Condition 2", "...", "Condition n"])
        self.normalized_data_table.set_default_row_count(10)
        table_frame_layout.addWidget(self.normalized_data_table)

        # ====== FINAL ASSEMBLY ======
        top_frame_layout.addWidget(import_data_frame,50)
        top_frame_layout.addWidget(normalization_section,50)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)

        self.main_layout.addWidget(self.main_splitter)

        self.radio_button_group.buttonClicked.connect(self.change_norm_svg)
        self.normalize_btn.clicked.connect(self.normalize_retention_time)
        self.add_ret_time_btn.clicked.connect(self.load_retention_data)
        self.add_2D_peak_data_btn.clicked.connect(self.load_experimental_peak_capacities)
        self.add_void_time_btn.clicked.connect(self.load_void_time_data)
        self.add_gradient_end_time_btn.clicked.connect(self.load_gradient_end_time_data)

    # ==============================
    # Data Handling & Selection
    # =============================*
    #

    def change_norm_svg(self):
        button_checked = self.radio_button_group.checkedButton()
        method = button_checked.objectName()

        if method == 'min_max':
            self.scaling_method_svg_qstack.setCurrentIndex(0)
            self.void_time_widget.setVisible(False)
            self.gradient_end_time_widget.setVisible(False)
            self.void_time_label.setVisible(False)
            self.gradient_end_time_label.setVisible(False)

        if method == 'void_max':
            self.scaling_method_svg_qstack.setCurrentIndex(1)
            self.void_time_widget.setVisible(True)
            self.void_time_label.setVisible(True)
            self.gradient_end_time_widget.setVisible(False)
            self.gradient_end_time_label.setVisible(False)

        if method == 'wosel':
            self.scaling_method_svg_qstack.setCurrentIndex(2)
            self.void_time_widget.setVisible(True)
            self.void_time_label.setVisible(True)
            self.gradient_end_time_widget.setVisible(True)
            self.gradient_end_time_label.setVisible(True)


    def normalize_retention_time(self):
        button_checked = self.radio_button_group.checkedButton()
        method = button_checked.objectName()
        self.model.normalize_retention_time(method)

        data = self.model.get_normalized_retention_time_df()


        self.normalized_data_table.async_set_table_data(data)

        self.retention_time_normalized.emit()


    def load_retention_data(self) -> None:
        """
        Opens a file dialog to select and load an Excel file containing normalized retention data.

        - Allows the user to select an Excel file and choose a sheet.
        - Loads the selected sheet into the `Orthogonality` model.
        - Updates the UI components accordingly.
        - Displays an error message and updates the GUI if loading fails.

        Raises:
            - FileNotFoundError: If the user cancels the file selection.
            - ValueError: If the selected sheet is invalid.
            - Exception: For unexpected errors.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")

        if not file_path:
            return  # User canceled the selection

        try:
            sheet_names = pd.ExcelFile(file_path, engine="openpyxl").sheet_names
            selected_sheet, ok = QInputDialog.getItem(self, "Select Sheet", "Choose a sheet:", sheet_names,
                                                      editable=False)

            if not ok:
                raise ValueError("No sheet selected")

            self.model.load_2d_set(filepath=file_path, sheetname=selected_sheet)

            if self.model.get_status() == "error":
                self.ret_time_import_status.set_error()
                QMessageBox.critical(self, "Error", "Failed to load the data. Please check the file format.")
                return

            # Successful load: update UI
            self.ret_time_import_status.set_valid()
            self.add_ret_time_filename.setText(file_path)

            data = self.model.get_retention_time_df()

            self.normalized_data_table.set_header_label(list(data.columns))

            self.normalized_data_table.async_set_table_data(data)

            self.retention_time_loaded.emit()

        except ValueError as e:
            self.ret_time_import_status.set_error()  # Ensure GUI shows failure status
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            self.ret_time_import_status.set_error()  # Ensure GUI shows failure status
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{str(e)}")

    def load_experimental_peak_capacities(self):
        fileName = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if fileName[0]:
            try:
                sheet_names_list = pd.ExcelFile(fileName[0], engine='openpyxl').sheet_names
                sheet, ok = QInputDialog.getItem(self, 'Select excel sheet', 'select sheet', sheet_names_list)
            except:
                ok = False

            if ok:
                self.model.load_data_frame_2d_peak(filepath=fileName[0],
                                                   sheetname=sheet)

                status = self.model.get_status()

                if status == 'error':
                    self.twoD_peak_status.set_error()
                else:
                    self.twoD_peak_status.set_valid()
                    self.add_2D_peak_data_linedit.setText(fileName[0])
                    self.exp_peak_capacities_loaded.emit()
            else:
                self.twoD_peak_status.set_error()

    def load_gradient_end_time_data(self):
        fileName = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if fileName[0]:
            try:
                sheet_names_list = pd.ExcelFile(fileName[0], engine='openpyxl').sheet_names
                sheet, ok = QInputDialog.getItem(self, 'Select excel sheet', 'select sheet', sheet_names_list)
            except:
                ok = False

            if ok:
                self.model.load_gradient_end_time(filepath=fileName[0],
                                                   sheetname=sheet)

                status = self.model.get_status()

                if status == 'error':
                    self.gradient_end_time_import_status.set_error()
                else:
                    self.gradient_end_time_import_status.set_valid()
                    self.add_gradient_end_time_filename.setText(fileName[0])
            else:
                self.gradient_end_time_import_status.set_error()

    def load_void_time_data(self):
        fileName = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if fileName[0]:
            try:
                sheet_names_list = pd.ExcelFile(fileName[0], engine='openpyxl').sheet_names
                sheet, ok = QInputDialog.getItem(self, 'Select excel sheet', 'select sheet', sheet_names_list)
            except:
                ok = False

            if ok:
                self.model.load_void_time(filepath=fileName[0],
                                                   sheetname=sheet)

                status = self.model.get_status()

                if status == 'error':
                    self.void_time_import_status.set_error()
                else:
                    self.void_time_import_status.set_valid()
                    self.add_void_time_filename.setText(fileName[0])
            else:
                self.void_time_import_status.set_error()



