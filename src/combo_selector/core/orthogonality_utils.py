"""Utility functions for orthogonality calculations in 2D chromatography analysis.

This module provides helper functions for:
- Loading data from Excel files
- Normalizing retention time series
- Computing geometric relationships between points and curves
- Calculating bin box histograms
- Computing percent fit metrics
- Clustering correlated metrics
"""

import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import tmean, tstd
from collections import Counter


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev environement and for PyInstaller bundle.

    This function resolves paths correctly whether running from source
    or from a PyInstaller-bundled executable.

    Args:
        relative_path (str): Path relative to this file, 
                            e.g. 'resources/icons/myicon.svg'

    Returns:
        str: Absolute path .

    Example:
        >>> icon_path = resource_path('resources/icons/app.svg')
        >>> # Returns full path whether in dev or bundled mode
    """
    try:
        # PyInstaller creates a temp folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Use the directory where this script is located (e.g., src/combo_selector/)
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def load_simple_table(filepath: str, sheetname: str = 0) -> pd.DataFrame:
    """Load a simple 2-row or 2-column table from an Excel file.

    Handles two table orientations:
    - Horizontal: 2 rows x N columns (row 0 = headers, row 1 = values)
    - Vertical: N rows x 2 columns (col 0 = headers, col 1 = values)

    Args:
        filepath (str): Path to the Excel file.
        sheetname (str | int, optional): Name or index of the sheet to load. 
                                         Defaults to 0 (first sheet).

    Returns:
        pd.DataFrame: Single-row DataFrame with column headers and values.

    Raises:
        ValueError: If table shape is not 2xN or Nx2.

    Example:
        >>> dataframe = load_simple_table("peak_capacities.xlsx", "Sheet1")
        >>> # Returns DataFrame with peak capacity values
    """
    df = pd.read_excel(filepath, sheet_name=sheetname, header=None)
    df = df.dropna(how="all").dropna(axis=1, how="all")

    # Check shape to decide orientation
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
        filepath: str,
        sheetname: str | int = 0,
        min_header_cols: int = 2,
        auto_fix_duplicates: bool = True
) -> pd.DataFrame:
    """Load a table from Excel, automatically detecting the header row.

    This function searches for the first row with at least `min_header_cols`
    non-NaN values and treats it as the header. It handles various Excel
    formatting issues including:
    - Headers not on the first row
    - Whitespace in column names
    - Duplicate column names
    - Unnamed columns

    Args:
        filepath (str): Path to the Excel file.
        sheetname (str | int, optional): Name or index of the sheet. Defaults to 0.
        min_header_cols (int, optional): Minimum number of non-NaN values required
                                         for a row to be considered a header. Defaults to 2.
        auto_fix_duplicates (bool, optional): If True, allows pandas to auto-rename
                                             duplicate columns with .1, .2 suffixes.
                                             If False, raises ValueError. Defaults to True.

    Returns:
        pd.DataFrame: Loaded table with cleaned column names.

    Raises:
        ValueError: If no header row is found or if duplicate columns exist and
                   auto_fix_duplicates is False.

    Example:
        >>> dataframe = load_table_with_header_anywhere("data.xlsx", "Retention Times")
        >>> # Automatically finds header row and loads data
    """

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
        print("⚠️ Warning: Duplicate columns found:", duplicates)
        if auto_fix_duplicates:
            # Pandas will already have renamed with .1, .2, etc. Keep those for now
            print("Duplicates were auto-renamed by pandas with .1, .2 etc.")
        else:
            raise ValueError(f"Duplicate column names found: {duplicates}")

    return df


def extract_set_number(name: str) -> int | None:
    """Extract the numeric set number from a set name string.

    Args:
        name (str): Set name containing a number, e.g., 'Set 1', 'Set 42'.

    Returns:
        int | None: The extracted integer, or None if no digits are found.

    Example:
        >>> extract_set_number("Set 15")
        15
        >>> extract_set_number("Set ABC")
        None
    """
    match = re.search(r"\d+", name)  # Find the first sequence of digits
    return int(match.group()) if match else None


def normalize_x_y_series(
        x_series: pd.Series,
        y_series: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Normalize two pandas Series using min-max normalization to [0, 1] range.

    Formula: (value - min) / (max - min)

    Args:
        x_series (pd.Series): X-coordinate series to normalize.
        y_series (pd.Series): Y-coordinate series to normalize.

    Returns:
        tuple[pd.Series, pd.Series]: Normalized x_series and y_series.
                                     Negative values are replaced with empty strings.

    Example:
        >>> x = pd.Series([1, 2, 3, 4, 5])
        >>> y = pd.Series([10, 20, 30, 40, 50])
        >>> x_norm, y_norm = normalize_x_y_series(x, y)
        >>> # x_norm: [0.0, 0.25, 0.5, 0.75, 1.0]
        >>> # y_norm: [0.0, 0.25, 0.5, 0.75, 1.0]
    """
    x_min = min(x_series)
    x_max = max(x_series)

    y_min = min(y_series)
    y_max = max(y_series)

    x_norm_series = x_series.apply(
        lambda x: (x - x_min) / (x_max - x_min) if x >= 0 else ""
    )
    y_norm_series = y_series.apply(
        lambda y: (y - y_min) / (y_max - y_min) if y >= 0 else ""
    )

    return x_norm_series, y_norm_series


