"""Unit and integration-style tests for core pairing and scoring flows."""

from __future__ import annotations

import os
import unittest

from tests.helpers import (
    CoreTestModel,
    make_elution_table,
    make_peak_capacity_table,
    make_retention_df_four_conditions,
    make_retention_df_three_conditions,
    make_temp_workbook,
)


class CorePipelineTests(unittest.TestCase):
    """Cover pair generation, optional sheets, and non-GUI scoring flow."""

    def tearDown(self) -> None:
        for path in getattr(self, "_temp_paths", []):
            if os.path.exists(path):
                os.remove(path)

    def _track(self, path: str) -> str:
        self._temp_paths = getattr(self, "_temp_paths", [])
        self._temp_paths.append(path)
        return path

    def test_retention_import_creates_exact_expected_pairs(self) -> None:
        retention = make_retention_df_three_conditions()
        workbook = self._track(make_temp_workbook({"Retention": retention}))
        model = CoreTestModel()

        model.load_retention_time(workbook, "Retention")

        self.assertEqual(model.get_number_of_condition(), 3)
        self.assertEqual(model.get_number_of_combination(), 3)
        self.assertEqual(
            model.get_combination_df()["2D Combination"].tolist(),
            [
                "HILIC - BEH Amide - EtOH - pH 7 vs RPLC - C18 - ACN/H$_2$O - pH 3",
                "HILIC - BEH Amide - EtOH - pH 7 vs SFC - Torus - MeOH - pH 6",
                "RPLC - C18 - ACN/H$_2$O - pH 3 vs SFC - Torus - MeOH - pH 6",
            ],
        )

    def test_optional_peak_capacity_and_elution_tables_update_results(self) -> None:
        retention = make_retention_df_three_conditions()
        condition_names = retention.columns.tolist()[1:]
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": retention,
                    "Peak": (make_peak_capacity_table(condition_names, [85, 112, 96], with_label_column=True), False),
                    "Elution": (make_elution_table(condition_names, [45, 60, 50], with_label_column=True), False),
                }
            )
        )
        model = CoreTestModel()
        model.load_retention_time(workbook, "Retention")

        model.load_hypothetical_2d_peak_capacity(workbook, "Peak")
        model.load_elution_composition_space_area_data(workbook, "Elution")

        self.assertEqual(model.peak_capacity_status, "peak_capacity_loaded")
        self.assertEqual(model.elution_data_status, "elution_data_loaded")
        self.assertEqual(
            model.get_combination_df()["Hypothetical 2D Peak Capacity"].tolist(),
            [9520, 8160, 10752],
        )
        self.assertEqual(model.get_combination_df()["Elution Domain"].tolist(), [27, 22, 30])

    def test_mismatched_peak_capacity_conditions_fail_cleanly(self) -> None:
        retention = make_retention_df_three_conditions()
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": retention,
                    "Peak": (
                        make_peak_capacity_table(
                            retention.columns.tolist()[1:3],
                            [85, 112],
                        ),
                        False,
                    ),
                }
            )
        )
        model = CoreTestModel()
        model.load_retention_time(workbook, "Retention")

        with self.assertRaisesRegex(ValueError, "Number of condition does not match"):
            model.load_hypothetical_2d_peak_capacity(workbook, "Peak")

    def test_core_pipeline_builds_metrics_groups_scores_and_rankings(self) -> None:
        retention = make_retention_df_four_conditions()
        condition_names = retention.columns.tolist()[1:]
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": retention,
                    "Peak": (make_peak_capacity_table(condition_names, [80, 95, 100, 110], with_label_column=True), False),
                    "Elution": (make_elution_table(condition_names, [45, 50, 55, 60], with_label_column=True), False),
                }
            )
        )
        model = CoreTestModel()
        metrics = [
            "Convex hull relative area",
            "Bin box counting",
            "Pearson Correlation",
            "Spearman Correlation",
            "Kendall Correlation",
        ]

        model.load_retention_time(workbook, "Retention")
        model.normalize_retention_time("min_max")
        model.load_hypothetical_2d_peak_capacity(workbook, "Peak")
        model.load_elution_composition_space_area_data(workbook, "Elution")

        for metric_name in metrics:
            model.om_function_map[metric_name]["func"]()

        model.update_metric_dataframes(metrics)
        groups = model.create_correlation_group("Values", threshold=0.0, tol=0.0)
        model.fill_correlation_group_average("Values")
        model.set_computed_score_dict(
            {
                "metric_list": metrics,
                "aggregation_method": "Mean",
                "score_used": "Default",
            }
        )
        model.update_table_results()

        self.assertFalse(model.get_orthogonality_metric_df().empty)
        self.assertFalse(groups.empty)
        self.assertIn("Average Group Correllation", model.get_correlation_group_df().columns)
        self.assertIn("Orthogonality Rank", model.get_orthogonality_result_df().columns)
        self.assertIn("Final Rank", model.get_orthogonality_result_df().columns)
        self.assertIn("Final Recommendation", model.get_orthogonality_result_df().columns)
        self.assertTrue(model.get_orthogonality_result_df()["Final Rank"].notna().all())
        self.assertTrue(
            model.get_orthogonality_metric_df()["Convex hull relative area"].between(0, 1).all()
        )
        self.assertTrue(
            model.get_orthogonality_metric_df()["Bin box counting"].between(0, 1).all()
        )
        self.assertGreaterEqual(
            model.get_orthogonality_result_df()["Final Rank"].min(),
            1,
        )

    def test_core_pipeline_without_optional_sheets_still_updates_results(self) -> None:
        retention = make_retention_df_three_conditions()
        workbook = self._track(make_temp_workbook({"Retention": retention}))
        model = CoreTestModel()
        metrics = [
            "Convex hull relative area",
            "Bin box counting",
            "Pearson Correlation",
        ]

        model.load_retention_time(workbook, "Retention")
        model.normalize_retention_time("min_max")

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

        results = model.get_orthogonality_result_df()
        self.assertTrue(results["Final Rank"].notna().all())
        self.assertTrue(results["Final Rank (Utility)"].notna().all())
        self.assertTrue(results["Criterion Highlight"].notna().all())
        self.assertTrue(results["Final Recommendation"].notna().all())

    def test_update_table_results_requires_metric_groups(self) -> None:
        retention = make_retention_df_three_conditions()
        workbook = self._track(make_temp_workbook({"Retention": retention}))
        model = CoreTestModel()
        metrics = ["Convex hull relative area", "Bin box counting"]

        model.load_retention_time(workbook, "Retention")
        model.normalize_retention_time("min_max")

        for metric_name in metrics:
            model.om_function_map[metric_name]["func"]()

        model.update_metric_dataframes(metrics)
        model.set_computed_score_dict(
            {
                "metric_list": metrics,
                "aggregation_method": "Mean",
                "score_used": "Default",
            }
        )

        with self.assertRaisesRegex(
            ValueError, "Metric groups must be built before updating table results"
        ):
            model.update_table_results()


if __name__ == "__main__":
    unittest.main()
