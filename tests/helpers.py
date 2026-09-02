"""Shared helpers for core logic tests."""

from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd

from combo_selector.core.data_manager import DataManager
from combo_selector.core.metric_engine import MetricEngine
from combo_selector.core.redundancy import Redundancy
from combo_selector.core.results_builder import ResultsBuilder
from combo_selector.core.scoring import Scoring


class DummyNanPolicyDialog:
    """Fail fast if a test fixture unexpectedly triggers the GUI NaN flow."""

    def exec_(self) -> None:
        raise AssertionError("Tests should use explicit NaN fixtures when covering dialog flows.")


class CoreTestModel(DataManager, MetricEngine, Redundancy, Scoring, ResultsBuilder):
    """Core-only model harness without Qt dependencies."""

    def __init__(self) -> None:
        self.nan_policy_dialog = DummyNanPolicyDialog()
        self.init_data()

    def init_data(self) -> None:
        """Reset data and metric registry together, like the full app expects."""
        DataManager.init_data(self)
        self.reset_om_status_computation_state()


def write_workbook(path: Path, sheets: dict[str, tuple[pd.DataFrame, bool] | pd.DataFrame]) -> Path:
    """Write an Excel workbook for tests.

    Each value can be either a DataFrame (written with headers) or a
    ``(DataFrame, write_header)`` tuple.
    """
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, spec in sheets.items():
            if isinstance(spec, tuple):
                frame, header = spec
            else:
                frame, header = spec, True
            frame.to_excel(writer, sheet_name=sheet_name, index=False, header=header)
    return path


def make_temp_workbook(sheets: dict[str, tuple[pd.DataFrame, bool] | pd.DataFrame]) -> str:
    """Create a temporary workbook and return its path."""
    handle = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    handle.close()
    write_workbook(Path(handle.name), sheets)
    return handle.name


def make_retention_df_three_conditions() -> pd.DataFrame:
    """Return a small deterministic retention-time fixture."""
    return pd.DataFrame(
        {
            "Analyte": ["Caffeine", "Quinine", "Rutin", "Theobromine"],
            "HILIC - BEH Amide - EtOH - pH 7": [1.0, 2.0, 3.0, 4.0],
            "RPLC - C18 - ACN/H$_2$O - pH 3": [4.0, 5.0, 8.0, 10.0],
            "SFC - Torus - MeOH - pH 6": [2.0, 3.0, 5.0, 8.0],
        }
    )


def make_retention_df_four_conditions() -> pd.DataFrame:
    """Return a fixture with enough variety for metric and ranking tests."""
    return pd.DataFrame(
        {
            "Analyte": ["Caffeine", "Quinine", "Rutin", "Theobromine", "Naringin"],
            "HILIC - BEH Amide - EtOH - pH 7": [1.0, 2.0, 3.0, 4.0, 5.0],
            "RPLC - C18 - ACN/H2O - pH 3": [5.0, 1.0, 4.0, 2.0, 3.0],
            "SFC - Torus - MeOH - pH 6": [2.0, 4.0, 1.0, 5.0, 3.0],
            "RPLC - Phenyl - MeOH/H2O - pH 5": [3.0, 5.0, 2.0, 1.0, 4.0],
        }
    )


def make_peak_capacity_table(condition_names: list[str], values: list[float], with_label_column: bool = False) -> pd.DataFrame:
    """Return a horizontal simple-table fixture for peak-capacity-like inputs."""
    if with_label_column:
        return pd.DataFrame(
            [
                [None, *condition_names],
                ["Peak capacity", *values],
            ]
        )
    return pd.DataFrame([condition_names, values])


def make_elution_table(condition_names: list[str], values: list[float], with_label_column: bool = False) -> pd.DataFrame:
    """Return a horizontal simple-table fixture for elution-composition inputs."""
    if with_label_column:
        return pd.DataFrame(
            [
                [None, *condition_names],
                ["Elution-Composition Ranges", *values],
            ]
        )
    return pd.DataFrame([condition_names, values])
