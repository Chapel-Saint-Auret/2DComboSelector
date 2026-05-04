"""Results table construction and final recommendation logic.

This module provides the :class:`ResultsBuilder` mixin which builds the
various result DataFrames (orthogonality table, feasibility table, etc.)
and computes the final recommendation factors.  It has no Qt dependencies.
"""

import re

import pandas as pd

from math import ceil

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

    def get_median_rank_score_table(self):
        """Get the median_rank_score sub-table.

        Returns:
            pd.DataFrame: median_rank_score table.
        """
        return self.median_rank_score_df

    def get_rank_score_grouped_by_chrom_mode_table(self):
        """Get the median_rank_score sub-table.

        Returns:
            pd.DataFrame: median_rank_score table.
        """
        return self.rank_score_grouped_by_chrom_mode_df

    def get_recommendation_distribution_group_table(self):
        """Get the recommendation_distribution_df sub-table.

        Returns:
            pd.DataFrame: recommendation_distribution_df table.
        """
        return self.recommendation_distribution_df


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

        self.orthogonality_result_df["Hypothetical 2D Peak Capacity"] = self.combination_df["Hypothetical 2D Peak Capacity"].copy()
        self.orthogonality_result_df["Hypothetical 2D Peak Capacity Rank"] = self.combination_df["Hypothetical 2D Peak Capacity"].copy()
        self.orthogonality_result_df["Elution Composition Space Area"] = self.combination_df["Elution Composition Space Area"].copy()
        self.orthogonality_result_df["Elution Composition Space Area Rank"] = self.combination_df["Elution Composition Space Area"].copy()

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
        # self.update_result_with_new_peak_capacity()
        self.compute_final_rank()

        self.compute_criterion_highlight()
        self.compute_final_recommendation_factor()

        self.create_orthogonality_table()
        self.create_practical_feasibility_table()
        self.create_separational_potential_table()
        self.create_final_recommendation_table()


        self.create_median_rank_score_based_on_chromatographic_group()
        self.create_rank_score_based_on_chromatographic_group()
        self.create_recommendation_distribution_group()

    def update_result_with_new_peak_capacity(self):
        """Update the results table with the most recent peak capacity data.

        Side Effects:
            - Updates ``"Practical 2D Peak Capacity"`` column in result DataFrames.
        """
        if (not self.coverage_score_df.empty and
                'Not available' not in self.combination_df['Hypothetical 2D Peak Capacity'].values):

            self.orthogonality_result_df['Practical 2D Peak Capacity'] = (
                self.combination_df['Hypothetical 2D Peak Capacity'] * self.coverage_score_df
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

        self.compute_final_rank()

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
            "Hypothetical 2D Peak Capacity",
            "Elution Composition Space Area",
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
            "Hypothetical 2D Peak Capacity Rank",
            "Elution Composition Space Area",
            "Final Recommendation",
            "Final Rank",
            "Criterion Higlight",
        ]

        self.final_recommendation_table_df = self.orthogonality_result_df[column_name].copy()

    def create_median_rank_score_based_on_chromatographic_group(self):

        column_name = [
            "Consensus Ranking",
            "Elution Composition Space Area Rank",
            "Hypothetical 2D Peak Capacity Rank",
            "Final Rank",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Composition Space Area Rank",
            "Hypothetical 2D Peak Capacity Rank",
        ]:
            self.orthogonality_result_df[col] = pd.to_numeric(self.orthogonality_result_df[col], errors="coerce").fillna(0)

        self.median_rank_score_df = (self.orthogonality_result_df.groupby("Chromatographic Mode")[column_name].median())

        # # Invert all ranks (lower rank → higher score) then normalize to 0–100
        # for col in column_name[0:-1]:
        #     inverted = self.median_rank_score_df[col].max() - self.median_rank_score_df[col]
        #     col_min, col_max = inverted.min(), inverted.max()
        #     if col_max > col_min:
        #         self.median_rank_score_df[col] = (inverted - col_min) / (col_max - col_min) * 100
        #     else:
        #         self.median_rank_score_df[col] = 50.0

        print('Median Rank Score Based on Chromatographic Mode')

    def create_rank_score_based_on_chromatographic_group(self):

        column_name = [
            "Consensus Ranking",
            "Elution Composition Space Area Rank",
            "Hypothetical 2D Peak Capacity Rank",
            "Final Rank",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Composition Space Area Rank",
            "Hypothetical 2D Peak Capacity Rank",
        ]:
            self.orthogonality_result_df[col] = pd.to_numeric(self.orthogonality_result_df[col], errors="coerce").fillna(0)

        self.rank_score_grouped_by_chrom_mode_df = self.orthogonality_result_df.groupby("Chromatographic Mode")[column_name]

    def create_recommendation_distribution_group(self):

        column_name = [
            "Consensus Ranking",
            "Elution Composition Space Area Rank",
            "Hypothetical 2D Peak Capacity Rank",
            "Final Rank",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Composition Space Area Rank",
            "Hypothetical 2D Peak Capacity Rank",
        ]:
            self.orthogonality_result_df[col] = pd.to_numeric(self.orthogonality_result_df[col], errors="coerce").fillna(0)

        self.recommendation_distribution_df = self.orthogonality_result_df.groupby("Chromatographic Mode")['Final Recommendation']
    # ------------------------------------------------------------------
    # Ranking / recommendation helpers
    # ------------------------------------------------------------------

    def compute_final_rank(self):
        """Compute the suggested rank for each combination.

        Side Effects:
            - Adds ``'Final Rank'`` column to ``self.orthogonality_result_df``.
        """

        if (self.peak_capacity_status in ["peak_capacity_loaded"] and
            self.elution_data_status in ["elution_data_loaded"] and
                'Consensus Ranking' in self.orthogonality_result_df.columns):

            self.orthogonality_result_df['Final Rank'] = pd.concat(
                [self.orthogonality_result_df['Hypothetical 2D Peak Capacity Rank'],
                 self.orthogonality_result_df['Elution Composition Space Area Rank'],
                 self.orthogonality_result_df['Consensus Ranking']],
                axis=1,
            ).mean(axis=1)

            self.orthogonality_result_df['Final Rank'] = (
                self.orthogonality_result_df['Final Rank'].rank(ascending=True, method='average')
            )

        elif (self.peak_capacity_status in ["peak_capacity_loaded"] and
                'Consensus Ranking' in self.orthogonality_result_df.columns):

            self.orthogonality_result_df['Final Rank'] = pd.concat(
                [self.orthogonality_result_df['Hypothetical 2D Peak Capacity Rank']
                    ,self.orthogonality_result_df['Consensus Ranking']],
                axis=1,
            ).mean(axis=1)

            self.orthogonality_result_df['Final Rank'] = (
                self.orthogonality_result_df['Final Rank'].rank(ascending=True, method='average')
            )

        elif (self.peak_capacity_status in ["elution_data_loaded"] and
                'Consensus Ranking' in self.orthogonality_result_df.columns):

            self.orthogonality_result_df['Final Rank'] = pd.concat(
                [self.orthogonality_result_df['Elution Composition Space Area Rank'],
                    self.orthogonality_result_df['Consensus Ranking']],
                axis=1,
            ).mean(axis=1)

        elif 'Consensus Ranking' in self.orthogonality_result_df.columns:
            self.orthogonality_result_df['Final Rank'] = (
                self.orthogonality_result_df['Consensus Ranking']
            )
        else:
            self.orthogonality_result_df['Final Rank'] = 'Not available'

    def compute_criterion_highlight(self):
        """
            Seuil Top 1% :
            K_1%,X = max(1, ceiling(0.01 x N))
            Seuil Top 5% :
            K_5%,X = max(1, ceiling(0.05 x N))
            Seuil Top 10% :
            K_10%,X = max(1, ceiling(0.10 x N))

            •	Top 1% in X si R_X,i <= K_1%,X
            •	sinon Top 5% in X si R_X,i <= K_5%,X
            •	sinon Top 10% in X si R_X,i <= K_10%,X
            •	sinon aucun badge pour ce critère

        """

        K_1  =  max(1,ceil(0.01*self.nb_condition))
        K_5  =  max(1,ceil(0.05*self.nb_condition))
        K_10 =  max(1,ceil(0.10*self.nb_condition))

        def is_top_1(rank):
            if rank <= K_1:
                return True
            else:
                return False

        def is_top_5(rank):
            if rank <= K_5:
                return True
            else:
                return False

        def is_top_10(rank):
            if rank <= K_10:
                return True
            else:
                return False

        def set_criterion(rank,criterion):
            """
            •	Top 1% in orthogonality
            •	Top 5% in orthogonality
            •	Top 10% in orthogonality
            """

            if is_top_1(rank):
                return f"Top 1% in {criterion}"

            elif is_top_5(rank):
                return f"Top 5% in {criterion}"

            elif is_top_10(rank):
                return f"Top 10% in {criterion}"

            else:
                return ''

        elution_rank_is_numeric = (self.orthogonality_result_df['Elution Composition Space Area Rank'] != 'Not available').any()
        peak_capacity_rank_is_numeric = (self.orthogonality_result_df['Hypothetical 2D Peak Capacity Rank'] != 'Not available').any()

        if 'Consensus Ranking' in self.orthogonality_result_df.columns:
            orthogonality_consensus_ranking = (self.orthogonality_result_df['Consensus Ranking'].
                                       apply(lambda rank: set_criterion(rank,criterion='O')))
        else:
            orthogonality_consensus_ranking = ''

        if 'Elution Composition Space Area Rank' in self.orthogonality_result_df.columns and elution_rank_is_numeric:
            elution_composition_space_area_ranking = (self.orthogonality_result_df['Elution Composition Space Area Rank'].
                                               apply(lambda rank: set_criterion(rank, criterion='ES')))
        else:
            elution_composition_space_area_ranking = ''

        if 'Hypothetical 2D Peak Capacity Rank' in self.orthogonality_result_df.columns and peak_capacity_rank_is_numeric:
            hypothetical_2d_peak_capacity_ranking = (self.orthogonality_result_df['Hypothetical 2D Peak Capacity Rank'].
                                               apply(lambda rank: set_criterion(rank, criterion='PS')))
        else:
            hypothetical_2d_peak_capacity_ranking = ''

        self.orthogonality_result_df["Criterion Higlight"] =(orthogonality_consensus_ranking + ' ' +
                                                             elution_composition_space_area_ranking + ' ' +
                                                             hypothetical_2d_peak_capacity_ranking)


    def compute_final_recommendation_factor(self):
        """Compute and assign a final recommendation label to each combination.

        Side Effects:
            - Adds ``"Final Recommendation"`` column to ``self.orthogonality_result_df``.
        """

        def is_highly_recommended(row):
            top_10_suggested_rank = int(0.1 * self.orthogonality_result_df['Final Rank'].max())
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row['Final Rank']
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
            bottom_30_suggested_rank = int(0.7 * self.orthogonality_result_df['Final Rank'].max())
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row['Final Rank']
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
            top_30_suggested_rank = int(0.3 * self.orthogonality_result_df['Final Rank'].max())
            top_60_suggested_rank = int(0.6 * self.orthogonality_result_df['Final Rank'].max())
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row['Final Rank']
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
            top_30_suggested_rank = int(0.3 * self.orthogonality_result_df['Final Rank'].max())
            suggested_rank = row['Final Rank']
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