def point_is_above_curve(x: float, y: float, curve: callable) -> bool:
    """Determine whether a point (x, y) lies above a curve.

    Args:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        curve (callable): A function representing the curve. Takes x as input
                         and returns the y-value on the curve.

    Returns:
        bool: True if the point is above the curve, False otherwise.

    Example:
        >>> curve = lambda x: x**2  # Parabola
        >>> point_is_above_curve(0.5, 0.5, curve)
        True  # Point (0.5, 0.5) is above y = x²
    """
    # Evaluate the curve at the given x-coordinate
    curve_y = curve(x)

    # Compare the y-coordinate of the point with the curve's y-value
    if curve_y < y:
        return True  # The point is above the curve
    else:
        return False  # The point is on or below the curve


def point_is_below_curve(x: float, y: float, curve: callable) -> bool:
    """Determine whether a point (x, y) lies below a curve.

    Args:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        curve (callable): A function representing the curve. Takes x as input
                         and returns the y-value on the curve.

    Returns:
        bool: True if the point is below the curve, False otherwise.

    Example:
        >>> curve = lambda x: x**2  # Parabola
        >>> point_is_below_curve(0.5, 0.1, curve)
        True  # Point (0.5, 0.1) is below y = x²
    """
    # Evaluate the curve at the given x-coordinate
    curve_y = curve(x)

    # Compare the y-coordinate of the point with the curve's y-value
    if curve_y > y:
        return True  # The point is below the curve
    else:
        return False  # The point is on or above the curve


def get_list_of_point_above_curve(
        x_series: np.ndarray | pd.Series,
        y_series: np.ndarray | pd.Series,
        curve: callable
) -> list[tuple[float, float]]:
    """Filter points that lie above a specified curve.

    Args:
        x_series (array-like): The x-coordinates of the points.
        y_series (array-like): The y-coordinates of the points.
        curve (callable): A function representing the curve. Takes x as input
                         and returns the y-value on the curve.

    Returns:
        list[tuple[float, float]]: List of (x, y) tuples for points above the curve.

    Example:
        >>> x = np.array([0.2, 0.5, 0.8])
        >>> y = np.array([0.1, 0.3, 0.7])
        >>> curve = lambda x: x**2
        >>> points = get_list_of_point_above_curve(x, y, curve)
        >>> # Returns points where y > x²
    """
    point_above = []

    # Iterate through the x and y coordinates
    for x, y in zip(x_series, y_series):
        # Check if the point is above the curve
        if point_is_above_curve(x, y, curve):
            point_above.append((x, y))  # Add the point to the list

    return point_above


