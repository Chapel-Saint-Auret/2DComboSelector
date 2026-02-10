"""Redundancy check page for analyzing metric correlations.

This module provides the RedundancyCheckPage class which handles:
- Computing correlation matrices for orthogonality metrics
- Visualizing correlations via interactive heatmaps
- Hierarchical clustering to group similar metrics
- Highlighting correlated metrics with adjustable threshold
- Triangle matrix display (upper/lower) to reduce visual clutter
- Grouping correlated metrics in a results table
"""

import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch
import seaborn as sns
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.neumorphism import BoxShadow
from combo_selector.ui.widgets.qcombobox_cmap import QComboBoxCmap
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

# Maps full metric names to abbreviated display names for heatmap labels
METRIC_CORR_MAP = {
    "Convex hull relative area": "Convex hull",
    "Bin box counting": "Bin box",
    "Gilar-Watson method": "Gilar-Watson",
    "Modeling approach": "Mod approach",
    "Conditional entropy": "Cond entropy",
    "Pearson Correlation": "Pear corr",
    "Spearman Correlation": "Spea corr",
    "Kendall Correlation": "Kend corr",
    "Asterisk equations": "Asterisk",
    "NND Arithm mean": "NND Amean",
    "NND Geom mean": "NND Gmean",
    "NND Harm mean": "NND Hmean",
    "%FIT": "%FIT",
    "%BIN": "%BIN",
}

# Checkbox icon paths
checked_icon_path = resource_path("icons/checkbox_checked.svg").replace("\\", "/")
unchecked_icon_path = resource_path("icons/checkbox_unchecked.svg").replace("\\", "/")


