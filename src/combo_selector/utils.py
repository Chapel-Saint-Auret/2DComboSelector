"""Utility helpers for file loading and versioning.

This module provides standalone helper functions used across the application:
- Excel table loading with automatic orientation detection
- Application version reading from ``pyproject.toml``
"""

import logging
import pandas as pd


def load_simple_table(filepath, sheetname=0):
    """Read a simple two-value table from an Excel sheet with no header row.

    The table can be laid out either horizontally (first row is header, second
    row contains values) or vertically (first column is header, second column
    contains values).  Empty rows and columns are stripped before detection.

    Args:
        filepath (str | Path): Path to the Excel file.
        sheetname (int | str): Sheet index or name to read. Defaults to 0.

    Returns:
        pd.DataFrame: Single-row DataFrame whose columns are the header labels
            and whose values are the corresponding data values.

    Raises:
        ValueError: If the table shape is not recognized as either a horizontal
            (2 rows × ≥2 cols) or vertical (≥2 rows × 2 cols) layout.
    """
    df = pd.read_excel(filepath, sheet_name=sheetname, header=None)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    # Check shape to decide
    if df.shape[0] == 2 and df.shape[1] >= 2:
        # Horizontal: first row is header
        columns = df.iloc[0]
        values = df.iloc[1]
        return pd.DataFrame([values.values], columns=columns)
    elif df.shape[1] == 2 and df.shape[0] >= 2:
        # Vertical: first col is header
        table = df.iloc[:, :2].dropna()
        columns = table.iloc[:, 0].astype(str).values
        values = table.iloc[:, 1].values
        return pd.DataFrame([values], columns=columns)
    else:
        raise ValueError("Table shape not recognized.")


def load_table_with_header_anywhere(
    filepath, sheetname=0, min_header_cols=2, auto_fix_duplicates=True
):
    """
    Loads the first table in an Excel sheet, starting from the first row
    with at least `min_header_cols` non-NaN values (assumed header).
    Strips whitespace from column names and warns or fixes duplicates.
    """
    from collections import Counter

    # Load all as raw (no header), strings to avoid type problems
    raw = pd.read_excel(filepath, sheet_name=sheetname, header=None, dtype=str)
    raw = raw.dropna(how="all", axis=0).dropna(how="all", axis=1)

    # Find first row with enough non-NaN entries (potential header)
    for i, row in raw.iterrows():
        if row.notna().sum() >= min_header_cols:
            header_row = i
            break
    else:
        raise ValueError("No header row found with sufficient columns.")

    # Now read again, skipping to that header row, using it as header
    df = pd.read_excel(filepath, sheet_name=sheetname, header=header_row)
    df = df.dropna(how="all")  # Drop fully empty rows
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]  # Drop unnamed columns

    # Strip all whitespace from columns
    df.columns = df.columns.str.strip()

    # Check for duplicates
    duplicates = [item for item, count in Counter(df.columns).items() if count > 1]
    if duplicates:
        logging.warning("Duplicate columns found: %s", duplicates)
        if auto_fix_duplicates:
            # Pandas will already have renamed with .1, .2, etc. Keep those for now
            # Optionally, you could further rename or alert here.
            logging.debug("Duplicates were auto-renamed by pandas with .1, .2 etc.")
        else:
            raise ValueError(f"Duplicate column names found: {duplicates}")

    return df


def get_version() -> str:
    """Return the installed package version shown by the application UI."""
    from combo_selector import __version__

    return __version__
