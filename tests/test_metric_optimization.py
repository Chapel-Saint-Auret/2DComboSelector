"""Regression tests for orthogonality-metric performance optimizations."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from combo_selector.core import metric_engine
from combo_selector.core.orthogonality_utils import compute_percent_fit_for_set

from tests.helpers import (
    CoreTestModel,
    make_retention_df_four_conditions,
    make_temp_workbook,
)


class MetricOptimizationTests(unittest.TestCase):
    """Ensure shared work is reused without changing metric outputs."""

    def setUp(self) -> None:
        self.workbook = make_temp_workbook(
            {"Retention": make_retention_df_four_conditions()}
        )
        self.model = CoreTestModel()
        self.model.load_retention_time(self.workbook, "Retention")
        self.model.normalize_retention_time("min_max")

    def tearDown(self) -> None:
        if os.path.exists(self.workbook):
            os.remove(self.workbook)

    def test_grid_metrics_share_one_mask_per_set_and_bin_setting(self) -> None:
        set_count = len(self.model.orthogonality_dict)

        with patch.object(
            metric_engine,
            "compute_bin_box_mask_color",
            wraps=metric_engine.compute_bin_box_mask_color,
        ) as compute_mask:
            self.model.compute_bin_box()
            self.model.compute_gilar_watson_metric()
            self.model.compute_modeling_approach()

            self.assertEqual(compute_mask.call_count, set_count)

            self.model.update_num_bins(self.model.bin_number + 1)
            self.model.compute_bin_box()
            self.assertEqual(compute_mask.call_count, 2 * set_count)

    def test_nnd_mean_reuses_computed_component_metrics(self) -> None:
        self.model.compute_ndd()

        with patch.object(
            self.model, "compute_ndd", wraps=self.model.compute_ndd
        ) as compute_ndd:
            self.model.compute_nnd_mean()

        compute_ndd.assert_not_called()

    def test_percent_fit_keeps_regression_value(self) -> None:
        set_key, result = compute_percent_fit_for_set(
            "Set 1", self.model.orthogonality_dict["Set 1"]
        )

        self.assertEqual(set_key, "Set 1")
        self.assertAlmostEqual(
            result["percent_fit"]["value"], 0.5123728892197839, places=12
        )


if __name__ == "__main__":
    unittest.main()