class RedundancyCheckPage(QFrame):
    """Page for analyzing and visualizing metric correlations.

    Provides a comprehensive interface for:
    - Computing correlation matrices between orthogonality metrics
    - Interactive heatmap visualization with customizable color maps
    - Hierarchical clustering to group similar metrics
    - Highlighting metrics above a correlation threshold
    - Triangle matrix views (upper/lower) for cleaner display
    - Adjustable correlation threshold with tolerance
    - Results table showing grouped correlated metrics

    The page helps identify redundant metrics that provide similar
    information, allowing users to select a minimal set of non-redundant
    metrics for their analysis.

    Attributes:
        model: Reference to the Orthogonality data model.
        corr_matrix (DataFrame): Current correlation matrix.
        heatmap_mask (ndarray): Boolean mask for triangle display.
        highlight_heatmap_mask (ndarray): Mask for highlighting correlated cells.
        fig (Figure): Matplotlib figure for heatmap.
        canvas (FigureCanvas): Qt canvas for displaying figure.

    Signals:
        correlation_group_ready: Emitted when correlation groups are updated.
    """

    correlation_group_ready = Signal()

    def __init__(self, model=None):
        """Initialize the RedundancyCheckPage with controls and visualization.

        Args:
            model: Orthogonality model instance containing metric data.

        Layout Structure:
            - Top section (side-by-side):
                - Left: Input panel (correlation parameters, display options)
                - Right: Heatmap visualization
            - Bottom section:
                - Correlation groups table
        """
        super().__init__()

        # --- State ---------------------------------------------------------
        self.model = model
        self.corr_matrix = None
        self.heatmap_mask = True
        self.highlight_heatmap_mask = False

        # --- Page frame & base layout --------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === TOP AREA ======================================================
        top_frame = self._create_top_section()

        # === BOTTOM AREA: table ============================================
        table_frame = self._create_table_section()

        # === Splitter + main layout ========================================
        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)
        self.main_splitter.setSizes([486, 204])
        self.main_layout.addWidget(self.main_splitter)

        # --- Signal connections --------------------------------------------
        self.corr_mat_cmap.currentTextChanged.connect(
            self.update_correlation_matrix_cmap
        )
        self.correlation_threshold.editingFinished.connect(
            self.update_correlation_group_table
        )
        self.correlation_threshold_tolerance.editingFinished.connect(
            self.update_correlation_group_table
        )
        self.highlight_threshold.stateChanged.connect(
            self.highlight_correlation_threshold
        )
        self.hierarchical_clustering.stateChanged.connect(
            self.plot_correlation_heat_map
        )
        self.show_triangle_grp.buttonClicked.connect(self.plot_correlation_heat_map)

    def _create_top_section(self) -> QFrame:
        """Create the top section with input panel and heatmap.

        Returns:
            QFrame: Configured top frame with input and plot sections.
        """
        top_frame = QFrame()
        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        # Left: Input section
        input_section = self._create_input_panel()

        # Right: Plot section
        plot_frame = self._create_plot_panel()

        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)

        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        return top_frame

    def _create_input_panel(self) -> QFrame:
        """Create the left input panel with correlation parameters.

        Returns:
            QFrame: Input section containing parameter controls and info.
        """
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

        # Correlation parameter group
        correlation_parameter_group = self._create_correlation_parameter_group()

        # Info group
        info_page_group = self._create_info_group()

        user_input_frame_layout.addWidget(correlation_parameter_group)
        user_input_frame_layout.addWidget(LineWidget("Horizontal"))
        user_input_frame_layout.addStretch()
        user_input_frame_layout.addWidget(info_page_group)

        return input_section

    def _create_correlation_parameter_group(self) -> QGroupBox:
        """Create correlation parameter controls group.

        Returns:
            QGroupBox: Group box with color, threshold, and display options.
        """
        correlation_parameter_group = QGroupBox("Correlation matrix parameter")
        correlation_parameter_group.setStyleSheet(f"""
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
            QLabel, QCheckBox {{
                background-color: transparent;
                color: #3f4c5a;
            }}
            QCheckBox::indicator:unchecked,
            QTreeWidget::indicator:unchecked {{
                image: url("{unchecked_icon_path}");
            }}
            QCheckBox::indicator:checked,
            QTreeWidget::indicator:checked {{
                image: url("{checked_icon_path}");
            }}
        """)

        correlation_parameter_layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.corr_mat_cmap = QComboBoxCmap()
        self.corr_mat_cmap.setCurrentText("BrBG")

        self.correlation_threshold = QDoubleSpinBox()
        self.correlation_threshold.setValue(0.85)

        self.correlation_threshold_tolerance = QDoubleSpinBox()
        self.correlation_threshold_tolerance.setValue(0.0)
        self.correlation_threshold_tolerance.setToolTip("""
            <p>A tolerance of <strong>0</strong> means a metric is only considered correlated if its value is
            <strong>greater than or equal</strong> to the threshold. A tolerance of <strong>0.05</strong> allows metrics
            with correlation values as low as <strong>(threshold - 0.05)</strong> to still be considered correlated.
            For instance, if the threshold is <strong>0.85</strong>, metrics with correlation values down to <strong>0.80</strong>
            will be included.</p>
        """)

        self.highlight_threshold = QCheckBox("Show correlated metric")
        self.highlight_threshold.setChecked(False)

        self.hierarchical_clustering = QCheckBox("Show hierarchical clustering")
        self.hierarchical_clustering.setChecked(False)

        self.lower_triangle_matrix = QCheckBox("Show lower triangle matrix")
        self.lower_triangle_matrix.setChecked(False)

        self.upper_triangle_matrix = QCheckBox("Show upper triangle matrix")
        self.upper_triangle_matrix.setChecked(False)

        self.show_triangle_grp = QButtonGroup()
        self.show_triangle_grp.addButton(self.lower_triangle_matrix)
        self.show_triangle_grp.addButton(self.upper_triangle_matrix)
        self.show_triangle_grp.setExclusive(False)

        form_layout.addRow("Color:", self.corr_mat_cmap)
        form_layout.addRow("Correlation threshold:", self.correlation_threshold)
        form_layout.addRow("Threshold tolerance:", self.correlation_threshold_tolerance)

        correlation_parameter_layout.addLayout(form_layout)
        correlation_parameter_layout.addWidget(self.highlight_threshold)
        correlation_parameter_layout.addWidget(self.hierarchical_clustering)
        correlation_parameter_layout.addWidget(self.lower_triangle_matrix)
        correlation_parameter_layout.addWidget(self.upper_triangle_matrix)
        correlation_parameter_group.setLayout(correlation_parameter_layout)

        return correlation_parameter_group

    def _create_info_group(self) -> QGroupBox:
        """Create info group with usage instructions.

        Returns:
            QGroupBox: Group box containing helpful information.
        """
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
            Metrics in the same group have a correlation value <strong>equal to or above</strong> the threshold,
            meaning they behave similarly.</p>
            <p><strong><u>Info 2</u>:</strong><br>
            The <strong>correlation threshold tolerance</strong> allows flexibility in detecting correlated metrics.
            If the absolute difference between a metric's correlation value and the threshold
            is less than or equal to the tolerance, the metric is considered correlated.</p>
        """)
        info_page_layout.addWidget(self.textEdit)
        info_page_group.setLayout(info_page_layout)

        return info_page_group

    def get_model(self):
        return self.model

    def _create_plot_panel(self) -> QFrame:
        """Create the right plot panel for correlation heatmap.

        Returns:
            QFrame: Plot frame containing toolbar and canvas.
        """
        plot_frame = QFrame()
        plot_frame.setStyleSheet("""
               background-color: #e7e7e7;
               border-top-left-radius: 10px;
               border-top-right-radius: 10px;
        """)
        plot_frame_layout = QVBoxLayout(plot_frame)
        plot_frame_layout.setContentsMargins(0, 0, 0, 0)

        plot_title = QLabel("Correlation matrix visualization")
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

        self.fig = Figure(figsize=(15, 15))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = CustomToolbar(self.canvas)

        self.fig.subplots_adjust(bottom=0.170)  # Space for long labels
        self._ax = self.canvas.figure.add_subplot(1, 1, 1)
        self._ax.set_box_aspect(1)
        self._ax.set_xlim(0, 1)
        self._ax.set_ylim(0, 1)

        plot_frame_layout.addWidget(plot_title)
        plot_frame_layout.addWidget(self.toolbar)
        plot_frame_layout.addWidget(self.canvas)

        return plot_frame

    def _create_table_section(self) -> QWidget:
        """Create the bottom table section for correlation groups.

        Returns:
            QWidget: Table frame containing correlation groups table.
        """
        table_frame = QWidget()
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.styled_table = StyledTable("Orthogonality result correlation table")
        self.styled_table.set_header_label(["Group", "Correlated OM"])
        self.styled_table.set_default_row_count(10)
        table_frame_layout.addWidget(self.styled_table)

        self.table_frame_shadow = BoxShadow()
        self.styled_table.setGraphicsEffect(self.table_frame_shadow)

        return table_frame

    # ==========================================================================
    # Page Initialization
    # ==========================================================================

    def init_page(self) -> None:
        """Initialize the page with correlation data.

        Side Effects:
            - Clears and resets table
            - Plots correlation heatmap if data available
            - Updates correlation groups table
        """
        self.styled_table.clean_table()
        self.styled_table.set_header_label(["Group", "Correlated OM"])

        if self.model.get_orthogonality_metric_corr_matrix_df().empty:
            return

        self.plot_correlation_heat_map()
        self.update_correlation_group_table()

    # ==========================================================================
    # Heatmap Visualization
    # ==========================================================================

    def plot_correlation_heat_map(self) -> None:
        """Plot correlation heatmap with optional clustering and masking.

        Side Effects:
            - Clears figure
            - Computes correlation matrix
            - Applies hierarchical clustering if enabled
            - Applies triangle masking if selected
            - Renders heatmap with seaborn
            - Highlights threshold if enabled
        """
        self.fig.clf()
        self.fig.patch.set_facecolor("white")
        self._ax = self.fig.add_subplot()

        self.corr_matrix = self.model.get_orthogonality_metric_corr_matrix_df().corr()

        if self.corr_matrix.empty:
            return

        cmap = self.corr_mat_cmap.currentText()

        # Map to abbreviated display names
        metric_list = [
            METRIC_CORR_MAP[metric] for metric in list(self.corr_matrix.columns)
        ]

        if self.hierarchical_clustering.checkState() == Qt.Checked:
            self.corr_matrix = self.cluster_corr(self.corr_matrix)

        # Determine triangle mask
        if self.lower_triangle_matrix.checkState() == Qt.Checked:
            self.heatmap_mask = np.triu(np.ones_like(self.corr_matrix, dtype=bool))
        elif self.upper_triangle_matrix.checkState() == Qt.Checked:
            self.heatmap_mask = np.tril(np.ones_like(self.corr_matrix, dtype=bool))
        else:
            self.heatmap_mask = np.zeros_like(self.corr_matrix, dtype=bool)

        # Plot heatmap
        g = sns.heatmap(
            self.corr_matrix,
            mask=self.heatmap_mask,
            vmin=self.corr_matrix.values.min(),
            vmax=1,
            square=True,
            cmap=cmap,
            linewidths=0.1,
            annot=True,
            annot_kws={"fontsize": 6},
            xticklabels=1,
            yticklabels=1,
            ax=self._ax,
        )

        g.set_xticklabels(metric_list, fontsize=7)
        g.set_yticklabels(metric_list, rotation=0, fontsize=7)

        self.highlight_correlation_threshold()

        sns.reset_defaults()
        self.fig.canvas.draw()

    def update_correlation_matrix_cmap(self, cmap: str) -> None:
        """Update the heatmap color map.

        Args:
            cmap (str): Name of the matplotlib color map.

        Side Effects:
            - Changes heatmap color scheme
            - Redraws canvas
        """
        quadmesh = self._ax.collections[0]
        quadmesh.set_cmap(cmap)
        self.fig.canvas.draw_idle()

    def highlight_correlation_threshold(self) -> None:
        """Highlight cells above correlation threshold with red borders.

        Side Effects:
            - Adds/removes red rectangles around correlated cells
            - Redraws canvas
        """
        if self.corr_matrix is None:
            return

        if self.highlight_threshold.checkState() == Qt.Unchecked:
            # Remove all rectangles
            for patch in self._ax.patches[:]:
                patch.remove()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
        else:
            threshold = self.correlation_threshold.value()
            tolerance = self.correlation_threshold_tolerance.value()

            # Create mask: Ignore diagonal and highlight values above threshold
            self.highlight_heatmap_mask = (
                                                  self.corr_matrix.abs() >= (threshold - tolerance)
                                          ) & (~np.eye(len(self.corr_matrix), dtype=bool))

            self.highlight_heatmap_mask = (
                                              ~self.heatmap_mask
                                          ) & self.highlight_heatmap_mask

            # Overlay red borders
            for i in range(len(self.corr_matrix)):
                for j in range(len(self.corr_matrix)):
                    if self.highlight_heatmap_mask.iloc[i, j]:
                        self._ax.add_patch(
                            Rectangle((j, i), 1, 1, fill=False, edgecolor="red", lw=1)
                        )

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    # ==========================================================================
    # Correlation Grouping
    # ==========================================================================

    def update_correlation_group_table(self) -> None:
        """Update the correlation groups table based on threshold.

        Side Effects:
            - Creates correlation groups in model
            - Updates table with grouped metrics
            - Sets up sorting/filtering proxy
            - Refreshes threshold highlighting
            - Emits correlation_group_ready signal
        """
        threshold = self.correlation_threshold.value()
        tolerance = self.correlation_threshold_tolerance.value()
        self.model.create_correlation_group(threshold=threshold, tol=tolerance)

        correlation_group_table = self.model.get_correlation_group_df()

        self.styled_table.async_set_table_data(correlation_group_table)
        self.styled_table.set_table_proxy()

        self.highlight_correlation_threshold()

        self.correlation_group_ready.emit()

    # ==========================================================================
    # Hierarchical Clustering
    # ==========================================================================

    def cluster_corr(self, corr_array: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """Rearrange correlation matrix using hierarchical clustering.

        Groups highly correlated variables next to each other using
        complete linkage clustering on pairwise distances.

        Args:
            corr_array (DataFrame): NxN correlation matrix.
            inplace (bool): Whether to modify in place or return a copy.

        Returns:
            DataFrame: Rearranged NxN correlation matrix.
        """
        pairwise_distances = sch.distance.pdist(corr_array)
        linkage = sch.linkage(pairwise_distances, method="complete")
        cluster_distance_threshold = pairwise_distances.max() / 2
        idx_to_cluster_array = sch.fcluster(
            linkage, cluster_distance_threshold, criterion="distance"
        )
        idx = np.argsort(idx_to_cluster_array)

        if not inplace:
            corr_array = corr_array.copy()

        if isinstance(corr_array, pd.DataFrame):
            return corr_array.iloc[idx, :].T.iloc[idx, :]
        return corr_array[idx, :][:, idx]