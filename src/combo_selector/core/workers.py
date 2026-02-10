"""Worker threads for asynchronous computation in the 2DComboSelector application.

This module provides QRunnable worker classes for offloading computationally intensive
tasks to background threads, keeping the GUI responsive. Each worker class handles
a specific type of computation:

- RedundancyWorker: Processes correlation heatmaps and redundancy checks
- ResultsWorker: Computes final results and rankings
- ResultsWorkerComputeCustomOMScore: Computes custom orthogonality scores
- OMWorkerComputeOM: Computes orthogonality metrics
- OMWorkerUpdateNumBin: Updates bin numbers for grid-based metrics
- TableDataWorker: Formats table data for display

All workers follow the Qt threading model using QRunnable and emit signals
to communicate with the main thread.
"""

import logging
import traceback

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class RedundancyWorkerSignals(QObject):
    """Signal container for RedundancyWorker.

    Attributes:
        finished (Signal): Emitted when redundancy computation is complete.
    """
    finished = Signal()


class RedundancyWorker(QRunnable):
    """Background worker for computing metric redundancy analysis.

    Processes correlation heatmap generation and identifies groups of correlated
    orthogonality metrics that may be redundant. Runs in a separate thread to
    avoid blocking the GUI.

    Attributes:
        page: Reference to the RedundancyCheckPage instance.
        signals (RedundancyWorkerSignals): Signal object for communication with main thread.
    """

    def __init__(self, page):
        """Initialize the redundancy worker.

        Args:
            page: RedundancyCheckPage instance containing the UI and data model.
        """
        super().__init__()
        self.page = page  # This is an instance of RedundancyCheckPage
        self.signals = RedundancyWorkerSignals()

    @Slot()
    def run(self):
        """Execute redundancy analysis in background thread.

        Performs the following operations:
        1. Plots correlation heatmap of orthogonality metrics
        2. Updates correlation group table showing related metrics
        3. Emits finished signal upon completion

        Side Effects:
            - Updates page's correlation heatmap visualization
            - Updates correlation group table
            - Emits finished signal
            - Logs exceptions if errors occur
        """
        try:
            self.page.plot_correlation_heat_map()

            self.page.update_correlation_group_table()

            self.signals.finished.emit()
        except Exception as e:
            logging.exception(f"[RedundancyWorker] Error: {e}")


class ResultsWorkerSignals(QObject):
    """Signal container for ResultsWorker classes.

    Attributes:
        finished (Signal): Emitted when computation is complete.
        progress (Signal[int]): Emitted with progress percentage (0-100).
    """
    finished = Signal()
    progress = Signal(int)


class ResultsWorker(QRunnable):
    """Background worker for computing final results with suggested scores.

    Computes suggested orthogonality scores based on correlation groups,
    calculates practical 2D peak capacities, and generates the final results table.

    Attributes:
        page: Reference to the ResultsPage instance.
        om_list: List of orthogonality metrics to use.
        signals (ResultsWorkerSignals): Signal object for communication.
    """

    def __init__(self, page, om_list):
        """Initialize the results' worker.

        Args:
            page: ResultsPage instance containing UI and data model.
            om_list: List of orthogonality metric names.
        """
        super().__init__()
        self.page = page
        self.om_list = om_list
        self.signals = ResultsWorkerSignals()

    @Slot()
    def run(self):
        """Execute results computation in background thread.

        Performs the following operations in sequence:
        1. Computes suggested orthogonality scores
        2. Calculates practical 2D peak capacities
        3. Creates final results table with rankings
        4. Emits finished signal

        Side Effects:
            - Updates model's suggested scores
            - Updates practical 2D peak capacity values
            - Creates results table in model
            - Emits finished signal
            - Logs exceptions if errors occur
        """
        try:

            self.page.get_model().compute_suggested_score()

            self.page.get_model().compute_practical_2d_peak_capacity()

            self.page.get_model().create_results_table()

            self.signals.finished.emit()
        except Exception as e:
            logging.exception(f"[ResultsWorker] Error: {e}")


class ResultsWorkerComputeCustomOMScore(QRunnable):
    """Background worker for computing custom orthogonality scores.

    Computes a custom orthogonality score based on user-selected metrics,
    then calculates practical 2D peak capacity and generates the results table.
    Emits progress updates during computation.

    Attributes:
        page: Reference to the ResultsPage instance.
        signals (ResultsWorkerSignals): Signal object for communication.
    """

    def __init__(self, page):
        """Initialize the custom score worker.

        Args:
            page: ResultsPage instance containing UI and data model.
        """
        super().__init__()
        self.page = page
        self.signals = ResultsWorkerSignals()

    @Slot()
    def run(self):
        """Execute custom score computation with progress reporting.

        Performs the following operations:
        1. Gets checked metrics from the page (progress: 30%)
        2. Computes custom orthogonality score (progress: 70%)
        3. Calculates practical 2D peak capacities (progress: 95%)
        4. Creates final results table
        5. Emits finished signal

        Side Effects:
            - Emits progress signals at 30%, 70%, and 95%
            - Updates model's computed scores
            - Updates practical 2D peak capacity values
            - Creates results table in model
            - Emits finished signal
            - Logs debug message and exceptions
        """
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


