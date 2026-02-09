"""Dialog for handling missing retention time (NaN) values in chromatography data.

This module provides a dialog that allows users to configure how missing
retention time values (NaN) should be handled during data processing.

Two options are available:
1. Remove peaks if NaN percentage exceeds a threshold
2. Keep all peaks and leave NaN values blank
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)


class NanPolicyDialog(QDialog):
    """Dialog for configuring NaN retention time handling policy.

    Presents users with two options for handling missing retention time data:

    Option 1: Remove peaks if the percentage of NaN retention times exceeds
              a user-defined threshold (default 50%).

    Option 2: Keep all peaks and leave NaN values blank.

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
        self.setWindowTitle("NaN Retention Time Policy")

        main_layout = QVBoxLayout(self)

        # Create button box
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        # Create group box with styling
        groupbox = QGroupBox("Missing retention times (NaN)")
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
        summary = QLabel(
            "Missing retention time values (NaN) have been detected across the dataset"
        )
        summary.setWordWrap(True)

        # Option 1: Remove peaks above threshold
        self.option_remove = QRadioButton(
            'Option 1: Remove peak(s) if number of conditions with "NaN" '
            'retention time exceeds'
        )
        self.option_remove.setChecked(True)
        self.option_remove.setObjectName("option 1")

        # Option 2: Keep all peaks
        self.option_keep = QRadioButton(
            "Option 2: Keep peaks and leave NaNs blank."
        )
        self.option_keep.setObjectName("option 2")

        # Radio button group
        self.option_button_grp = QButtonGroup()
        self.option_button_grp.addButton(self.option_remove)
        self.option_button_grp.addButton(self.option_keep)
        self.option_button_grp.setExclusive(True)

        # Threshold spin box
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setSuffix("%")
        self.threshold_spin.setFixedWidth(73)
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(50)  # Default: 50%

        # Option 1 layout
        row1 = QHBoxLayout()
        row1.addWidget(self.option_remove, 1)
        row1.addWidget(self.threshold_spin, 0, Qt.AlignLeft)
        row1.addWidget(QLabel(" of total conditions"))

        # Explanatory note
        note = QLabel(
            'Note: Peak(s) with fewer "NaN" retention times than the threshold '
            'are kept, and the missing values remain blank.'
        )
        note.setWordWrap(True)

        # Assemble layout
        groupbox_layout.addWidget(summary)
        groupbox_layout.addLayout(row1)
        groupbox_layout.addWidget(note)
        groupbox_layout.addSpacing(4)
        groupbox_layout.addWidget(self.option_keep)

        # Connect signals
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.threshold_spin.valueChanged.connect(self.set_threshold)

    def set_threshold(self) -> None:
        """Update the model with the new threshold value.

        Called automatically when the threshold spin box value changes.

        Side Effects:
            - Calls model.set_nan_policy_threshold() if model exists
        """
        if self.model:
            self.model.set_nan_policy_threshold(self.threshold_spin.value())

    def accept(self) -> None:
        """Apply the selected NaN policy and close the dialog.

        Side Effects:
            - Calls model.clean_nan_value() with selected option
            - Closes dialog with accept status
        """
        if self.model:
            checked_option = self.option_button_grp.checkedButton()
            self.model.clean_nan_value(option=checked_option.objectName())

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
            self.threshold = 50
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