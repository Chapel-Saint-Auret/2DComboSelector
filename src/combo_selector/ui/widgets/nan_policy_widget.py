"""Dialog for retention-time data cleanup operations in chromatography data.

This module provides a dialog that allows users to configure how missing
retention time values and other quality issues should be handled during data
processing.

Available operations include removing compounds/conditions by missing-value
threshold, keeping blank values, and replacing retention times below
condition-specific thresholds with blank values.
"""

import sys

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QSizePolicy,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from combo_selector.ui.widgets.removal_summary_dialog import RemovalSummaryDialog
from combo_selector.ui.widgets.line_widget import LineWidget

class NanPolicyDialog(QDialog):
    """Dialog for configuring retention-time data cleanup operations.

    Presents users with options for handling missing retention time data and
    threshold-based retention-time blanking:

    Option 1: Remove peaks if the percentage of NaN retention times exceeds
              a user-defined threshold (default 50%).

    Option 2: Remove conditions if the percentage of missing values exceeds
              a user-defined threshold (default 50%).

    Option 3: Keep all compounds and leave missing values blank.

    Option 4: Replace retention times below loaded condition-specific
              thresholds with blank values.

    The dialog communicates with a model object to apply the selected policy.

    Attributes:
        model (object): Data model with methods:
            - set_nan_policy_threshold(int): Set NaN threshold percentage
            - clean_nan_value(option=str): Apply NaN cleaning policy
        option_remove (QRadioButton): Radio button for option 1 (remove peaks).
        option_keep (QRadioButton): Radio button for option 2 (keep peaks).
        threshold_spin (QSpinBox): Spin box for threshold percentage (0-100).
        option_button_grp (QButtonGroup): Group for radio buttons.

    Example:
        >>> class MockModel:
        ...     def set_nan_policy_threshold(self, value):
        ...         print(f"Threshold set to {value}%")
        ...     def clean_nan_value(self, option):
        ...         print(f"Cleaning with {option}")
        >>> 
        >>> model = MockModel()
        >>> dialog = NanPolicyDialog(model)
        >>> dialog.exec()
    """

    def __init__(self, model=None):
        """Initialize the NaN policy dialog.

        Args:
            model (object, optional): Data model to communicate policy settings.
                Should implement:
                - set_nan_policy_threshold(int): Set threshold
                - clean_nan_value(option=str): Apply policy
        """
        super().__init__()

        self.model = model
        main_layout = QVBoxLayout(self)

        self.setFixedWidth(600)

        # Create button box
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        # Create group box with styling
        groupbox = QGroupBox("Retention Time Data Cleanup Options")
        groupbox.setStyleSheet("""
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
            QLabel#sub-title {
                background-color: transparent;
                color: #2C3E50;
                font-family: "Segoe UI";
                font-weight: bold;
            }
        """)

        groupbox_layout = QVBoxLayout()
        groupbox.setLayout(groupbox_layout)

        main_layout.addWidget(groupbox)
        main_layout.addWidget(self.buttonBox)

        # Summary text
        font = QFont()
        font.setBold(True)
        summary = QLabel(
            "Select one or more cleanup operations to apply:"
        )
        summary.setFont(font)
        summary.setWordWrap(True)

        # Option 1: Remove peaks above threshold
        self.option_remove_compound = QRadioButton(
            "Remove compounds with missing values in more than"
        )
        # self.option_remove_compound.setChecked(True)
        self.option_remove_compound.setObjectName("option 1")

        # Option 2: Keep all peaks
        self.option_remove_condition = QRadioButton(
            'Remove conditions with more than'
        )
        self.option_remove_condition.setObjectName("option 2")

        self.option_replace = QRadioButton(
            'Keep all compounds and leave missing values empty'
        )
        self.option_replace.setChecked(True)

        self.option_replace.setObjectName("option 3")

        self.option_replace_below_threshold = QRadioButton(
            "Replace retention times below condition-specific thresholds with blank"
        )
        self.option_replace_below_threshold.setObjectName("option 4")

        # Radio button group
        self.option_button_grp = QButtonGroup()
        self.option_button_grp.addButton(self.option_remove_compound)
        self.option_button_grp.addButton(self.option_remove_condition)
        self.option_button_grp.addButton(self.option_replace)
        self.option_button_grp.addButton(self.option_replace_below_threshold)
        self.option_button_grp.setExclusive(False)

        self.update_button_state()

        # Threshold spin box
        self.threshold1_spin = QSpinBox()
        self.threshold1_spin.setSuffix("%")
        self.threshold1_spin.setFixedWidth(73)
        self.threshold1_spin.setRange(0, 100)
        self.threshold1_spin.setValue(50)  # Default: 50%

        # Threshold spin box
        self.threshold2_spin = QSpinBox()
        self.threshold2_spin.setSuffix("%")
        self.threshold2_spin.setFixedWidth(73)
        self.threshold2_spin.setRange(0, 100)
        self.threshold2_spin.setValue(50)  # Default: 50%

        # Option 1 layout
        row1 = QHBoxLayout()
        row1.addWidget(self.option_remove_compound)
        row1.addWidget(self.threshold1_spin)
        row1.addWidget(QLabel(" of condition."))

        row1.addStretch()

        # Option 2 layout
        row2 = QHBoxLayout()
        row2.addWidget(self.option_remove_condition)
        row2.addWidget(self.threshold2_spin)
        row2.addWidget(QLabel(" missing values."))
        # Explanatory note
        note = QLabel(
            'Note: Compounds below this threshold will be kept, and their missing values will remain empty.'
        )
        note.setWordWrap(True)

        self.rt_threshold_file_label = QLineEdit()
        self.rt_threshold_file_label.setPlaceholderText("No threshold file loaded...")
        self.rt_threshold_file_label.setReadOnly(True)

        self.rt_threshold_load_btn = QPushButton("Browse…")
        self.rt_threshold_load_btn.clicked.connect(self._load_rt_threshold_file)

        row4_file = QHBoxLayout()
        row4_file.addWidget(self.rt_threshold_file_label)
        row4_file.addWidget(self.rt_threshold_load_btn)

        self.rt_threshold_note = QLabel(
            "Load a single-row Excel file whose columns match the condition names. "
            "Each value is the minimum acceptable retention time for that condition. "
            "Any RT below this value will be replaced with blank."
        )
        self.rt_threshold_note.setWordWrap(True)

        # Assemble layout
        groupbox_layout.addWidget(summary)
        groupbox_layout.addWidget(self.option_replace)
        groupbox_layout.addWidget(LineWidget())
        groupbox_layout.addLayout(row1)
        groupbox_layout.addSpacing(4)
        groupbox_layout.addLayout(row2)
        groupbox_layout.addWidget(note)
        groupbox_layout.addWidget(LineWidget())
        groupbox_layout.addWidget(self.option_replace_below_threshold)
        groupbox_layout.addLayout(row4_file)
        groupbox_layout.addWidget(self.rt_threshold_note)

        # Connect signals
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.threshold1_spin.valueChanged.connect(self.set_threshold1)
        self.threshold2_spin.valueChanged.connect(self.set_threshold2)
        self.option_button_grp.buttonClicked.connect(self.update_button_state)

    def update_button_state(self):

        if self.option_replace.isChecked():
            self.option_button_grp.setExclusive(True)
            self.option_remove_compound.setChecked(False)
            self.option_remove_condition.setChecked(False)
            self.option_replace_below_threshold.setChecked(False)

        if (self.option_remove_compound.isChecked() or
                self.option_remove_condition.isChecked() or
                self.option_replace_below_threshold.isChecked()):
            self.option_button_grp.setExclusive(False)

    def _load_rt_threshold_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open RT Threshold File", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            sheet_names = pd.ExcelFile(file_path, engine="openpyxl").sheet_names
            selected_sheet, ok = QInputDialog.getItem(
                self, "Select Sheet", "Choose a sheet:", sheet_names, editable=False
            )
            if not ok:
                return

            if self.model:
                self.model.load_rt_below_threshold_data(file_path, selected_sheet)
                self.rt_threshold_file_label.setText(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load threshold file:\n{e}")

    def set_threshold1(self) -> None:
        """Update the model with the new threshold value.

        Called automatically when the threshold spin box value changes.

        Side Effects:
            - Calls model.set_nan_policy_threshold() if model exists
        """
        if self.model:
            self.model.set_nan_policy_option1_threshold(self.threshold1_spin.value())

    def set_threshold2(self) -> None:
        """Update the model with the new threshold value.

        Called automatically when the threshold spin box value changes.

        Side Effects:
            - Calls model.set_nan_policy_threshold() if model exists
        """
        if self.model:
            self.model.set_nan_policy_option2_threshold(self.threshold2_spin.value())

    def accept(self) -> None:
        """Apply the selected NaN policy and close the dialog.

        Side Effects:
            - Calls model.clean_nan_value() with selected option
            - Closes dialog with accept status
        """
        if self.model:

            checked_button =[button.objectName() for button in self.option_button_grp.buttons() if button.isChecked()]
            self.model.clean_nan_value(option_list=checked_button)

        compound_list = self.model.get_removed_compound_list()
        condition_list = self.model.get_removed_condition_list()

        dlg = RemovalSummaryDialog(
            compounds=compound_list,
            conditions=condition_list,
        )

        result = dlg.exec()

        super().accept()


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Example showing the NaN policy dialog with a mock model."""


    # Mock model to demonstrate the interface
    class MockDataModel:
        """Mock data model for demonstration purposes."""

        def __init__(self):
            """Initialize the mock model with default threshold."""
            self.policy = None

        def set_nan_policy_threshold(self, value: int) -> None:
            """Set the NaN threshold percentage.

            Args:
                value (int): Threshold percentage (0-100).
            """
            self.threshold = value
            print(f"✓ Threshold set to {value}%")

        def clean_nan_value(self, option: str) -> None:
            """Apply NaN cleaning policy.

            Args:
                option (str): Either "option 1" or "option 2".
            """
            self.policy = option

            if option == "option 1":
                print(f"✓ Removing peaks with >{self.threshold}% NaN retention times")
            else:
                print("✓ Keeping all peaks, leaving NaN values blank")


    app = QApplication(sys.argv)

    # Create mock model
    model = MockDataModel()

    # Create and show dialog
    dialog = NanPolicyDialog(model)

    result = dialog.exec()

    if result == QDialog.Accepted:
        print("\n--- Dialog accepted ---")
        print(f"Final threshold: {model.threshold}%")
        print(f"Selected policy: {model.policy}")
    else:
        print("\n--- Dialog cancelled ---")

    sys.exit(0)