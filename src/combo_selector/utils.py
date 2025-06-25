import os,sys
import pandas as pd


def resource_path(relative_path):
    """
    Get absolute path to resource in dev, pip, or PyInstaller (frozen).
    Example: resource_path("icons/close_window.svg")
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller: resources bundled in _internal/resources
        base = os.path.join(os.path.dirname(sys.executable), "_internal", "resources")
        abs_path = os.path.join(base, relative_path)
        if os.path.exists(abs_path):
            return abs_path
        raise FileNotFoundError(f"Resource not found: {relative_path} (expected at {abs_path})")
    else:
        # Dev or pip: resources inside the installed package
        try:
            from importlib.resources import files
            package = 'combo_selector.resources'
            resource_file = files(package) / relative_path
            if resource_file.is_file():
                return str(resource_file)
        except Exception:
            pass  # Fallback to direct path below

        # fallback: directly from filesystem (for IDE, etc.)
        dev_path = os.path.join(os.path.dirname(__file__), 'resources', relative_path)
        if os.path.exists(dev_path):
            return dev_path
        raise FileNotFoundError(f"Resource not found: {relative_path} (checked {dev_path})")

def load_simple_table(filepath, sheetname=0):
    df = pd.read_excel(filepath, sheet_name=sheetname, header=None)
    df = df.dropna(how='all').dropna(axis=1, how='all')
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


def load_table_with_header_anywhere(filepath, sheetname=0, min_header_cols=2, auto_fix_duplicates=True):
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
    df = df.dropna(how="all")    # Drop fully empty rows
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Drop unnamed columns

    # Strip all whitespace from columns
    df.columns = df.columns.str.strip()

    # Check for duplicates
    duplicates = [item for item, count in Counter(df.columns).items() if count > 1]
    if duplicates:
        print("⚠️ Warning: Duplicate columns found:", duplicates)
        if auto_fix_duplicates:
            # Pandas will already have renamed with .1, .2, etc. Keep those for now
            # Optionally, you could further rename or alert here.
            print("Duplicates were auto-renamed by pandas with .1, .2 etc.")
        else:
            raise ValueError(f"Duplicate column names found: {duplicates}")

    return df