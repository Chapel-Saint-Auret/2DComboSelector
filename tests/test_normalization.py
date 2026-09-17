"""Unit tests for normalization behavior and failure paths."""

# Test inventory:
# - Verify deterministic min-max normalization values.
# - Verify void-max normalization using condition-specific void times.
# - Verify WOSEL normalization using condition-specific gradient end times.
# - Verify that void-max rejects missing reference data.
# - Verify that WOSEL rejects missing reference data.

from __future__ import annotations

import os
import unittest

import pandas as pd

from tests.helpers import CoreTestModel, make_retention_df_three_conditions, make_temp_workbook


class NormalizationTests(unittest.TestCase):
    """Verify deterministic normalization outputs."""

    def tearDown(self) -> None:
        """Remove temporary input workbooks created by normalization tests."""
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

    def _load_model(self) -> CoreTestModel:
        """Return a model loaded with the standard three-condition fixture."""
        # Create and track the common workbook used by normalization scenarios.
        workbook = self._track(make_temp_workbook({"Retention": make_retention_df_three_conditions()}))
        # Load raw retention times but leave normalization to each test.
        model = CoreTestModel()
        model.load_retention_time(workbook, "Retention")
        return model

    def test_min_max_normalization_matches_expected_values(self) -> None:
        """Min–max normalization must reproduce expected zero-to-one values."""
        # Arrange the common raw retention-time model.
        model = self._load_model()

        # Act by applying column-wise min-max normalization.
        model.normalize_retention_time("min_max")
        data = model.get_normalized_retention_time_df()

        # Define the analytical values expected for each condition.
        expected = {
            "HILIC - BEH Amide - EtOH - pH 7": [0.0, 1 / 3, 2 / 3, 1.0],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [0.0, 1 / 6, 2 / 3, 1.0],
            "SFC - Torus - MeOH - pH 6": [0.0, 1 / 6, 0.5, 1.0],
        }

        # Assert state changes and every normalized numerical value.
        self.assertEqual(model.get_status(), "normalized")
        self.assertTrue(model.get_is_normalized())
        for column, values in expected.items():
            for actual, expected_value in zip(data[column].tolist(), values):
                self.assertAlmostEqual(actual, expected_value, places=7)

    def test_void_max_normalization_matches_expected_values(self) -> None:
        """Void–max normalization must use the supplied void-time references."""
        # Arrange raw data and condition-specific void-time references.
        model = self._load_model()
        model.void_time_df = pd.DataFrame(
            [[0.5, 3.5, 1.0]],
            columns=model.get_retention_time_df().columns.tolist()[2:],
        )

        # Act by applying void-to-maximum normalization.
        model.normalize_retention_time("void_max")
        data = model.get_normalized_retention_time_df()

        # Define the analytically calculated normalized values.
        expected = {
            "HILIC - BEH Amide - EtOH - pH 7": [1 / 7, 3 / 7, 5 / 7, 1.0],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [1 / 13, 3 / 13, 9 / 13, 1.0],
            "SFC - Torus - MeOH - pH 6": [1 / 7, 2 / 7, 4 / 7, 1.0],
        }

        # Assert every condition and analyte value within numerical tolerance.
        for column, values in expected.items():
            for actual, expected_value in zip(data[column].tolist(), values):
                self.assertAlmostEqual(actual, expected_value, places=7)

    def test_wosel_normalization_matches_expected_values(self) -> None:
        """WOSEL normalization must use the supplied gradient-end references."""
        # Arrange raw data with both void-time and gradient-end references.
        model = self._load_model()
        condition_names = model.get_retention_time_df().columns.tolist()[2:]
        model.void_time_df = pd.DataFrame([[0.5, 3.5, 1.0]], columns=condition_names)
        model.gradient_end_time_df = pd.DataFrame([[5.0, 12.0, 8.0]], columns=condition_names)

        # Act by applying the WOSEL normalization formula.
        model.normalize_retention_time("wosel")
        data = model.get_normalized_retention_time_df()

        # Define the analytically calculated WOSEL values.
        expected = {
            "HILIC - BEH Amide - EtOH - pH 7": [1 / 9, 1 / 3, 5 / 9, 7 / 9],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [1 / 17, 3 / 17, 9 / 17, 13 / 17],
            "SFC - Torus - MeOH - pH 6": [1 / 7, 2 / 7, 4 / 7, 1.0],
        }

        # Assert every condition and analyte value within numerical tolerance.
        for column, values in expected.items():
            for actual, expected_value in zip(data[column].tolist(), values):
                self.assertAlmostEqual(actual, expected_value, places=7)

    def test_void_max_requires_matching_void_time_data(self) -> None:
        """Void–max normalization must reject missing void-time information."""
        # Arrange a model without the void-time input required by void-max.
        model = self._load_model()

        # Act and assert that the missing prerequisite is reported clearly.
        with self.assertRaisesRegex(ValueError, "Void time data is not loaded"):
            model.normalize_retention_time("void_max")

    def test_wosel_requires_gradient_end_time_data(self) -> None:
        """WOSEL normalization must reject missing gradient-end information."""
        # Arrange void times but intentionally omit gradient-end times.
        model = self._load_model()
        condition_names = model.get_retention_time_df().columns.tolist()[2:]
        model.void_time_df = pd.DataFrame([[0.5, 3.5, 1.0]], columns=condition_names)

        # Act and assert that WOSEL rejects the incomplete reference data.
        with self.assertRaisesRegex(ValueError, "Gradient end time data is not loaded"):
            model.normalize_retention_time("wosel")


if __name__ == "__main__":
    unittest.main()
