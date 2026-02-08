"""Main application entry point for 2D Combo Selector.

This module provides the main application class that orchestrates all
pages, manages the data model, and coordinates background worker threads
for computationally intensive tasks.

The application follows a multi-page wizard-like workflow:
1. Home: Introduction and overview
2. Import & Normalize: Load and normalize retention time data
3. Pairwise Plotting: Visualize 2D combinations
4. OM Calculation: Compute orthogonality metrics
5. Redundancy Check: Identify correlated metrics
6. Results: Rank and compare combinations
7. Export: Save results and figures

Background workers are used for:
- Redundancy analysis (correlation matrix computation)
- Results computation (score aggregation and ranking)
"""

import sys

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from combo_selector.core.orthogonality import Orthogonality
from combo_selector.core.workers import RedundancyWorker, ResultsWorker
from combo_selector.ui.pages.export_page import ExportPage
from combo_selector.ui.pages.home_page import HomePage
from combo_selector.ui.pages.import_data_page import ImportDataPage
from combo_selector.ui.pages.om_calculation_page import OMCalculationPage
from combo_selector.ui.pages.plot_pairwise_page import PlotPairWisePage
from combo_selector.ui.pages.redundancy_check_page import RedundancyCheckPage
from combo_selector.ui.pages.results_page import ResultsPage
from combo_selector.ui.widgets.custom_main_window import CustomMainWindow
from combo_selector.utils import resource_path


