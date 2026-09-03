"""Fast unit tests for Excel parsing helpers and import rules."""

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
        for path in getattr(self, "_temp_paths", []):
            if os.path.exists(path):
                os.remove(path)

    def _track(self, path: str) -> str:
        self._temp_paths = getattr(self, "_temp_paths", [])
        self._temp_paths.append(path)
        return path

    def test_load_table_with_header_anywhere_skips_leading_rows(self) -> None:
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

        loaded = load_table_with_header_anywhere(workbook, "Retention")

        self.assertEqual(list(loaded.columns), ["Compound", "Cond A", "Cond B", "Cond C"])
        self.assertEqual(len(loaded), 2)

    def test_load_retention_time_renames_first_column_to_compound_name(self) -> None:
        workbook = self._track(make_temp_workbook({"Retention": make_retention_df_three_conditions()}))
        model = CoreTestModel()

        model.load_retention_time(workbook, "Retention")

        self.assertEqual(model.get_status(), "loaded")
        self.assertEqual(model.get_retention_time_df().columns[1], "Compound Name")
        self.assertEqual(model.get_compound_name_list(), ["Caffeine", "Quinine", "Rutin", "Theobromine"])

    def test_load_table_with_header_anywhere_rejects_duplicate_headers_when_requested(self) -> None:
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

        with self.assertRaisesRegex(ValueError, "Duplicate column names found"):
            load_table_with_header_anywhere(workbook, "Retention", auto_fix_duplicates=False)

    def test_load_simple_table_accepts_optional_label_column_from_release_format(self) -> None:
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

        loaded = load_simple_table(workbook, "Peak")

        self.assertEqual(list(loaded.columns), conditions)
        self.assertEqual(loaded.iloc[0].tolist(), [85, 112, 96])

    def test_load_simple_table_ignores_surrounding_empty_rows_and_columns(self) -> None:
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

        loaded = load_simple_table(workbook, "Peak")

        self.assertEqual(list(loaded.columns), ["Cond A", "Cond B"])
        self.assertEqual(loaded.iloc[0].tolist(), [85, 112])

    def test_load_simple_table_rejects_unrecognized_shape(self) -> None:
        path = self._track(make_temp_workbook({"Invalid": (pd.DataFrame([[1], [2], [3]]), False)}))

        with self.assertRaisesRegex(ValueError, "Table shape not recognized"):
            load_simple_table(path, "Invalid")

    def test_load_retention_time_rejects_non_numeric_condition_values(self) -> None:
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

        model.load_retention_time(workbook, "Retention")

        self.assertEqual(model.get_status(), "error")

    def test_load_peak_capacity_rejects_non_numeric_values(self) -> None:
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

        with self.assertRaisesRegex(ValueError, "Peak capacity data contains non-numeric values"):
            model.load_hypothetical_2d_peak_capacity(workbook, "Peak")

    def test_load_elution_table_rejects_non_numeric_values(self) -> None:
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

        with self.assertRaisesRegex(ValueError, "Elution-composition data contains non-numeric values"):
            model.load_elution_composition_space_area_data(workbook, "Elution")


if __name__ == "__main__":
    unittest.main()
