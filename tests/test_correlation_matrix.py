"""Tests for safe correlation-matrix display helpers."""

from __future__ import annotations

import unittest

import pandas as pd

from combo_selector.core.orthogonality_utils import build_correlation_matrix_for_display


class CorrelationMatrixDisplayTests(unittest.TestCase):
    """Verify safe display behavior for degenerate correlation inputs."""

    def test_returns_identity_fallback_for_all_nan_correlation_matrix(self) -> None:
        source_df = pd.DataFrame(
            {
                "Metric A": [0.5],
                "Metric B": [0.2],
                "Metric C": [0.8],
            }
        )

        matrix, notice = build_correlation_matrix_for_display(source_df, "spearman")

        self.assertEqual(matrix.columns.tolist(), ["Metric A", "Metric B", "Metric C"])
        self.assertEqual(matrix.index.tolist(), ["Metric A", "Metric B", "Metric C"])
        self.assertEqual(matrix.values.tolist(), [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        self.assertIsNotNone(notice)

    def test_preserves_regular_correlation_matrix(self) -> None:
        source_df = pd.DataFrame(
            {
                "Metric A": [0.1, 0.4, 0.9],
                "Metric B": [0.2, 0.5, 0.8],
                "Metric C": [0.9, 0.4, 0.1],
            }
        )

        matrix, notice = build_correlation_matrix_for_display(source_df, "spearman")

        self.assertTrue(matrix.notna().all().all())
        self.assertIsNone(notice)


if __name__ == "__main__":
    unittest.main()
