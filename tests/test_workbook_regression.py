"""Regression tests for checked-in workbook fixtures."""

from __future__ import annotations

import unittest

from tests.helpers import CoreTestModel, get_fixture_path


class WorkbookRegressionTests(unittest.TestCase):
    """Verify workbook layouts that mirror the documented release format."""

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
            ["HILIC - BEH Amide - EtOH - pH 7 vs RPLC - C18 - ACN/H$_2$O - pH 3"],
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


if __name__ == "__main__":
    unittest.main()
