"""Orthogonality metric computation engine.

This module provides the :class:`MetricEngine` mixin which contains every
``compute_*`` method along with the function-status registry and the shared
``update_metrics`` helper.  It has **zero Qt dependencies** and can be
imported and unit-tested without a running Qt application.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from math import acos, atan, log2, pi, sqrt, tan

import numpy as np
import pandas as pd

from scipy.cluster.hierarchy import linkage
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import (
    gmean,
    hmean,
    kendalltau,
    linregress,
    pearsonr,
    spearmanr,
    tmean,
)

from combo_selector.core.orthogonality_utils import (
    FuncStatus,
    METRIC_MAPPING,
    UI_TO_MODEL_MAPPING,
    compute_bin_box_mask_color,
    compute_percent_fit_for_set,
    extract_set_number,
)


class MetricEngine:
    """Mixin that contains all orthogonality metric computation methods.

    Intended to be combined with the other mixin classes via multiple
    inheritance in :class:`~combo_selector.core.orthogonality.Orthogonality`.
    All methods operate on ``self`` which is the shared ``Orthogonality``
    instance so cross-module attribute access works naturally.

    This class intentionally contains **no Qt imports** so its methods can be
    unit-tested without a running Qt application.
    """

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

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

    def get_orthogonality_score_df(self) -> dict:
        """Get the orthogonality scores dictionary.

        Returns:
            dict: Dictionary mapping set names to their orthogonality scores.
        """
        return self.orthogonality_score

    # ------------------------------------------------------------------
    # Registry / status management
    # ------------------------------------------------------------------

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
            "heinisch": 0,
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

    def update_num_bins(self, nb_bin: int) -> None:
        """Set the number of bins for box calculations and update dependent properties.

        Args:
            nb_bin (int): Number of bins to use for box-based calculations.
                         Must be a positive integer.

        Raises:
            ValueError: If input is not a positive integer.
        """
        if not isinstance(nb_bin, int) or nb_bin <= 0:
            raise ValueError("Number of bins must be a positive integer")

        self.bin_number = nb_bin

        # reset function computed status in order to re compute with new bin number
        for metric in ["Bin box counting", "Modeling approach", "Gilar-Watson method"]:
            self.om_function_map[metric]["status"] = FuncStatus.NOT_COMPUTED

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

    # ------------------------------------------------------------------
    # Metric computations
    # ------------------------------------------------------------------

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
            set_data = self.orthogonality_dict[set_key]
            x, y = set_data["x_values"], set_data["y_values"]
            print(set_key)

            # Stack the x and y coordinates into a 2D array of shape (n_points, 2)
            subset = np.vstack((x, y)).T

            # remove duplicate pointS
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
                    (0.63 * p_square))

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
            H_x = np.sum(px_nz * np.log2(px_nz))
            py_nz = py[py > 0]
            H_y = np.sum(py_nz * np.log2(py_nz))

            pxy_nz = pxy.flatten()[pxy.flatten() > 0]
            H_xy = np.sum(pxy_nz * np.log2(pxy_nz))

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
        the Practical 2D Peak Capacity based on geometric considerations.

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

    # ------------------------------------------------------------------
    # Scoring helpers that live close to the metric data
    # ------------------------------------------------------------------

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
