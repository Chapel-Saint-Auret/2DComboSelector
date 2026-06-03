"""Redundancy analysis: correlation groups, rho coverage and distribution.

This module provides the :class:`Redundancy` mixin which identifies groups of
correlated orthogonality metrics and computes per-group coverage / distribution
correlations.  It has no Qt dependencies.
"""

import string

import pandas as pd
import numpy as np
from scipy.stats import spearmanr, tmean

from combo_selector.core.orthogonality_utils import cluster_and_fuse


class Redundancy:
    """Mixin that handles metric redundancy analysis via correlation groups.

    Intended to be combined with the other mixin classes via multiple
    inheritance in :class:`~combo_selector.core.orthogonality.Orthogonality`.
    All methods operate on ``self`` which is the shared ``Orthogonality``
    instance so cross-module attribute access works naturally.
    """

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_correlation_group_df(self) -> pd.DataFrame:
        """Get the DataFrame of correlated orthogonality metric groups.

        Returns:
            pd.DataFrame: DataFrame with groups of correlated metrics.
        """
        return self.correlation_group_df

    def get_coverage_distribution_matrix_df(self) -> pd.DataFrame:
        """Get the coverage vs distribution correlation matrix DataFrame.

        Returns:
            pd.DataFrame: coverage vs distribution correlation matrix DataFrame.
        """
        return self.coverage_distribution_df

    # ------------------------------------------------------------------
    # Correlation groups
    # ------------------------------------------------------------------

    def create_correlation_group(
        self, matrix_type: str, threshold: float, tol: float
    ) -> pd.DataFrame:
        """Identify and group correlated orthogonality metrics based on correlation threshold.

        This method finds groups of metrics that are highly correlated with each other,
        which is useful for identifying redundant metrics and creating suggested scores.

        Args:
            threshold (float): Correlation coefficient threshold (0-1). Pairs with absolute
                             correlation >= threshold are considered correlated.
            tol (float): Tolerance value to adjust the threshold.

        Returns:
            pd.DataFrame: DataFrame with 'Group' and 'Correlated Metrics' columns, where each
                         row represents a group of correlated metrics.

        Note:
            Algorithm based on work by @yatharthranjan
            https://medium.com/@yatharthranjan/finding-top-correlation-pairs-from-a-large-number-of-variables-in-pandas-f530be53e82a
        """

        if matrix_type == "Values":
            if self.orthogonality_metric_corr_matrix_df.empty:
                return pd.DataFrame()

            corr_matrix = self.orthogonality_metric_corr_matrix_df.corr()
        else:
            if self.orthogonality_metric_ranking_corr_matrix_df.empty:
                return pd.DataFrame()

            corr_matrix = self.orthogonality_metric_ranking_corr_matrix_df.corr()

        correlated_metrics = set()

        for row in corr_matrix.itertuples():
            row_metric_list = []
            row_metric_name = row.Index
            row_metric_list.append(row_metric_name)

            for i in range(1, len(row)):
                column_metric_name = corr_matrix.columns[i - 1]
                value = row[i]
                if abs(value) >= (threshold - tol):
                    row_metric_list.append(column_metric_name)

            # convert list in to set() to sort metric name, it will ease the process
            # to remove duplicate group of correlated metric
            row_metric_list = sorted(set(row_metric_list))

            # you cannot add list in set() object
            correlated_metrics.add(tuple(row_metric_list))

        sorted_correlated_metrics = sorted(correlated_metrics, key=len, reverse=True)

        groups, sorted_correlated_metrics = cluster_and_fuse(sorted_correlated_metrics)

        # If you pass a list of tuples directly → Pandas splits the tuples into multiple columns.
        # If you pass a dictionary with a column name → Pandas keeps each tuple as a single cell in that column.
        self.correlation_group_df = pd.DataFrame(
            {"Correlated Metrics": list(sorted_correlated_metrics)}
        )

        # Add a new column with letters A-Z
        self.correlation_group_df["Group"] = list(
            string.ascii_uppercase[: len(self.correlation_group_df)]
        )

        self.correlation_group_df = self.correlation_group_df[
            ["Group", "Correlated Metrics"]
        ]

        return self.correlation_group_df

    def compute_rho_coverage(self) -> None:
        """Compute Spearman correlation (ρ) between each metric and the coverage anchor.

        Uses the bin box counting metric ranking as the coverage anchor.
        Populates ``metric_rho_coverage`` (per-metric) and
        ``group_rho_coverage`` (mean per correlation group).

        Side Effects:
            - Updates ``self.metric_rho_coverage`` with absolute Spearman ρ values.
            - Updates ``self.group_rho_coverage`` with trimmed means per group.
        """

        coverage_anchor = self.orthogonality_metric_ranking_df["Bin box counting"]

        # dictionary of rho coverage value per group
        self.group_rho_coverage = {}

        # dictionary of rho coverage value per metric
        self.metric_rho_coverage = {}

        temp_df = self.correlation_group_df.rename(
            columns={"Correlated Metrics": "Correlated_Metrics"}
        )

        for row in temp_df.itertuples():
            group = row.Group
            rho_coverage_list = []

            correlated_metrics_list = row.Correlated_Metrics

            for metric in correlated_metrics_list:
                values = self.orthogonality_metric_ranking_df[metric]
                rho_coverage = spearmanr(coverage_anchor, values)[0]

                rho_coverage_list.append(abs(rho_coverage))
                self.metric_rho_coverage[metric] = abs(rho_coverage)

            self.metric_rho_coverage = dict(sorted(self.metric_rho_coverage.items()))
            self.group_rho_coverage[group] = tmean(rho_coverage_list)

    def compute_rho_distribution(self) -> None:
        """Compute Spearman correlation (ρ) between each metric and the distribution anchor.

        Uses the mean chromatographic coverage (cc_mean) rank as the
        distribution anchor.  Populates ``metric_rho_distribution`` (per-metric)
        and ``group_rho_distribution`` (mean per correlation group).

        Side Effects:
            - Calls :meth:`compute_cc_mean`.
            - Updates ``self.metric_rho_distribution`` with absolute ρ values.
            - Updates ``self.group_rho_distribution`` with trimmed means per group.
        """

        self.compute_cc_mean()

        om_dataframe = pd.DataFrame(self.orthogonality_score).T

        distribution_anchor = om_dataframe["cc_mean"].rank(
            ascending=False, method="average"
        )

        # dictionary of rho distribution value per group
        self.group_rho_distribution = {}

        # dictionary of rho coverage value per metric
        self.metric_rho_distribution = {}

        temp_df = self.correlation_group_df.rename(
            columns={"Correlated Metrics": "Correlated_Metrics"}
        )

        for row in temp_df.itertuples():
            group = row.Group
            rho_distribution_list = []

            correlated_metrics_list = row.Correlated_Metrics

            for metric in correlated_metrics_list:
                values = self.orthogonality_metric_ranking_df[metric]
                rho_distribution = spearmanr(distribution_anchor, values)[0]

                rho_distribution_list.append(abs(rho_distribution))
                self.metric_rho_distribution[metric] = abs(rho_distribution)

            self.metric_rho_distribution = dict(
                sorted(self.metric_rho_distribution.items())
            )
            self.group_rho_distribution[group] = tmean(rho_distribution_list)

    def build_coverage_distribution_matrix(self) -> None:
        """Build a DataFrame summarising ρ coverage and ρ distribution per metric.

        Combines :attr:`metric_rho_coverage` and :attr:`metric_rho_distribution`
        into a transposed DataFrame stored in ``coverage_distribution_df``.

        Side Effects:
            - Creates and stores ``self.coverage_distribution_df``.
        """
        self.coverage_distribution_df = pd.DataFrame(
            {
                "rho coverage ": self.metric_rho_coverage,
                "rho distribution": self.metric_rho_distribution,
            }
        )

        self.coverage_distribution_df.index.name = "Metric"

        self.coverage_distribution_df = self.coverage_distribution_df.T

    def fill_correlation_group_average(self, matrix_type: str = "Values") -> None:
        """Compute average pairwise correlation for each correlation group.

        For each group in ``correlation_group_df``, calculates the mean and
        standard deviation of the lower-triangle pairwise correlations within
        the group's sub-matrix.

        Args:
            matrix_type (str): Which correlation matrix to use. ``"Values"``
                uses raw metric values; any other value uses the ranking matrix.
                Defaults to ``"Values"``.

        Side Effects:
            - Adds ``"Average Group Correlation"`` column to
              ``self.correlation_group_df``.
        """
        average_redundancy_list = []

        for group, correlated_metrics_list in zip(
            self.correlation_group_df["Group"],
            self.correlation_group_df["Correlated Metrics"],
        ):
            # 1. Get your sub-matrix
            if matrix_type == "Values":
                corr_matrix = self.orthogonality_metric_corr_matrix_df.corr()
            else:
                corr_matrix = self.orthogonality_metric_ranking_corr_matrix_df.corr()

            corr_matrix = corr_matrix.loc[
                correlated_metrics_list, correlated_metrics_list
            ]

            # 2. Create a mask for the upper triangle
            # k=1 excludes the diagonal (the 1.0s) (this is when you want to take the diagonal)
            # k=0 includes the diagonal in the mask
            # np.triu returns the upper triangle
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=0)

            # 3. Mask the matrix and "stack" it
            # .stack() removes all the NaNs, leaving only the unique pairs
            unique_pairs = corr_matrix.where(~mask).stack()

            # 4. Calculate your clean mean
            average_redundancy = round(float(unique_pairs.mean()), 2)
            std_redundancy = round(float(unique_pairs.std()), 2)

            average_redundancy_list.append(f"{average_redundancy} ± {std_redundancy}")

        self.correlation_group_df["Average Group Correlation"] = average_redundancy_list

    def fill_correlation_group_classification(self) -> None:
        """Assign a coverage/distribution category label to each correlation group.

        Computes ρ coverage and ρ distribution for each group and assigns
        ``"Coverage-like"``, ``"Distribution-like"``, or ``"Mixed"`` categories
        to ``correlation_group_df["Classification"]``.

        Side Effects:
            - Calls :meth:`compute_rho_coverage` and :meth:`compute_rho_distribution`.
            - Adds ``"Category"`` column to ``self.correlation_group_df``.
        """
        self.compute_rho_coverage()
        self.compute_rho_distribution()

        category_list = []

        for group in self.group_rho_coverage.keys():
            rho_coverage = self.group_rho_coverage[group]
            rho_distribution = self.group_rho_distribution[group]

            if rho_coverage >= 0.9 > rho_distribution:
                category = "Coverage-like"
            elif rho_distribution >= 0.9 > rho_coverage:
                category = "Distribution-like"
            elif rho_coverage >= 0.9 and rho_distribution >= 0.9:
                category = "Hybrid"
            else:
                category = "Other"

            category_list.append(category)

        self.correlation_group_df["Classification"] = category_list
