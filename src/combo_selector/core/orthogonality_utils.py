import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import tmean, tstd


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller bundle.

    :param relative_path: Path relative to this file, e.g. 'resources/icons/myicon.svg'
    :return: Absolute path usable by Qt
    """
    try:
        # PyInstaller creates a temp folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Use the directory where this script is located (e.g., src/combo_selector/)
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def load_simple_table(filepath, sheetname=0):
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
        print("⚠️ Warning: Duplicate columns found:", duplicates)
        if auto_fix_duplicates:
            # Pandas will already have renamed with .1, .2, etc. Keep those for now
            # Optionally, you could further rename or alert here.
            print("Duplicates were auto-renamed by pandas with .1, .2 etc.")
        else:
            raise ValueError(f"Duplicate column names found: {duplicates}")

    return df


# --- Usage example ---
# df_norm_rt = load_table_with_header_anywhere("Data Soraya 5.xlsx", sheetname="Normalize RT")
# print(df_norm_rt)


def extract_set_number(name):
    match = re.search(r"\d+", name)  # Find the first sequence of digits
    return int(match.group()) if match else None


def normalize_x_y_series(x_series, y_series):
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

    # cast value to float to avoid issue introduced by empty string
    return x_norm_series, y_norm_series


def point_is_above_curve(x, y, curve):
    """
    Determines whether a given point (x, y) lies above a specified curve.

    Parameters:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        curve (callable): A function representing the curve. It should take a single argument (x)
                          and return the corresponding y-value on the curve.

    Returns:
        bool: True if the point (x, y) is above the curve, False otherwise.
    """
    # Evaluate the curve at the given x-coordinate
    curve_y = curve(x)

    # Compare the y-coordinate of the point with the curve's y-value
    if curve_y < y:
        return True  # The point is above the curve
    else:
        return False  # The point is on or below the curve


def point_is_below_curve(x, y, curve):
    """
    Determines whether a given point (x, y) lies below a specified curve.

    Parameters:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        curve (callable): A function representing the curve. It should take a single argument (x)
                          and return the corresponding y-value on the curve.

    Returns:
        bool: True if the point (x, y) is below the curve, False otherwise.
    """
    # Evaluate the curve at the given x-coordinate
    curve_y = curve(x)

    # Compare the y-coordinate of the point with the curve's y-value
    if curve_y > y:
        return True  # The point is below the curve
    else:
        return False  # The point is on or above the curve


def get_list_of_point_above_curve(x_series, y_series, curve):
    """
    Returns a list of points that lie above a specified curve.

    Parameters:
        x_series (array-like): The x-coordinates of the points.
        y_series (array-like): The y-coordinates of the points.
        curve (callable): A function representing the curve. It should take a single argument (x)
                          and return the corresponding y-value on the curve.

    Returns:
        list: A list of tuples, where each tuple contains the (x, y) coordinates of a point
              that lies above the curve.
    """
    point_above = []

    # Iterate through the x and y coordinates
    for x, y in zip(x_series, y_series):
        # Check if the point is above the curve
        if point_is_above_curve(x, y, curve):
            point_above.append((x, y))  # Add the point to the list

    return point_above


def get_list_of_point_below_curve(x_series, y_series, curve):
    """
    Returns a list of points that lie below a specified curve.

    Parameters:
        x_series (array-like): The x-coordinates of the points.
        y_series (array-like): The y-coordinates of the points.
        curve (callable): A function representing the curve. It should take a single argument (x)
                          and return the corresponding y-value on the curve.

    Returns:
        list: A list of tuples, where each tuple contains the (x, y) coordinates of a point
              that lies below the curve.
    """
    point_below = []

    # Iterate through the x and y coordinates
    for x, y in zip(x_series, y_series):
        # Check if the point is below the curve
        if point_is_below_curve(x, y, curve):
            point_below.append((x, y))  # Add the point to the list

    return point_below


def compute_bin_box_mask_color(x, y, nb_boxes):
    """
    Computes a masked 2D histogram (bin box mask color) for the given x and y data.

    Parameters:
        x (array-like): The x-coordinates of the data points.
        y (array-like): The y-coordinates of the data points.
        nb_boxes (int): The number of bins along each axis.

    Returns:
        numpy.ma.MaskedArray: A masked array representing the 2D histogram, where bins with no data points are masked.
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


def compute_percent_fit_for_set(set_key, set_data):
    def objective(x, peak, curve):
        y = curve(x)
        return (x - peak[0]) ** 2 + (y - peak[1]) ** 2

    def compute_minimal_distances1(peaks, curve):
        results = []
        for peak in peaks:
            res = minimize_scalar(
                objective, method="bounded", bounds=(0.0, 1.0), args=(peak, curve)
            )
            results.append(res.x)  # Or res.fun for actual minimal value
        return results

    def compute_minimal_distances(peaks, curve, num_points=50, fine_range=0.01):
        xs = np.linspace(0, 1, num_points)

        def optimize_peak(peak):
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

    set_number = set_key

    if set_key == "Set 270":
        toto = 2
    x, y = set_data["x_values"], set_data["y_values"]
    quadratic_model_xy = np.poly1d(np.polyfit(x, y, 2))
    quadratic_model_yx = np.poly1d(np.polyfit(x, y, 2))

    # Your helpers must return list of (x, y) tuples!
    peak_above_xy = get_list_of_point_above_curve(x, y, quadratic_model_xy)
    peak_above_yx = get_list_of_point_above_curve(y, x, quadratic_model_yx)
    peak_below_xy = get_list_of_point_below_curve(x, y, quadratic_model_xy)
    peak_below_yx = get_list_of_point_below_curve(y, x, quadratic_model_yx)

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

    delta_xy_avg = ((1 - abs(1 - (xy1_avg * 4))) + (1 - abs(1 - (xy2_avg * 4)))) / 2
    delta_xy_sd = ((1 - abs(1 - (xy1_sd * 7))) + (1 - abs(1 - (xy2_sd * 7)))) / 2
    delta_yx_avg = ((1 - abs(1 - (yx1_avg * 4))) + (1 - abs(1 - (yx2_avg * 4)))) / 2
    delta_yx_sd = ((1 - abs(1 - (yx1_sd * 7))) + (1 - abs(1 - (yx2_sd * 7)))) / 2

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


def cluster_and_fuse(data):
    # 1) Build a mapping: item → list of tuple-indices
    item_to_idxs = {}
    for idx, tpl in enumerate(data):
        for item in tpl:
            if item not in item_to_idxs:
                item_to_idxs[item] = [idx]
            elif idx not in item_to_idxs[item]:
                item_to_idxs[item].append(idx)

    visited = []  # indices we’ve already enqueued/seen
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