# Add these imports at the top of workers.py
import traceback
import numpy as np
import pandas as pd


class OMWorkerSignals(QObject):
    """Signal container for orthogonality metric workers.

    Attributes:
        progress (Signal[int, str]): Emitted with (percentage, metric_name).
        finished (Signal): Emitted when computation is complete.
        error (Signal[tuple]): Emitted with (exception, traceback_string).
        result (Signal[object]): Emitted with computation result.
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int, str)  # (percentage, metric_name)


class OMWorkerComputeOM(QRunnable):
    """Background worker for computing orthogonality metrics.

    Computes the selected orthogonality metrics (convex hull, bin box, correlations,
    etc.) in a background thread to avoid freezing the GUI during intensive calculations.

    Attributes:
        metric_list (list): List of metric names (UI format) to compute.
        model (Orthogonality): The orthogonality data model.
        signals (OMWorkerSignals): Signal object for progress and completion.
    """

    def __init__(self, metric_list, model):
        """Initialize the orthogonality metric computation worker.

        Args:
            metric_list (list): List of metric names to compute (e.g.,
                               ['Convex hull relative area', 'Bin box counting']).
            model (Orthogonality): Orthogonality model instance.
        """
        super().__init__()
        self.metric_list = metric_list
        self.model = model
        self.signals = OMWorkerSignals()

    @Slot()
    def run(self):
        """Execute orthogonality metric computation with progress reporting.

        Computes each metric individually using the model's om_function_map,
        emitting progress updates for each metric. Always emits
        finished signal, even if an exception occurs.

        Side Effects:
            - Emits progress signals during computation (0-100%)
            - Updates model's orthogonality_dict with computed metrics
            - Updates model's table_data
            - Updates model's orthogonality_metric_df DataFrames
            - Always emits finished signal in finally block
            - Logs exceptions if errors occur
        """
        try:
            # Import these here to avoid circular dependencies
            from combo_selector.core.orthogonality import (
                METRIC_MAPPING,
                UI_TO_MODEL_MAPPING,
                METRIC_WEIGHTS,
                DEFAULT_WEIGHT,
                FuncStatus
            )

            # Calculate total weight for progress tracking
            total_weight = sum(
                METRIC_WEIGHTS.get(metric, DEFAULT_WEIGHT)
                for metric in self.metric_list
                if self.model.om_function_map[metric]["status"] != FuncStatus.COMPUTED
            )
            accumulated_weight = 0

            for metric_name in self.metric_list:
                if self.model.om_function_map[metric_name]["status"] != FuncStatus.COMPUTED:
                    # Emit progress with current metric name BEFORE computing
                    progress_percent = int((accumulated_weight / total_weight) * 100) if total_weight > 0 else 0
                    self.signals.progress.emit(progress_percent, metric_name)

                    # Compute the metric using the function from om_function_map
                    self.model.om_function_map[metric_name]["func"]()

                    # Mark as computed
                    self.model.om_function_map[metric_name]["status"] = FuncStatus.COMPUTED

                    # Update accumulated weight
                    accumulated_weight += METRIC_WEIGHTS.get(metric_name, DEFAULT_WEIGHT)

            # Emit 100% completion with last metric
            last_metric = self.metric_list[-1] if self.metric_list else ""
            self.signals.progress.emit(100, last_metric)

            # Update the DataFrames (replicate end of model's compute_orthogonality_metric)
            self._update_metric_dataframes()

        except Exception as e:
            self.signals.error.emit((e, traceback.format_exc()))
            logging.exception(f"[OMWorkerComputeOM] Error: {e}")
        finally:
            self.signals.finished.emit()

    def _update_metric_dataframes(self):
        """Update orthogonality metric DataFrames after all computations.

        This replicates the DataFrame update logic from the model's
        compute_orthogonality_metric method.

        Side Effects:
            - Updates model.orthogonality_metric_df
            - Updates model.orthogonality_metric_corr_matrix_df
        """
        from combo_selector.core.orthogonality import METRIC_MAPPING, UI_TO_MODEL_MAPPING

        # Get column indices for the computed metrics
        column_index = [
            METRIC_MAPPING[UI_TO_MODEL_MAPPING[metric]]["table_index"]
            for metric in self.metric_list
        ]

        orthogonality_table_df = pd.DataFrame(self.model.table_data)

        # Correlation matrix table only contains metric with no set number and combination title
        self.model.orthogonality_metric_df = orthogonality_table_df.iloc[
            :, np.r_[column_index]
        ]

        # Add column name
        self.model.orthogonality_metric_df.columns = self.metric_list

        self.model.orthogonality_metric_corr_matrix_df = self.model.orthogonality_metric_df

        # 0 and 1 indexes are for set number and combination title
        column_index = [0, 1] + column_index
        self.model.orthogonality_metric_df = orthogonality_table_df.iloc[
            :, np.r_[column_index]
        ]

        # Adding column names directly
        self.model.orthogonality_metric_df.columns = ["Set #", "2D Combination"] + self.metric_list


class OMWorkerUpdateNumBin(QRunnable):
    """Background worker for updating bin numbers in grid-based metrics.

    Updates the number of bins used in bin box counting, Gilar-Watson, and
    modeling approach metrics. This requires recomputing affected metrics
    with the new bin configuration.

    Attributes:
        nb_bin (int): New number of bins per axis.
        checked_metric_list (list): List of currently selected metrics.
        model (Orthogonality): The orthogonality data model.
        signals (OMWorkerSignals): Signal object for progress and completion.
    """

    def __init__(self, nb_bin, checked_metric_list, model):
        """Initialize the bin number update worker.

        Args:
            nb_bin (int): Number of bins per axis (e.g., 14 for 14x14 grid).
            checked_metric_list (list): List of selected metric names.
            model (Orthogonality): Orthogonality model instance.
        """
        super().__init__()
        self.checked_metric_list = checked_metric_list
        self.model = model
        self.nb_bin = nb_bin
        self.signals = OMWorkerSignals()

    @Slot()
    def run(self):
        """Execute bin number update with progress reporting.

        Updates the model's bin_number property and recomputes bin-dependent
        metrics. Always emits finished signal, even if an exception occurs.

        Side Effects:
            - Updates model's bin_number attribute
            - Emits progress signals during recomputation
            - Recomputes bin-dependent metrics if they were previously computed
            - Always emits finished signal in finally block
            - Logs exceptions if errors occur
        """
        try:
            self.model.update_num_bins(
                self.nb_bin, self.checked_metric_list, self.signals.progress
            )

        except Exception as e:
            logging.exception(f"[Unable to update number of bin] Error: {e}")
        finally:
            self.signals.finished.emit()


class TableDataWorkerSignals(QObject):
    """Signal container for TableDataWorker.

    Attributes:
        finished (Signal[object, object, object]): Emitted with (formatted_data, row_count, col_count)
                                                   when formatting is complete.
    """
    finished = Signal(object, object, object)  # formatted_data, row_count, col_count


class TableDataWorker(QRunnable):
    """Background worker for formatting table data for display.

    Converts pandas DataFrame data into formatted strings suitable for display
    in Qt table widgets. Applies custom formatting rules based on column types
    (e.g., integers for peak capacities, 3 decimal places for floats).

    Attributes:
        data (pd.DataFrame): Raw data to format.
        header_labels (list): Column header names for determining format rules.
        signals (TableDataWorkerSignals): Signal object for returning results.
    """

    def __init__(self, data, header_labels):
        """Initialize the table data formatting worker.

        Args:
            data (pd.DataFrame): DataFrame containing the data to format.
            header_labels (list): List of column header names.
        """
        super().__init__()
        self.data = data
        self.header_labels = header_labels
        self.signals = TableDataWorkerSignals()

    @Slot()
    def run(self):
        """Execute table data formatting in background thread.

        Formats each cell according to column-specific rules:
        - Peak capacity columns: Rounded integers
        - Float columns: 3 decimal places
        - Other columns: String conversion

        Side Effects:
            - Emits finished signal with (formatted_data, row_count, col_count)

        Note:
            Uses a nested format_value function to apply column-specific formatting.
        """
        data_cast = self.data.astype(object)
        data_list = data_cast.values.tolist()

        def format_value(val, col_idx):
            """Format a single cell value based on its column.

            Args:
                val: The value to format.
                col_idx (int): Column index for determining format rules.

            Returns:
                str: Formatted string representation of the value.
            """
            label = (
                self.header_labels[col_idx] if col_idx < len(self.header_labels) else ""
            )
            if label in ["Practical 2D peak capacity", "Predicted 2D peak capacity"]:
                try:
                    return str(int(round(float(val))))
                except Exception:
                    return str(val)
            if isinstance(val, (int, float)):
                return f"{val:.3f}" if isinstance(val, float) else str(val)
            return str(val)

        formatted_data = [
            [format_value(val, j) for j, val in enumerate(row)] for row in data_list
        ]

        row_count = len(data_list)
        col_count = len(data_list[0]) if row_count > 0 else 0
        self.signals.finished.emit(formatted_data, row_count, col_count)