def get_list_of_point_below_curve(
        x_series: np.ndarray | pd.Series,
        y_series: np.ndarray | pd.Series,
        curve: callable
) -> list[tuple[float, float]]:
    """Filter points that lie below a specified curve.

    Args:
        x_series (array-like): The x-coordinates of the points.
        y_series (array-like): The y-coordinates of the points.
        curve (callable): A function representing the curve. Takes x as input
                         and returns the y-value on the curve.

    Returns:
        list[tuple[float, float]]: List of (x, y) tuples for points below the curve.

    Example:
        >>> x = np.array([0.2, 0.5, 0.8])
        >>> y = np.array([0.01, 0.1, 0.3])
        >>> curve = lambda x: x**2
        >>> points = get_list_of_point_below_curve(x, y, curve)
        >>> # Returns points where y < x²
    """
    point_below = []

    # Iterate through the x and y coordinates
    for x, y in zip(x_series, y_series):
        # Check if the point is below the curve
        if point_is_below_curve(x, y, curve):
            point_below.append((x, y))  # Add the point to the list

    return point_below


def compute_bin_box_mask_color(
        x: np.ndarray | pd.Series,
        y: np.ndarray | pd.Series,
        nb_boxes: int
) -> tuple[np.ma.MaskedArray, np.ndarray, np.ndarray]:
    """Compute a masked 2D histogram showing which bins contain data points.

    Creates a 2D histogram over [0, 1] x [0, 1] space and masks empty bins.
    This is used for bin box counting orthogonality metrics.

    Args:
        x (array-like): The x-coordinates of the data points.
        y (array-like): The y-coordinates of the data points.
        nb_boxes (int): The number of bins along each axis.

    Returns:
        tuple[np.ma.MaskedArray, np.ndarray, np.ndarray]: 
            - Masked histogram (transposed), with empty bins masked
            - x bin edges
            - y bin edges

    Example:
        >>> x = np.random.rand(100)
        >>> y = np.random.rand(100)
        >>> hist, x_edges, y_edges = compute_bin_box_mask_color(x, y, 10)
        >>> # hist.count() gives number of occupied bins
    """
    # Compute the 2D histogram edges based on the range [0, 1]
    h, x_edges, y_edges = np.histogram2d([0, 1], [0, 1], bins=(nb_boxes, nb_boxes))

    # Find the indices of the bins to which each data point belongs
    idx_x = np.digitize(x, x_edges, right=True)
    idx_y = np.digitize(y, y_edges, right=True)

    # Filter indices to ensure they are within the valid range
    idx = np.logical_and(idx_x > 0, idx_x <= nb_boxes)
    idx = np.logical_and(idx, idx_y > 0)
    idx = np.logical_and(idx, idx_y <= nb_boxes)
    idx_x = idx_x[idx] - 1  # Convert to 0-based indexing
    idx_y = idx_y[idx] - 1  # Convert to 0-based indexing

    # Create a mask for bins with no data points
    mask = np.ones_like(h)
    mask[idx_x, idx_y] = 0  # Set mask to 0 for bins with data points
    mask = np.ma.masked_equal(mask, 1)  # Mask bins with no data points

    # Apply the mask to the histogram
    h_color = np.ma.masked_array(h, mask=mask)

    return h_color.T, x_edges, y_edges


