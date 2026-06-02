"""Data loading, normalization, and NaN-policy management for orthogonality analysis.

This module provides the :class:`DataManager` mixin.  When combined with the
other mixin classes via :class:`~combo_selector.core.orthogonality.Orthogonality`,
it contributes all data-IO and preprocessing behaviour without introducing any
Qt dependency of its own (except for the :class:`NanPolicyDialog` that it
instantiates on behalf of the Qt-aware facade).
"""

from itertools import combinations
from math import sqrt

import pandas as pd

from combo_selector.core.orthogonality_utils import (
    METRIC_MAPPING,
    extract_set_number,
    load_simple_table,
    load_table_with_header_anywhere,
    normalize_x_y_series,
)
from combo_selector.ui.widgets.nan_policy_widget import NanPolicyDialog


class DataManager:
    """Mixin that handles all data loading, normalization, and NaN policy.

    Intended to be combined with the other mixin classes via multiple
    inheritance in :class:`~combo_selector.core.orthogonality.Orthogonality`.
    All methods operate on ``self`` which is the shared ``Orthogonality``
    instance, so cross-module attribute access works naturally.
    """

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def init_data(self) -> None:
        """Initialize or reset all data structures to their default empty states.

        This method creates empty DataFrames and data structures for storing
        retention times, metrics, scores, and results.
        """
        self.table_data = []
        self.compound_name_list = []
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
        self.orthogonality_table_df = pd.DataFrame()
        self.filtered_result_df = pd.DataFrame()
        self.practical_feasibility_table_df = pd.DataFrame()
        self.separational_potential_table_df = pd.DataFrame()
        self.final_recommendation_table_df = pd.DataFrame()
        self.orthogonality_group_ranking_df = pd.DataFrame()
        self.orthogonality_metric_ranking_df = pd.DataFrame()
        self.orthogonality_metric_ranking_corr_matrix_df = pd.DataFrame()
        self.coverage_distribution_df = pd.DataFrame()
        self.coverage_score_df = pd.DataFrame()
        self.gradient_end_time_df = pd.DataFrame()
        self.void_time_df = pd.DataFrame()
        self.rt_below_threshold_df = None
        self.combination_df = pd.DataFrame()
        self.retention_time_df = pd.DataFrame()
        self.normalized_retention_time_df = pd.DataFrame()

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_has_nan_value(self) -> bool:
        """returns has_nan_value status.

        Returns:
            bool: True if NaN values are present in the data, False otherwise.
        """
        return self.has_nan_value

    def get_compound_name_list(self) -> list:
        """returns compound_name_list.

        Returns:
            list: The list of compounds name
        """
        return self.compound_name_list

    def get_removed_compound_list(self) -> list:
        """returns removed_compound_list.

        Returns:
            list: The list of compounds removed
        """
        return self.removed_compound_list

    def get_removed_condition_list(self) -> list:
        """returns removed_condition_list.

        Returns:
            list: The list of conditions removed
        """
        return self.removed_condition_list

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

    def get_number_of_combination(self):
        return self.nb_combination

    def get_number_of_condition(self) -> int:
        """Get the number of experimental conditions.

        Returns:
            int: The number of conditions (columns) in the dataset.
        """
        return self.nb_condition

    def get_combination_df(self) -> pd.DataFrame:
        """Get the DataFrame containing column combinations and peak information.

        Returns:
            pd.DataFrame: DataFrame with Set #, 2D Combination, Number of peaks,
                         and Hypothetical 2D Peak Capacity columns.
        """
        return self.combination_df

    def get_status(self) -> str:
        """Get the current status of the analysis.

        Returns:
            str: Current status indicator (e.g., 'loaded', 'error', 'complete','no_data')
        """
        return self.status

    def set_nan_policy_option1_threshold(self, threshold: float) -> None:
        """Set the threshold for handling NaN values in the data for option 1.

        Args:
            threshold (float): Percentage threshold (0-100) for NaN tolerance.
                              Peaks with NaN percentage above this will be removed.
        """
        self.nan_policy_option1_threshold = threshold

    def set_nan_policy_option2_threshold(self, threshold: float) -> None:
        """Set the thresoption2hold for handling NaN values in the data for option 2.

        Args:
            threshold (float): Percentage threshold (0-100) for NaN tolerance.
                              Peaks with NaN percentage above this will be removed.
        """
        self.nan_policy_option2_threshold = threshold

    # ------------------------------------------------------------------
    # NaN policy
    # ------------------------------------------------------------------

    def remove_compound(self):
        self.removed_compound_list = []
        remove_compound_index = []

        for row_data in self.retention_time_df.iterrows():
            peak_retention_time = row_data[1]
            nan_count = (peak_retention_time.isna() | (peak_retention_time == "")).sum()

            # nan_policy_threshold is % of total condition
            if (nan_count * 100) / self.nb_condition > self.nan_policy_option1_threshold:
                remove_compound_index.append(row_data[0])
                self.removed_compound_list.append(row_data[1][1])

        self.retention_time_df = self.retention_time_df.drop(remove_compound_index)
        self.compound_name_list = self.retention_time_df['Compound Name'].tolist()
        self.retention_time_df = self.retention_time_df.astype(object).fillna("")

    def remove_condition(self):
        self.removed_condition_list = []

        for column_data in self.retention_time_df.T.iterrows():
            condition_retention_time = column_data[1]
            nan_count = (condition_retention_time.isna() | (condition_retention_time == "")).sum()

            # nan_policy_threshold is % of total condition
            if (nan_count * 100) / self.nb_peaks > self.nan_policy_option2_threshold:
                self.removed_condition_list.append(column_data[0])

        self.retention_time_df = self.retention_time_df.drop(columns=self.removed_condition_list)
        self.retention_time_df = self.retention_time_df.astype(object).fillna("")

    def clear_all_nan(self):
        self.removed_compound_list = []
        self.removed_condition_list = []

        self.retention_time_df = self.retention_time_df.astype(object).fillna("")

    def load_rt_below_threshold_data(self, filepath: str, sheetname: str) -> None:
        """Load per-condition minimum retention time thresholds from a single-row Excel file.

        Args:
            filepath (str): Path to the Excel file.
            sheetname (str): Name of the sheet to load.

        The file must have one row of numeric values; each column header must match
        a condition name in the retention time DataFrame.
        """
        self.rt_below_threshold_df = load_simple_table(filepath, sheetname)

    def replace_rt_below_threshold(self):
        """Replace retention times below per-condition thresholds with blank strings.

        For each condition column, any RT value strictly below the loaded threshold
        for that condition is replaced with "".

        Requires load_rt_below_threshold_data() to have been called first.
        """
        if self.rt_below_threshold_df is None:
            return

        if self.rt_below_threshold_df.empty:
            return

        metadata_column_count = 2  # 'Peak#' and 'Compound Name'
        for column_name in self.retention_time_df.columns[metadata_column_count:]:
            if column_name not in self.rt_below_threshold_df.columns:
                continue
            threshold = self.rt_below_threshold_df[column_name].iloc[0]
            try:
                threshold = float(threshold)
            except (TypeError, ValueError):
                continue

            def _blank_if_below_threshold(value):
                if value == "" or pd.isna(value):
                    return value
                try:
                    return "" if float(value) < threshold else value
                except (TypeError, ValueError):
                    return value

            self.retention_time_df[column_name] = self.retention_time_df[column_name].apply(
                _blank_if_below_threshold
            )

    def clean_nan_value(self, option_list: str) -> None:
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
        function_map = {"option 1": self.remove_compound,
                        "option 2": self.replace_rt_below_threshold,
                        "option 3": self.remove_condition,
                        "option 4": self.clear_all_nan,
                        }

        for option in option_list:
            function_map[option]()

        # update column_names list after droping some of them
        self.column_names = self.retention_time_df.columns.tolist()[2:]

        #minus 1 to remove the peak column
        num_columns = len(self.column_names)

        #always start at 1 because index 0 is for the peak# column
        current_column = 0
        set_number = 1

        #initial orthogonality dict and table_data
        self.orthogonality_dict = {}
        self.table_data = []

        while current_column < num_columns:
            current_column_name = self.column_names[current_column]
            x_values = self.retention_time_df[current_column_name]

            if num_columns > 2:
                # current_column + 1 means we start the column next to the current column
                # num_columns + 1 is used because range function always stop at n-1
                next_column_list = list(range(current_column + 1, num_columns))
            else:
                # the dataframe only has 2 column
                next_column_list = [1]

            for next_column in next_column_list:
                next_column_name = self.column_names[next_column]
                set_key = f"Set {set_number}"
                set_title = f"{current_column_name} vs {next_column_name}"
                y_values = self.retention_time_df[next_column_name]

                # Initialize table data by adding a new row with None values
                self.table_data.append([None] * len(METRIC_MAPPING))

                # Update metadata columns
                self.update_metrics(set_key, "set_number", set_number)
                self.update_metrics(set_key, "title", set_title)
                self.update_metrics(set_key, "orthogonality_score", 0)
                self.update_metrics(set_key, "orthogonality_ranking", 0)
                self.update_metrics(set_key, "coverage_score", 0)
                self.update_metrics(set_key, "distribution_score", 0)
                self.update_metrics(set_key, "agreement_index", 0)
                self.update_metrics(set_key, "outlier_metric_flag", 0)
                self.update_metrics(set_key, "orthogonality_value", 0)
                self.update_metrics(set_key, "2d_peak_capacity", 'Not available')
                self.update_metrics(set_key, "elution_composition_space", 'Not available')
                self.update_metrics(set_key, "heinisch", 0)

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
                    self.update_metrics(set_key, "nb_peaks", nb_peaks)

                    # Update orthogonality dictionary
                    self.orthogonality_dict[set_key] = {
                        "title": set_title,
                        "x_values": x_series,
                        "x_title": self.column_names[current_column],
                        "y_title": self.column_names[next_column],
                        "y_values": y_series,
                        "nb_peaks": nb_peaks,
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
                        "orthogonality_score": 0,
                        "orthogonality_ranking": 0,
                        "coverage_score": 0,
                        "distribution_score": 0,
                        "agreement_index": 0,
                        "outlier_metric_flag": 0,
                        "orthogonality_value": 0,
                        "practical_2d_peak": 0,
                        "heinisch": 0,
                        "2d_peak_capacity": "no data loaded",
                    }

                else:
                    self.orthogonality_dict.pop(set_key)

                set_number += 1

            current_column += 1

        self.update_combination_df()

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

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

        self.status = "normalized"

    def normalize_retention_time_min_max(self) -> None:
        """Normalize retention times using min-max normalization for each column.

        Formula: (x - rt_min) / (rt_max - rt_min)

        Side Effects:
            - Updates normalized_retention_time_df
            - Calls set_orthogonality_dict_x_y_series() to update metric dictionaries
            - Sets status to 'error' if normalization fails
        """
        data_frame_copy = self.retention_time_df.copy()

        #[2:] is because first two columns are compound# and compound name
        for column_name in data_frame_copy.columns[2:]:
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

        #[2:] is because first two columns are compound# and compound name
        for column_name in data_frame_copy.columns[2:]:
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

        #[2:] is because first two columns are compound# and compound name
        for column_name in data_frame_copy.columns[2:]:
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

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

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
            self.status = "loaded"

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

            self.status = "loaded"

        except Exception as e:
            print(f"Error loading end time: {str(e)}")
            self.status = "error"
            raise

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

            #rename automatically the first column (which should be the "Compound Name')
            self.retention_time_df = self.retention_time_df.rename(
                columns={self.retention_time_df.columns[0]: 'Compound Name'}
            )

            # check there is nan value in data frame
            self.has_nan_value = self.retention_time_df.iloc[:,1:].isnull().any().any()
            #[1:] is used because first column is compound name
            self.column_names = self.retention_time_df.columns.tolist()[1:]
            self.nb_condition = num_columns = len(self.column_names)
            self.nb_peaks = len(self.retention_time_df.iloc[:, 0])

            self.compound_name_list = self.retention_time_df['Compound Name'].tolist()

            # Initialize loop parameters
            self.retention_time_df.insert(
                0, "Peak #", range(1, len(self.retention_time_df) + 1)
            )

            current_column = 0
            set_number = 1

            if self.has_nan_value:
                self.nan_policy_dialog.exec_()
            else:

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
                        self.update_metrics(set_key, "orthogonality_score", 0)
                        self.update_metrics(set_key, "orthogonality_ranking", 0)
                        self.update_metrics(set_key, "coverage_score", 0)
                        self.update_metrics(set_key, "distribution_score", 0)
                        self.update_metrics(set_key, "agreement_index", 0)
                        self.update_metrics(set_key, "outlier_metric_flag", 0)
                        self.update_metrics(set_key, "orthogonality_value", 0)
                        self.update_metrics(set_key, "2d_peak_capacity", 'Not available')
                        self.update_metrics(set_key, "elution_composition_space",'Not available')
                        self.update_metrics(set_key, "heinisch", 0)

                        # Update orthogonality dictionary
                        self.orthogonality_dict[set_key] = {
                            "title": set_title,
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
                            "orthogonality_score": 0,
                            "orthogonality_ranking": 0,
                            "coverage_score": 0,
                            "distribution_score": 0,
                            "agreement_index": 0,
                            "outlier_metric_flag": 0,
                            "orthogonality_value": 0,
                            "practical_2d_peak": 0,
                            "heinisch": 0,
                            "2d_peak_capacity": "no data loaded",
                        }
                        set_number += 1

                    current_column += 1

            self.update_combination_df()
            self.create_results_table()
            self.set_compatibility()
            self.set_complexity()

            self.status = "loaded"
        except Exception as e:
            issue = str(e)
            print(f"Error loading data: {issue}")
            self.status = "error"

    def load_hypothetical_2d_peak_capacity(self, filepath: str, sheetname: str) -> None:
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

            # remove condition that has already been removed with the clean data widget
            if set(self.removed_condition_list).issubset(set(self.retention_time_df_2d_peaks.columns)):
                self.retention_time_df_2d_peaks = self.retention_time_df_2d_peaks.drop(columns=self.removed_condition_list)

            columns = self.retention_time_df_2d_peaks.columns.tolist()
            num_columns = len(columns)
            set_number = 1

            if len(self.column_names) != num_columns:
                raise ValueError("Number of condition does not match the number of condition in retention time data.")


            for col1_idx, col2_idx in combinations(range(num_columns), 2):
                set_key = f"Set {set_number}"
                expected_title = f"{columns[col1_idx]} vs {columns[col2_idx]}"

                # Calculate 2D peak capacity
                n1 = self.retention_time_df_2d_peaks.iloc[0, col1_idx]
                n2 = self.retention_time_df_2d_peaks.iloc[0, col2_idx]
                peak_capacity = int(n1 * n2)

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
                        table_row_index=set_number - 1
                    )
                    self.update_metrics(
                        set_key, "title", expected_title, table_row_index=set_number - 1
                    )
                    self.update_metrics(
                        set_key,
                        "2d_peak_capacity",
                        peak_capacity,
                        table_row_index=set_number - 1
                    )

                set_number += 1

            combination_table = [row[3] for row in self.table_data]

            self.combination_df["Hypothetical 2D Peak Capacity"] = self.orthogonality_result_df['Hypothetical 2D Peak Capacity'] \
                = combination_table
            self.peak_capacity_status = "peak_capacity_loaded"
            self.orthogonality_result_df['Peak Capacity Rank'] = self.combination_df["Hypothetical 2D Peak Capacity"].rank(ascending=False, method='average').astype(int)
            p_min = self.combination_df["Hypothetical 2D Peak Capacity"].min()
            p_max = self.combination_df["Hypothetical 2D Peak Capacity"].max()
            self.orthogonality_result_df['Peak Capacity Utility'] = self.combination_df["Hypothetical 2D Peak Capacity"].apply(lambda x:(x-p_min)/(p_max-p_min))
            self.status = "loaded"
        except Exception as e:
            print(f"Error loading 2D peaks: {str(e)}")
            self.status = "error"
            raise

    def load_elution_composition_space_area_data(self, filepath: str, sheetname: str) -> None:
        """Elution composition space area data from an Excel file.

        Args:
            filepath (str): Path to the Excel file.
            sheetname (str): Name of the sheet to load.

        Side Effects:
            - Loads data into retention_time_df_2d_peaks
            - Updates 'elution_composition_space' in orthogonality_dict and table_data for each set
            - Updates combination_df with elution data information
            - Sets status to 'elution_data_status' on success or 'error' on failure

        Raises:
            Exception: Re-raises any exception after setting status to 'error'.
        """
        try:
            # Load data and clean columns once (no redundant file reading)
            self.load_elution_composition_df = load_simple_table(filepath, sheetname)

            # remove condition that has already been removed with the clean data widget
            if set(self.removed_condition_list).issubset(set(self.load_elution_composition_df.columns)):
                self.load_elution_composition_df = self.load_elution_composition_df.drop(
                    columns=self.removed_condition_list)

            columns = self.load_elution_composition_df.columns.tolist()
            num_columns = len(columns)
            set_number = 1

            if len(self.column_names) != num_columns:
                raise ValueError("Number of condition does not match the number of condition in retention time data.")

            for col1_idx, col2_idx in combinations(range(num_columns), 2):
                set_key = f"Set {set_number}"
                expected_title = f"{columns[col1_idx]} vs {columns[col2_idx]}"

                # Calculate Elution domain
                e1 = self.load_elution_composition_df.iloc[0, col1_idx]
                e2 = self.load_elution_composition_df.iloc[0, col2_idx]
                elution_composition_space = int((e1 * e2) / 100)

                # Use helper function for updates
                self.update_metrics(set_key,"elution_composition_space",elution_composition_space,table_row_index=set_number - 1)

                set_number += 1

            combination_table = [row[4] for row in self.table_data]

            self.combination_df['Elution Domain'] = self.orthogonality_result_df['Elution Domain'] \
                = combination_table
            self.orthogonality_result_df['Elution Domain Rank'] = self.combination_df['Elution Domain'].rank(ascending=False, method='average')
            self.orthogonality_result_df['Elution Domain Utility'] = self.combination_df['Elution Domain'].apply(lambda x: x/100)
            self.status = self.elution_data_status = "elution_data_loaded"

        except Exception as e:
            print(f"Error loading Elution composition space area data: {str(e)}")
            self.status = "error"
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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
        num_columns = len(self.column_names) - 1

        current_column = 0
        set_number = 1

        while current_column < num_columns:
            current_column_name = self.column_names[current_column]
            x_values = self.normalized_retention_time_df[current_column_name]

            if num_columns > 2:
                next_column_list = list(range(current_column + 1, num_columns + 1))
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

    def update_combination_df(self) -> None:
        """Update the combination DataFrame with set information and peak counts.

        Only updates if the 'Hypothetical 2D Peak Capacity' column is empty.

        Side Effects:
            Updates combination_df with data from table_data (columns 0-3).
        """

        combination_table = [row[0:5] for row in self.table_data]
        self.combination_df = pd.DataFrame(
            combination_table,
            columns=[
                "Combination #",
                "2D Combination",
                "Number of peaks",
                "Hypothetical 2D Peak Capacity",
                "Elution Domain",
            ],
        )

        self.nb_peaks = self.combination_df["Number of peaks"].max()
        self.nb_combination = len(self.combination_df["2D Combination"])
        self.bin_number = round(sqrt(self.nb_peaks))
