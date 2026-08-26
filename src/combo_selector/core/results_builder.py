"""Results table construction and final recommendation logic.

This module provides the :class:`ResultsBuilder` mixin which builds the
various result DataFrames (orthogonality table, feasibility table, etc.)
and computes the final recommendation factors.  It has no Qt dependencies.
"""

import re

import pandas as pd

from math import ceil

from combo_selector.core.orthogonality_utils import CHROM_MODE, METRIC_MAPPING,FEASABILITY
from combo_selector.core.orthogonality_utils import get_symmetric_mode_dict


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

    def get_chromatographic_mode_list(self):
        """Return chromatographic mode list."""
        return self.list_of_chrom_mode

    def get_filtered_result_df(self):
        """Return filtered result df."""
        return self.filtered_result_df

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

    def get_old_approach_table(self):
        """Get the old approach sub-table.

        Returns:
            pd.DataFrame: Old approach table.
        """
        return self.old_approach_table_df


    def get_median_rank_score_table(self):
        """Get the median_rank_score sub-table.

        Returns:
            pd.DataFrame: median_rank_score table.
        """
        return self.median_rank_score_df

    def get_median_utility_score_table(self):
        """Get the median_utility_score sub-table.

        Returns:
            pd.DataFrame: median_utility_score table.
        """
        return self.median_utility_score_df

    def get_rank_score_grouped_by_chrom_mode_table(self):
        """Get the rank_score_grouped_by_chrom_mode sub-table.

        Returns:
            pd.DataFrame: rank_score_grouped_by_chrom_mode table.
        """
        return self.rank_score_grouped_by_chrom_mode_df

    def get_utility_score_grouped_by_chrom_mode_table(self):
        """Get the utility_score_grouped_by_chrom_mode sub-table.

        Returns:
            pd.DataFrame: utility_score_grouped_by_chrom_mode table.
        """
        return self.utility_score_grouped_by_chrom_mode_df

    def get_rank_score_grouped_by_recommendation_table(self):
        """Get the rank_score_grouped_by_final_recommendation_df sub-table.

        Returns:
            pd.DataFrame: rank_score_grouped_by_final_recommendation_df table.
        """

        return self.rank_score_grouped_by_final_recommendation_df

    def get_recommendation_distribution_group_table(self):
        """Get the recommendation_distribution_df sub-table.

        Returns:
            pd.DataFrame: recommendation_distribution_df table.
        """
        return self.recommendation_distribution_df

    def get_detected_compounds_grouped_by_mode_table(self):
        """Get the recommendation_distribution_df sub-table.

        Returns:
            pd.DataFrame: recommendation_distribution_df table.
        """
        return self.detected_compounds_grouped_by_mode

    def get_detected_compounds_grouped_by_combination_mode_table(self):
        """Get the recommendation_distribution_df sub-table.

        Returns:
            pd.DataFrame: recommendation_distribution_df table.
        """
        return self.detected_compounds_grouped_by_combination_mode

    def get_metric_agreement_grouped_by_combination_mode_table(self):
        """Get the metric_agreement_grouped_by_combination_mode sub-table.

        Returns:
            pd.DataFrame: metric_agreement_grouped_by_combination_mode table.
        """
        return self.metric_agreement_grouped_by_combination_mode


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

        self.list_of_chrom_mode = list(self.orthogonality_result_df.groupby("Chromatographic Mode").groups)

        self.orthogonality_result_df["Number of peaks"] = self.combination_df["Number of peaks"]
        self.orthogonality_result_df["Hypothetical 2D Peak Capacity"] = self.combination_df["Hypothetical 2D Peak Capacity"].copy()
        self.orthogonality_result_df["Peak Capacity Rank"] = self.combination_df["Hypothetical 2D Peak Capacity"].copy()
        self.orthogonality_result_df["Peak Capacity Utility"] = self.combination_df["Hypothetical 2D Peak Capacity"].copy()
        self.orthogonality_result_df["Elution Domain"] = self.combination_df["Elution Domain"].copy()
        self.orthogonality_result_df["Elution Domain Rank"] = self.combination_df["Elution Domain"].copy()
        self.orthogonality_result_df["Elution Domain Utility"] = self.combination_df["Elution Domain"].copy()
    def apply_multi_column_filter(self, filter_spec_list:list = None) -> None:
        """Apply all active multi-column filters to the results table."""
        if filter_spec_list is None:
            active_filters = list(self.active_multi_column_filters.values())
        elif not filter_spec_list:
            self.active_multi_column_filters = {}
            active_filters = []
        else:
            for filter_spec in filter_spec_list:
                filter_name = filter_spec.get("filter_name")
                if not filter_name:
                    continue
                self.active_multi_column_filters[filter_name] = filter_spec.copy()

            active_filters = list(self.active_multi_column_filters.values())

        mask = pd.Series(True, index=self.orthogonality_result_df.index)

        for filter_spec in active_filters:
            col_name = filter_spec.get("filter_name")
            pattern = filter_spec.get("patterns", "")

            if not col_name or col_name not in self.orthogonality_result_df.columns:
                continue
            if not pattern:
                continue

            mask &= self.orthogonality_result_df[col_name].astype(str).str.contains(
                pattern, na=False, regex=True
            )

        self.filtered_result_df = self.orthogonality_result_df[mask].copy()

        self.create_orthogonality_table()
        self.create_practical_feasibility_table()
        self.create_separational_potential_table()
        self.create_final_recommendation_table()
        self.create_old_approach_table()

        self.create_median_rank_score_based_on_chromatographic_group()
        self.create_median_utility_score_based_on_chromatographic_group()
        self.create_rank_score_based_on_chromatographic_group()
        self.create_utility_score_based_on_chromatographic_group()
        self.create_rank_score_based_on_recommendation_class()
        self.create_recommendation_distribution_group()
        self.create_detected_compounds_grouped_by_mode()
        self.create_detected_compounds_grouped_by_combination_mode()
        self.create_metric_agreement_grouped_by_combination_mode()

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
        self.compute_consensus_orthogonality_ranking()
        self.compute_custom_orthogonality_score()
        self.assess_metric_removal_impact_on_orthogonality_rank()
        self.compute_suggested_score()
        self.assess_metric_removal_impact_on_orthogonality_rank_old_approach()
        self.compute_practical_2d_peak_capacity()
        self.compute_coverage_score()
        self.compute_distribution_score()
        self.compute_agreement_index()
        self.compute_outlier_metric_flag()
        self.compute_peak_detection_rate()
        self.compute_peak_selectivity_factor()
        self.compute_final_results()

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

        self.compute_final_results()

    def create_orthogonality_table(self):
        """Build the orthogonality sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.orthogonality_table_df``.
        """

        score_used = self.score_computed_method_info['score_used']

        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Coverage Score",
            "Distribution Score",
            # The ternary operator selects the correct string inline
            "Orthogonality Utility" if score_used == 'Default' else "Computed Orthogonality Score",
            "Agreement Indicator"
        ]

        self.orthogonality_table_df = self.filtered_result_df[column_name].copy()

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

        self.practical_feasibility_table_df = self.filtered_result_df[column_name].copy()

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
            "Elution Domain",
        ]

        self.separational_potential_table_df = self.filtered_result_df[column_name].copy()

    def create_final_recommendation_table(self):
        """Build the final recommendation sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.final_recommendaFinal Rank (Utility)tion_table_df``.
        """
        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Orthogonality Utility",
            "Peak Capacity Utility",
            "Elution Domain Utility",
            "Final Score (Utility)",
            "Final Rank (Utility)",
            "Final Recommendation",
            "Criterion Highlight",
        ]

        self.final_recommendation_table_df = self.filtered_result_df[column_name].copy()

    def create_old_approach_table(self):
        """Build the final recommendation sub-table from the results DataFrame.

        Side Effects:
            - Creates ``self.final_recommendation_table_df``.
        """
        column_name = [
            "Combination #",
            "2D Combination",
            "Chromatographic Mode",
            "Suggested Orthogonality Score",
            "Suggested Orthogonality Rank",
            "Practical Peak Capacity",
            "Practical Peak Capacity Rank"
        ]

        self.old_approach_table_df = self.filtered_result_df[column_name].copy()

    def create_median_rank_score_based_on_chromatographic_group(self):
        """Create median rank values grouped by chromatographic mode."""

        column_name = [
            "2D Combination",
            "Combination #",
            "Orthogonality Rank",
            "Elution Domain Rank",
            "Peak Capacity Rank",
            "Final Rank (Utility)",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Domain Rank",
            "Peak Capacity Rank",
        ]:
            self.filtered_result_df[col] = pd.to_numeric(self.filtered_result_df[col], errors="coerce").fillna(0)

        self.median_rank_score_df = (self.filtered_result_df.groupby("Chromatographic Mode")[column_name].median(numeric_only=True))

    def create_median_utility_score_based_on_chromatographic_group(self):
        """Create median utility values grouped by chromatographic mode."""

        column_name = [
            "2D Combination",
            "Combination #",
            "Orthogonality Utility",
            "Elution Domain Utility",
            "Peak Capacity Utility",
            "Final Score (Utility)",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Domain Utility",
            "Peak Capacity Utility",
        ]:
            self.filtered_result_df[col] = pd.to_numeric(self.filtered_result_df[col], errors="coerce").fillna(0)

        self.median_utility_score_df = (self.filtered_result_df.groupby("Chromatographic Mode")[column_name].median(numeric_only=True))

    def create_utility_score_based_on_chromatographic_group(self):
        """Create utility-score groups keyed by chromatographic mode."""

        column_name = [
            "2D Combination",
            "Combination #",
            "Orthogonality Utility",
            "Final Recommendation",
            "Final Score (Utility)",
            "Elution Domain Utility",
            "Peak Capacity Utility",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Domain Utility",
            "Peak Capacity Utility",
        ]:
            self.filtered_result_df[col] = pd.to_numeric(self.filtered_result_df[col], errors="coerce").fillna(0)

        self.utility_score_grouped_by_chrom_mode_df = self.filtered_result_df.groupby("Chromatographic Mode")[column_name]

    def create_rank_score_based_on_chromatographic_group(self):
        """Create rank-score groups keyed by chromatographic mode."""

        column_name = [
            "2D Combination",
            "Combination #",
            "Orthogonality Rank",
            "Final Recommendation",
            "Final Rank (Utility)",
            "Elution Domain Rank",
            "Peak Capacity Rank",
            "Peak Detection Rate (%)",
        ]

        for col in [
            "Elution Domain Rank",
            "Peak Capacity Rank",
        ]:
            self.filtered_result_df[col] = pd.to_numeric(self.filtered_result_df[col], errors="coerce").fillna(0)

        self.rank_score_grouped_by_chrom_mode_df = self.filtered_result_df.groupby("Chromatographic Mode")[column_name]

    def create_rank_score_based_on_recommendation_class(self):
        """Create rank-score groups keyed by final recommendation."""
        column_name = [
            "2D Combination",
            "Combination #",
            "Final Rank (Utility)",
            "Chromatographic Mode",
        ]

        for col in [
            "Elution Domain Utility",
            "Peak Capacity Utility",
        ]:
            self.filtered_result_df[col] = pd.to_numeric(self.filtered_result_df[col], errors="coerce").fillna(0)
        self.rank_score_grouped_by_final_recommendation_df = self.filtered_result_df.groupby("Final Recommendation")[column_name]

    def create_recommendation_distribution_group(self):
        """Create recommendation distribution groups by chromatographic mode."""

        for col in [
            "Elution Domain Utility",
            "Peak Capacity Utility",
        ]:
            self.filtered_result_df[col] = pd.to_numeric(self.filtered_result_df[col], errors="coerce").fillna(0)

        self.recommendation_distribution_df = self.filtered_result_df.groupby("Chromatographic Mode")['Final Recommendation']

    def create_detected_compounds_grouped_by_mode(self):
        """Create detected compounds grouped by mode."""

        def get_mode(col_name):
            """Return mode."""
            # Loop through the known chromatography modes
            # and return the first mode found as a substring of the column name
            for mode in CHROM_MODE:
                if mode in col_name:
                    return mode
            return None  # no mode found in the column name

        # Copy the source DataFrame so we don't modify the original
        raw_df = self.normalized_retention_time_df.copy()

        # Replace empty strings '' with actual NaN (pd.NA),
        # otherwise .notna() would not detect them as "missing"
        # .notna() returns a DataFrame of booleans (True = non-empty cell)
        # .sum() adds up the True values per column (True counts as 1)
        # -> result: a Series with index = column names, values = count of non-empty cells
        non_empty_counts = raw_df.replace('', pd.NA).notna().sum()

        # Drop columns that are not measurement columns
        # (identifiers, not chromatographic data)
        non_empty_counts = non_empty_counts.drop(['Peak #', 'Compound Name'])

        # Build a dictionary {column_name: mode} for every column in the source DataFrame
        # get_mode() is called once per column name
        col_to_mode = {col: get_mode(col) for col in self.normalized_retention_time_df.columns}

        # Convert the Series into a DataFrame: the index (column names) becomes a regular column
        long_df = non_empty_counts.reset_index()

        # Rename the two resulting columns for clarity
        long_df.columns = ['column_name', 'count']

        # For each value in column_name, look up the matching mode in col_to_mode
        # and create a new 'mode' column with the result
        long_df['mode'] = long_df['column_name'].map(col_to_mode)

        # Sort rows by mode so columns belonging to the same mode appear together
        long_df = long_df.sort_values('mode')

        # Group rows by mode: returns a DataFrameGroupBy object (not a plain DataFrame)
        # This object is "lazy": it computes nothing until you call
        # a method on it (.sum(), .apply(), or loop with for mode, group in ...)
        self.detected_compounds_grouped_by_mode = long_df.groupby('mode')

    def create_detected_compounds_grouped_by_combination_mode(self):
        """Create detected compounds grouped by combination mode."""

        self.detected_compounds_grouped_by_combination_mode = self.filtered_result_df.groupby("Chromatographic Mode")["Number of peaks"]

    def create_metric_agreement_grouped_by_combination_mode(self):
        """Create metric agreement grouped by combination mode."""

        self.metric_agreement_grouped_by_combination_mode = self.filtered_result_df.groupby("Chromatographic Mode")["Agreement Indicator"]
    # ------------------------------------------------------------------
    # Ranking / recommendation helpers
    # ------------------------------------------------------------------
    def set_performance_penalty(self,penalty):
        """Set performance penalty."""
        self.penalty_is_on = penalty == 'On'

    def set_orthogonality_threshold_penalty(self,threshold):
        """Set orthogonality threshold penalty."""
        self.orthogonality_threshold_penalty = threshold

    def set_elution_threshold_penalty(self,threshold):
        """Set elution threshold penalty."""
        self.elution_threshold_penalty = threshold

    def compute_final_results(self):
        """Compute final results."""
        self.compute_final_rank()

        self.compute_criterion_highlight()
        self.compute_final_recommendation_factor()

        self.apply_multi_column_filter()

    def compute_final_rank(self):
        """Compute the suggested rank for each combination.

        Combines whichever of the three scoring components are available -
        Orthogonality (O), Peak Capacity (P) and Elution Domain (D) - into:
          - 'Final Rank': average of the available *_Rank columns, re-ranked
            (kept as-is when Orthogonality is the only component available).
          - 'Final Rank (Utility)': average of the available *_Utility columns
            (S_raw), optionally penalized when elution data is available.

        Side Effects:
            - Adds 'Final Rank' to self.orthogonality_result_df.
            - Adds 'S_raw', 'Final Score (Utility)' and 'Final Rank (Utility)'
              to self.orthogonality_result_df.
            - When the elution-domain penalty is applied, also adds 'p_o'/'p_d'.
        """
        df = self.orthogonality_result_df

        if 'Orthogonality Rank' not in df.columns:
            df['Final Rank'] = 'Not available'
            df['Final Score (Utility)'] = 'Not available'
            df['Final Rank (Utility)'] = 'Not available'
            return

        # --- Orthogonality component (always available) ---
        score_used = self.score_computed_method_info['score_used']
        if score_used == 'Default':
            rank_O = df['Orthogonality Rank']
            util_O = df['Orthogonality Utility']
        else:
            rank_O = util_O = df['Computed Orthogonality Rank']

        peak_capacity_available = self.peak_capacity_status == "peak_capacity_loaded"
        elution_data_available = self.elution_data_status == "elution_data_loaded"

        # ------------------------------------------------------------------
        # Final Rank: average of the available *_Rank columns, re-ranked.
        # If Orthogonality is the only component, keep its rank as-is
        # (nothing to average, so no re-ranking needed).
        # ------------------------------------------------------------------
        rank_components = [rank_O]
        if peak_capacity_available:
            rank_components.append(df['Peak Capacity Rank'])
        if elution_data_available:
            rank_components.append(df['Elution Domain Rank'])

        if len(rank_components) > 1:
            df['Final Rank'] = pd.concat(rank_components, axis=1).mean(axis=1).rank(ascending=True, method='average')
        else:
            df['Final Rank'] = rank_components[0]

        # ------------------------------------------------------------------
        # Final Rank (Utility): average of the available *_Utility columns
        # (S_raw), optionally penalized when elution data is available.
        #
        #   P_O = min(1, U_O / orthogonality_threshold_penalty)
        #   P_D = min(1, U_D / elution_threshold_penalty)
        #   S_final = S_raw * P_O * P_D   (only when elution data is loaded
        #                                   AND penalty_is_on)
        # ------------------------------------------------------------------
        utility_components = [util_O]
        if peak_capacity_available:
            utility_components.append(df['Peak Capacity Utility'])
        if elution_data_available:
            utility_components.append(df['Elution Domain Utility'])

        s_raw = pd.concat(utility_components, axis=1).mean(axis=1)

        if elution_data_available and self.penalty_is_on:
            p_o = util_O.apply(lambda x: min(1, x / self.orthogonality_threshold_penalty))
            p_d = df['Elution Domain Utility'].apply(lambda x: min(1, x / self.elution_threshold_penalty))
            df['p_o'] = p_o
            df['p_d'] = p_d
            s_final = s_raw * p_o * p_d
        else:
            s_final = s_raw

        df['S_raw'] = s_raw
        df['Final Score (Utility)'] = s_final
        df['Final Rank (Utility)'] = s_final.rank(ascending=False, method='average')

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
        K_70 =  max(1,ceil(0.70*self.nb_condition))

        def is_top_1(rank):
            """Return whether a rank falls within the top 1%."""
            if rank <= K_1:
                return True
            else:
                return False

        def is_top_5(rank):
            """Return whether a rank falls within the top 5%."""
            if rank <= K_5:
                return True
            else:
                return False
        def is_bottom_30(rank):
            """Return whether a rank falls within the bottom 30%."""
            if rank >= K_70:
                return True
            else:
                return False

        def is_top_10(rank):
            """Return whether a rank falls within the top 10%."""
            if rank <= K_10:
                return True
            else:
                return False

        def set_criterion(rank,criterion):
            """Return the criterion badge text for a rank value."""

            if is_top_10(rank):
                return f"Top 10% in {criterion}"

            elif is_bottom_30(rank):
                return f"Bottom 30% in {criterion}"

            else:
                return ''

        def set_penality_flag(ortho,elution):
            """Return the penalty-threshold message for a result row."""
            if ortho < 0.7 and elution < 0.30:
                return "Below penalty threshold: O + Δφ"
            elif ortho<0.7:
                return "Below penalty threshold: O"
            elif elution<0.3:
                return "Below penalty threshold: Δφ"
            else:
                return ''


        elution_rank_is_numeric = (self.orthogonality_result_df['Elution Domain Rank'] != 'Not available').any()
        peak_capacity_rank_is_numeric = (self.orthogonality_result_df['Peak Capacity Rank'] != 'Not available').any()

        score_used = self.score_computed_method_info['score_used']

        if score_used == 'Default':
            orthogonality_rank = self.orthogonality_result_df['Orthogonality Rank']
        else:
            orthogonality_rank = self.orthogonality_result_df['Computed Orthogonality Rank']


        if 'Orthogonality Rank' in self.orthogonality_result_df.columns:
            orthogonality_consensus_ranking = (orthogonality_rank.
                                       apply(lambda rank: set_criterion(rank,criterion='O')))
        else:
            orthogonality_consensus_ranking = ''

        if 'Elution Domain Rank' in self.orthogonality_result_df.columns and elution_rank_is_numeric:
            elution_composition_space_area_ranking = (self.orthogonality_result_df['Elution Domain Rank'].
                                               apply(lambda rank: set_criterion(rank, criterion='Δφ')))
        else:
            elution_composition_space_area_ranking = ''

        if 'Peak Capacity Rank' in self.orthogonality_result_df.columns and peak_capacity_rank_is_numeric:
            hypothetical_2d_peak_capacity_ranking = (self.orthogonality_result_df['Peak Capacity Rank'].
                                               apply(lambda rank: set_criterion(rank, criterion='nc')))
        else:
            hypothetical_2d_peak_capacity_ranking = ''

        if 'Agreement Indicator' in self.orthogonality_result_df.columns:
            low_orthogonality_agreement = (self.orthogonality_result_df['Agreement Indicator'].
                                                     apply(lambda x: 'Low Orthogonality Agreement' if x <0.8 else ''))
        else:
            low_orthogonality_agreement = ''

        if 'Elution Domain Utility' in self.orthogonality_result_df.columns and 'Orthogonality Utility' in self.orthogonality_result_df.columns:
            if score_used == 'Default':
                penality_flag = self.orthogonality_result_df.apply(lambda x: set_penality_flag(x['Orthogonality Utility'],x['Elution Domain Utility']),axis=1)
            else:
                penality_flag = ''
        else:
            penality_flag = ''

        self.orthogonality_result_df["Criterion Highlight"] =(orthogonality_consensus_ranking + ' ' +
                                                             elution_composition_space_area_ranking + ' ' +
                                                             hypothetical_2d_peak_capacity_ranking + ' ' +
                                                             low_orthogonality_agreement +
                                                             penality_flag)

        self.orthogonality_result_df["Criterion Highlight"] = (self.orthogonality_result_df["Criterion Highlight"]
                                                              .apply(lambda x: x.strip() if x.strip() else '---'))


    def compute_final_recommendation_factor(self):
        """Compute and assign a final recommendation label to each combination.

        Side Effects:
            - Adds ``"Final Recommendation"`` column to ``self.orthogonality_result_df``.
        """

        # Guard: compute_final_rank() sets 'Final Rank (Utility)' to the string
        # 'Not available' when no peak capacity / elution data has been loaded yet.
        # Calling .quantile() on a non-numeric column raises TypeError, so bail early.
        if not pd.api.types.is_numeric_dtype(
            self.orthogonality_result_df["Final Rank (Utility)"]
        ):
            self.orthogonality_result_df["Final Recommendation"] = "Not available"
            self.orthogonality_result_df["Final Recommendation tooltip"] = ""
            return

        rank_col = self.orthogonality_result_df["Final Rank (Utility)"]
        top_10_threshold = rank_col.quantile(0.1)
        top_30_threshold = rank_col.quantile(0.3)
        top_70_threshold = rank_col.quantile(0.7)

        def is_highly_recommended(row):
            """Return whether a row meets the highly recommended criteria."""
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row["Final Rank (Utility)"]
            compatibility = row['Compatibility']
            complexity = row['Complexity']

            if (peak_rate > 80
                    and suggested_rank <= top_10_threshold
                    and compatibility in ['High', 'Moderate']
                    and complexity in ['Low', 'Moderate']):
                return True
            else:
                return False

        def is_recommended(row):
            """Return whether a row meets the recommended criteria."""
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row["Final Rank (Utility)"]
            compatibility = row['Compatibility']
            complexity = row['Complexity']

            if (peak_rate > 60
                    and suggested_rank <= top_30_threshold
                    and compatibility not in ['Low']
                    and complexity not in ['High']):
                return True
            else:
                return False

        def is_use_with_caution(row):
            """Return whether a row should be flagged for cautious use."""
            peak_rate = row['Peak Detection Rate (%)']
            suggested_rank = row["Final Rank (Utility)"]
            compatibility = row['Compatibility']
            complexity = row['Complexity']

            if (40 <= peak_rate <= 60
                    or top_30_threshold < suggested_rank < top_70_threshold
                    or compatibility in ['Low']
                    or complexity in ['High']):
                return True
            else:
                return False

        def is_not_recommended(row):
            """Return whether a row should be marked as not recommended."""
            suggested_rank = row["Final Rank (Utility)"]
            peak_rate = row['Peak Detection Rate (%)']

            if peak_rate < 40 or suggested_rank >= top_70_threshold:
                return True
            else:
                return False

        def set_final_recommendation(row):
            """Return the final recommendation label for one result row."""
            if is_not_recommended(row):
                return 'Not recommended'

            if is_highly_recommended(row):
                return 'Highly recommended'

            if is_recommended(row):
                return 'Recommended'

            if is_use_with_caution(row):
                return 'Use with caution'

            return '---'

        def set_final_recommendation_text(row):

            """
            Final consensus Rank : Valeur (avec le seuil en orange, rouge, jaune ou vert)
            Peak Detection Rate : Idem (Failed criteria si il fail nos criteres definis)
            Complexity : High, medium etc (Failed criteria)
            Compatibility : Idem (Failed criteria)
            """
            if is_not_recommended(row):
                tooltip = (
                    f"<table>"
                    f"<tr><td><b>Final Consensus Rank:</b></td><td style='color: black;'>{row['Final Rank (Utility)']}</td></tr>"
                    f"<tr><td><b>Peak Detection Rate:</b></td><td style='color: bkack'>{row['Peak Detection Rate (%)']}%</td></tr>"
                    f"<tr><td><b>Complexity:</b></td><td style='color:black;'>{row['Complexity']}</td></tr>"
                    f"<tr><td><b>Compatibility:</b></td><td style='color: black;'>{row['Compatibility']}</td></tr>"
                    f"</table>"
                )
                return tooltip

            if is_highly_recommended(row):
                tooltip = (
                    f"<table>"
                    f"<tr><td><b>Final Consensus Rank:</b></td><td style='color: black;'>{row['Final Rank (Utility)']}</td></tr>"
                    f"<tr><td><b>Peak Detection Rate:</b></td><td style='color: black;'>{row['Peak Detection Rate (%)']}%</td></tr>"
                    f"<tr><td><b>Complexity:</b></td><td style='color: black;'>{row['Complexity']}</td></tr>"
                    f"<tr><td><b>Compatibility:</b></td><td style='color: black;'>{row['Compatibility']}</td></tr>"
                    f"</table>"
                )
                return tooltip

            if is_recommended(row):
                tooltip = (
                    f"<table>"
                    f"<tr><td><b>Final Consensus Rank:</b></td><td style='color: black;'>{row['Final Rank (Utility)']}</td></tr>"
                    f"<tr><td><b>Peak Detection Rate:</b></td><td style='color: black;'>{row['Peak Detection Rate (%)']}%</td></tr>"
                    f"<tr><td><b>Complexity:</b></td><td style='black'>{row['Complexity']}</td></tr>"
                    f"<tr><td><b>Compatibility:</b></td><td style='color: black'>{row['Compatibility']}</td></tr>"
                    f"</table>"
                )
                return tooltip

            if is_use_with_caution(row):
                tooltip = (f"<table>"
                    f"<tr><td><b>Final Consensus Rank:</b></td><td style='color: black;'>{row['Final Rank (Utility)']}</td></tr>"
			        f"<tr><td><b>Peak Detection Rate:</b></td><td style='color:black;'>{row['Peak Detection Rate (%)']}%</td></tr>"
			        f"<tr><td><b>Complexity:</b></td><td style='color: black;'>{row['Complexity']}</td></tr>"
			        f"<tr><td><b>Compatibility:</b></td><td style='color:black;'>{row['Compatibility']}</td></tr>"
			        f"</table>")

                return tooltip

            return '---'

        self.orthogonality_result_df["Final Recommendation"] = (
            self.orthogonality_result_df.apply(lambda row: set_final_recommendation(row), axis=1)
        )

        self.orthogonality_result_df["Final Recommendation tooltip"] = (
            self.orthogonality_result_df.apply(lambda row: set_final_recommendation_text(row), axis=1)
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

            mode_dict = get_symmetric_mode_dict(FEASABILITY, mode)

            compatibility_list.append(mode_dict['Compatibility'])

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

            mode_dict = get_symmetric_mode_dict(FEASABILITY,mode)

            complexity_list.append(mode_dict['Complexity'])

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
