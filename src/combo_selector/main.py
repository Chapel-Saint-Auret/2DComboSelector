import sys,os
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

# Custom Modules - adjusted import paths for src/combo_selector layout
from combo_selector.utils import resource_path
from combo_selector.ui.widgets.custom_main_window import CustomMainWindow
from combo_selector.core.orthogonality import Orthogonality
from combo_selector.core.workers import RedundancyWorker, ResultsWorker
from combo_selector.ui.pages.home_page import HomePage
from combo_selector.ui.pages.import_data_page import ImportDataPage
from combo_selector.ui.pages.plot_pairwise_page import PlotPairWisePage
from combo_selector.ui.pages.om_calculation_page import OMCalculationPage
from combo_selector.ui.pages.redundancy_check_page import RedundancyCheckPage
from combo_selector.ui.pages.results_page import ResultsPage
from combo_selector.ui.pages.export_page import ExportPage

class ComboSelectorMain(CustomMainWindow):
    def __init__(self):
        super().__init__()

        self.metric_list_for_figure = []
        self._cached_metric_list = []
        self.set_window_title('2D COMBO SELECTOR')

        self.threadpool = QThreadPool()

        self.model = Orthogonality()
        self.home_page = HomePage(self.model)
        self.import_data_page = ImportDataPage(self.model)
        self.plot_page = PlotPairWisePage(self.model)
        self.om_calculation_page = OMCalculationPage(self.model)
        self.redundancy_page = RedundancyCheckPage(self.model)
        self.results_page = ResultsPage(self.model)
        self.export_page = ExportPage(self.model)

        self.menu_file = self.menu_bar.addAction('Import datas')

        self.side_bar_menu.add_side_bar_button('HOME', self.home_page)
        self.side_bar_menu.add_side_bar_button('RETENTION TIME\nNORMALIZATION', self.import_data_page)
        self.side_bar_menu.add_side_bar_button('DATA PLOTTING\nPAIRWISE', self.plot_page)
        self.side_bar_menu.add_side_bar_button('ORTHOGONALITY \nMETRIC (OM)\nCALCULATION', self.om_calculation_page)
        self.side_bar_menu.add_side_bar_button('REDUNDANCY\nCHECK', self.redundancy_page)
        self.side_bar_menu.add_side_bar_button('RESULTS', self.results_page)
        self.side_bar_menu.add_side_bar_button('EXPORT', self.export_page)

        self.side_bar_menu.button_clicked.connect(self.side_bar_menu_clicked)
        self.import_data_page.retention_time_loaded.connect(self.init_pages)
        self.import_data_page.exp_peak_capacities_loaded.connect(self.update_results_with_new_exp_peak_capacities)
        self.import_data_page.retention_time_normalized.connect(self.plot_page.update_dataset_selector_state)
        self.om_calculation_page.metric_computed.connect(self.orthogonality_metric_computed)
        self.redundancy_page.correlation_group_ready.connect(self.results_page.update_suggested_score_data)

    def init_pages(self):
        self.plot_page.init_page()
        self.om_calculation_page.init_page()
        self.redundancy_page.init_page()

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

    w = ComboSelectorMain()
    w.show()
    app.exec()
if __name__ == '__main__':
    main()