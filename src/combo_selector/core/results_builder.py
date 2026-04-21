"""Results table construction and final recommendation logic.

This module provides the :class:`ResultsBuilder` mixin which builds the
various result DataFrames (orthogonality table, feasibility table, etc.)
and computes the final recommendation factors.  It has no Qt dependencies.
"""

import re

import pandas as pd

from combo_selector.core.orthogonality_utils import CHROM_MODE, METRIC_MAPPING


class ResultsBuilder:
    """Mixin that builds results tables and computes final recommendation factors.

    Intended to be combined with the other mixin classes via multiple
    inheritance in :class:`~combo_selector.core.orthogonality.Orthogonality`.
    All methods operate on ``self`` which is the shared ``Orthogonality``
    instance so cross-module attribute access works naturally.
    """

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_orthogonality_result_df(self) -> pd.DataFrame:
        """Get the final orthogonality results DataFrame with rankings.

        Returns:
            pd.DataFrame: Results DataFrame with set numbers, scores, and rankings.
        """
        return self.orthogonality_result_df

    def get_orthogonality_table(self):
        """Get the orthogonality sub-table.

        Returns:
            pd.DataFrame: Orthogonality metrics table.
        """
        return self.orthogonality_table_df

    def get_practical_feasibility_table(self):
        """Get the practical feasibility sub-table.

        Returns:
            pd.DataFrame: Practical feasibility table.
        """
        return self.practical_feasibility_table_df

    def get_separational_potential_table(self):
        """Get the separational potential sub-table.

        Returns:
            pd.DataFrame: Separational potential table.
        """
        return self.separational_potential_table_df

    def get_final_recommendation_table(self):
        """Get the final recommendation sub-table.

        Returns:
            pd.DataFrame: Final recommendation table.
        """
        return self.final_recommendation_table_df

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

    # ------------------------------------------------------------------
    # Table builders
    # ------------------------------------------------------------------

    def create_results_table(self) -> None:
        """Create the final results DataFrame with scores and rankings.

        Extracts set numbers, titles, scores, and practical 2D peak capacities,
        then computes rankings based on practical 2D peak capacity.

        Side Effects:
            Updates orthogonality_result_df with final results and rankings.
        """
        column_name = [
            "set_number",
            "title"
        ]

        # get column index of orthogonality metric in table_data
        column_index = [METRIC_MAPPING[name]["table_index"] for name in column_name]

        self.orthogonality_result_df = pd.DataFrame(self.table_data)

        # correlation matrix table only contains metric with no set number and combination title
        self.orthogonality_result_df = self.orthogonality_result_df.iloc[
            :, column_index
        ]

        # add column name
        self.orthogonality_result_df.columns = [
            "Combination #",
            "2D Combination",
        ]

        self.orthogonality_result_df["Chromatographic Mode"] = (
            self.build_chromatographic_mode(self.orthogonality_result_df["2D Combination"])
        )

    def update_table_results(self) -> None:
        """Recompute all result columns and update the results table.

        Sequentially computes:
        - Consensus orthogonality score and ranking
        - Coverage and distribution scores
        - Agreement index
        - Outlier metric flags
        - Practical 2D peak capacity

        Side Effects:
            - Updates ``self.orthogonality_result_df`` with all result columns.
        """
        self.compute_consensus_orthogonality_score()
        self.compute_consensus_orthogonality_ranking()
        self.compute_coverage_score()
        self.compute_distribution_score()
        self.compute_agreement_index()
        self.compute_outlier_metric_flag()
        self.compute_peak_detection_rate()
        self.compute_peak_selectivity_factor()
        self.update_result_with_new_peak_capacity()
        self.compute_suggested_rank()

        self.compute_final_recommendation_factor()

        self.create_orthogonality_table()
        self.create_practical_feasibility_table()
        self.create_separational_potential_table()
        self.create_final_recommendation_table()

    def update_result_with_new_peak_capacity(self):
        """Update the results table with the most recent peak capacity data.

        Side Effects:
            - Updates ``"Practical 2D Peak Capacity"`` column in result DataFrames.
        """
        if (not self.coverage_score_df.empty and
                'Not available' not in self.combination_df['Hypothetical 2D peak capacity'].values):

            self.orthogonality_result_df['Practical 2D Peak Capacity'] = (
                self.combination_df['Hypothetical 2D peak capacity'] * self.coverage_score_df
            )
        else:
            self.orthogonality_result_df['Practical 2D Peak Capacity'] = 'Not available'

        if 'Practical 2D Peak Capacity' in self.separational_potential_table_df.columns:
            self.separational_potential_table_df['Practical 2D Peak Capacity'] = (
                self.orthogonality_result_df['Practical 2D Peak Capacity'].copy()
            )
        else:
            self.separational_potential_table_df['Practical 2D Peak Capacity'] = 'Not available'

        if 'Practical 2D Peak Capacity' in self.final_recommendation_table_df.columns:
            self.final_recommendation_table_df['Practical 2D Peak Capacity'] = (
                self.orthogonality_result_df['Practical 2D Peak Capacity'].copy()
            )
        else:
            self.final_recommendation_table_df['Practical 2D Peak Capacity'] = 'Not available'

        self.compute_suggested_rank()

    def create_orthogonality_table(self):
        """Build the orthogonality sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.orthogonality_table_df``.
        """
        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Coverage Score",
            "Distribution Score",
            "Consensus Score",
            "Consensus Ranking",
            "Agreement Indicator",
            "Outlier Group Flag",
        ]

        self.orthogonality_table_df = self.orthogonality_result_df[column_name].copy()

    def create_practical_feasibility_table(self):
        """Build the practical feasibility sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.practical_feasibility_table_df``.
        """
        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Complexity",
            "Compatibility",
            "Peak Detection Rate (%)",
            "Peak Detection Rate Status",
        ]

        self.practical_feasibility_table_df = self.orthogonality_result_df[column_name].copy()

    def create_separational_potential_table(self):
        """Build the separational potential sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.separational_potential_table_df``.
        """
        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Practical 2D Peak Capacity",
            "Selectivity Factor",
        ]

        self.separational_potential_table_df = self.orthogonality_result_df[column_name].copy()

    def create_final_recommendation_table(self):
        """Build the final recommendation sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.final_recommendation_table_df``.
        """
        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Consensus Ranking",
            "Peak Detection Rate (%)",
            "Practical 2D Peak Capacity",
            "Compatibility",
            "Complexity",
            "Final Recommendation",
            "Suggested Rank",
        ]

        self.final_recommendation_table_df = self.orthogonality_result_df[column_name].copy()

    # ------------------------------------------------------------------
    # Ranking / recommendation helpers
    # ------------------------------------------------------------------

    def compute_suggested_rank(self):
        """Compute the suggested rank for each combination.

        Side Effects:
            - Adds ``"Suggested Rank"`` column to ``self.orthogonality_result_df``.
        """
        practical_peak_capacity_rank = (
            self.orthogonality_result_df['Practical 2D Peak Capacity']
            .rank(ascending=False, method='average')
        )

        if (self.peak_capacity_status in ["peak_capacity_loaded"] and
                'Consensus Ranking' in self.orthogonality_result_df.columns):
            self.orthogonality_result_df["Suggested Rank"] = pd.concat(
                [practical_peak_capacity_rank,
                 self.orthogonality_result_df['Consensus Ranking']],
                axis=1,
            ).mean(axis=1)
            self.orthogonality_result_df["Suggested Rank"] = (
                self.orthogonality_result_df["Suggested Rank"].rank(ascending=True, method='average')
            )
        elif 'Consensus Ranking' in self.orthogonality_result_df.columns:
            self.orthogonality_result_df["Suggested Rank"] = (
                self.orthogonality_result_df['Consensus Ranking']
            )
        else:
            self.orthogonality_result_df["Suggested Rank"] = 'Not available'

    def compute_final_recommendation_factor(self):
        """Compute and assign a final recommendation label to each combination.

        Side Effects:
            - Adds ``"Final Recommendation"`` column to ``self.orthogonality_result_df``.
        """

        def is_highly_recommended(row):
            top_10_suggested_rank = int(0.1 * self.orthogonality_result_df["Suggested Rank"].max())
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row['Suggested Rank']
            compatibility = row['Compatibility']
            complexity = row['Complexity']

            if (peak_rate > 80
                    and suggested_rank <= top_10_suggested_rank
                    and compatibility in ['Good', 'Moderate']
                    and complexity in ['Low', 'Moderate']):
                return True
            else:
                return False

        def is_recommended(row):
            bottom_30_suggested_rank = int(0.7 * self.orthogonality_result_df["Suggested Rank"].max())
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row['Suggested Rank']
            compatibility = row['Compatibility']
            complexity = row['Complexity']

            if (peak_rate > 60
                    and suggested_rank >= bottom_30_suggested_rank
                    and compatibility not in ['Good']
                    and complexity not in ['Low']):
                return True
            else:
                return False

        def is_use_with_caution(row):
            top_30_suggested_rank = int(0.3 * self.orthogonality_result_df["Suggested Rank"].max())
            top_60_suggested_rank = int(0.6 * self.orthogonality_result_df["Suggested Rank"].max())
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row['Suggested Rank']
            compatibility = row['Compatibility']
            complexity = row['Complexity']

            if (40 <= peak_rate < 70
                    or top_30_suggested_rank <= suggested_rank <= top_60_suggested_rank
                    or compatibility in ['Good']
                    or complexity in ['Low']):
                return True
            else:
                return False

        def is_not_recommended(row):
            top_30_suggested_rank = int(0.3 * self.orthogonality_result_df["Suggested Rank"].max())
            suggested_rank = row['Suggested Rank']
            peak_rate = row['Peak Detection Rate (%)']

            if peak_rate < 40 or suggested_rank < top_30_suggested_rank:
                return True
            else:
                return False

        def set_final_recommendation(row):
            if is_highly_recommended(row):
                return 'Highly recommended'

            if is_not_recommended(row):
                return 'Not recommended'

            if is_recommended(row):
                return 'Recommended'

            if is_use_with_caution(row):
                return 'Use with caution'

            return '---'

        self.orthogonality_result_df["Final Recommendation"] = (
            self.orthogonality_result_df.apply(lambda row: set_final_recommendation(row), axis=1)
        )

    # ------------------------------------------------------------------
    # Chromatographic mode helpers
    # ------------------------------------------------------------------

    def set_compatibility(self):
        """Assign a hardware compatibility label to each combination.

        Compares the two Chromatographic Modes in each combination and assigns
        ``"High"``, ``"Moderate"``, or ``"Low"`` to the ``"Compatibility"`` column.

        Side Effects:
            - Adds ``"Compatibility"`` column to ``self.orthogonality_result_df``.
        """
        compatibility_list = []

        for mode in self.orthogonality_result_df["Chromatographic Mode"]:
            parts = mode.split(' vs ')
            if len(parts) == 2:
                a, b = parts[0].strip(), parts[1].strip()

                if a == b:
                    compatibility_list.append('Good')
                elif a != b and {a, b} == {'HILIC', 'RPLC'}:
                    compatibility_list.append('Moderate')
                else:
                    compatibility_list.append('Low')
            else:
                compatibility_list.append('Unknown')

        self.orthogonality_result_df["Compatibility"] = compatibility_list

    def set_complexity(self):
        """Assign a method development complexity label to each combination.

        Compares the two Chromatographic Modes and assigns ``"Low"``,
        ``"Medium"``, ``"High"``, or ``"NC"`` to the ``"Complexity"`` column.

        Side Effects:
            - Adds ``"Complexity"`` column to ``self.orthogonality_result_df``.
        """
        complexity_list = []

        for mode in self.orthogonality_result_df["Chromatographic Mode"]:
            parts = mode.split(' vs ')

            if len(parts) == 2:
                a, b = parts[0].strip(), parts[1].strip()

                if a == b:
                    complexity_list.append('Low')
                elif a != b and {a, b} == {'HILIC', 'RPLC'}:
                    complexity_list.append('Moderate')
                elif a in ['SFC'] or b in ['SFC']:
                    complexity_list.append('High')
                else:
                    complexity_list.append('NC')
            else:
                complexity_list.append('Unknown')

        self.orthogonality_result_df['Complexity'] = complexity_list

    def build_chromatographic_mode(self, combination_list):
        """Extract Chromatographic Mode tokens from combination name strings.

        Tokenises each combination name and keeps only tokens that appear in
        ``CHROM_MODE``, joining them with spaces.

        Args:
            combination_list (list[str]): List of combination name strings.

        Returns:
            list[str]: List of space-joined Chromatographic Mode tokens,
                one entry per input combination.
        """
        chromatographic_mode = []

        for combination in combination_list:
            tokens = re.findall(r'\b[A-Za-z0-9-]+\b', combination)

            tokens_cleaned = [token for token in tokens if token in CHROM_MODE]

            chromatographic_mode.append(' '.join(tokens_cleaned))

        return chromatographic_mode
