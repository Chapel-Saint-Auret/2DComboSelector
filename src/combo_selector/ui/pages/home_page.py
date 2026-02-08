import sys
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
)

from combo_selector.utils import resource_path

PLOT_SIZE = QSize(600, 400)


class HomePage(QFrame):

    data_loaded = Signal()
    peak_data_loaded = Signal()

    def __init__(self, model=None, title="Unnamed"):
        super().__init__()

        self.model = model

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Main frame
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        top_frame = QFrame()
        # top_frame.setStyleSheet('background-color: #f0f0f0;')
        top_frame_layout = QHBoxLayout(top_frame)

        user_input_scroll_area = QScrollArea()
        user_input_scroll_area.setFixedWidth(290)
        user_input_frame = QFrame()
        user_input_frame.setFixedWidth(280)
        user_input_frame_layout = QVBoxLayout(user_input_frame)
        # Scroll Area Properties
        user_input_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        user_input_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        user_input_scroll_area.setWidgetResizable(True)
        user_input_scroll_area.setWidget(user_input_frame)

        # Information Section
        info_group = QGroupBox("Info")

        info_group.setStyleSheet("""
            QGroupBox {
                 font-size: 18px;
                 font-weight: bold;
 
                border: 1px solid lightgray;
                border-radius: 10px;
                background-color: #e7e7e7;
                margin-top: 30px;  /* Moves the whole groupbox down */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;

                padding: 10px 10px;  /* More spacing around title */
                color:#3f4c5a;
                margin-top: -10px;  /* Moves title upwards */
            }
        """)

        info_layout = QVBoxLayout()
        self.textEdit = QLabel()
        self.textEdit.setTextFormat(Qt.TextFormat.RichText)  # Ensure rich text mode
        self.textEdit.setWordWrap(True)  # Enable text wrapping
        self.textEdit.setText(
            '<p><strong><span style="text-decoration: underline;">Step 1</span>: Data Plotting (Pairwise)</strong><br>'
            "Visualize the dataset by plotting pairwise combinations of variables to explore their relationships."
            "</p>"
            '<p><strong><span style="text-decoration: underline;">Step 2</span>: Select an Orthogonality Metric</strong><br>'
            "Choose from multiple orthogonality metrics, then display and compare them based on the selected dataset."
            "</p>"
            '<p><strong><span style="text-decoration: underline;">Step 3</span>: Correlation Matrix & Grouping</strong><br>'
            "Generate a heatmap of the correlation matrix and identify groups of correlated metrics based on a defined threshold."
            "</p>"
            '<p><strong><span style="text-decoration: underline;">Step 4</span>: Compute Scores & Rank Combinations</strong><br>'
            "Calculate orthogonality scores and rank the best metric combinations for further analysis."
            "</p>"
        )

        self.textEdit.setText(
            '<p><strong><span style="text-decoration: underline;">Step 1</span>: Pairwise Data Visualization</strong><br>'
            "Begin by plotting pairwise combinations of condition to visually assess potential correlations within the dataset."
            "</p>"
            '<p><strong><span style="text-decoration: underline;">Step 2</span>: Selection of Orthogonality Metrics</strong><br>'
            "Choose appropriate orthogonality metrics to evaluate the independence between condition, facilitating the identification of complementary separation modes."
            "</p>"
            '<p><strong><span style="text-decoration: underline;">Step 3</span>: Correlation Matrix and Group Formation</strong><br>'
            "Construct a correlation matrix heatmap to quantify relationships between metrics and define groups of correlated metrics based on a specified threshold."
            "</p>"
            '<p><strong><span style="text-decoration: underline;">Step 4</span>: Computation of Orthogonality Scores and Ranking</strong><br>'
            "Calculate orthogonality scores for the identified combinations and rank them to determine the most effective pairings  separation for comprehensive analysis."
            "</p>"
        )

        info_layout.addWidget(self.textEdit)
        info_layout.addStretch()

        info_group.setLayout(info_layout)

        user_input_frame_layout.addStretch()
        user_input_frame_layout.addWidget(info_group)
        user_input_frame_layout.addStretch()

        home_content_frame = QFrame()
        # home_content_frame.setLineWidth(5)
        home_content_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        # home_content_frame.setStyleSheet("border: 1px solid lightgray; border-radius: 1px;")
        home_content_frame_layout = QVBoxLayout(home_content_frame)
        home_content_frame_layout.setContentsMargins(5, 5, 5, 5)

        self.tool_presentation = QSvgWidget()
        # self.suggested_score.setFixedWidth(450)
        self.tool_presentation.load(resource_path("icons/home_page_monochrome.svg"))
        self.tool_presentation.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        home_content_frame_layout.addWidget(self.tool_presentation)

        # top_frame_layout.addWidget(user_input_scroll_area)
        # top_frame_layout.addWidget(home_content_frame)

        # self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        # self.main_splitter.addWidget(user_input_scroll_area)
        # self.main_splitter.addWidget(home_content_frame)

        # self.main_layout.addWidget(self.main_splitter)
        self.main_layout.addWidget(home_content_frame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HomePage()
    window.show()
    sys.exit(app.exec())