class ComboSelectorMain(CustomMainWindow):
    """Main application window for 2D Combo Selector.

    Manages the application's multi-page interface and coordinates
    data flow between pages. Uses background threads for intensive
    computations to maintain UI responsiveness.

    Attributes:
        model (Orthogonality): Core data model containing all analysis data.
        thread pool (QThreadPool): Thread pool for background computations.
        home_page (HomePage): Welcome and introduction page.
        import_data_page (ImportDataPage): Data import and normalization page.
        plot_page (PlotPairWisePage): Pairwise data visualization page.
        om_calculation_page (OMCalculationPage): Metric calculation page.
        redundancy_page (RedundancyCheckPage): Metric correlation analysis page.
        results_page (ResultsPage): Final ranking and results page.
        export_page (ExportPage): Data and figure export page.
        _cached_metric_list (list): Cached list of computed metric names.
        metric_list_for_figure (list): Metric names formatted for figures.

    Signal Flow:
        1. retention_time_loaded → init_pages()
        2. retention_time_normalized → update_plots()
        3. metric_computed → orthogonality_metric_computed()
           → redundancy worker → results worker → pages initialized
        4. exp_peak_capacities_loaded → update_results_with_new_exp_peak_capacities()
    """

    def __init__(self):
        """Initialize the main application window.

        Creates all pages, sets up the sidebar navigation, and connects
        inter-page signals for workflow coordination.
        """
        super().__init__()

        # --- State management ----------------------------------------------
        self.redundancy_worker = None
        self._cached_metric_list = []
        self.metric_list_for_figure = []
        self.threadpool = QThreadPool()

        # --- Core model ----------------------------------------------------
        self.model = Orthogonality()

        # --- Page initialization -------------------------------------------
        self.home_page = HomePage(self.model)
        self.import_data_page = ImportDataPage(self.model)
        self.plot_page = PlotPairWisePage(self.model)
        self.om_calculation_page = OMCalculationPage(self.model)
        self.redundancy_page = RedundancyCheckPage(self.model)
        self.results_page = ResultsPage(self.model)
        self.export_page = ExportPage(self.model)

        # --- Sidebar navigation setup --------------------------------------
        self.add_side_bar_item(
            "Home", self.home_page, resource_path("icons/home_icon.png")
        )
        self.add_side_bar_item(
            "Retention Time\nNormalization",
            self.import_data_page,
            resource_path("icons/norm_icon.svg"),
        )
        self.add_side_bar_item(
            "Data plotting\nPairwise",
            self.plot_page,
            resource_path("icons/pairwise_icon.png"),
        )
        self.add_side_bar_item(
            "Orthogonality Metric \nCalculation",
            self.om_calculation_page,
            resource_path("icons/om_icon.png"),
        )
        self.add_side_bar_item(
            "Redundancy\nCheck",
            self.redundancy_page,
            resource_path("icons/redund_icon.png"),
        )
        self.add_side_bar_item(
            "Results", self.results_page, resource_path("icons/rank_icon.png")
        )
        self.add_side_bar_item(
            "Export", self.export_page, resource_path("icons/export_icon.png")
        )

        # --- Signal connections --------------------------------------------
        self.import_data_page.retention_time_loaded.connect(self.init_pages)
        self.import_data_page.exp_peak_capacities_loaded.connect(
            self.update_results_with_new_exp_peak_capacities
        )
        self.import_data_page.retention_time_normalized.connect(self.update_plots)
        self.om_calculation_page.metric_computed.connect(
            self.orthogonality_metric_computed
        )
        self.redundancy_page.correlation_group_ready.connect(
            self.results_page.compute_custom_orthogonality_metric_score
        )

    def init_pages(self) -> None:
        """Initialize pages after retention time data is loaded.

        Called when retention time data has been successfully loaded
        and normalized. Initializes all downstream pages that depend
        on this data.

        Side Effects:
            - Initializes plot page with dataset combinations
            - Initializes OM calculation page with metric options
            - Initializes redundancy page (empty until metrics computed)
        """
        self.plot_page.init_page()
        self.om_calculation_page.init_page()
        self.redundancy_page.init_page()

    def update_plots(self) -> None:
        """Update plots after retention time normalization.

        Called when retention times have been re-normalized with
        different parameters. Refreshes all visualizations to reflect
        the updated data.

        Side Effects:
            - Refreshes pairwise plot datasets
            - Refreshes OM calculation visualizations
        """
        self.plot_page.update_dataset_selector_state()
        self.om_calculation_page.update_om_selector_state()

    def orthogonality_metric_computed(self, metric_list: tuple) -> None:
        """Handle completion of orthogonality metric computation.

        Triggered when all selected orthogonality metrics have been
        computed. Starts the redundancy analysis worker thread, which
        will then trigger the results worker upon completion.

        Args:
            metric_list (tuple): Tuple of (metric_names, figure_metric_names)
                - metric_names: List of computed metric column names
                - figure_metric_names: List of metric names for figure labels

        Side Effects:
            - Caches metric lists for later use
            - Starts redundancy worker in background thread
            - Worker completion triggers results page initialization
        """
        self._cached_metric_list = metric_list[0]
        self.metric_list_for_figure = metric_list[1]

        if self._cached_metric_list:
            self.redundancy_worker = RedundancyWorker(self.redundancy_page)
            self.redundancy_worker.signals.finished.connect(
                self._start_results_worker_after_redundancy
            )
            self.threadpool.start(self.redundancy_worker)

    def update_results_with_new_exp_peak_capacities(self) -> None:
        """Update results when experimental peak capacities are loaded.

        Called when the user provides experimental peak capacity data
        to supplement or replace hypothetical calculations.

        Side Effects:
            - Updates plot page with new peak capacity data
            - Refreshes plot dataset selectors
            - Triggers results worker to recompute with new data
        """
        self.plot_page.update_table_peak_data()
        self.plot_page.update_dataset_selector_state()
        self._start_results_worker_after_redundancy()

    def _start_results_worker_after_redundancy(self) -> None:
        """Start the results worker after redundancy analysis completes.

        Private method that initiates the results computation worker.
        This is called either after redundancy analysis finishes or
        when peak capacity data is updated.

        Side Effects:
            - Creates and starts ResultsWorker in background thread
            - Worker completion triggers page initialization
        """
        self.results_worker = ResultsWorker(
            self.results_page, self._cached_metric_list
        )
        self.results_worker.signals.finished.connect(self._on_results_worker_finished)
        self.threadpool.start(self.results_worker)

    def _on_results_worker_finished(self) -> None:
        """Handle completion of results worker.

        Called when the results worker has finished computing scores
        and rankings. Initializes the results and export pages with
        the final data.

        Side Effects:
            - Initializes results page with metric list
            - Updates status bar message
            - Initializes export page with figure metrics
            - Updates status bar message again
        """
        self.results_page.init_page(self._cached_metric_list)
        self.set_status_text("Result page ready!")
        self.export_page.init_page(self.metric_list_for_figure)
        self.set_status_text("Export page ready!")


def main():
    """Main application entry point.

    Creates the Qt application instance, sets the window icon,
    and starts the event loop.

    Returns:
        int: Application exit code (0 for success).
    """
    app = QApplication(sys.argv)
    app_icon = QIcon(resource_path("icons/app_logo.svg"))
    app.setWindowIcon(app_icon)

    window = ComboSelectorMain()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()