def compute_percent_fit_for_set(
        set_key: str,
        set_data: dict
) -> tuple[str, dict]:
    """Compute the %FIT orthogonality metric for a single set.

    The %FIT metric measures how well peaks fit to quadratic regression curves.
    It evaluates both X vs Y and Y vs X regressions, computing minimal distances
    for points above and below each curve.

    Args:
        set_key (str): Identifier for the set (e.g., 'Set 1').
        set_data (dict): Dictionary containing 'x_values' and 'y_values' keys
                        with retention time data.

    Returns:
        tuple[str, dict]: 
            - set_key: The input set identifier
            - result: Dictionary containing:
                - 'quadratic_reg_xy': Quadratic model for X vs Y
                - 'quadratic_reg_yx': Quadratic model for Y vs X
                - 'percent_fit': Dict with delta values and final %FIT value

    Note:
        This function uses multithreading internally for peak optimization.
        The %FIT value ranges from 0 (poor fit) to 1 (perfect fit).

    Example:
        >>> set_data = {'x_values': x_series, 'y_values': y_series}
        >>> set_key, result = compute_percent_fit_for_set('Set 1', set_data)
        >>> percent_fit_value = result['percent_fit']['value']
    """

    def objective(x: float, peak: tuple, curve: callable) -> float:
        """Objective function for minimizing distance from peak to curve.

        Args:
            x (float): X-coordinate on curve to evaluate.
            peak (tuple): (x, y) coordinates of the peak.
            curve (callable): Curve function.

        Returns:
            float: Squared Euclidean distance from peak to curve at x.
        """
        y = curve(x)
        return (x - peak[0]) ** 2 + (y - peak[1]) ** 2

    def compute_minimal_distances(
            peaks: list,
            curve: callable,
            num_points: int = 50,
            fine_range: float = 0.01
    ) -> list[float]:
        """Compute minimal distance from each peak to curve with refinement.

        Uses coarse grid search followed by fine optimization for efficiency.
        Multithreaded for performance.

        Args:
            peaks (list): List of (x, y) peak coordinates.
            curve (callable): Curve function.
            num_points (int, optional): Number of points in coarse grid. Defaults to 50.
            fine_range (float, optional): Range for fine optimization. Defaults to 0.01.

        Returns:
            list[float]: X-coordinates on curve closest to each peak.
        """
        xs = np.linspace(0, 1, num_points)

        def optimize_peak(peak: tuple) -> float:
            """Optimize distance for a single peak."""
            ys = curve(xs)
            dists = (xs - peak[0]) ** 2 + (ys - peak[1]) ** 2
            min_idx = np.argmin(dists)
            x0 = xs[min_idx]
            left = max(0, x0 - fine_range)
            right = min(1, x0 + fine_range)
            res = minimize_scalar(
                objective, method="bounded", bounds=(left, right), args=(peak, curve)
            )
            return res.x

        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(optimize_peak, peaks))
        return results

    x, y = set_data["x_values"], set_data["y_values"]
    quadratic_model_xy = np.poly1d(np.polyfit(x, y, 2))
    quadratic_model_yx = np.poly1d(np.polyfit(x, y, 2))

    # Separate peaks above and below curves
    peak_above_xy = get_list_of_point_above_curve(x, y, quadratic_model_xy)
    peak_above_yx = get_list_of_point_above_curve(y, x, quadratic_model_yx)
    peak_below_xy = get_list_of_point_below_curve(x, y, quadratic_model_xy)
    peak_below_yx = get_list_of_point_below_curve(y, x, quadratic_model_yx)

    # Compute minimal distances
    minimal_distance_below_xy = compute_minimal_distances(
        peak_below_xy, quadratic_model_xy
    )
    minimal_distance_below_yx = compute_minimal_distances(
        peak_below_yx, quadratic_model_yx
    )
    minimal_distance_above_xy = compute_minimal_distances(
        peak_above_xy, quadratic_model_xy
    )
    minimal_distance_above_yx = compute_minimal_distances(
        peak_above_yx, quadratic_model_yx
    )

    # Compute statistics for distances
    xy1_avg = tmean(minimal_distance_below_xy) if minimal_distance_below_xy else 0
    yx1_avg = tmean(minimal_distance_below_yx) if minimal_distance_below_yx else 0
    xy1_sd = (
        tstd(minimal_distance_below_xy) if len(minimal_distance_below_xy) > 1 else 0
    )
    yx1_sd = (
        tstd(minimal_distance_below_yx) if len(minimal_distance_below_yx) > 1 else 0
    )

    xy2_avg = tmean(minimal_distance_above_xy) if minimal_distance_above_xy else 0
    yx2_avg = tmean(minimal_distance_above_yx) if minimal_distance_above_yx else 0
    xy2_sd = (
        tstd(minimal_distance_above_xy) if len(minimal_distance_above_xy) > 1 else 0
    )
    yx2_sd = (
        tstd(minimal_distance_above_yx) if len(minimal_distance_above_yx) > 1 else 0
    )

    # Compute delta values (normalized fit metrics)
    delta_xy_avg = ((1 - abs(1 - (xy1_avg * 4))) + (1 - abs(1 - (xy2_avg * 4)))) / 2
    delta_xy_sd = ((1 - abs(1 - (xy1_sd * 7))) + (1 - abs(1 - (xy2_sd * 7)))) / 2
    delta_yx_avg = ((1 - abs(1 - (yx1_avg * 4))) + (1 - abs(1 - (yx2_avg * 4)))) / 2
    delta_yx_sd = ((1 - abs(1 - (yx1_sd * 7))) + (1 - abs(1 - (yx2_sd * 7)))) / 2

    # Final %FIT metric (mean of all delta values)
    percent_fit = (delta_xy_avg + delta_xy_sd + delta_yx_avg + delta_yx_sd) / 4

    # Return all needed info to update set_data in main thread
    result = {
        "quadratic_reg_xy": quadratic_model_xy,
        "quadratic_reg_yx": quadratic_model_yx,
        "percent_fit": {
            "delta_xy_avg": delta_xy_avg,
            "delta_xy_sd": delta_xy_sd,
            "delta_yx_avg": delta_yx_avg,
            "delta_yx_sd": delta_yx_sd,
            "value": abs(percent_fit),
        },
    }
    return set_key, result


