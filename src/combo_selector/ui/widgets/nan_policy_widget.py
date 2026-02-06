# --- Missing RT (NaN) handling widget ---------------------------------------
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
    """
    Mock-up UI for handling missing retention times (NaN).
    Text + placeholder widgets only; no logic.
    """

    def __init__(self, model=None):
        super().__init__()

        self.model = model
        # self.setModal(False)

        main_layout = QVBoxLayout(self)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)

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

        # --- Summary text (static placeholder) ------------------------------
        summary = QLabel(
            "Missing retention time values (NaN) have been detected across the dataset"
        )
        summary.setWordWrap(True)

        # --- Option 1 -------------------------------------------------------
        self.option_remove = QRadioButton(
            'Option 1: Remove peak(s) if number of conditions with "NaN" retention time exceeds'
        )

        self.option_remove.setChecked(True)
        self.option_remove.setObjectName("option 1")

        # --- Option 2 -------------------------------------------------------
        self.option_keep = QRadioButton("Option 2: Keep peaks and leave NaNs blank.")
        self.option_keep.setObjectName("option 2")

        self.option_button_grp = QButtonGroup()
        self.option_button_grp.addButton(self.option_remove)
        self.option_button_grp.addButton(self.option_keep)
        self.option_button_grp.setExclusive(True)

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setSuffix("%")
        self.threshold_spin.setFixedWidth(73)
        self.threshold_spin.setRange(0, 100)  # placeholder range
        self.threshold_spin.setValue(50)  # placeholder default

        row1 = QHBoxLayout()
        row1.addWidget(self.option_remove, 1)
        row1.addWidget(self.threshold_spin, 0, Qt.AlignLeft)
        row1.addWidget(QLabel(" of total condition"))

        note = QLabel(
            'Note: Peak(s) with fewer "NaN" retention times than the threshold are kept, '
            "and the missing values remain blank."
        )
        note.setWordWrap(True)

        # --- Layout ---------------------------------------------------------

        groupbox_layout.addWidget(summary)
        groupbox_layout.addLayout(row1)
        groupbox_layout.addWidget(note)
        groupbox_layout.addSpacing(4)
        groupbox_layout.addWidget(self.option_keep)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.threshold_spin.valueChanged.connect(self.set_threshold)

    def set_threshold(self):
        self.model.set_nan_policy_threshold(self.threshold_spin.value())

    def accept(self):
        checked_option = self.option_button_grp.checkedButton()
        self.model.clean_nan_value(option=checked_option.objectName())

        super().accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NanPolicyDialog()
    window.show()
    sys.exit(app.exec())
