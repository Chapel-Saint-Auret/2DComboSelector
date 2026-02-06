import logging

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

# Setup logger

class RedundancyWorkerSignals(QObject):
    finished = Signal()


class RedundancyWorker(QRunnable):
    def __init__(self, page):
        super().__init__()
        self.page = page  # This is an instance of RedundancyCheckPage
        self.signals = RedundancyWorkerSignals()

    @Slot()
    def run(self):
        try:
            self.page.plot_correlation_heat_map()

            self.page.update_correlation_group_table()

            self.signals.finished.emit()
        except Exception as e:
            logging.exception(f"[RedundancyWorker] Error: {e}")


class ResultsWorkerSignals(QObject):
    finished = Signal()
    progress = Signal(int)


class ResultsWorker(QRunnable):
    def __init__(self, page, om_list):
        super().__init__()
        self.page = page
        self.om_list = om_list
        self.signals = ResultsWorkerSignals()

    @Slot()
    def run(self):
        try:

            self.page.get_model().compute_suggested_score()

            self.page.get_model().compute_practical_2d_peak_capacity()

            self.page.get_model().create_results_table()

            self.signals.finished.emit()
        except Exception as e:
            logging.exception(f"[ResultsWorker] Error: {e}")


class ResultsWorkerComputeCustomOMScore(QRunnable):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.signals = ResultsWorkerSignals()

    @Slot()
    def run(self):
        try:
            metric_list = self.page.om_list.get_checked_items()
            self.signals.progress.emit(30)
            self.page.get_model().compute_custom_orthogonality_score(metric_list)
            self.signals.progress.emit(70)
            self.page.get_model().compute_practical_2d_peak_capacity()
            self.signals.progress.emit(95)
            self.page.get_model().create_results_table()

            logging.debug("ResultsWorker finished")
            self.signals.finished.emit()
        except Exception as e:
            logging.exception(f"[ResultsWorker] Error: {e}")


class OMWorkerSignals(QObject):
    progress = Signal(int)
    finished = Signal()

# om_worker_thread.py

class OMWorkerComputeOM(QRunnable):
    def __init__(self, metric_list, model):
        super().__init__()
        self.metric_list = metric_list
        self.model = model  # not just a function now
        self.signals = OMWorkerSignals()

    @Slot()
    def run(self):
        try:
            self.model.compute_orthogonality_metric(self.metric_list, self.signals.progress)
        except Exception as e:
            logging.exception(f"[OMWorkerComputeOM] Error: {e}")
        finally:
            self.signals.finished.emit()

class OMWorkerUpdateNumBin(QRunnable):
    def __init__(self, nb_bin,checked_metric_list,model):
        super().__init__()
        self.checked_metric_list = checked_metric_list  # not just a function now
        self.model = model  # not just a function now
        self.nb_bin = nb_bin
        self.signals = OMWorkerSignals()

    @Slot()
    def run(self):
        try:
            self.model.update_num_bins(self.nb_bin, self.checked_metric_list, self.signals.progress)

        except Exception as e:
            logging.exception(f"[Unable to update number of bin] Error: {e}")
        finally:
            self.signals.finished.emit()



class TableDataWorkerSignals(QObject):
    finished = Signal(object, object, object)  # formatted_data, row_count, col_count

class TableDataWorker(QRunnable):
    def __init__(self, data, header_labels):
        super().__init__()
        self.data = data
        self.header_labels = header_labels
        self.signals = TableDataWorkerSignals()

    @Slot()
    def run(self):
        data_cast = self.data.astype(object)
        data_list = data_cast.values.tolist()

        def format_value(val, col_idx):
            label = self.header_labels[col_idx] if col_idx < len(self.header_labels) else ""
            if label in ["Practical 2D peak capacity","Predicted 2D peak capacity"]:
                try:
                    return str(int(round(float(val))))
                except Exception:
                    return str(val)
            if isinstance(val, (int, float)):
                return f"{val:.3f}" if isinstance(val, float) else str(val)
            return str(val)

        formatted_data = [
            [format_value(val, j) for j, val in enumerate(row)]
            for row in data_list
        ]

        row_count = len(data_list)
        col_count = len(data_list[0]) if row_count > 0 else 0
        self.signals.finished.emit(formatted_data, row_count, col_count)