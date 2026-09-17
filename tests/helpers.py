"""Shared helpers for core logic tests."""

# Helper inventory:
# - Provide a GUI-free NaN-policy guard for core tests.
# - Combine the core mixins into a lightweight test model.
# - Create temporary Excel workbooks from DataFrame specifications.
# - Resolve checked-in fixture paths.
# - Execute the standard ranking pipeline used by regression tests.
# - Build deterministic three- and four-condition retention tables.
# - Build optional peak-capacity and elution-composition input tables.

from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd

from combo_selector.core.data_manager import DataManager
from combo_selector.core.metric_engine import MetricEngine
from combo_selector.core.redundancy import Redundancy
from combo_selector.core.results_builder import ResultsBuilder
from combo_selector.core.scoring import Scoring


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class DummyNanPolicyDialog:
    """Fail fast if a test fixture unexpectedly triggers the GUI NaN flow."""

    def exec_(self) -> None:
        # Any unexpected dialog request would block an automated test run.
        raise AssertionError("Tests should use explicit NaN fixtures when covering dialog flows.")


class CoreTestModel(DataManager, MetricEngine, Redundancy, Scoring, ResultsBuilder):
    """Core-only model harness without Qt dependencies."""

    def __init__(self) -> None:
        # Replace the Qt dialog dependency with a deterministic test double.
        self.nan_policy_dialog = DummyNanPolicyDialog()
        # Initialize the same model state used by the application core.
        self.init_data()

    def init_data(self) -> None:
        """Reset data and metric registry together, like the full app expects."""
        # Reset imported data, options, statuses, and result DataFrames.
        DataManager.init_data(self)
        # Restore the metric registry normally initialized by the GUI model.
        self.reset_om_status_computation_state()


def write_workbook(path: Path, sheets: dict[str, tuple[pd.DataFrame, bool] | pd.DataFrame]) -> Path:
    """Write an Excel workbook for tests.

    Each value can be either a DataFrame (written with headers) or a
    ``(DataFrame, write_header)`` tuple.
    """
    # Open one writer so every requested table is stored in the same workbook.
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, spec in sheets.items():
            # A tuple lets a test explicitly control whether headers are written.
            if isinstance(spec, tuple):
                frame, header = spec
            else:
                # Plain DataFrames use their column names by default.
                frame, header = spec, True
            # Write without an index because application inputs do not use one.
            frame.to_excel(writer, sheet_name=sheet_name, index=False, header=header)
    # Return the input path to support compact fixture construction in tests.
    return path


def make_temp_workbook(sheets: dict[str, tuple[pd.DataFrame, bool] | pd.DataFrame]) -> str:
    """Create a temporary workbook and return its path."""
    # Reserve a unique Windows-compatible file path without keeping it open.
    handle = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    handle.close()
    # Populate the reserved file with the requested sheet definitions.
    write_workbook(Path(handle.name), sheets)
    # Tests use strings because the production loading API accepts file names.
    return handle.name


def get_fixture_path(filename: str) -> str:
    """Return the absolute path to a checked-in workbook fixture."""
    # Resolve relative fixture names independently of the current directory.
    return str(FIXTURES_DIR / filename)


def build_ranked_model(
    workbook: str,
    retention_sheet: str = "Retention Time Table",
    peak_capacity_sheet: str | None = None,
    elution_sheet: str | None = None,
    metrics: list[str] | None = None,
) -> CoreTestModel:
    """Build a computed core model from a workbook fixture."""
    # Use a small representative metric set unless a test supplies another one.
    if metrics is None:
        metrics = [
            "Convex hull relative area",
            "Bin box counting",
            "Pearson Correlation",
            "Spearman Correlation",
            "Kendall Correlation",
        ]

    # Create the GUI-free model and load the mandatory retention-time input.
    model = CoreTestModel()
    model.load_retention_time(workbook, retention_sheet)
    # Normalize coordinates before calculating orthogonality metrics.
    model.normalize_retention_time("min_max")

    # Load optional peak-capacity data only when the caller names its sheet.
    if peak_capacity_sheet:
        model.load_hypothetical_2d_peak_capacity(workbook, peak_capacity_sheet)
    # Load optional elution-domain data only when the caller names its sheet.
    if elution_sheet:
        model.load_elution_composition_space_area_data(workbook, elution_sheet)

    # Execute each requested metric through the same registry as the application.
    for metric_name in metrics:
        model.om_function_map[metric_name]["func"]()

    # Assemble raw metric values into the result DataFrames.
    model.update_metric_dataframes(metrics)
    # Create deterministic metric groups without excluding correlations.
    model.create_correlation_group("Values", threshold=0.0, tol=0.0)
    # Aggregate the grouped metrics used by the consensus score.
    model.fill_correlation_group_average("Values")
    # Select the default mean-based consensus configuration.
    model.set_computed_score_dict(
        {
            "metric_list": metrics,
            "aggregation_method": "Mean",
            "score_used": "Default",
        }
    )
    # Build scores, ranks, diagnostics, and recommendations.
    model.update_table_results()
    # Return the fully computed model so tests can inspect intermediate columns.
    return model


def make_retention_df_three_conditions() -> pd.DataFrame:
    """Return a small deterministic retention-time fixture."""
    # Three conditions generate exactly three pairwise combinations.
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
    # Four deliberately distinct elution orders generate six non-trivial pairs.
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
    # Reproduce the documented release layout when a label column is requested.
    if with_label_column:
        return pd.DataFrame(
            [
                [None, *condition_names],
                ["Peak capacity", *values],
            ]
        )
    # Otherwise return the minimal two-row format accepted by the parser.
    return pd.DataFrame([condition_names, values])


def make_elution_table(condition_names: list[str], values: list[float], with_label_column: bool = False) -> pd.DataFrame:
    """Return a horizontal simple-table fixture for elution-composition inputs."""
    # Reproduce the documented release layout when a label column is requested.
    if with_label_column:
        return pd.DataFrame(
            [
                [None, *condition_names],
                ["Elution-Composition Ranges", *values],
            ]
        )
    # Otherwise return the minimal two-row format accepted by the parser.
    return pd.DataFrame([condition_names, values])
