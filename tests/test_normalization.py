"""Unit tests for normalization behavior and failure paths."""

from __future__ import annotations

import os
import unittest

import pandas as pd

from tests.helpers import CoreTestModel, make_retention_df_three_conditions, make_temp_workbook


class NormalizationTests(unittest.TestCase):
    """Verify deterministic normalization outputs."""

    def tearDown(self) -> None:
        for path in getattr(self, "_temp_paths", []):
            if os.path.exists(path):
                os.remove(path)

    def _track(self, path: str) -> str:
        self._temp_paths = getattr(self, "_temp_paths", [])
        self._temp_paths.append(path)
        return path

    def _load_model(self) -> CoreTestModel:
        workbook = self._track(make_temp_workbook({"Retention": make_retention_df_three_conditions()}))
        model = CoreTestModel()
        model.load_retention_time(workbook, "Retention")
        return model

    def test_min_max_normalization_matches_expected_values(self) -> None:
        model = self._load_model()

        model.normalize_retention_time("min_max")
        data = model.get_normalized_retention_time_df()

        expected = {
            "HILIC - BEH Amide - EtOH - pH 7": [0.0, 1 / 3, 2 / 3, 1.0],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [0.0, 1 / 6, 2 / 3, 1.0],
            "SFC - Torus - MeOH - pH 6": [0.0, 1 / 6, 0.5, 1.0],
        }

        self.assertEqual(model.get_status(), "normalized")
        self.assertTrue(model.get_is_normalized())
        for column, values in expected.items():
            for actual, expected_value in zip(data[column].tolist(), values):
                self.assertAlmostEqual(actual, expected_value, places=7)

    def test_void_max_normalization_matches_expected_values(self) -> None:
        model = self._load_model()
        model.void_time_df = pd.DataFrame(
            [[0.5, 3.5, 1.0]],
            columns=model.get_retention_time_df().columns.tolist()[2:],
        )

        model.normalize_retention_time("void_max")
        data = model.get_normalized_retention_time_df()

        expected = {
            "HILIC - BEH Amide - EtOH - pH 7": [1 / 7, 3 / 7, 5 / 7, 1.0],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [1 / 13, 3 / 13, 9 / 13, 1.0],
            "SFC - Torus - MeOH - pH 6": [1 / 7, 2 / 7, 4 / 7, 1.0],
        }

        for column, values in expected.items():
            for actual, expected_value in zip(data[column].tolist(), values):
                self.assertAlmostEqual(actual, expected_value, places=7)

    def test_wosel_normalization_matches_expected_values(self) -> None:
        model = self._load_model()
        condition_names = model.get_retention_time_df().columns.tolist()[2:]
        model.void_time_df = pd.DataFrame([[0.5, 3.5, 1.0]], columns=condition_names)
        model.gradient_end_time_df = pd.DataFrame([[5.0, 12.0, 8.0]], columns=condition_names)

        model.normalize_retention_time("wosel")
        data = model.get_normalized_retention_time_df()

        expected = {
            "HILIC - BEH Amide - EtOH - pH 7": [1 / 9, 1 / 3, 5 / 9, 7 / 9],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [1 / 17, 3 / 17, 9 / 17, 13 / 17],
            "SFC - Torus - MeOH - pH 6": [1 / 7, 2 / 7, 4 / 7, 1.0],
        }

        for column, values in expected.items():
            for actual, expected_value in zip(data[column].tolist(), values):
                self.assertAlmostEqual(actual, expected_value, places=7)

    def test_void_max_requires_matching_void_time_data(self) -> None:
        model = self._load_model()

        with self.assertRaisesRegex(ValueError, "Void time data is not loaded"):
            model.normalize_retention_time("void_max")

    def test_wosel_requires_gradient_end_time_data(self) -> None:
        model = self._load_model()
        condition_names = model.get_retention_time_df().columns.tolist()[2:]
        model.void_time_df = pd.DataFrame([[0.5, 3.5, 1.0]], columns=condition_names)

        with self.assertRaisesRegex(ValueError, "Gradient end time data is not loaded"):
            model.normalize_retention_time("wosel")


if __name__ == "__main__":
    unittest.main()
