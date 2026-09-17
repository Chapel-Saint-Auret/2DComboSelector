"""Regression tests for checked-in workbook fixtures."""

# Test inventory:
# - Verify loading of all inputs from the documented release workbook format.
# - Verify loading of a retention-only release workbook.
# - Verify rejection of a workbook with insufficient conditions.
# - Verify rejection of an invalid optional-sheet layout.
# - Verify exact condition-name matching across input sheets.
# - Verify rejection of duplicated condition headers.
# - Verify rejection of a missing condition header.
# - Verify safe ranking of a workbook containing one combination.
# - Verify pair generation, scores, diagnostics, and ranks for six combinations.

from __future__ import annotations

import unittest

from tests.helpers import CoreTestModel, get_fixture_path


class WorkbookRegressionTests(unittest.TestCase):
    """Verify workbook layouts that mirror the documented release format."""

    def _run_release_format_pipeline(self, fixture_name: str) -> CoreTestModel:
        """Run the standard metric and ranking pipeline for one release fixture."""
        # Resolve the checked-in workbook and create a GUI-free application model.
        model = CoreTestModel()
        workbook = get_fixture_path(fixture_name)
        metrics = [
            "Convex hull relative area",
            "Bin box counting",
            "Pearson Correlation",
            "Spearman Correlation",
            "Kendall Correlation",
        ]

        # Load mandatory and optional inputs using their documented sheet names.
        model.load_retention_time(workbook, "Retention Time Table")
        model.normalize_retention_time("min_max")
        model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")
        model.load_elution_composition_space_area_data(
            workbook, "Elution-Composition Range Table"
        )

        # Compute each metric through the same registry used by the application.
        for metric_name in metrics:
            model.om_function_map[metric_name]["func"]()

        # Group metrics, aggregate consensus scores, and generate final results.
        model.update_metric_dataframes(metrics)
        model.create_correlation_group("Values", threshold=0.0, tol=0.0)
        model.fill_correlation_group_average("Values")
        model.set_computed_score_dict(
            {
                "metric_list": metrics,
                "aggregation_method": "Mean",
                "score_used": "Default",
            }
        )
        model.update_table_results()
        # Return the completed model for scenario-specific assertions.
        return model

    def test_valid_release_format_workbook_loads_all_core_inputs(self) -> None:
        """The reference workbook must load retention and both optional inputs."""
        # Arrange the documented workbook containing every supported core input.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_valid.xlsx")

        # Act by loading retention, peak-capacity, and elution-domain sheets.
        model.load_retention_time(workbook, "Retention Time Table")
        model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")
        model.load_elution_composition_space_area_data(
            workbook, "Elution-Composition Range Table"
        )

        # Assert load status, generated pair, and values derived from optional data.
        self.assertEqual(model.get_status(), "elution_data_loaded")
        self.assertEqual(model.get_number_of_condition(), 2)
        self.assertEqual(model.get_number_of_combination(), 1)
        self.assertEqual(
            model.get_combination_df()["2D Combination"].tolist(),
            ["HILIC - BEH Amide - EtOH - pH 7 vs RPLC - C18 - ACN/H2O - pH 3"],
        )
        self.assertEqual(
            model.get_combination_df()["Hypothetical 2D Peak Capacity"].tolist(),
            [9520],
        )
        self.assertEqual(
            model.get_orthogonality_result_df()["Peak Capacity Utility"].tolist(),
            [1.0],
        )
        self.assertEqual(model.get_combination_df()["Elution Domain"].tolist(), [27])

    def test_retention_only_release_format_workbook_loads(self) -> None:
        """The retention-only template must load without optional-sheet data."""
        # Arrange a workbook that deliberately omits both optional sheets.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_retention_only.xlsx")

        # Act by loading only the mandatory retention table.
        model.load_retention_time(workbook, "Retention Time Table")

        # Assert successful pairing and explicit unavailable optional-input states.
        self.assertEqual(model.get_status(), "loaded")
        self.assertEqual(model.get_number_of_condition(), 2)
        self.assertEqual(model.get_number_of_combination(), 1)
        self.assertEqual(model.peak_capacity_status, "no_data")
        self.assertEqual(model.elution_data_status, "no_data")

    def test_bad_release_format_workbook_fails_on_insufficient_conditions(self) -> None:
        """A workbook with fewer than two conditions must be rejected."""
        # Arrange the invalid fixture containing only one chromatographic condition.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_bad.xlsx")

        # Act by attempting a normal retention import.
        model.load_retention_time(workbook, "Retention Time Table")

        # Assert the error state and the safely retained parsed input structure.
        self.assertEqual(model.get_status(), "error")
        self.assertEqual(model.get_number_of_condition(), 1)
        self.assertEqual(model.get_retention_time_df().columns.tolist(), ["Compound Name", "HILIC - BEH Amide - EtOH - pH 7"])

    def test_bad_release_format_workbook_rejects_invalid_optional_sheet_shape(self) -> None:
        """An optional sheet with an invalid layout must fail explicitly."""
        # Arrange the bad fixture and first load its valid retention sheet.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_bad.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")

        # Act and assert that its malformed optional sheet is rejected explicitly.
        with self.assertRaisesRegex(ValueError, "Table shape not recognized"):
            model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")

    def test_optional_sheet_condition_names_must_match_retention_sheet(self) -> None:
        """Optional-sheet headers must match the retention conditions exactly."""
        # Arrange a fixture whose optional headers differ from retention headers.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_mismatched_names.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")

        # Assert peak-capacity header validation independently.
        with self.assertRaisesRegex(
            ValueError, "Peak capacity condition names do not match"
        ):
            model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")

        # Assert elution-composition header validation independently.
        with self.assertRaisesRegex(
            ValueError, "Elution-composition condition names do not match"
        ):
            model.load_elution_composition_space_area_data(
                workbook, "Elution-Composition Range Table"
            )

    def test_release_format_workbook_rejects_duplicate_condition_names(self) -> None:
        """The release template must reject duplicated condition headers."""
        # Arrange the release fixture containing duplicated condition names.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_duplicate_conditions.xlsx")

        # Act by importing it through the validated retention loader.
        model.load_retention_time(workbook, "Retention Time Table")

        # Assert rejection and removal of ambiguous retention data.
        self.assertEqual(model.get_status(), "error")
        self.assertTrue(model.get_retention_time_df().empty)

    def test_release_format_workbook_rejects_missing_condition_header(self) -> None:
        """The release template must reject a missing condition header."""
        # Arrange the release fixture containing one absent condition header.
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_missing_condition_header.xlsx")

        # Act by importing it through the validated retention loader.
        model.load_retention_time(workbook, "Retention Time Table")

        # Assert the error state and the single valid condition retained for diagnosis.
        self.assertEqual(model.get_status(), "error")
        self.assertEqual(model.get_number_of_condition(), 1)
        self.assertEqual(
            model.get_retention_time_df().columns.tolist(),
            ["Compound Name", "HILIC - BEH Amide - EtOH - pH 7"],
        )

    def test_valid_release_format_ranking_regression_handles_single_combination(self) -> None:
        """A valid two-condition workbook must rank its single combination safely."""
        # Act by running the complete pipeline on the two-condition fixture.
        model = self._run_release_format_pipeline("release_format_valid.xlsx")
        results = model.get_orthogonality_result_df()

        # Assert the sole generated pair and all single-item ranking outputs.
        self.assertEqual(
            results["2D Combination"].tolist(),
            ["HILIC - BEH Amide - EtOH - pH 7 vs RPLC - C18 - ACN/H2O - pH 3"],
        )
        self.assertEqual(results["Orthogonality Rank"].tolist(), [1.0])
        self.assertEqual(results["Orthogonality Utility"].tolist(), [1.0])
        self.assertEqual(results["Final Rank"].tolist(), [1.0])
        self.assertEqual(results["Final Rank (Utility)"].tolist(), [1.0])
        self.assertEqual(results["Agreement Indicator"].tolist(), [100])
        self.assertTrue(results["Final Recommendation"].notna().all())

    def test_ranking_release_format_workbook_locks_pair_generation_and_ranking(self) -> None:
        """The ranking fixture must preserve pairs, scores, diagnostics, and ranks."""
        # Act by running the complete pipeline on the four-condition fixture.
        model = self._run_release_format_pipeline("release_format_ranking.xlsx")
        combinations = model.get_combination_df()
        results = model.get_orthogonality_result_df()

        # Assert exact pair generation and optional-criterion values.
        self.assertEqual(model.get_number_of_condition(), 4)
        self.assertEqual(model.get_number_of_combination(), 6)
        self.assertEqual(
            combinations["2D Combination"].tolist(),
            [
                "HILIC - BEH Amide - EtOH - pH 7 vs RPLC - C18 - ACN/H2O - pH 3",
                "HILIC - BEH Amide - EtOH - pH 7 vs SFC - Torus - MeOH - pH 6",
                "HILIC - BEH Amide - EtOH - pH 7 vs RPLC - Phenyl - MeOH/H2O - pH 5",
                "RPLC - C18 - ACN/H2O - pH 3 vs SFC - Torus - MeOH - pH 6",
                "RPLC - C18 - ACN/H2O - pH 3 vs RPLC - Phenyl - MeOH/H2O - pH 5",
                "SFC - Torus - MeOH - pH 6 vs RPLC - Phenyl - MeOH/H2O - pH 5",
            ],
        )
        self.assertEqual(
            combinations["Hypothetical 2D Peak Capacity"].tolist(),
            [7600, 8000, 8800, 9500, 10450, 11000],
        )
        self.assertEqual(combinations["Elution Domain"].tolist(), [22, 24, 27, 27, 30, 33])
        self.assertEqual(results["Final Rank"].tolist(), [6.0, 4.0, 3.0, 5.0, 2.0, 1.0])
        # The complete penalty product gives combinations 1 and 4 equal final
        # utility scores, so pandas assigns both the average rank of 5.5.
        self.assertEqual(
            results["Final Rank (Utility)"].tolist(), [5.5, 4.0, 3.0, 5.5, 2.0, 1.0]
        )

        # Extract and verify the three best combinations under the final rank.
        top_three = results.sort_values("Final Rank")["2D Combination"].head(3).tolist()
        self.assertEqual(
            top_three,
            [
                "SFC - Torus - MeOH - pH 6 vs RPLC - Phenyl - MeOH/H2O - pH 5",
                "RPLC - C18 - ACN/H2O - pH 3 vs RPLC - Phenyl - MeOH/H2O - pH 5",
                "HILIC - BEH Amide - EtOH - pH 7 vs RPLC - Phenyl - MeOH/H2O - pH 5",
            ],
        )

        # Verify the identity and diagnostics of the best-ranked combination.
        best = results.loc[results["Final Rank"].idxmin()]
        self.assertEqual(
            best["2D Combination"],
            "SFC - Torus - MeOH - pH 6 vs RPLC - Phenyl - MeOH/H2O - pH 5",
        )
        self.assertAlmostEqual(best["Orthogonality Utility"], 0.9)
        self.assertAlmostEqual(best["Coverage Score"], 0.734375)
        self.assertAlmostEqual(best["Distribution Score"], 1.0)
        self.assertAlmostEqual(best["Suggested Orthogonality Score"], 0.88575)
        self.assertAlmostEqual(best["Practical Peak Capacity"], 9743.25)
        self.assertEqual(int(best["Agreement Indicator"]), 100)

        # Metric-removal diagnostics must not leave their temporary scores in
        # the state used by the final practical peak-capacity calculation.
        for row_index, data_set in enumerate(model.orthogonality_score):
            expected_score = results["Suggested Orthogonality Score"].iloc[row_index]
            self.assertAlmostEqual(
                model.orthogonality_score[data_set]["suggested_score"],
                expected_score,
            )
            self.assertAlmostEqual(model.table_data[row_index][26], expected_score)


if __name__ == "__main__":
    unittest.main()
