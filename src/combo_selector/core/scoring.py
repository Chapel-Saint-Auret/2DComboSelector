"""Scoring and ranking computations for orthogonality analysis.

This module provides the :class:`Scoring` mixin which computes consensus
scores, coverage / distribution scores, ranking, and related helpers.
It has no Qt dependencies.
"""

import numpy as np
import pandas as pd
from scipy.stats import iqr, median_abs_deviation

from combo_selector.core.orthogonality_utils import (
    METRIC_MAPPING,
    METRIC_CATEGORY,
    UI_TO_MODEL_MAPPING,
    extract_set_number,
)


class Scoring:
    """Mixin that computes orthogonality scores and rankings.

    Intended to be combined with the other mixin classes via multiple
    inheritance in :class:`~combo_selector.core.orthogonality.Orthogonality`.
    All methods operate on ``self`` which is the shared ``Orthogonality``
    instance so cross-module attribute access works naturally.
    """

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_orthogonality_metric_df(self) -> pd.DataFrame:
        """Get the orthogonality metrics DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all computed orthogonality metrics
                         for each column combination set.
        """
        return self.orthogonality_metric_df

    def get_orthogonality_metric_ranking_df(self) -> pd.DataFrame:
        """Get the orthogonality metrics ranking DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all computed orthogonality metrics ranking
                         for each column combination set.
        """
        return self.orthogonality_metric_ranking_df

    def get_orthogonality_metric_corr_matrix_df(self) -> pd.DataFrame:
        """Get the orthogonality metric correlation matrix DataFrame.

        Returns:
            pd.DataFrame: Correlation matrix of orthogonality metrics.
        """
        return self.orthogonality_metric_corr_matrix_df

    def get_orthogonality_metric_ranking_corr_matrix_df(self) -> pd.DataFrame:
        """Get the orthogonality metric ranking correlation matrix DataFrame.

        Returns:
            pd.DataFrame: Correlation matrix of orthogonality metrics.
        """
        return self.orthogonality_metric_ranking_corr_matrix_df

    def get_metric_removal_impact_on_orthogonality_rank_df(self) -> pd.DataFrame:
        """Get the metric removal impact DataFrame (asses the impact of metric removed
        in orthogonality rank.

        Returns:
            pd.DataFrame: removal impact DataFrame.
        """
        return self.metric_removal_impact_df
    # ------------------------------------------------------------------
    # DataFrame helpers
    # ------------------------------------------------------------------

    def update_metric_dataframes(self, metric_list):
        """Update orthogonality metric DataFrames after all computations.

        This replicates the DataFrame update logic from the model's
        compute_orthogonality_metric method.

        Side Effects:
            - Updates model.orthogonality_metric_df
            - Updates model.orthogonality_metric_corr_matrix_df
        """

        # Get column indices for the computed metrics
        column_index = [
            METRIC_MAPPING[UI_TO_MODEL_MAPPING[metric]]["table_index"]
            for metric in metric_list
        ]

        orthogonality_table_df = pd.DataFrame(self.table_data)

        # For Correlation matrix table only contains metric with no set number and combination title
        self.orthogonality_metric_df = orthogonality_table_df.iloc[
            :, np.r_[column_index]
        ]

        # Add column name
        self.orthogonality_metric_df.columns = metric_list
        self.orthogonality_metric_corr_matrix_df = self.orthogonality_metric_df

        # rank each metric result across the combination
        self.orthogonality_metric_ranking_corr_matrix_df = self.orthogonality_metric_ranking_df = \
            self.orthogonality_metric_df.rank(ascending=False, method='average')

        def force_scale(col):
            """Rescale a rank column to the range [1, nb_combination].

            Args:
                col (pd.Series): Series of rank values to rescale.

            Returns:
                pd.Series: Rescaled values in [1, ``nb_combination``].
            """
            return ((col - col.min()) / (col.max() - col.min())) * (self.nb_combination - 1) + 1

        self.orthogonality_metric_ranking_df = self.orthogonality_metric_ranking_df.apply(force_scale).round(2)

        # 0 and 1 indexes are for set number and combination title
        column_index = [0, 1] + column_index
        self.orthogonality_metric_df = orthogonality_table_df.iloc[
            :, np.r_[column_index]
        ]

        # set and combination title dataframe
        set_and_title_df = orthogonality_table_df.iloc[:, np.r_[0, 1]]

        self.orthogonality_metric_ranking_df = pd.concat([set_and_title_df, self.orthogonality_metric_ranking_df], axis=1)

        # Adding column names directly
        self.orthogonality_metric_df.columns = self.orthogonality_metric_ranking_df.columns = \
            (["Combination #", "2D Combination"] + metric_list)

    def update_metric_ranking_dataframe(self):
        """Recompute the metric ranking DataFrame from the current metric scores.

        Re-ranks all metrics across combinations using average rank.

        Side Effects:
            - Updates ``self.orthogonality_metric_ranking_df``.
        """
        self.orthogonality_metric_ranking_df = self.orthogonality_metric_df.rank(ascending=False, method='average')

    # ------------------------------------------------------------------
    # Custom / suggested score
    # ------------------------------------------------------------------

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

    def compute_suggested_score_not_used(self) -> None:
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

    # ------------------------------------------------------------------
    # Consensus scoring
    # ------------------------------------------------------------------

    def compute_consensus_orthogonality_ranking(self):
        """Compute the consensus orthogonality ranking across correlation groups.

        For each group, takes the median rank of its correlated metrics, sums
        across groups, then ranks combinations by the aggregated score.

        Side Effects:
            - Populates ``self.orthogonality_group_ranking_df`` with per-group ranks.
            - Adds ``"Orthogonality ranking"`` column to ``self.orthogonality_result_df``.
        """
        # Create a local dictionary instead of assigning column-by-column to an live instance DataFrame
        group_ranks = {}
        metric_rank_df = self.orthogonality_metric_ranking_df.copy()

        for group, Correlated_Metrics_list in zip(self.correlation_group_df['Group'],
                                                  self.correlation_group_df['Correlated Metrics']):
            group_ranks[group] = metric_rank_df[Correlated_Metrics_list].median(axis=1)

        # Instantiate cleanly in one single block - this completely bypasses shape caching bugs
        self.orthogonality_group_ranking_df = pd.DataFrame(group_ranks)

        consensus_orthogonality_ranking_df = self.orthogonality_group_ranking_df.sum(axis=1)
        consensus_orthogonality_ranking_df = consensus_orthogonality_ranking_df.rank(ascending=True, method='average')

        self.orthogonality_result_df['Orthogonality Rank'] = consensus_orthogonality_ranking_df
        self.orthogonality_result_df['Orthogonality Utility'] = consensus_orthogonality_ranking_df.apply(
            lambda x: 1 - ((x - 1) / (self.nb_combination - 1))
        )



    def assess_metric_removal_impact_on_orthogonality_rank(self) -> pd.DataFrame:
        """Assess the impact of removing each metric on orthogonality rank.

        For each metric present in ``self.correlation_group_df['Correlated Metrics']``,
        this method removes the metric from its group(s), recomputes the consensus
        orthogonality ranking, compares the new rank to the original rank, and stores
        the median of the rank differences.

        Groups that become empty after metric removal are discarded.

        Returns:
            pd.DataFrame: DataFrame with:
                - ``"Metric Removed"``
                - ``"Median Orthogonality Rank Difference"``
        """
        if self.correlation_group_df.empty:
            return pd.DataFrame(
                columns=["Metric Removed", "Median Orthogonality Rank Difference"]
            )

        original_correlation_group_df = self.correlation_group_df.copy(deep=True)
        original_orthogonality_group_ranking_df = self.orthogonality_group_ranking_df.copy(deep=True)
        original_orthogonality_result_df = self.orthogonality_result_df.copy(deep=True)

        original_rank = self.orthogonality_result_df["Orthogonality Rank"].copy()

        results = []

        metric_list = sorted({
            metric
            for correlated_metrics in self.correlation_group_df["Correlated Metrics"]
            for metric in correlated_metrics
        })

        for metric_to_remove in metric_list:
            temp_correlation_group_df = original_correlation_group_df.copy(deep=True)

            # this remove the metric_to_remove from the correlation group
            temp_correlation_group_df["Correlated Metrics"] = temp_correlation_group_df[
                "Correlated Metrics"
            ].apply(
                lambda metrics: [metric for metric in metrics if metric != metric_to_remove])

            # remove empty groups
            temp_correlation_group_df = temp_correlation_group_df[
                temp_correlation_group_df["Correlated Metrics"].map(len) > 0
                ].reset_index(drop=True)

            # if all groups disappear after removal, skip this metric
            if temp_correlation_group_df.empty:
                results.append({
                    "Metric Removed": metric_to_remove,
                    "Median Orthogonality Rank Difference": np.nan,
                })
                continue

            # temporarily replace correlation groups and recompute ranking
            self.correlation_group_df = temp_correlation_group_df

            # compute the orthoganlity rank with the removed metric
            self.compute_consensus_orthogonality_ranking()

            new_rank = self.orthogonality_result_df["Orthogonality Rank"].copy()

            rank_diff = abs(original_rank - new_rank)
            median_rank_diff = rank_diff.median()

            results.append({
                "Metric Removed": metric_to_remove,
                "Median Orthogonality Rank Difference": median_rank_diff,
            })

        # restore original state
        self.correlation_group_df = original_correlation_group_df
        self.orthogonality_group_ranking_df = original_orthogonality_group_ranking_df
        self.orthogonality_result_df = original_orthogonality_result_df

        self.metric_removal_impact_df = pd.DataFrame(results).sort_values(
            by="Median Orthogonality Rank Difference",
            ascending=False
        ).reset_index(drop=True)

        self.metric_removal_impact_df['Median Orthogonality Rank Difference'] = \
        self.metric_removal_impact_df['Median Orthogonality Rank Difference'].apply(lambda x: (x*100)/self.nb_combination)


    def compute_consensus_orthogonality_score(self):
        """Compute the consensus orthogonality score as the median of group medians.

        For each correlation group, computes the column-wise median of its
        correlated metrics, then takes the overall median across groups.

        Side Effects:
            - Populates ``self.consensus_orthogonality_score_df``.
            - Adds ``"Orthogonality score"`` column to ``self.orthogonality_result_df``.
        """
        self.consensus_orthogonality_score_df = pd.DataFrame()
        metric_df = self.orthogonality_metric_df.copy()

        for group, Correlated_Metrics_list in zip(self.correlation_group_df['Group'],
                                                  self.correlation_group_df['Correlated Metrics']):
            self.consensus_orthogonality_score_df[group] = metric_df[Correlated_Metrics_list].median(axis=1)

        self.consensus_orthogonality_score_df = self.consensus_orthogonality_score_df.median(axis=1)

        self.orthogonality_result_df['Consensus Score'] = self.consensus_orthogonality_score_df

    def compute_coverage_score(self):
        """Compute the coverage score as the median of coverage-like metrics.

        Filters correlation groups whose category is ``"Coverage-like"`` and
        computes the row-wise median of all coverage metrics.

        Side Effects:
            - Populates ``self.coverage_score_df``.
            - Adds ``"Coverage score"`` column to ``self.orthogonality_result_df``.
        """
        self.coverage_score_df = pd.DataFrame()
        metric_df = self.orthogonality_metric_df.copy()
        computed_metric_list = metric_df.columns.tolist()[2:]
        coverage_metric_list = []

        computed_metric_list
        for metric in computed_metric_list:
            if METRIC_CATEGORY[metric] == "Coverage":
                coverage_metric_list.append(metric)

        if coverage_metric_list:
            self.coverage_score_df = metric_df[coverage_metric_list].median(axis=1)
            self.orthogonality_result_df['Coverage Score'] = self.coverage_score_df.copy()
        else:
            self.orthogonality_result_df['Coverage Score'] = 0

    def compute_distribution_score(self):
        """Compute the distribution score as the median of distribution-like metrics.

        Filters correlation groups whose category is ``"Distribution-like"`` and
        computes the row-wise median of all distribution metrics.

        Side Effects:
            - Populates ``self.distribution_score_df``.
            - Adds ``"Distribution score"`` column to ``self.orthogonality_result_df``.
        """
        self.distribution_score_df = pd.DataFrame()
        metric_df = self.orthogonality_metric_df.copy()
        computed_metric_list = metric_df.columns.tolist()[2:]
        distribution_metric_list = []

        for metric in computed_metric_list:
            if METRIC_CATEGORY[metric] == "Distribution":
                distribution_metric_list.append(metric)

        if distribution_metric_list:
            self.distribution_score_df = metric_df[distribution_metric_list].median(axis=1)
            self.orthogonality_result_df['Distribution Score'] = self.distribution_score_df.copy()
        else:
            self.orthogonality_result_df['Distribution Score'] = 0

    def compute_agreement_index(self):
        """Compute the agreement index across correlation groups.

        Measures the inter-group rank consistency by computing the IQR of
        group ranks for each combination, then normalising to [0, 1] where
        1 = perfect agreement.

        Side Effects:
            - Adds ``"Agreement index"`` column to ``self.orthogonality_result_df``.
        """

        agreement_index_df = self.orthogonality_group_ranking_df.apply(iqr, axis=1)

        agreement_index_df = 1 - (agreement_index_df / (self.nb_combination - 1))

        self.orthogonality_result_df['Agreement Indicator'] = agreement_index_df

    def compute_outlier_metric_flag(self):
        """Flag combinations whose group rank deviates more than τ from the group median.

        Uses three nested helpers (:func:`compute_deviations`,
        :func:`compute_outlier_flag`, :func:`write_outlier_result`) to
        identify and summarise outlier groups per combination.

        Side Effects:
            - Adds ``"Outlier metric flag"`` column to ``self.orthogonality_result_df``.
        """

        def compute_deviations(ranks, median):
            """Compute absolute deviations of ranks from their median.

            Args:
                ranks (list[float]): Rank values for a group.
                median (float): Median rank for the group.

            Returns:
                list[float]: Absolute deviations from the median.
            """
            return [abs(rank - median) for rank in ranks]

        def compute_outlier_flag(deviations, threshold):
            """Determine which deviations exceed the threshold.

            Args:
                deviations (list[float]): Absolute deviation values.
                threshold (float): Maximum allowed deviation.

            Returns:
                list[bool]: ``True`` for each deviation that exceeds the threshold.
            """
            return [dev > threshold for dev in deviations]

        def write_outlier_result(group_and_count):
            """Format a human-readable summary of outlier groups.

            Args:
                group_and_count (Iterable[tuple[str, int]]): Pairs of group
                    letter and outlier count.

            Returns:
                str: Comma-separated ``"GroupLetter: count"`` pairs, or
                    ``"No outliers"`` if all counts are zero.
            """
            result = [
                f"{group_letter}: {count}"
                for group_letter, count in group_and_count
                if count > 0
            ]
            return ", ".join(result) if result else "No outliers"

        rank_per_metric_per_group = pd.DataFrame()
        metric_rank_df = self.orthogonality_metric_ranking_df.copy()
        tau = 3

        for group, Correlated_Metrics_list in zip(self.correlation_group_df['Group'],
                                                   self.correlation_group_df['Correlated Metrics']):
            rank_per_metric_per_group[group] = metric_rank_df[Correlated_Metrics_list].apply(list, axis=1)

        r_g = self.orthogonality_group_ranking_df
        m_g = r_g.mean(axis=1)

        d_g = r_g.sub(m_g, axis=0).abs()

        d_g_percent = d_g.apply(lambda x: 100*(x/(self.nb_combination-1)))


        median_g = self.orthogonality_group_ranking_df

        mad_g = rank_per_metric_per_group.map(lambda x: median_abs_deviation(x))

        deviation = rank_per_metric_per_group.combine(median_g, lambda s1, s2: pd.Series([compute_deviations(a, b) for a, b in zip(s1, s2)]))

        outlier_flag = deviation.combine(mad_g * tau, lambda s1, s2: pd.Series([compute_outlier_flag(a, b) for a, b in zip(s1, s2)]))

        outlier_count = outlier_flag.map(lambda x: sum(x)).apply(list, axis=1)

        outlier_group = outlier_flag.apply(lambda row: row.index.tolist(), axis=1)

        outlier_metric_flag = outlier_group.T.combine(outlier_count.T, lambda s1, s2: write_outlier_result(zip(s1, s2)))

        self.orthogonality_result_df['Outlier Flag'] = outlier_metric_flag

    def compute_peak_detection_rate(self):
        """Compute the peak detection rate for each combination.

        Side Effects:
            - Adds ``"Peak Detection Rate (%)"`` column to ``self.orthogonality_result_df``.
            - Adds ``"Peak Detection Rate Status"`` column to ``self.orthogonality_result_df``.
        """

        def set_peak_detection_rate_status(peak_detection_rate):
            """         •    Red: < 40 %
            •    Orange: 40–60 %
            •    Yellow: 60–80 %
            •    Green: > 80 %

            •	Below Threshold
            •	Caution
            •	Acceptable
            •	High
            """
            if peak_detection_rate < 40:
                return 'Insufficient'
            elif 40 <= peak_detection_rate < 60:
                return 'Cautionary'
            elif 60 <= peak_detection_rate < 80:
                return 'Acceptable'
            else:
                return 'Suitable'

        nb_of_max_peak = self.combination_df["Number of peaks"].max()
        self.orthogonality_result_df["Peak Detection Rate (%)"] = (
            self.combination_df["Number of peaks"].apply(lambda x: int((x / nb_of_max_peak) * 100))
        )

        self.orthogonality_result_df["Peak Detection Rate Status"] = (
            self.orthogonality_result_df["Peak Detection Rate (%)"].apply(
                lambda x: set_peak_detection_rate_status(x)
            )
        )

    def compute_peak_selectivity_factor(self):
        """Placeholder for selectivity factor computation.

        Side Effects:
            - Adds ``"Selectivity Factor"`` column to ``self.orthogonality_result_df``.
        """
        self.orthogonality_result_df["Selectivity Factor"] = 'Not available'
