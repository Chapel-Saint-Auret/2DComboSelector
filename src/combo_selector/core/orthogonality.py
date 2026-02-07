import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from itertools import combinations
from math import acos, atan, log2, pi, sqrt, tan

import pandas as pd
from PySide6.QtCore import QObject, Signal
from numpy import sum
from scipy.cluster.hierarchy import linkage
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import gmean, hmean, kendalltau, linregress, pearsonr, spearmanr

from combo_selector.core.orthogonality_utils import *

METRIC_MAPPING = {
    "set_number": {
        "table_index": 0,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "title": {"table_index": 1, "include_in_score": True, "include_in_corr_mat": False},
    "nb_peaks": {
        "table_index": 2,
        "include_in_score": False,
        "include_in_corr_mat": False,
    },
    "2d_peak_capacity": {
        "table_index": 3,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "convex_hull": {
        "table_index": 4,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "bin_box_ratio": {
        "table_index": 5,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "pearson_r": {
        "table_index": 6,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "spearman_rho": {
        "table_index": 7,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "kendall_tau": {
        "table_index": 8,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "cc_mean": {
        "table_index": 9,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "asterisk_metrics": {
        "table_index": 10,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "nnd_arithmetic_mean": {
        "table_index": 11,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "nnd_geom_mean": {
        "table_index": 12,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "nnd_harm_mean": {
        "table_index": 13,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "nnd_mean": {
        "table_index": 14,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "percent_fit": {
        "table_index": 15,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "percent_bin": {
        "table_index": 16,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "mean_bin_box_percent_bin": {
        "table_index": 17,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "asterisk_convex_hull_mean": {
        "table_index": 18,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "mean_bin_box_percent_bin_nnd_mean": {
        "table_index": 19,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "computed_score": {
        "table_index": 20,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "suggested_score": {
        "table_index": 21,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "orthogonality_factor": {
        "table_index": 22,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "practical_2d_peak_capacity": {
        "table_index": 23,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "orthogonality_value": {
        "table_index": 24,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "gilar-watson": {
        "table_index": 25,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "modeling_approach": {
        "table_index": 26,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "conditional_entropy": {
        "table_index": 27,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "geometric_approach": {
        "table_index": 28,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
}

UI_TO_MODEL_MAPPING = {
    "Convex hull relative area": "convex_hull",
    "Bin box counting": "bin_box_ratio",
    "Pearson Correlation": "pearson_r",
    "Spearman Correlation": "spearman_rho",
    "Kendall Correlation": "kendall_tau",
    "CC mean": "cc_mean",
    "Asterisk equations": "asterisk_metrics",
    "Asterisk + Cnvx Hull mean": "asterisk_convex_hull_mean",
    "NND Arithm mean": "nnd_arithmetic_mean",
    "NND Geom mean": "nnd_geom_mean",
    "NND Harm mean": "nnd_harm_mean",
    "NND mean": "nnd_mean",
    "%FIT": "percent_fit",
    "Bin box + %BIN": "percent_bin",
    "%BIN": "percent_bin",
    "mean (Bin box + %BIN)": "mean_bin_box_percent_bin",
    "mean(Bin box + %BIN + NND mean)": "mean_bin_box_percent_bin_nnd_mean",
    "Gilar-Watson method": "gilar-watson",
    "Modeling approach": "modeling_approach",
    "Geometric approach": "geometric_approach",
    "Conditional entropy": "conditional_entropy",
}

METRIC_WEIGHTS = {"%FIT": 10}
DEFAULT_WEIGHT = 1


class FuncStatus(Enum):
    """Enumeration for tracking the computation status of orthogonality metric functions.

    Attributes:
        NOT_COMPUTED: The function has not been computed yet.
        COMPUTED: The function has been successfully computed.
    """
    NOT_COMPUTED = 0
    COMPUTED = 1


class Orthogonality(QObject):
    """Main class for computing and managing orthogonality metrics for 2D chromatography analysis.

    This class handles loading retention time data,normalization of retention time, computing various orthogonality metrics,
    and managing results for multi-dimensional chromatography column selection.

    Signals:
        progressChanged: Qt signal emitting progress updates (int) during metric computation.

    Attributes:
        column_names (list): Names of chromatography columns being analyzed.
        orthogonality_metric_df (pd.DataFrame): DataFrame containing computed orthogonality metrics.
        correlation_group_df (pd.DataFrame): DataFrame of correlated orthogonality metric groups.
        orthogonality_result_df (pd.DataFrame): Final results DataFrame with rankings.
        retention_time_df (pd.DataFrame): Loaded retention time data.
        normalized_retention_time_df (pd.DataFrame): Normalized retention time data.
        combination_df (pd.DataFrame): DataFrame of column combinations.
        bin_number (int): Number of bins for box-based calculations (default: 14).
        nb_condition (int): Number of experimental conditions.
        nb_combination (int): Number of column combinations being analyzed.
        status (str): Current processing status ('no_data', 'loaded', 'error', etc.).
    """
    progressChanged = Signal(int)

    def __init__(self):
        """Initialize the Orthogonality object with default values and data structures."""
        super().__init__()
        self.column_names = []
        self.orthogonality_metric_df = None
        self.correlation_group_df = None
        self.orthogonality_result_df = None
        self.retention_time_df = None
        self.norm_ret_time_table = None
        self.normalized_retention_time_df = None
        self.gradient_end_time_df = None
        self.void_time_df = None
        self.combination_df = None
        self.orthogonality_metric_corr_matrix_df = None
        self.orthogonality_corr_mat = None
        self.orthogonality_score = None
        self.orthogonality_dict = None
        self.has_nan_value = False
        self.nan_policy_threshold = 50
        self.table_data = None
        self.om_function_map = None
        self.nb_peaks = None
        self.bin_number = 14
        self.nb_condition = 0
        self.nb_combination = 0
        self.retention_time_df = None
        self.retention_time_df_2d_peaks = None
        self.use_suggested_score = True
        self.status = "no_data"
        self.init_data()
        self.reset_om_status_computation_state()

    def get_has_nan_value(self) -> bool:
        """returns has_nan_value status.

        Returns:
            bool: True if NaN values are present in the data, False otherwise.
        """
        return self.has_nan_value

    def get_retention_time_df(self) -> pd.DataFrame:
        """Get the retention time DataFrame.

        Returns:
            pd.DataFrame: The loaded retention time data.
        """
        return self.retention_time_df

    def get_normalized_retention_time_df(self) -> pd.DataFrame:
        """Get the normalized retention time DataFrame.

        Returns:
            pd.DataFrame: The normalized retention time data.
        """
        return self.normalized_retention_time_df

    def get_number_of_condition(self) -> int:
        """Get the number of experimental conditions.

        Returns:
            int: The number of conditions (columns) in the dataset.
        """
        return self.nb_condition

    def get_number_of_combination(self) -> int:
        """Get the number of column combinations being analyzed.

        Returns:
            int: The number of 1D column combinations.
        """
        return self.nb_combination

    def get_number_of_bin(self) -> int:
        """Get the current number of bins used for box-based calculations.

        Returns:
            int: The number of bins per axis.
        """
        return self.bin_number

    def get_status(self) -> str:
        """Get the current status of the analysis.

        Returns:
            str: Current status indicator (e.g., 'loaded', 'error', 'complete','no_data')
        """
        return self.status

    def get_orthogonality_dict(self) -> dict:
        """Get the orthogonality dictionary containing analysis raw data for each set.

        Returns:
            dict: The orthogonality dictionary with keys as set names (e.g., 'Set 1')
                  and values as dictionaries of computed metrics.
        """
        return self.orthogonality_dict

    def get_table_data(self) -> list:
        """Get the table data containing computed metrics for tabular display.

        Returns:
            list: A list of lists, where each inner list represents a row of computed metrics
                  for a specific set.
        """
        return self.table_data

    def get_combination_df(self) -> pd.DataFrame:
        """Get the DataFrame containing column combinations and peak information.

        Returns:
            pd.DataFrame: DataFrame with Set #, 2D Combination, Number of peaks, 
                         and Hypothetical 2D peak capacity columns.
        """
        return self.combination_df

    def get_orthogonality_metric_df(self) -> pd.DataFrame:
        """Get the orthogonality metrics DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all computed orthogonality metrics 
                         for each column combination set.
        """
        return self.orthogonality_metric_df

    def get_orthogonality_metric_corr_matrix_df(self) -> pd.DataFrame:
        """Get the orthogonality metric correlation matrix DataFrame.

        Returns:
            pd.DataFrame: Correlation matrix of orthogonality metrics.
        """
        return self.orthogonality_metric_corr_matrix_df

    def get_orthogonality_result_df(self) -> pd.DataFrame:
        """Get the final orthogonality results DataFrame with rankings.

        Returns:
            pd.DataFrame: Results DataFrame with set numbers, scores, and rankings.
        """
        return self.orthogonality_result_df

    def get_orthogonality_score_df(self) -> dict:
        """Get the orthogonality scores dictionary.

        Returns:
            dict: Dictionary mapping set names to their orthogonality scores.
        """
        return self.orthogonality_score

    def get_correlation_group_df(self) -> pd.DataFrame:
        """Get the DataFrame of correlated orthogonality metric groups.

        Returns:
            pd.DataFrame: DataFrame with groups of correlated metrics.
        """
        return self.correlation_group_df

    def set_nan_policy_threshold(self, threshold: float) -> None:
        """Set the threshold for handling NaN values in the data.

        Args:
            threshold (float): Percentage threshold (0-100) for NaN tolerance.
                              Peaks with NaN percentage above this will be removed.
        """
        self.nan_policy_threshold = threshold

    def init_data(self) -> None:
        """Initialize or reset all data structures to their default empty states.

        This method creates empty DataFrames and data structures for storing
        retention times, metrics, scores, and results.
        """
        self.table_data = []
        self.norm_ret_time_table = []
        self.orthogonality_dict = {}
        self.orthogonality_score = {}
        self.orthogonality_corr_mat = {}
        self.orthogonality_metric_corr_matrix_df = pd.DataFrame()
        self.retention_time_df = pd.DataFrame()
        self.normalized_retention_time_df = pd.DataFrame()
        self.orthogonality_result_df = pd.DataFrame()
        self.correlation_group_df = pd.DataFrame()
        self.orthogonality_metric_df = pd.DataFrame()

        self.combination_df = pd.DataFrame(
            columns=[
                "Set #",
                "2D Combination",
                "Number of peaks",
                "Hypothetical 2D peak capacity",
            ]
        )

    def get_default_orthogonality_entry(self) -> dict:
        """Get a default dictionary structure for storing orthogonality metrics for one set.

        Returns:
            dict: Dictionary with default zero/empty values for all orthogonality metrics,
                  including convex hull, bin box, correlation coefficients, and various
                  computed scores.
        """
        return {
            "title": "",
            "type": "",
            "x_values": [],
            "x_title": "",
            "y_title": "",
            "y_values": [],
            "nb_peaks": 0,
            "hull_subset": 0,
            "convex_hull": 0,
            "bin_box": {"color_mask": 0, "edges": [0, 0]},
            "gilar-watson": {"color_mask": 0, "edges": [0, 0]},
            "modeling_approach": {"color_mask": 0, "edges": [0, 0]},
            "geometric_approach": 0,
            "conditional_entropy": {"histogram": 0, "edges": [0, 0], "value": 0},
            "bin_box_ratio": 0,
            "linregress": 0,
            "linregress_rvalue": 0,
            "quadratic_reg_xy": 0,
            "quadratic_reg_yx": 0,
            "pearson_r": 0,
            "spearman_rho": 0,
            "kendall_tau": 0,
            "asterisk_metrics": {
                "a0": 0,
                "z_minus": 0,
                "z_plus": 0,
                "z1": 0,
                "z2": 0,
                "sigma_sz_minus": 0,
                "sigma_sz_plus": 0,
                "sigma_sz1": 0,
                "sigma_sz2": 0,
            },
            "a_mean": 0,
            "g_mean": 0,
            "h_mean": 0,
            "percent_fit": {
                "delta_xy_avg": 0,
                "delta_xy_sd": 0,
                "delta_yx_avg": 0,
                "delta_yx_sd": 0,
                "value": 0,
            },
            "percent_bin": {
                "value": 0,
                "mask": 0,
                "sad_dev": 0,
                "sad_dev_ns": 0,
                "sad_dev_fs": 0,
            },
            "computed_score": 0,
            "orthogonality_factor": 0,
            "orthogonality_value": 0,
            "practical_2d_peak": 0,
            "2d_peak_capacity": "no data loaded",
        }

    def reset_om_status_computation_state(self) -> None:
        """Reset the computation status of all orthogonality metric functions.

        Sets all metric functions in om_function_map to NOT_COMPUTED status,
        allowing them to be recalculated.
        """
        self.om_function_map = {
            "Convex hull relative area": {
                "func": self.compute_convex_hull,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Bin box counting": {
                "func": self.compute_bin_box,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Pearson Correlation": {
                "func": self.compute_pearson,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Spearman Correlation": {
                "func": self.compute_spearman,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Kendall Correlation": {
                "func": self.compute_kendall,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "CC mean": {"func": self.compute_cc_mean, "status": FuncStatus.NOT_COMPUTED},
            "Asterisk equations": {
                "func": self.compute_asterisk,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "NND Arithm mean": {
                "func": self.compute_ndd,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "NND Geom mean": {
                "func": self.compute_ndd,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "NND Harm mean": {
                "func": self.compute_ndd,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "NND mean": {
                "func": self.compute_nnd_mean,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "%BIN": {
                "func": self.compute_percent_bin,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "%FIT": {
                "func": self.compute_percent_fit,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Gilar-Watson method": {
                "func": self.compute_gilar_watson_metric,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Modeling approach": {
                "func": self.compute_modeling_approach,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Geometric approach": {
                "func": self.compute_geometric_approach,
                "status": FuncStatus.NOT_COMPUTED,
            },
            "Conditional entropy": {
                "func": self.compute_conditional_entropy,
                "status": FuncStatus.NOT_COMPUTED,
            },
        }

    def update_num_bins(self, nb_bin: int, metric_list=None, progress_cb=None) -> None:
        """Set the number of bins for box calculations and update dependent properties.

        Args:
            nb_bin (int): Number of bins to use for box-based calculations.
                         Must be a positive integer.
            metric_list (list, optional): List of metrics to recompute.
            progress_cb (Signal, optional): Progress callback signal for updates.

        Raises:
            ValueError: If input is not a positive integer.
        """
        if not isinstance(nb_bin, int) or nb_bin <= 0:
            raise ValueError("Number of bins must be a positive integer")

        self.bin_number = nb_bin

        # reset function computed status in order to re compute with new bin number
        for metric in ["Bin box counting", "Modeling approach", "Gilar-Watson method"]:
            self.om_function_map[metric]["status"] = FuncStatus.NOT_COMPUTED

    def compute_orthogonality_metric(self, metric_list: list, progress_cb: Signal) -> None:
        """Compute orthogonality metrics for all sets and emit progress updates.

        Args:
            metric_list (list): List of metric names (UI format) to compute.
            progress_cb (Signal): Qt Signal for emitting progress percentage (0-100).

        Side Effects:
            - Computes all uncomputed metrics in metric_list
            - Updates orthogonality_metric_df and orthogonality_metric_corr_matrix_df
            - Emits progress updates via progress_cb
        """
        total_weight = sum(
            METRIC_WEIGHTS.get(metric, DEFAULT_WEIGHT)
            for metric in metric_list
            if self.om_function_map[metric]["status"] != FuncStatus.COMPUTED
        )
        accumulated_weight = 0

        for metric in metric_list:
            if self.om_function_map[metric]["status"] != FuncStatus.COMPUTED:
                self.om_function_map[metric]["func"]()
                accumulated_weight += METRIC_WEIGHTS.get(metric, DEFAULT_WEIGHT)
                percent = int((accumulated_weight / total_weight) * 100)
                progress_cb.emit(percent)

        # get column index of orthogonality metric in table_data
        column_index = [
            METRIC_MAPPING[UI_TO_MODEL_MAPPING[metric]]["table_index"]
            for metric in metric_list
        ]

        orthogonality_table_df = pd.DataFrame(self.table_data)

        # correlation matrix table only contains metric with no set number and combination title
        self.orthogonality_metric_df = orthogonality_table_df.iloc[
            :, np.r_[column_index]
        ]

        # add column name
        self.orthogonality_metric_df.columns = metric_list

        self.orthogonality_metric_corr_matrix_df = self.orthogonality_metric_df

        # 0 and 1 indexes are for set number and combination title
        column_index = [0, 1] + column_index
        self.orthogonality_metric_df = orthogonality_table_df.iloc[
            :, np.r_[column_index]
        ]

        # Adding column names directly
        self.orthogonality_metric_df.columns = ["Set #", "2D Combination"] + metric_list

    def set_orthogonality_value(self, selected_orthogonality: str) -> None:
        """Set the orthogonality value for each set based on a selected metric.

        Args:
            selected_orthogonality (str): The key of the selected orthogonality metric 
                                         (e.g., 'convex_hull', 'pearson_r').

        Side Effects:
            Updates orthogonality_value in both orthogonality_score and orthogonality_dict
            for all sets.
        """
        for data_set in self.orthogonality_dict:
            self.orthogonality_score[data_set]["orthogonality_value"] = (
                self.orthogonality_score[data_set][selected_orthogonality]
            )
            self.orthogonality_dict[data_set]["orthogonality_value"] = (
                self.orthogonality_score[data_set][selected_orthogonality]
            )

    def create_correlation_group(self, threshold: float, tol: float) -> pd.DataFrame:
        """Identify and group correlated orthogonality metrics based on correlation threshold.

        This method finds groups of metrics that are highly correlated with each other,
        which is useful for identifying redundant metrics and creating suggested scores.

        Args:
            threshold (float): Correlation coefficient threshold (0-1). Pairs with absolute
                             correlation >= threshold are considered correlated.
            tol (float): Tolerance value to adjust the threshold.

        Returns:
            pd.DataFrame: DataFrame with 'Group' and 'Correlated OM' columns, where each
                         row represents a group of correlated metrics.

        Note:
            Algorithm based on work by @yatharthranjan
            https://medium.com/@yatharthranjan/finding-top-correlation-pairs-from-a-large-number-of-variables-in-pandas-f530be53e82a
        """
        if self.orthogonality_metric_corr_matrix_df.empty:
            return pd.DataFrame()

        correlated_pair = {}
        orig_corr = self.orthogonality_metric_corr_matrix_df.corr()
        c = orig_corr.abs()

        correlated_metric = set()

        for row in orig_corr.itertuples():

            row_metric_list = []
            row_metric_name = row.Index
            row_metric_list.append(row_metric_name)

            for i in range(1, len(row)):
                column_metric_name = orig_corr.columns[i - 1]
                value = row[i]
                if abs(value) >= (threshold - tol):
                    row_metric_list.append(column_metric_name)

            # convert list in to set() to sort metric name, it will ease the process
            # to remove dupplicate groupe of correlated metric
            row_metric_list = sorted(set(row_metric_list))

            # you cannot add list in set() object
            correlated_metric.add(tuple(row_metric_list))

        sorted_correlated_metric = sorted(correlated_metric, key=len, reverse=True)

        groups, sorted_correlated_metric = cluster_and_fuse(sorted_correlated_metric)

        # If you pass a list of tuples directly → Pandas splits the tuples into multiple columns.
        # If you pass a dictionary with a column name → Pandas keeps each tuple as a single cell in that column.
        self.correlation_group_df = pd.DataFrame(
            {"Correlated OM": list(sorted_correlated_metric)}
        )

        # Add a new column with letters A-Z
        self.correlation_group_df["Group"] = list(
            string.ascii_uppercase[: len(self.correlation_group_df)]
        )

        self.correlation_group_df = self.correlation_group_df[
            ["Group", "Correlated OM"]
        ]

        return self.correlation_group_df

    def compute_custom_orthogonality_score(self, metric_list: list) -> None:
        """Compute a custom orthogonality score as the mean of selected metrics.

        Args:
            metric_list (list): A list of metric keys (UI format, e.g., ['Convex hull relative area', 'Pearson Correlation'])
                               used to compute the orthogonality score.

        Side Effects:
            Updates computed_score and orthogonality_value in orthogonality_score
            and table_data for each set.
        """
        num_metric = len(metric_list)
        if not num_metric:
            return  # Exit early if the metric list is empty

        # Iterate through each set in the orthogonality dictionary
        for index, data_set in enumerate(self.orthogonality_dict):
            # Reset the sum for each set
            score_sum = 0

            # Calculate the sum of the selected metric values
            for metric in metric_list:
                # the metrics name from the UI are different from the one in the model
                metric = UI_TO_MODEL_MAPPING[metric]
                score_sum += self.orthogonality_score[data_set][metric]

            # Compute the mean score
            mean_score = score_sum / num_metric

            set_number = extract_set_number(data_set)
            # Update the orthogonality score and dictionary using the helper function

            self.update_metrics(
                data_set, "computed_score", mean_score, table_row_index=set_number - 1
            )
            self.update_metrics(
                data_set,
                "orthogonality_value",
                mean_score,
                table_row_index=set_number - 1,
            )

    def om_using_nb_bin_computed(self) -> None:
        """Placeholder method for future bin-dependent orthogonality metric handling.

        Currently, does nothing, reserved for future functionality.
        """
        pass

    def suggested_om_score_flag(self, flag: bool) -> None:
        """Set whether to use suggested score or computed score for practical 2D peak capacity computation.

        Args:
            flag (bool): If True, use suggested_score; if False, use computed_score.
        """
        self.use_suggested_score = flag

    def compute_suggested_score(self) -> None:
        """Compute suggested orthogonality scores based on correlation groups.

        The suggested score is calculated as the mean of group means, where each group
        contains correlated metrics. This reduces bias from redundant metrics.

        Side Effects:
            Updates suggested_score and orthogonality_value in orthogonality_score
            and table_data for each set.
        """
        # Iterate through each set in the orthogonality dictionary
        for index, data_set in enumerate(self.orthogonality_score):
            # Reset the sum for each set

            mean_sum = 0

            for row in self.correlation_group_df.itertuples():
                group_sum = 0
                om_group = row[2]
                group_size = len(om_group)

                for metric in om_group:
                    metric = UI_TO_MODEL_MAPPING[metric]
                    group_sum += self.orthogonality_score[data_set][metric]

                group_mean = group_sum / group_size
                mean_sum += group_mean

            # Compute the mean score
            if len(self.correlation_group_df) == 0:
                return
            om_score = mean_sum / len(self.correlation_group_df)

            set_number = extract_set_number(data_set)
            # Update the orthogonality score and dictionary using the helper function
            self.update_metrics(
                data_set, "suggested_score", om_score, table_row_index=set_number - 1
            )
            self.update_metrics(
                data_set,
                "orthogonality_value",
                om_score,
                table_row_index=set_number - 1,
            )

    def compute_practical_2d_peak_capacity(self) -> None:
        """Compute practical 2D peak capacity for each set.

        Practical 2D peak capacity = orthogonality_score * hypothetical_2d_peak_capacity
        Uses either suggested_score or computed_score based on use_suggested_score flag.

        Side Effects:
            Updates practical_2d_peak_capacity in orthogonality_score and table_data
            for each set.

        Note:
            Only runs if status is 'peak_capacity_loaded'.
        """
        if self.status not in ["peak_capacity_loaded"]:
            return

        if self.use_suggested_score:
            om_score = "suggested_score"
        else:
            om_score = "computed_score"

        # Iterate through each set in the orthogonality dictionary
        for index, data_set in enumerate(self.orthogonality_dict):
            practical_2d_peak_capacity = (
                    self.orthogonality_score[data_set][om_score]
                    * self.orthogonality_score[data_set]["2d_peak_capacity"]
            )

            set_number = extract_set_number(data_set)
            self.update_metrics(
                data_set,
                "practical_2d_peak_capacity",
                practical_2d_peak_capacity,
                table_row_index=set_number - 1,
            )

    def create_results_table(self) -> None:
        """Create the final results DataFrame with scores and rankings.

        Extracts set numbers, titles, scores, and practical 2D peak capacities,
        then computes rankings based on practical 2D peak capacity.

        Side Effects:
            Updates orthogonality_result_df with final results and rankings.
        """
        if self.use_suggested_score:
            om_score = "suggested_score"
            om_score_label = "Suggested score"
        else:
            om_score = "computed_score"
            om_score_label = "Computed score"

        column_name = [
            "set_number",
            "title",
            "suggested_score",
            "computed_score",
            "practical_2d_peak_capacity",
        ]

        # get column index of orthogonality metric in table_data
        column_index = [METRIC_MAPPING[name]["table_index"] for name in column_name]

        self.orthogonality_result_df = pd.DataFrame(self.table_data)

        # correlation matrix table only contains metric with no set number and combination title
        self.orthogonality_result_df = self.orthogonality_result_df.iloc[
            :, np.r_[column_index]
        ]

        # add column name
        self.orthogonality_result_df.columns = [
            "Set #",
            "2D Combination",
            "Suggested score",
            "Computed score",
            "Practical 2D peak capacity",
        ]

        self.orthogonality_result_df.fillna(0)

        self.orthogonality_result_df["Ranking"] = (
            self.orthogonality_result_df["Practical 2D peak capacity"]
            .rank(method="dense", ascending=False)
            .astype("Int64", errors="ignore")
        )

        self.set_orthogonality_ranking_argument("Practical 2D peak capacity")

    def set_orthogonality_ranking_argument(self, argument: str) -> None:
        """Set the ranking criterion for the results table.

        Args:
            argument (str): Column name to rank by (e.g., 'Practical 2D peak capacity').

        Side Effects:
            Updates 'Ranking' column in orthogonality_result_df based on the specified column.
        """
        self.orthogonality_result_df["Ranking"] = (
            self.orthogonality_result_df[argument]
            .rank(method="dense", ascending=False)
            .astype("Int64", errors="ignore")
        )

    def compute_orthogonality_factor(self, method_list: list) -> None:
        """Compute the orthogonality factor as the product of selected method values.

        Args:
            method_list (list): A list of method keys (model format, e.g., ['convex_hull', 'pearson_r'])
                               used to compute the orthogonality factor.

        Side Effects:
            Updates orthogonality_factor in orthogonality_score for each set.
        """
        num_methods = len(method_list)
        if not num_methods:
            return  # Exit early if the method list is empty

        # Iterate through each set in the orthogonality dictionary
        for data_set in self.orthogonality_dict:
            # Initialize the product for each set
            product = 1

            # Calculate the product of the selected method values
            for method in method_list:
                product *= self.orthogonality_score[data_set][method]

            # Update the orthogonality factor using the helper function
            self.update_metrics(data_set, "orthogonality_factor", product)

    def update_metrics(self, dict_key: str, metric_name: str, value, table_row_index: int = -1) -> None:
        """Update orthogonality score and table data for a given metric.

        Args:
            dict_key (str): The key in the orthogonality dictionary (e.g., 'Set 1').
            metric_name (str): The name of the metric to update(e.g., 'convex_hull').
            value: The computed value of the metric.
            table_row_index (int, optional): The row index in table_data. Defaults to -1(means add at last position).

        Side Effects:
            Updates orthogonality_score and table_data with the new metric value.
        """
        # Update orthogonality score
        if METRIC_MAPPING[metric_name]["include_in_score"]:

            # Update a set with a new metric
            if dict_key in self.orthogonality_score:
                self.orthogonality_score[dict_key].update({metric_name: value})
            else:
                # add new set in orthogonality_score dict
                self.orthogonality_score.update({dict_key: {}})
                self.orthogonality_score[dict_key].update({metric_name: value})

        # Update table data
        table_index = METRIC_MAPPING[metric_name]["table_index"]
        self.table_data[table_row_index][table_index] = value

    def normalize_retention_time_min_max(self) -> None:
        """Normalize retention times using min-max normalization for each column.

        Formula: (x - rt_min) / (rt_max - rt_min)

        Side Effects:
            - Updates normalized_retention_time_df
            - Calls set_orthogonality_dict_x_y_series() to update metric dictionaries
            - Sets status to 'error' if normalization fails
        """
        data_frame_copy = self.retention_time_df.copy()

        for column_name in data_frame_copy.columns[1:]:
            column_value = data_frame_copy[column_name]

            # maximum and Rt0 retention time
            column_value_cleaned = list(filter(None, column_value))
            try:
                rt_min = min(column_value_cleaned)
                rt_max = max(column_value_cleaned)

            except Exception as e:
                issue = str(e)
                print(f"Error while normalizing {column_name} : {issue}")
                print(f"Unmatch void time column name (cannot find {column_name})")
                self.status = "error"

            # Normalizing data
            data_frame_copy[column_name] = column_value.apply(
                lambda x: (x - rt_min) / (rt_max - rt_min) if x else ""
            )

        self.normalized_retention_time_df = data_frame_copy.copy()

        # delete copy
        del data_frame_copy

        self.set_orthogonality_dict_x_y_series()

    def normalize_retention_time_void_max(self) -> None:
        """Normalize retention times using void time and max retention time.

        Formula: (x - rt_0) / (rt_max - rt_0)
        Requires void_time_df (rt_0) to be loaded.

        Side Effects:
            - Updates normalized_retention_time_df
            - Calls set_orthogonality_dict_x_y_series() to update metric dictionaries
            - Sets status to 'error' if normalization fails or void_time_df is missing
        """
        data_frame_copy = self.retention_time_df.copy()

        for column_name in data_frame_copy.columns[1:]:
            column_value = data_frame_copy[column_name]

            # maximum and Rt0 retention time

            try:
                rt_0 = self.void_time_df[column_name]

            except Exception as e:
                issue = str(e)
                print(f"Error while normalizing {column_name} : {issue}")
                print(f"Unmatch void time column name (cannot find {column_name})")
                self.status = "error"

            rt_max = column_value.max()

            # Normalizing data
            data_frame_copy[column_name] = column_value.apply(
                lambda x: (x - rt_0) / (rt_max - rt_0)
            )

        self.normalized_retention_time_df = data_frame_copy.copy()

        # delete copy
        del data_frame_copy

        self.set_orthogonality_dict_x_y_series()

    def normalize_retention_time_wosel(self) -> None:
        """Normalize retention times using Wosel method (void time and gradient end time).

        Formula: (x - rt_0) / (rt_end - rt_0)
        Requires void_time_df (rt_0) and gradient_end_time_df (rt_end) to be loaded.

        Side Effects:
            - Updates normalized_retention_time_df
            - Calls set_orthogonality_dict_x_y_series() to update metric dictionaries
            - Sets status to 'error' if required data is missing
        """
        data_frame_copy = self.retention_time_df.copy()

        for column_name in data_frame_copy.columns[1:]:
            column_value = data_frame_copy[column_name]

            # maximum and Rt0 retention time

            try:
                rt_0 = self.void_time_df[column_name]
                rt_end = self.gradient_end_time_df[column_name]

            except Exception as e:
                issue = str(e)
                print(f"Error while normalizing {column_name} : {issue}")
                print(f"Unmatch void time column name (cannot find {column_name})")
                self.status = "error"

            # Normalizing data
            data_frame_copy[column_name] = column_value.apply(
                lambda x: (x - rt_0) / (rt_end - rt_0)
            )

        self.normalized_retention_time_df = data_frame_copy.copy()

        # delete copy
        del data_frame_copy

        self.set_orthogonality_dict_x_y_series()

    def load_gradient_end_time(self, filepath: str, sheetname: str) -> None:
        """Load gradient end time data from an Excel file.

        Args:
            filepath (str): Path to the Excel file.
            sheetname (str): Name of the sheet to load.

        Side Effects:
            - Loads data into gradient_end_time_df
            - Sets status to 'error' if loading fails

        Raises:
            Exception: Re-raises any exception after setting status to 'error'.
        """
        try:

            self.gradient_end_time_df = load_simple_table(filepath, sheetname)

        except Exception as e:
            print(f"Error loading gradient time: {str(e)}")
            self.status = "error"
            raise

    def load_void_time(self, filepath: str, sheetname: str) -> None:
        """Load void time (t0) data from an Excel file.

        Args:
            filepath (str): Path to the Excel file.
            sheetname (str): Name of the sheet to load.

        Side Effects:
            - Loads data into void_time_df
            - Prints void_time_df for debugging
            - Sets status to 'error' if loading fails

        Raises:
            Exception: Re-raises any exception after setting status to 'error'.
        """
        try:

            # Read table, assuming headers are on the second row (row index 1, i.e., header=1)
            self.void_time_df = load_simple_table(filepath, sheetname)

            print(self.void_time_df)

        except Exception as e:
            print(f"Error loading end time: {str(e)}")
            self.status = "error"
            raise

    def set_orthogonality_dict_x_y_series(self) -> None:
        """Update x_values and y_values in orthogonality_dict from normalized retention times.

        each pairwise is a combination of two 1D LC condition , x_values contains all the retention times for the 1st
        condition and y_values for the 2nd condition.

        Creates all pairwise combinations of columns and populates the orthogonality_dict
        with normalized x,y series after removing incomplete pairs.

        Side Effects:
            - Updates x_values, y_values, and nb_peaks in orthogonality_dict
            - Calls update_combination_df() to refresh combination DataFrame
            - Removes sets with no valid data points
        """
        num_columns = len(self.column_names)

        current_column = 0
        set_number = 1

        while current_column < num_columns:
            current_column_name = self.column_names[current_column]
            x_values = self.normalized_retention_time_df[current_column_name]

            if num_columns > 2:
                next_column_list = list(range(current_column + 1, num_columns))
            else:
                # the dataframe only has 2 column
                next_column_list = [1]

            for next_column in next_column_list:
                next_column_name = self.column_names[next_column]
                set_key = f"Set {set_number}"
                y_values = self.normalized_retention_time_df[next_column_name]

                # check if x,y pair element contains at least one empty item.
                # if an empty item exist on an x,y pair, that pair will be deleted from the list
                x_y_pair_list = list(zip(x_values, y_values))
                x_y_pair_list = [
                    pair for pair in x_y_pair_list if pair[0] != "" and pair[1] != ""
                ]

                if x_y_pair_list:
                    # unpack x and y list cleaned of incomplete x y pairs

                    x_series, y_series = zip(*x_y_pair_list)

                    # working with pd.Series makes operation on list easier
                    x_series = pd.Series(x_series)
                    y_series = pd.Series(y_series)

                    nb_peaks = len(x_y_pair_list)

                    # in case 1 or 0 has been deleted from the list, retention time should be normalized again
                    x_series, y_series = normalize_x_y_series(x_series, y_series)

                    # Update orthogonality dictionary
                    self.orthogonality_dict[set_key]["x_values"] = x_series
                    self.orthogonality_dict[set_key]["y_values"] = y_series
                    self.orthogonality_dict[set_key]["nb_peaks"] = nb_peaks
                    set_number = extract_set_number(set_key)
                    self.update_metrics(
                        set_key, "nb_peaks", nb_peaks, table_row_index=set_number - 1
                    )

                else:
                    if set_key in self.orthogonality_dict:
                        self.orthogonality_dict.pop(set_key)

                set_number += 1

            current_column += 1

        self.update_combination_df()

    def normalize_retention_time(self, method: str) -> None:
        """Normalize retention time data using the specified method.

        Args:
            method (str): Normalization method to use:
                         - 'min_max': Min-max normalization
                         - 'void_max': Void time to max normalization
                         - 'wosel': Wosel normalization (void time to gradient end)
        """
        if method == "min_max":
            self.normalize_retention_time_min_max()

        if method == "void_max":
            self.normalize_retention_time_void_max()

        if method == "wosel":
            self.normalize_retention_time_wosel()

    def clean_nan_value(self, option: str) -> None:
        """Handle NaN values in retention time data according to the specified option.

        Args:
            option (str): NaN handling method:
                         - 'option 1': Remove peaks with NaN% > nan_policy_threshold
                         - 'option 2': Replace all NaN with empty strings

        Side Effects:
            - Modifies retention_time_df
            - Updates orthogonality_dict with cleaned x,y series
            - Calls update_combination_df() to refresh combination DataFrame
        """
        peak_list = []
        if option == "option 1":
            for row_data in self.retention_time_df.iterrows():
                peak_retention_time = row_data[1]
                nan_count = peak_retention_time.isna().sum()

                # nan_policy_threshold is % of total condition
                if (nan_count * 100) / self.nb_condition > self.nan_policy_threshold:
                    peak_list.append(row_data[0])

            self.retention_time_df = self.retention_time_df.drop(peak_list)
            self.retention_time_df = self.retention_time_df.fillna("")

        if option == "option 2":
            self.retention_time_df = self.retention_time_df.fillna("")

        num_columns = len(self.column_names)

        current_column = 0
        set_number = 1

        while current_column < num_columns:
            current_column_name = self.column_names[current_column]
            x_values = self.retention_time_df[current_column_name]

            if num_columns > 2:
                next_column_list = list(range(current_column + 1, num_columns))
            else:
                # the dataframe only has 2 column
                next_column_list = [1]

            for next_column in next_column_list:
                next_column_name = self.column_names[next_column]
                set_key = f"Set {set_number}"
                y_values = self.retention_time_df[next_column_name]

                # check if x,y pair element contains at least one empty item.
                # if an empty item exist on an x,y pair, that pair will be deleted from the list
                x_y_pair_list = list(zip(x_values, y_values))
                x_y_pair_list = [
                    pair for pair in x_y_pair_list if pair[0] != "" and pair[1] != ""
                ]

                if x_y_pair_list:
                    # unpack x and y list cleaned of incomplete x y pairs

                    x_series, y_series = zip(*x_y_pair_list)

                    # working with pd.Series makes operation on list easier
                    x_series = pd.Series(x_series)
                    y_series = pd.Series(y_series)

                    nb_peaks = len(x_y_pair_list)

                    # Update orthogonality dictionary
                    self.orthogonality_dict[set_key]["x_values"] = x_series
                    self.orthogonality_dict[set_key]["y_values"] = y_series
                    self.orthogonality_dict[set_key]["nb_peaks"] = nb_peaks

                    set_number = extract_set_number(set_key)
                    self.update_metrics(
                        set_key, "nb_peaks", nb_peaks, table_row_index=set_number - 1
                    )

                else:
                    self.orthogonality_dict.pop(set_key)

                set_number += 1

            current_column += 1

        self.update_combination_df()

    def update_combination_df(self) -> None:
        """Update the combination DataFrame with set information and peak counts.

        Only updates if the 'Hypothetical 2D peak capacity' column is empty.

        Side Effects:
            Updates combination_df with data from table_data (columns 0-3).
        """
        # Check if combination_df exists and has the third column filled (not empty)
        if self.combination_df["Hypothetical 2D peak capacity"].isnull().all():
            # Otherwise, fill with two columns
            combination_table = [row[0:4] for row in self.table_data]
            self.combination_df = pd.DataFrame(
                combination_table,
                columns=[
                    "Set #",
                    "2D Combination",
                    "Number of peaks",
                    "Hypothetical 2D peak capacity",
                ],
            )
        else:
            # already filled
            return

    def load_retention_time(self, filepath: str, sheetname: str) -> None:
        """Load retention time data from an Excel file and initialize analysis structures.

        Args:
            filepath (str): Path to the Excel file with the raw data.
            sheetname (str): Name of the sheet to load.

        Side Effects:
            - Initializes/resets all data structures via init_data()
            - Loads data into retention_time_df
            - Detects NaN values and sets has_nan_value flag
            - Creates all pairwise column combinations
            - Initializes orthogonality_dict and table_data for each combination
            - Sets status to 'loaded' on success or 'error' on failure

        Raises:
            Exception: Re-raises any exception after setting status to 'error'.
        """
        try:
            # table_data should be reset when loading new normalized time
            self.init_data()

            self.retention_time_df = load_table_with_header_anywhere(
                filepath, sheetname
            )

            # check there is nan value in data frame
            self.has_nan_value = self.retention_time_df.isnull().any().any()

            self.column_names = self.retention_time_df.columns.tolist()
            self.nb_condition = num_columns = len(self.column_names)
            self.nb_peaks = len(self.retention_time_df.iloc[:, 0])

            # Initialize loop parameters
            self.retention_time_df.insert(
                0, "Peak #", range(1, len(self.retention_time_df) + 1)
            )

            current_column = 0
            set_number = 1

            while current_column < num_columns:
                current_column_name = self.column_names[current_column]
                x_values = self.retention_time_df[current_column_name]

                for next_column in range(current_column + 1, num_columns):
                    next_column_name = self.column_names[next_column]
                    set_key = f"Set {set_number}"
                    set_title = f"{current_column_name} vs {next_column_name}"
                    y_values = self.retention_time_df[next_column_name]

                    # Initialize table data by adding a new row with None values
                    self.table_data.append([None] * len(METRIC_MAPPING))

                    # Update metadata columns
                    self.update_metrics(set_key, "set_number", set_number)
                    self.update_metrics(set_key, "title", set_title)
                    self.update_metrics(set_key, "nb_peaks", self.nb_peaks)
                    self.update_metrics(set_key, "suggested_score", 0)
                    self.update_metrics(set_key, "computed_score", 0)
                    self.update_metrics(set_key, "orthogonality_factor", 0)
                    self.update_metrics(set_key, "orthogonality_value", 0)
                    self.update_metrics(set_key, "practical_2d_peak_capacity", 0)

                    # Determine column types
                    column1_type = "HILIC" if current_column < 8 else "RPLC"
                    column2_type = "HILIC" if next_column < 8 else "RPLC"

                    # Update orthogonality dictionary
                    self.orthogonality_dict[set_key] = {
                        "title": set_title,
                        "type": f"{column1_type}|{column2_type}",
                        "x_values": x_values,
                        "x_title": self.column_names[current_column],
                        "y_title": self.column_names[next_column],
                        "y_values": y_values,
                        "nb_peaks": self.nb_peaks,
                        "hull_subset": 0,
                        "convex_hull": 0,
                        "bin_box": {"color_mask": 0, "edges": [0, 0]},
                        "gilar-watson": {"color_mask": 0, "edges": [0, 0]},
                        "modeling_approach": {"color_mask": 0, "edges": [0, 0]},
                        "geometric_approach": 0,
                        "conditional_entropy": {
                            "histogram": 0,
                            "edges": [0, 0],
                            "value": 0,
                        },
                        "bin_box_ratio": 0,
                        "linregress": 0,
                        "linregress_rvalue": 0,
                        "quadratic_reg_xy": 0,
                        "quadratic_reg_yx": 0,
                        "pearson_r": 0,
                        "spearman_rho": 0,
                        "kendall_tau": 0,
                        "asterisk_metrics": {
                            "a0": 0,
                            "z_minus": 0,
                            "z_plus": 0,
                            "z1": 0,
                            "z2": 0,
                            "sigma_sz_minus": 0,
                            "sigma_sz_plus": 0,
                            "sigma_sz1": 0,
                            "sigma_sz2": 0,
                        },
                        "a_mean": 0,
                        "g_mean": 0,
                        "h_mean": 0,
                        "percent_fit": {
                            "delta_xy_avg": 0,
                            "delta_xy_sd": 0,
                            "delta_yx_avg": 0,
                            "delta_yx_sd": 0,
                            "value": 0,
                        },
                        "percent_bin": {
                            "value": 0,
                            "mask": 0,
                            "sad_dev": 0,
                            "sad_dev_ns": 0,
                            "sad_dev_fs": 0,
                        },
                        "computed_score": 0,
                        "orthogonality_factor": 0,
                        "orthogonality_value": 0,
                        "practical_2d_peak": 0,
                        "2d_peak_capacity": "no data loaded",
                    }
                    set_number += 1

                current_column += 1

            self.nb_combination = set_number - 1

            self.update_combination_df()

            self.status = "loaded"
        except Exception as e:
            issue = str(e)
            print(f"Error loading data: {issue}")
            self.status = "error"

    def compute_convex_hull(self) -> None:
        """Compute the convex hull volume for each set of peak distribution.

        The convex hull represents the smallest convex polygon containing all peaks.
        Its area is used as an orthogonality metric (higher is better).

        Side Effects:
            - Updates 'convex_hull' and 'hull_subset' in orthogonality_dict
            - Updates convex_hull metric in table_data
            - Sets 'Convex hull relative area' status to COMPUTED

        Note:
            Returns 0 if points are collinear or duplicate points reduce rank to 1.
        """
        for set_key in self.orthogonality_dict.keys():
            print(set_key)
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            # Stack the x and y coordinates into a 2D array of shape (n_points, 2)
            subset = np.vstack((x, y)).T

            # remove duplicate point
            subset = np.unique(subset, axis=0)

            # check that points all lie on a 1D subspace, the rank will be 1.
            p0 = subset[0]
            diffs = subset - p0
            rank = np.linalg.matrix_rank(diffs)

            if rank <= 1:
                cvx_volume = 0.0
                convex_hull = None
            else:
                # Compute the convex hull for the set of points
                convex_hull = ConvexHull(subset)
                cvx_volume = convex_hull.volume

            set_data["convex_hull"] = convex_hull
            set_data["hull_subset"] = subset
            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "convex_hull", cvx_volume, table_row_index=set_number - 1
            )

        self.om_function_map["Convex hull relative area"][
            "status"
        ] = FuncStatus.COMPUTED

    def compute_bin_box(self) -> None:
        """Compute the bin box ratio orthogonality metric for each set.

        Divides the [0,1] x [0,1] space into a grid and calculates the fraction
        of bins that contain at least one peak.

        Side Effects:
            - Updates 'bin_box' (color_mask and edges) and 'bin_box_ratio' in orthogonality_dict
            - Updates bin_box_ratio metric in table_data
            - Sets 'Bin box counting' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            h_color, x_edges, y_edges = compute_bin_box_mask_color(
                x, y, self.bin_number
            )

            bin_box_ratio = h_color.count() / (self.bin_number * self.bin_number)
            set_data["bin_box"]["color_mask"] = h_color
            set_data["bin_box"]["edges"] = [x_edges, y_edges]
            set_data["bin_box_ratio"] = bin_box_ratio

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "bin_box_ratio", bin_box_ratio, table_row_index=set_number - 1
            )

        self.om_function_map["Bin box counting"]["status"] = FuncStatus.COMPUTED

    def compute_pearson(self) -> None:
        """Compute Pearson correlation coefficient for each set .

        This orthogonality metric is calculated as 1 - r^2, where r is the Pearson
        correlation coefficient. Higher values indicate better orthogonality.

        Side Effects:
            - Updates 'pearson_r' in orthogonality_dict (raw correlation)
            - Updates pearson_r metric in table_data (as 1 - r^2)
            - Sets 'Pearson Correlation' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            pearson_r = pearsonr(x, y)[0]
            set_data["pearson_r"] = pearson_r

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "pearson_r", (1 - pearson_r ** 2), table_row_index=set_number - 1
            )

        self.om_function_map["Pearson Correlation"]["status"] = FuncStatus.COMPUTED

    def compute_spearman(self) -> None:
        """Compute Spearman rank correlation coefficient for each set.

        This orthogonality metric is calculated as 1 - rho^2, where rho is the Spearman
        rank correlation coefficient.

        Side Effects:
            - Updates 'spearman_rho' in orthogonality_dict (raw correlation)
            - Updates spearman_rho metric in table_data (as 1 - rho^2)
            - Sets 'Spearman Correlation' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            spearman_rho = spearmanr(x, y)[0]
            set_data["spearman_rho"] = spearman_rho

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key,
                "spearman_rho",
                (1 - spearman_rho ** 2),
                table_row_index=set_number - 1,
            )

        self.om_function_map["Spearman Correlation"]["status"] = FuncStatus.COMPUTED

    def compute_kendall(self) -> None:
        """Compute Kendall's tau correlation coefficient for each set.

        This orthogonality metric is calculated as 1 - tau^2, where tau is Kendall's tau
        correlation coefficient.

        Side Effects:
            - Updates 'kendall_tau' in orthogonality_dict (raw correlation)
            - Updates kendall_tau metric in table_data (as 1 - tau^2)
            - Sets 'Kendall Correlation' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            kendall_tau = kendalltau(x, y)[0]
            set_data["kendall_tau"] = kendall_tau

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key,
                "kendall_tau",
                (1 - kendall_tau ** 2),
                table_row_index=set_number - 1,
            )

        self.om_function_map["Kendall Correlation"]["status"] = FuncStatus.COMPUTED

    def compute_cc_mean(self) -> None:
        """Compute the mean of correlation coefficient-based orthogonality metrics.

        Calculates the trimmed mean of (1 - r^2), (1 - rho^2), and (1 - tau^2).e

        Side Effects:
            - Updates cc_mean metric in table_data
            - Sets 'CC mean' status to COMPUTED

        Note:
            Requires Pearson, Spearman, and Kendall to be computed first.
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]

            r = set_data["pearson_r"]
            rho = set_data["spearman_rho"]
            tau = set_data["kendall_tau"]

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key,
                "cc_mean",
                tmean([(1 - r ** 2), (1 - rho ** 2), (1 - tau ** 2)]),
                table_row_index=set_number - 1,
            )

        self.om_function_map["CC mean"]["status"] = FuncStatus.COMPUTED

    def compute_asterisk(self) -> None:
        """Compute the a0cs (asterisk) metric based on standard deviations of retention differences.

        The asterisk metric evaluates orthogonality using four intermediate z-values
        computed from differences between and within dimensions.

        Side Effects:
            - Updates 'asterisk_metrics' in orthogonality_dict with all intermediate values
            - Updates asterisk_metrics (a0cs value) in table_data
            - Sets 'Asterisk equations' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            # Compute differences and their standard deviations
            diff_sigma_sz_minus = x.subtract(y)
            sigma_sz_minus = diff_sigma_sz_minus.std()

            diff_sigma_sz_plus = y.subtract(
                1 - x
            )  # Equivalent to y.subtract(x.rsub(1))
            sigma_sz_plus = diff_sigma_sz_plus.std()

            diff_sigma_sz1 = x.subtract(0.5)
            sigma_sz1 = diff_sigma_sz1.std()

            diff_sigma_sz2 = y.subtract(0.5)
            sigma_sz2 = diff_sigma_sz2.std()

            # Compute intermediate z values
            z_minus = abs(1 - (2.5 * abs(sigma_sz_minus - 0.4)))
            z_plus = abs(1 - (2.5 * abs(sigma_sz_plus - 0.4)))
            z1 = 1 - abs(2.5 * sigma_sz1 * sqrt(2) - 1)
            z2 = 1 - abs(2.5 * sigma_sz2 * sqrt(2) - 1)

            # Compute the a0cs metric
            a0cs = sqrt(z_minus * z_plus * z1 * z2)

            set_data["asterisk_metrics"] = {
                "a0": a0cs,
                "z_minus": z_minus,
                "z_plus": z_plus,
                "z1": z1,
                "z2": z2,
                "sigma_sz_minus": sigma_sz_minus,
                "sigma_sz_plus": sigma_sz_plus,
                "sigma_sz1": sigma_sz1,
                "sigma_sz2": sigma_sz2,
            }

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "asterisk_metrics", a0cs, table_row_index=set_number - 1
            )

        self.om_function_map["Asterisk equations"]["status"] = FuncStatus.COMPUTED

    def compute_ndd(self) -> None:
        """Compute normalized nearest-neighbor distance metrics (arithmetic, geometric, harmonic means).

        Computes the Euclidean distance matrix, performs hierarchical clustering,
        and normalizes the arithmetic, harmonic, and geometric means of distances.

        Side Effects:
            - Updates 'a_mean', 'g_mean', 'h_mean' in orthogonality_dict
            - Updates nnd_arithmetic_mean, nnd_geom_mean, nnd_harm_mean in table_data
            - Sets 'NND Arithm mean', 'NND Geom mean', 'NND Harm mean' statuses to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            # Concatenate the input series into a DataFrame
            data = pd.concat([x, y], axis=1)

            # Compute the Euclidean distance matrix
            distance_matrix = pdist(data, "euclidean")

            # Perform hierarchical clustering using the single linkage method
            linkage_matrix = linkage(distance_matrix, "single")

            # Extract the distance values from the linkage matrix
            distances = linkage_matrix[:, 2]

            # Remove distances equal to 0
            distances = distances[distances > 0]

            # Compute the arithmetic, harmonic, and geometric means of the distances
            ao = tmean(distances)
            ho = hmean(distances)
            go = gmean(distances)

            nb_peaks = set_data["nb_peaks"]

            # Normalize the means using the number of peaks
            ao = (ao * (sqrt(nb_peaks) - 1)) / 0.64
            ho = (ho * (sqrt(nb_peaks) - 1)) / 0.64
            go = (go * (sqrt(nb_peaks) - 1)) / 0.64

            set_data["a_mean"] = ao
            set_data["g_mean"] = go
            set_data["h_mean"] = ho

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "nnd_arithmetic_mean", ao, table_row_index=set_number - 1
            )
            self.update_metrics(
                set_key, "nnd_geom_mean", go, table_row_index=set_number - 1
            )
            self.update_metrics(
                set_key, "nnd_harm_mean", ho, table_row_index=set_number - 1
            )

        self.om_function_map["NND Arithm mean"]["status"] = FuncStatus.COMPUTED
        self.om_function_map["NND Geom mean"]["status"] = FuncStatus.COMPUTED
        self.om_function_map["NND Harm mean"]["status"] = FuncStatus.COMPUTED

    def compute_nnd_mean(self) -> None:
        """Compute the mean of NND (nearest-neighbor distance) metrics.

        Calculates the trimmed mean of arithmetic, geometric, and harmonic NND means.
        Calls compute_ndd() first to ensure NND metrics are available.

        Side Effects:
            - Updates 'nnd_mean' in orthogonality_dict
            - Updates nnd_mean metric in table_data
            - Sets 'NND mean' status to COMPUTED
        """
        self.compute_ndd()

        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            ao = set_data["a_mean"]
            go = set_data["g_mean"]
            ho = set_data["h_mean"]

            nnd_mean = tmean([ao, go, ho])
            set_data["nnd_mean"] = nnd_mean

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "nnd_mean", nnd_mean, table_row_index=set_number - 1
            )

        self.om_function_map["NND mean"]["status"] = FuncStatus.COMPUTED

    def compute_percent_bin(self) -> None:
        """Compute the percent bin (%BIN) orthogonality metric for each set.

        Measures how evenly peaks are distributed across a 5x5 grid using sum of
        absolute deviations (SAD) from the ideal uniform distribution.

        Side Effects:
            - Updates 'percent_bin' in orthogonality_dict with value, mask, edges, and SAD values
            - Updates percent_bin metric in table_data
            - Sets '%BIN' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            # Compute the 2D histogram edges based on the range [0, 1]
            h, x_edges, y_edges = np.histogram2d([0, 1], [0, 1], bins=(5, 5))

            # Compute the 2D histogram for the input data using the same edges
            h_count = np.histogram2d(x, y, bins=[x_edges, y_edges])

            # Calculate the number of peaks and bins
            nb_peaks = len(x)
            nb_bins = 25
            avg_p_b = nb_peaks / nb_bins  # Average peaks per bin

            # Compute the sum of absolute deviations (SAD) from the average peaks per bin
            sad_dev = 0
            for bins in h_count[0]:
                for peaks_in_bin in bins:
                    sad_dev += abs(peaks_in_bin - avg_p_b)

            # Compute the ideal peaks per bin for full peak spreading
            ideal_peaks_per_bin, remaining_peaks = divmod(nb_peaks, nb_bins)
            peaks_per_bin_list = [ideal_peaks_per_bin] * nb_bins

            # Distribute the remaining peaks evenly across bins
            for i in range(remaining_peaks):
                peaks_per_bin_list[i] += 1

            # Compute the sum of absolute deviations for full peak spreading
            sad_dev_fs = 0
            for peaks_in_bin in peaks_per_bin_list:
                sad_dev_fs += abs(peaks_in_bin - avg_p_b)

            # Compute the sum of absolute deviations for no peak spreading
            sum_abs_dev_full = abs(nb_peaks - avg_p_b)  # All peaks in one bin
            sum_abs_dev_empty = (nb_bins - 1) * abs(
                0 - avg_p_b
            )  # Remaining bins are empty
            sad_dev_ns = sum_abs_dev_full + sum_abs_dev_empty

            # Compute the percentage of bin occupancy
            percent_bin = 1 - ((sad_dev - sad_dev_fs) / (sad_dev_ns - sad_dev_fs))

            # Compute the bin box mask
            h_color, x_edges, y_edges = compute_bin_box_mask_color(x, y, 5)

            set_data["percent_bin"] = {
                "value": percent_bin,
                "mask": h_color,
                "edges": [x_edges, y_edges],
                "sad_dev": sad_dev,
                "sad_dev_ns": sad_dev_ns,
                "sad_dev_fs": sad_dev_fs,
            }

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "percent_bin", percent_bin, table_row_index=set_number - 1
            )

        self.om_function_map["%BIN"]["status"] = FuncStatus.COMPUTED

    def compute_percent_fit(self) -> None:
        """Compute the %FIT orthogonality metric for each set using multithreading.

        Uses ThreadPoolExecutor to compute %FIT metric concurrently for all sets,
        improving performance for computationally intensive calculations.

        Side Effects:
            - Updates 'percent_fit' in orthogonality_dict
            - Updates percent_fit metric in table_data
            - Sets '%FIT' status to COMPUTED (implicitly, after all computations)

        Note:
            The actual computation is delegated to compute_percent_fit_for_set function.
        """
        sets = list(self.orthogonality_dict.items())
        results = []

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(compute_percent_fit_for_set, set_key, set_data)
                for set_key, set_data in sets
            ]
            for future in as_completed(futures):
                set_key, result = future.result()
                # Update in main thread: orthogonality_dict and table
                self.orthogonality_dict[set_key].update(result)
                set_number = extract_set_number(set_key)
                self.update_metrics(
                    set_key,
                    "percent_fit",
                    result["percent_fit"]["value"],
                    table_row_index=set_number - 1,
                )

    def compute_gilar_watson_metric(self) -> None:
        """Compute the Gilar-Watson orthogonality metric for each set.

        This metric accounts for expected bin occupancy based on the number of peaks
        and bins, using an exponential model for random peak distribution.

        Formula: (occupied_bins - nb_bins) / (0.63 * total_bins - nb_bins)

        Side Effects:
            - Updates 'gilar-watson' in orthogonality_dict with color_mask and edges
            - Updates gilar-watson metric in table_data
            - Sets 'Gilar-Watson method' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]

            h_color, x_edges, y_edges = compute_bin_box_mask_color(
                x, y, self.bin_number
            )
            p_square = self.bin_number * self.bin_number
            sum_bin = h_color.count()

            orthogonality = (sum_bin - self.bin_number) / (
                    (0.63 * p_square) - self.bin_number
            )

            set_data["gilar-watson"]["color_mask"] = h_color
            set_data["gilar-watson"]["edges"] = [x_edges, y_edges]

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key, "gilar-watson", orthogonality, table_row_index=set_number - 1
            )

        self.om_function_map["Gilar-Watson method"]["status"] = FuncStatus.COMPUTED

    def compute_modeling_approach(self) -> None:
        """Compute orthogonality using the modeling approach metric.

        This method combines bin coverage (C_pert) with correlation-based spread (C_peaks).
        It builds a 2D histogram and performs linear regression to evaluate orthogonality.

        Formula: orthogonality = C_pert * C_peaks
                 where C_pert = occupied_bins / (0.63 * total_bins)
                 and C_peaks = 1 - R²

        Side Effects:
            - Updates 'modeling_approach' with color_mask and edges in orthogonality_dict
            - Updates 'linregress' and 'linregress_rvalue' in orthogonality_dict
            - Updates modeling_approach metric in table_data
            - Sets 'Modeling approach' status to COMPUTED
        """
        # Loop over each data set in the orthogonality dictionary
        for set_key, set_data in self.orthogonality_dict.items():
            # Extract normalized retention‐time arrays for this set
            x = set_data["x_values"]
            y = set_data["y_values"]

            # 1) Compute masked 2D histogram: bins with no data are masked
            h_color, x_edges, y_edges = compute_bin_box_mask_color(
                x, y, self.bin_number
            )

            set_data["modeling_approach"]["color_mask"] = h_color
            set_data["modeling_approach"]["edges"] = [x_edges, y_edges]

            # 2) Calculate bin-coverage term C_pert
            p_square = self.bin_number * self.bin_number
            sum_bin = h_color.count()
            c_pert = sum_bin / (0.63 * p_square)

            # 3) Perform OLS regression of y vs. x to get R²
            regression_result = linregress(x, y)
            R2 = regression_result.rvalue ** 2
            set_data["linregress"] = regression_result

            c_peaks = 1.0 - R2
            set_data["linregress_rvalue"] = c_peaks

            # 4) Compute overall orthogonality = C_pert * C_peaks
            orthogonality = c_pert * c_peaks

            # 5) Determine the table row index from the set key
            set_number = extract_set_number(set_key)
            # 6) Update the metrics table with the new orthogonality value
            self.update_metrics(
                set_key,
                "modeling_approach",
                orthogonality,
                table_row_index=set_number - 1,
            )

        self.om_function_map["Modeling approach"]["status"] = FuncStatus.COMPUTED

    def compute_conditional_entropy(self) -> None:
        """Compute conditional entropy-based orthogonality metric for each set.

        Measures orthogonality using information theory: how much information about Y
        is gained from knowing X. Higher conditional entropy relative to Y's entropy
        indicates better orthogonality.

        Formula: H(Y|X) / H(Y)

        Side Effects:
            - Updates 'conditional_entropy' with value, histogram, and edges in orthogonality_dict
            - Updates conditional_entropy metric in table_data
            - Sets 'Conditional entropy' status to COMPUTED
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x = set_data["x_values"]
            y = set_data["y_values"]

            bin_number = round(1 + log2(self.nb_peaks))
            # 1) Marginals via histogram
            count_x, _ = np.histogram(x, bins=bin_number, range=(0, 1))
            count_y, _ = np.histogram(y, bins=bin_number, range=(0, 1))
            px = count_x / float(self.nb_peaks)
            py = count_y / float(self.nb_peaks)

            # 2) Joint via 2D histogram

            count_xy, x_edges, y_edges = np.histogram2d(
                x, y, bins=[bin_number, bin_number], range=[[0, 1], [0, 1]]
            )
            pxy = count_xy / float(self.nb_peaks)

            # 3) Entropies
            px_nz = px[px > 0]
            H_x = sum(px_nz * np.log2(px_nz))
            py_nz = py[py > 0]
            H_y = sum(py_nz * np.log2(py_nz))

            pxy_nz = pxy.flatten()[pxy.flatten() > 0]
            H_xy = sum(pxy_nz * np.log2(pxy_nz))

            # 4) Conditional entropy
            H_y_given_x = H_xy - H_x
            conditional_entropy = H_y_given_x / H_y

            set_data["conditional_entropy"]["value"] = conditional_entropy
            set_data["conditional_entropy"]["histogram"] = count_xy
            set_data["conditional_entropy"]["edges"] = [x_edges, y_edges]

            set_number = extract_set_number(set_key)
            self.update_metrics(
                set_key,
                "conditional_entropy",
                conditional_entropy,
                table_row_index=set_number - 1,
            )

        self.om_function_map["Conditional entropy"]["status"] = FuncStatus.COMPUTED

    def compute_geometric_approach(self) -> None:
        """Compute geometric orthogonality metric based on 2D peak capacity geometry.

        Uses the angle between dimensions (beta) and peak capacities to compute
        the practical peak capacity based on geometric considerations.

        Requires retention_time_df_2d_peaks to be loaded first.

        Side Effects:
            - Updates geometric_approach metric in table_data
            - Sets 'Geometric approach' status to COMPUTED

        Note:
            Uses standardized retention times and peak capacity data to compute
            the angle beta via arccos(correlation) and geometric formulas.
        """
        for set_key in self.orthogonality_dict.keys():
            set_data = self.orthogonality_dict[set_key]
            x = np.array(set_data["x_values"])
            y = np.array(set_data["y_values"])

            D1_title = set_data["x_title"]
            D2_title = set_data["y_title"]

            # Build a tiny DataFrame so we can standardize easily:
            K = pd.DataFrame({D1_title: x, D2_title: y})

            #  Mean‐center and scale each column
            mu_1 = K[D1_title].mean()
            mu_2 = K[D2_title].mean()

            sigma_1 = K[D1_title].std(ddof=0)
            sigma_2 = K[D2_title].std(ddof=0)

            K[D1_title] = (K[D1_title] - mu_1) / sigma_1
            K[D2_title] = (K[D2_title] - mu_2) / sigma_2

            # Compute Pearson correlation C12 on the standardized columns
            C12 = K[D1_title].corr(K[D2_title])

            #  Compute beta = arccos(C12)  (radians)
            beta = acos(C12)

            N1 = np.array(self.retention_time_df_2d_peaks[D1_title])
            N2 = np.array(self.retention_time_df_2d_peaks[D2_title])

            # Scale alpha' by (1 - 2*beta/pi)
            alpha_prim = atan(N2 / N1)

            alpha = alpha_prim * (1.0 - (2.0 * beta / pi))

            gamma = (pi / 2.0) - beta - alpha

            Np = (N1 * N2) - (0.5 * N2 * tan(gamma)) - (0.5 * N1 * tan(alpha))

            orthogonality = Np / (N1 * N2)

            set_number = extract_set_number(set_key)

            self.update_metrics(
                set_key,
                "geometric_approach",
                orthogonality[0],
                table_row_index=set_number - 1,
            )

        self.om_function_map["Geometric approach"]["status"] = FuncStatus.COMPUTED

    def load_data_frame_2d_peak(self, filepath: str, sheetname: str) -> None:
        """Load 2D peak capacity data from an Excel file.

        Args:
            filepath (str): Path to the Excel file.
            sheetname (str): Name of the sheet to load.

        Side Effects:
            - Loads data into retention_time_df_2d_peaks
            - Updates '2d_peak_capacity' in orthogonality_dict and table_data for each set
            - Updates combination_df with peak capacity information
            - Sets status to 'peak_capacity_loaded' on success or 'error' on failure

        Raises:
            Exception: Re-raises any exception after setting status to 'error'.
        """
        try:
            # Load data and clean columns once (no redundant file reading)

            self.retention_time_df_2d_peaks = load_simple_table(filepath, sheetname)

            columns = self.retention_time_df_2d_peaks.columns.tolist()
            num_columns = len(columns)
            set_number = 1

            for col1_idx, col2_idx in combinations(range(num_columns), 2):
                set_key = f"Set {set_number}"
                expected_title = f"{columns[col1_idx]} vs {columns[col2_idx]}"

                # Calculate 2D peak capacity
                x_peak = self.retention_time_df_2d_peaks.iloc[0, col1_idx]
                y_peak = self.retention_time_df_2d_peaks.iloc[0, col2_idx]
                peak_capacity = x_peak * y_peak

                if set_key not in self.orthogonality_dict:
                    self.orthogonality_dict[set_key] = (
                        self.get_default_orthogonality_entry()
                    )
                    self.orthogonality_dict[set_key]["title"] = expected_title

                    # Initialize table data by adding a new row with None values
                    self.table_data.append([None] * len(METRIC_MAPPING))

                    # Use helper function for updates
                    self.update_metrics(set_key, "set_number", set_number)
                    self.update_metrics(set_key, "title", expected_title)
                    self.update_metrics(set_key, "2d_peak_capacity", peak_capacity)

                else:
                    # Use helper function for updates
                    self.update_metrics(
                        set_key,
                        "set_number",
                        set_number,
                        table_row_index=set_number - 1,
                    )
                    self.update_metrics(
                        set_key, "title", expected_title, table_row_index=set_number - 1
                    )
                    self.update_metrics(
                        set_key,
                        "2d_peak_capacity",
                        peak_capacity,
                        table_row_index=set_number - 1,
                    )

                set_number += 1

            combination_table = [row[0:4] for row in self.table_data]
            self.combination_df = pd.DataFrame(
                combination_table,
                columns=[
                    "Set #",
                    "2D Combination",
                    "Number of peaks",
                    "Hypothetical 2D peak capacity",
                ],
            )

            self.status = "peak_capacity_loaded"

        except Exception as e:
            print(f"Error loading 2D peaks: {str(e)}")
            self.status = "error"
            raise
