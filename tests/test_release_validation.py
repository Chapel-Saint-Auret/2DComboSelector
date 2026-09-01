import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from combo_selector.core.data_manager import DataManager
from combo_selector.app_profile import resolve_app_profile
from combo_selector.core.orthogonality_utils import (
    load_simple_table,
    load_table_with_header_anywhere,
)
from combo_selector.utils import get_version


class DummyDataManager(DataManager):
    pass


class ReleaseValidationTests(unittest.TestCase):
    def _create_excel_file(self, frame: pd.DataFrame, sheet_name: str = "Sheet1") -> Path:
        temp_dir = Path(tempfile.mkdtemp())
        file_path = temp_dir / "test.xlsx"
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            frame.to_excel(writer, sheet_name=sheet_name, header=False, index=False)
        return file_path

    def test_get_version_matches_pyproject(self):
        pyproject_path = REPO_ROOT / "pyproject.toml"
        version = None

        for line in pyproject_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("version"):
                version = stripped.split("=", 1)[1].strip().strip('"')
                break

        self.assertIsNotNone(version)
        self.assertEqual(get_version(), version)

    def test_resolve_app_profile_defaults_to_advanced(self):
        self.assertEqual(resolve_app_profile(None).key, "advanced")
        self.assertEqual(resolve_app_profile("unknown").key, "advanced")

    def test_resolve_app_profile_supports_user_mode(self):
        profile = resolve_app_profile("user")

        self.assertEqual(profile.key, "user")
        self.assertFalse(profile.show_pairwise_page)
        self.assertFalse(profile.show_redundancy_page)
        self.assertFalse(profile.allow_custom_results_settings)

    def test_load_simple_table_supports_horizontal_layout(self):
        frame = pd.DataFrame([["Condition A", "Condition B"], [100, 200]])
        file_path = self._create_excel_file(frame)

        loaded = load_simple_table(file_path)

        self.assertEqual(loaded.columns.tolist(), ["Condition A", "Condition B"])
        self.assertEqual(loaded.iloc[0].tolist(), [100, 200])

    def test_load_simple_table_supports_vertical_layout(self):
        frame = pd.DataFrame([["Condition A", 100], ["Condition B", 200]])
        file_path = self._create_excel_file(frame)

        loaded = load_simple_table(file_path)

        self.assertEqual(loaded.columns.tolist(), ["Condition A", "Condition B"])
        self.assertEqual(loaded.iloc[0].tolist(), [100, 200])

    def test_load_table_with_header_anywhere_skips_preamble_rows(self):
        temp_dir = Path(tempfile.mkdtemp())
        file_path = temp_dir / "retention.xlsx"
        raw = pd.DataFrame(
            [
                ["Notes", "ignored", None, None],
                [None, None, None, None],
                ["Peak #", "Compound Name", "Cond A", "Cond B"],
                [1, "Caffeine", 1.2, 2.4],
                [2, "Quinine", 1.8, 3.1],
            ]
        )
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            raw.to_excel(writer, sheet_name="RT", header=False, index=False)

        loaded = load_table_with_header_anywhere(file_path, sheetname="RT")

        self.assertEqual(
            loaded.columns.tolist(), ["Peak #", "Compound Name", "Cond A", "Cond B"]
        )
        self.assertEqual(len(loaded), 2)

    def test_retention_time_validation_accepts_complete_loaded_data(self):
        model = DummyDataManager()
        model.init_data()
        model.retention_time_df = pd.DataFrame(
            {
                "Peak #": [1, 2],
                "Compound Name": ["Caffeine", "Quinine"],
                "Cond A": [1.2, 1.8],
                "Cond B": [2.4, 3.1],
            }
        )
        model.compound_name_list = ["Caffeine", "Quinine"]
        model.nb_peaks = 2

        self.assertIsNone(model.get_retention_time_validation_error(require_pairs=True))
        self.assertTrue(model.has_valid_loaded_retention_time_data(require_pairs=True))

    def test_retention_time_validation_rejects_missing_condition_columns(self):
        model = DummyDataManager()
        model.init_data()
        model.retention_time_df = pd.DataFrame(
            {
                "Peak #": [1, 2],
                "Compound Name": ["Caffeine", "Quinine"],
            }
        )
        model.compound_name_list = ["Caffeine", "Quinine"]
        model.nb_peaks = 2

        self.assertEqual(
            model.get_retention_time_validation_error(require_pairs=True),
            "Retention time data does not contain any condition columns.",
        )


if __name__ == "__main__":
    unittest.main()
