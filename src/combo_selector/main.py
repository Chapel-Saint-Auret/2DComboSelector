import os
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
# Custom Modules - adjusted import paths for src/combo_selector layout
from combo_selector.utils import resource_path


class ComboSelectorMain(CustomMainWindow):
    def __init__(self):
        super().__init__()

        self.metric_list_for_figure = []
        self._cached_metric_list = []

        self.threadpool = QThreadPool()

        self.model = Orthogonality()
        self.home_page = HomePage(self.model)
        self.import_data_page = ImportDataPage(self.model)
        self.plot_page = PlotPairWisePage(self.model)
        self.om_calculation_page = OMCalculationPage(self.model)
        self.redundancy_page = RedundancyCheckPage(self.model)
        self.results_page = ResultsPage(self.model)
        self.export_page = ExportPage(self.model)


        self.add_side_bar_item('Home', self.home_page,resource_path('icons/home_icon.png'))
        self.add_side_bar_item('Retention Time\nNormalization', self.import_data_page,resource_path('icons/norm_icon.svg'))
        self.add_side_bar_item('Data plotting\nPairwise', self.plot_page,resource_path('icons/pairwise_icon.png'))
        self.add_side_bar_item('Orthogonality Metric \nCalculation', self.om_calculation_page,resource_path('icons/om_icon.png'))
        self.add_side_bar_item('Redundancy\nCheck', self.redundancy_page,resource_path('icons/redund_icon.png'))
        self.add_side_bar_item('Results', self.results_page,resource_path('icons/rank_icon.png'))
        self.add_side_bar_item('Export', self.export_page,resource_path('icons/export_icon.png'))

        # self.side_bar_menu.button_clicked.connect(self.side_bar_menu_clicked)
        self.import_data_page.retention_time_loaded.connect(self.init_pages)
        self.import_data_page.exp_peak_capacities_loaded.connect(self.update_results_with_new_exp_peak_capacities)
        self.import_data_page.retention_time_normalized.connect(self.update_plots)
        self.om_calculation_page.metric_computed.connect(self.orthogonality_metric_computed)
        self.redundancy_page.correlation_group_ready.connect(self.results_page.update_suggested_score_data)

    def init_pages(self):
        self.plot_page.init_page()
        self.om_calculation_page.init_page()
        self.redundancy_page.init_page()

    def update_plots(self):
        self.plot_page.update_dataset_selector_state()
        self.om_calculation_page.update_om_selector_state()


    def orthogonality_metric_computed1(self, metric_list):
        self.redundancy_page.init_page()
        self.results_page.init_page(metric_list[0])
        self.export_page.init_page(metric_list[1])

    def orthogonality_metric_computed(self, metric_list):
        # Store metric list temporarily
        self._cached_metric_list = metric_list[0]
        self.metric_list_for_figure = metric_list[1]

        if self._cached_metric_list:
            self.redundancy_worker = RedundancyWorker(self.redundancy_page)
            self.redundancy_worker.signals.finished.connect(self._start_results_worker_after_redundancy)
            self.threadpool.start(self.redundancy_worker)

    def update_results_with_new_exp_peak_capacities(self):
        self.plot_page.update_table_peak_data()
        self.plot_page.update_dataset_selector_state()
        self._start_results_worker_after_redundancy()

    def _start_results_worker_after_redundancy(self):
        self.results_worker = ResultsWorker(self.results_page, self._cached_metric_list)
        self.results_worker.signals.finished.connect(self._on_results_worker_finished)
        self.threadpool.start(self.results_worker)

    def _on_results_worker_finished(self):
        self.results_page.init_page(self._cached_metric_list)
        self.set_status_text('Result page ready!')
        self.export_page.init_page(self.metric_list_for_figure)
        self.set_status_text('Export page ready!')

    def side_bar_menu_clicked(self, index):
        pass

def main():
    app = QApplication(sys.argv)
    app_icon = QIcon(resource_path('icons/app_logo.svg'))
    app.setWindowIcon(app_icon)

    w = ComboSelectorMain()
    w.show()
    app.exec()
if __name__ == '__main__':
    main()