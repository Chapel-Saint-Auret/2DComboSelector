"""Fast unit tests for Excel parsing helpers and import rules."""

# Test inventory:
# - Verify detection of a table located below introductory spreadsheet rows.
# - Verify standardization of the retention-table compound-name column.
# - Verify rejection of duplicated condition headers in strict mode.
# - Verify the documented optional-table layout with a leading label column.
# - Verify removal of empty rows and columns surrounding optional input data.
# - Verify rejection of an unsupported optional-table shape.
# - Verify rejection of non-numerical retention-time values.
# - Verify rejection of non-numerical peak-capacity values.
# - Verify rejection of non-numerical elution-composition values.

from __future__ import annotations

import os
import unittest

import pandas as pd

from combo_selector.core.orthogonality_utils import (
    load_simple_table,
    load_table_with_header_anywhere,
)

from tests.helpers import (
    CoreTestModel,
    make_peak_capacity_table,
    make_retention_df_three_conditions,
    write_workbook,
    make_temp_workbook,
)


class ExcelParsingTests(unittest.TestCase):
    """Cover workbook parsing and retention-import expectations."""

    def tearDown(self) -> None:
        """Remove temporary spreadsheets created by parsing tests."""
        # Clean every workbook registered by the current test instance.
        for path in getattr(self, "_temp_paths", []):
            if os.path.exists(path):
                os.remove(path)

    def _track(self, path: str) -> str:
        """Register a temporary workbook for cleanup and return its path."""
        # Create the registry lazily, then retain the new temporary path.
        self._temp_paths = getattr(self, "_temp_paths", [])
        self._temp_paths.append(path)
        return path

    def test_load_table_with_header_anywhere_skips_leading_rows(self) -> None:
        """Header detection must ignore explanatory rows above the real table."""
        # Arrange a sheet with an empty row before its real header.
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": (
                        pd.DataFrame(
                            [
                                [None, None, None, None],
                                ["Compound", "Cond A", "Cond B", "Cond C"],
                                ["A", 1.0, 2.0, 3.0],
                                ["B", 4.0, 5.0, 6.0],
                            ]
                        ),
                        False,
                    )
                }
            )
        )

        # Act by asking the parser to locate the header automatically.
        loaded = load_table_with_header_anywhere(workbook, "Retention")

        # Assert that only the two data rows and detected headers remain.
        self.assertEqual(list(loaded.columns), ["Compound", "Cond A", "Cond B", "Cond C"])
        self.assertEqual(len(loaded), 2)

    def test_load_retention_time_renames_first_column_to_compound_name(self) -> None:
        """Retention import must standardize the first column as compound names."""
        # Arrange a valid retention workbook with a generic first-column name.
        workbook = self._track(make_temp_workbook({"Retention": make_retention_df_three_conditions()}))
        model = CoreTestModel()

        # Act by importing it through the production model API.
        model.load_retention_time(workbook, "Retention")

        # Assert successful loading and standardized compound metadata.
        self.assertEqual(model.get_status(), "loaded")
        self.assertEqual(model.get_retention_time_df().columns[1], "Compound Name")
        self.assertEqual(model.get_compound_name_list(), ["Caffeine", "Quinine", "Rutin", "Theobromine"])

    def test_load_table_with_header_anywhere_rejects_duplicate_headers_when_requested(self) -> None:
        """Strict header parsing must reject duplicated condition names."""
        # Arrange two condition columns carrying the same header.
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": pd.DataFrame(
                        [["A", 1.0, 3.0], ["B", 2.0, 4.0]],
                        columns=["Compound", "Cond A", "Cond A"],
                    )
                }
            )
        )

        # Act and assert that strict parsing rejects ambiguous columns.
        with self.assertRaisesRegex(ValueError, "Duplicate column names found"):
            load_table_with_header_anywhere(workbook, "Retention", auto_fix_duplicates=False)

    def test_load_simple_table_accepts_optional_label_column_from_release_format(self) -> None:
        """Optional one-row inputs must accept the documented leading label column."""
        # Arrange the documented optional layout with a descriptive label cell.
        retention = make_retention_df_three_conditions()
        conditions = retention.columns.tolist()[1:]
        workbook = self._track(
            make_temp_workbook(
                {
                    "Peak": (
                        make_peak_capacity_table(conditions, [85, 112, 96], with_label_column=True),
                        False,
                    )
                }
            )
        )

        # Act by parsing the optional single-row table.
        loaded = load_simple_table(workbook, "Peak")

        # Assert that the label is removed while conditions and values are retained.
        self.assertEqual(list(loaded.columns), conditions)
        self.assertEqual(loaded.iloc[0].tolist(), [85, 112, 96])

    def test_load_simple_table_ignores_surrounding_empty_rows_and_columns(self) -> None:
        """Optional-table parsing must ignore blank rows and columns around data."""
        # Arrange valid optional data surrounded by fully empty rows and columns.
        workbook = self._track(
            make_temp_workbook(
                {
                    "Peak": (
                        pd.DataFrame(
                            [
                                [None, None, None, None, None],
                                [None, None, "Cond A", "Cond B", None],
                                [None, "Peak capacity", 85, 112, None],
                                [None, None, None, None, None],
                            ]
                        ),
                        False,
                    )
                }
            )
        )

        # Act by parsing and trimming the optional table.
        loaded = load_simple_table(workbook, "Peak")

        # Assert that only meaningful headers and values remain.
        self.assertEqual(list(loaded.columns), ["Cond A", "Cond B"])
        self.assertEqual(loaded.iloc[0].tolist(), [85, 112])

    def test_load_simple_table_rejects_unrecognized_shape(self) -> None:
        """Optional input with an unsupported layout must raise a clear error."""
        # Arrange a three-row single-column layout unsupported by the parser.
        path = self._track(make_temp_workbook({"Invalid": (pd.DataFrame([[1], [2], [3]]), False)}))

        # Act and assert that the parser reports the unsupported shape.
        with self.assertRaisesRegex(ValueError, "Table shape not recognized"):
            load_simple_table(path, "Invalid")

    def test_load_retention_time_rejects_non_numeric_condition_values(self) -> None:
        """Retention-time condition columns must contain only numerical values."""
        # Arrange a retention column containing one non-numerical value.
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": pd.DataFrame(
                        {
                            "Analyte": ["A", "B"],
                            "Cond A": [1.0, "bad"],
                            "Cond B": [2.0, 3.0],
                        }
                    )
                }
            )
        )
        model = CoreTestModel()

        # Act by importing through the model's validated loading path.
        model.load_retention_time(workbook, "Retention")

        # Assert that validation places the model in its error state.
        self.assertEqual(model.get_status(), "error")

    def test_load_peak_capacity_rejects_non_numeric_values(self) -> None:
        """Peak-capacity input must reject non-numerical condition values."""
        # Arrange peak-capacity data containing one invalid text value.
        retention = make_retention_df_three_conditions()
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": retention,
                    "Peak": (
                        pd.DataFrame(
                            [
                                [None, *retention.columns.tolist()[1:]],
                                ["Peak capacity", 85, "bad", 96],
                            ]
                        ),
                        False,
                    ),
                }
            )
        )
        model = CoreTestModel()
        model.load_retention_time(workbook, "Retention")

        # Act and assert that optional-input validation identifies the problem.
        with self.assertRaisesRegex(ValueError, "Peak capacity data contains non-numeric values"):
            model.load_hypothetical_2d_peak_capacity(workbook, "Peak")

    def test_load_elution_table_rejects_non_numeric_values(self) -> None:
        """Elution-composition input must reject non-numerical condition values."""
        # Arrange elution-composition data containing one invalid text value.
        retention = make_retention_df_three_conditions()
        workbook = self._track(
            make_temp_workbook(
                {
                    "Retention": retention,
                    "Elution": (
                        pd.DataFrame(
                            [
                                [None, *retention.columns.tolist()[1:]],
                                ["Elution-Composition Ranges", 45, 60, "bad"],
                            ]
                        ),
                        False,
                    ),
                }
            )
        )
        model = CoreTestModel()
        model.load_retention_time(workbook, "Retention")

        # Act and assert that optional-input validation identifies the problem.
        with self.assertRaisesRegex(ValueError, "Elution-composition data contains non-numeric values"):
            model.load_elution_composition_space_area_data(workbook, "Elution")


if __name__ == "__main__":
    unittest.main()
