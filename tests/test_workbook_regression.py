"""Regression tests for checked-in workbook fixtures."""

from __future__ import annotations

import unittest

from tests.helpers import CoreTestModel, get_fixture_path


class WorkbookRegressionTests(unittest.TestCase):
    """Verify workbook layouts that mirror the documented release format."""

    def _run_release_format_valid_pipeline(self) -> CoreTestModel:
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_valid.xlsx")
        metrics = [
            "Convex hull relative area",
            "Bin box counting",
            "Pearson Correlation",
            "Spearman Correlation",
            "Kendall Correlation",
        ]

        model.load_retention_time(workbook, "Retention Time Table")
        model.normalize_retention_time("min_max")
        model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")
        model.load_elution_composition_space_area_data(
            workbook, "Elution-Composition Range Table"
        )

        for metric_name in metrics:
            model.om_function_map[metric_name]["func"]()

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
        return model

    def test_valid_release_format_workbook_loads_all_core_inputs(self) -> None:
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_valid.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")
        model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")
        model.load_elution_composition_space_area_data(
            workbook, "Elution-Composition Range Table"
        )

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
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_retention_only.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")

        self.assertEqual(model.get_status(), "loaded")
        self.assertEqual(model.get_number_of_condition(), 2)
        self.assertEqual(model.get_number_of_combination(), 1)
        self.assertEqual(model.peak_capacity_status, "no_data")
        self.assertEqual(model.elution_data_status, "no_data")

    def test_bad_release_format_workbook_fails_on_insufficient_conditions(self) -> None:
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_bad.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")

        self.assertEqual(model.get_status(), "error")
        self.assertEqual(model.get_number_of_condition(), 1)
        self.assertEqual(model.get_retention_time_df().columns.tolist(), ["Compound Name", "HILIC - BEH Amide - EtOH - pH 7"])

    def test_bad_release_format_workbook_rejects_invalid_optional_sheet_shape(self) -> None:
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_bad.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")

        with self.assertRaisesRegex(ValueError, "Table shape not recognized"):
            model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")

    def test_optional_sheet_condition_names_must_match_retention_sheet(self) -> None:
        model = CoreTestModel()
        workbook = get_fixture_path("release_format_mismatched_names.xlsx")

        model.load_retention_time(workbook, "Retention Time Table")

        with self.assertRaisesRegex(
            ValueError, "Peak capacity condition names do not match"
        ):
            model.load_hypothetical_2d_peak_capacity(workbook, "1D peak capacity table")

        with self.assertRaisesRegex(
            ValueError, "Elution-composition condition names do not match"
        ):
            model.load_elution_composition_space_area_data(
                workbook, "Elution-Composition Range Table"
            )

    def test_valid_release_format_ranking_regression_handles_single_combination(self) -> None:
        model = self._run_release_format_valid_pipeline()
        results = model.get_orthogonality_result_df()

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


if __name__ == "__main__":
    unittest.main()