def cluster_and_fuse(data: list[tuple]) -> tuple[list[list[tuple]], list[list]]:
    """Cluster tuples that share common items and fuse them into groups.

    Uses breadth-first search (BFS) to identify connected components where
    tuples are connected if they share at least one common item.

    Args:
        data (list[tuple]): List of tuples, where each tuple contains items
                           (e.g., metric names) that may overlap with other tuples.

    Returns:
        tuple[list[list[tuple]], list[list]]:
            - grouped: List of clusters, each containing the original tuples
            - fused: List of clusters, each containing unique items in first-seen order

    Example:
        >>> data = [('A', 'B'), ('B', 'C'), ('D', 'E')]
        >>> grouped, fused = cluster_and_fuse(data)
        >>> # grouped = [[('A', 'B'), ('B', 'C')], [('D', 'E')]]
        >>> # fused = [['A', 'B', 'C'], ['D', 'E']]

    Note:
        Used for grouping correlated orthogonality metrics that share common
        correlations into coherent clusters.
    """
    # 1) Build a mapping: item → list of tuple-indices
    item_to_idxs = {}
    for idx, tpl in enumerate(data):
        for item in tpl:
            if item not in item_to_idxs:
                item_to_idxs[item] = [idx]
            elif idx not in item_to_idxs[item]:
                item_to_idxs[item].append(idx)

    visited = []  # indices we've already enqueued/seen
    clusters = []  # list of connected components (each is a list of indices)

    # 2) For each tuple-index, do a BFS (using a plain list as queue)
    for start in range(len(data)):
        if start in visited:
            continue

        queue = [start]
        visited.append(start)
        comp = []

        while queue:
            curr = queue.pop(0)  # dequeue
            comp.append(curr)

            # enqueue all neighbours sharing any item
            for item in data[curr]:
                for nbr in item_to_idxs[item]:
                    if nbr not in visited:
                        visited.append(nbr)
                        queue.append(nbr)

        clusters.append(comp)

    # 3a) grouped: list of list of tuples
    grouped = [[data[i] for i in comp] for comp in clusters]

    # 3b) fused: list of list of unique items (in first-seen order)
    fused = []
    for comp in clusters:
        seen = []
        for idx in comp:
            for item in data[idx]:
                if item not in seen:
                    seen.append(item)
        fused.append(seen)

    return grouped, fused