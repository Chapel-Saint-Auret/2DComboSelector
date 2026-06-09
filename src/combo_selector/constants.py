"""Central constants module for 2DComboSelector.

All named constants used across the application are gathered here so they are
easy to find, compare, and update in one place.

Sections
--------
1. Domain / chromatography constants
2. UI data constants (metric maps, visualization metadata)
3. Colour palette constants
4. Stylesheet constants (depend on the colour palette)
5. Text-content constants (tips, guide text)
"""

from PySide6.QtCore import QSize

# ---------------------------------------------------------------------------
# 1. Domain / chromatography constants
# ---------------------------------------------------------------------------

CHROM_MODE = ["RPLC", "HILIC", "IEX", "SEC", "HIC", "SFC", "vs"]

# Pairwise feasibility info indexed by "ModeA vs ModeB"
FEASIBILITY = {
    "RPLC vs RPLC": {"Compatibility": "High", "Complexity": "Low"},
    "RPLC vs HILIC": {"Compatibility": "Moderate", "Complexity": "Moderate"},
    "RPLC vs SFC": {"Compatibility": "Low", "Complexity": "High"},
    "HILIC vs HILIC": {"Compatibility": "High", "Complexity": "Low"},
    "HILIC vs SFC": {"Compatibility": "Moderate", "Complexity": "High"},
    "SFC vs SFC": {"Compatibility": "Moderate", "Complexity": "High"},
}

# Ordered levels used to populate feasibility filter dialogs
FEASIBILITY_LEVELS = ["High", "Moderate", "Low"]

METRIC_MAPPING = {
    "set_number": {
        "table_index": 0,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "title": {"table_index": 1, "include_in_score": True, "include_in_corr_mat": False},
    "nb_peaks": {
        "table_index": 2,
        "include_in_score": False,
        "include_in_corr_mat": False,
    },
    "2d_peak_capacity": {
        "table_index": 3,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "elution_composition_space": {
        "table_index": 4,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "convex_hull": {
        "table_index": 5,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "bin_box_ratio": {
        "table_index": 6,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "pearson_r": {
        "table_index": 7,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "spearman_rho": {
        "table_index": 8,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "kendall_tau": {
        "table_index": 9,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "cc_mean": {
        "table_index": 10,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "asterisk_metrics": {
        "table_index": 11,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "nnd_arithmetic_mean": {
        "table_index": 12,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "nnd_geom_mean": {
        "table_index": 13,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "nnd_harm_mean": {
        "table_index": 14,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "nnd_mean": {
        "table_index": 15,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "percent_fit": {
        "table_index": 16,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "percent_bin": {
        "table_index": 17,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "mean_bin_box_percent_bin": {
        "table_index": 18,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "asterisk_convex_hull_mean": {
        "table_index": 19,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "mean_bin_box_percent_bin_nnd_mean": {
        "table_index": 20,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "orthogonality_score": {
        "table_index": 21,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "orthogonality_ranking": {
        "table_index": 22,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "coverage_score": {
        "table_index": 23,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "practical_2d_peak_capacity": {
        "table_index": 24,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "heinisch": {
        "table_index": 25,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "orthogonality_value": {
        "table_index": 26,
        "include_in_score": True,
        "include_in_corr_mat": False,
    },
    "gilar-watson": {
        "table_index": 27,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "modeling_approach": {
        "table_index": 28,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "conditional_entropy": {
        "table_index": 29,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "geometric_approach": {
        "table_index": 30,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "distribution_score": {
        "table_index": 31,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "agreement_index": {
        "table_index": 32,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
    "outlier_metric_flag": {
        "table_index": 33,
        "include_in_score": True,
        "include_in_corr_mat": True,
    },
}

# Maps UI metric display names → internal DataFrame column names
UI_TO_MODEL_MAPPING = {
    "Convex hull relative area": "convex_hull",
    "Bin box counting": "bin_box_ratio",
    "Pearson Correlation": "pearson_r",
    "Spearman Correlation": "spearman_rho",
    "Kendall Correlation": "kendall_tau",
    "CC mean": "cc_mean",
    "Asterisk equations": "asterisk_metrics",
    "Asterisk + Cnvx Hull mean": "asterisk_convex_hull_mean",
    "NND Arithm mean": "nnd_arithmetic_mean",
    "NND Geom mean": "nnd_geom_mean",
    "NND Harm mean": "nnd_harm_mean",
    "NND mean": "nnd_mean",
    "%FIT": "percent_fit",
    "Bin box + %BIN": "percent_bin",
    "%BIN": "percent_bin",
    "mean (Bin box + %BIN)": "mean_bin_box_percent_bin",
    "mean(Bin box + %BIN + NND mean)": "mean_bin_box_percent_bin_nnd_mean",
    "Gilar-Watson method": "gilar-watson",
    "Modeling approach": "modeling_approach",
    "Geometric approach": "geometric_approach",
    "Conditional entropy": "conditional_entropy",
    # Results-page score names
    "Suggested score": "suggested_score",
    "Computed score": "computed_score",
}

METRIC_CATEGORY = {
    "Convex hull relative area": "Coverage",
    "Bin box counting": "Coverage",
    "Gilar-Watson method": "Coverage",
    "Modeling approach": "NC",
    "Conditional entropy": "Distribution",
    "Pearson Correlation": "Distribution",
    "Spearman Correlation": "Distribution",
    "Kendall Correlation": "Distribution",
    "Asterisk equations": "Distribution",
    "NND Arithm mean": "Distribution",
    "NND Geom mean": "Distribution",
    "NND Harm mean": "Distribution",
    "%FIT": "Distribution",
    "%BIN": "Coverage",
}

METRIC_WEIGHTS = {"%FIT": 10}
DEFAULT_WEIGHT = 1

# ---------------------------------------------------------------------------
# 2. UI data constants
# ---------------------------------------------------------------------------

# Results-page status / recommendation lists
PEAK_RATE_STATUS = ["Suitable", "Acceptable", "Cautionary", "Insufficient"]
FINAL_RECOMMENDATION = [
    "Highly recommended",
    "Recommended",
    "Use with caution",
    "Not recommended",
]

# Maps metric display name → plot visualization type (None = no visualization)
METRIC_PLOT_MAP = {
    "Convex hull relative area": "Convex Hull",
    "Bin box counting": "Bin Box",
    "Pearson Correlation": "Linear regression",
    "Spearman Correlation": "Linear regression",
    "Kendall Correlation": "Linear regression",
    "Asterisk equations": "Asterisk",
    "%FIT": "%FIT yx",
    "%BIN": "%BIN",
    "Gilar-Watson method": None,
    "Modeling approach": "Modeling approach",
    "Geometric approach": "Geometric approach",
    "Conditional entropy": "Conditional entropy",
    "NND Arithm mean": None,
    "NND Geom mean": None,
    "NND Harm mean": None,
    "NND mean": None,
}

# Maps metric display name → short label used in the correlation matrix
METRIC_CORR_MAP = {
    "Convex hull relative area": "CH Area",
    "Bin box counting": "Bin Box",
    "Gilar-Watson method": "Gilar-W",
    "Modeling approach": "Mod App",
    "Conditional entropy": "Cond Ent",
    "Pearson Correlation": "Pearson",
    "Spearman Correlation": "Spearman",
    "Kendall Correlation": "Kendall",
    "Asterisk equations": "Asterisk",
    "NND Arithm mean": "NND-A",
    "NND Geom mean": "NND-G",
    "NND Harm mean": "NND-H",
    "%FIT": "%FIT",
    "%BIN": "%BIN",
}

# Plot-subset threshold percentages
SUBSET_THRESHOLDS = {
    "All": 100,
    "Top 50%": 50,
    "Top 20%": 20,
    "Top 10%": 10,
}

# Maps UI criteria names → (rank column, value column) pairs for scatter plots
CRITERIA_COLUMN_MAP = {
    "All criteria": None,
    "Orthogonality": ("Orthogonality Rank", "Orthogonality"),
    "Elution Domain": ("Elution Domain Rank", "Elution Domain"),
    "Peak Capacity": ("Peak Capacity Rank", "Peak Capacity"),
    "Final consensus": ("Final Rank", "Final Consensus Rank"),
    "Peak rate": ("Peak Detection Rate (%)", "Peak rate (%)"),
}

CATEGORY_ORDER = [
    "Highly recommended",
    "Recommended",
    "Use with caution",
    "Not recommended",
]

# Recommendation category colours used in plots
COLORS = {
    "Highly recommended": "#1a7a2e",
    "Recommended": "#6abf4b",
    "Use with caution": "#f5a623",
    "Not recommended": "#d94f3d",
}

# Available plot types for the visualization options panel
PLOT_TYPES = [
    "Orthogonality Space",
    "Metric Removal Impact On Orthogonality Rank",
    "Multi-Criteria Space",
    "Chromatographic Mode Performance",
    "Recommendation Distribution",
    "Feasibility Profile",
    "Final Rank vs Recommendation",
    "Final Rank Shift Scatter",
    "Final Rank Shift Distribution",
    "Rank Shift by Combination",
    "Top Rank Overlap",
]

PLOT_DESCRIPTIONS = {
    "Orthogonality Space":
        "Scatter plot of chromatographic condition pairs in orthogonality space.",
    "Metric Removal Impact On Orthogonality Rank":
        "Shows the median orthogonality rank obtained after removing each metric from its correlation group.",
    "Multi-Criteria Space":
        "Scatter plot of solutions in criteria space to explore trade-offs between objectives.",
    "Chromatographic Mode Performance":
        "Compares chromatographic modes across selected criteria.",
    "Recommendation Distribution":
        "Shows the distribution of recommended condition pairs.",
    "Feasibility Profile":
        "Displays feasibility scores across the evaluated condition space.",
    "Final Rank vs Recommendation":
        "Cross-plots the final consensus rank against recommendation scores.",
    "Final Rank Shift Scatter":
        "",
    "Final Rank Shift Distribution":
        "",
    "Rank Shift by Combination":
        "Lollipop chart showing rank shift (New − Old) for each combination, sorted by old rank.",
    "Top Rank Overlap":
        "Bar chart comparing how many combinations are shared between old and new top-10, top-50, and top-100 lists.",
}

CRITERIA_ITEMS = [
    "All criteria",
    "Orthogonality",
    "Elution Domain",
    "Peak Capacity",
    "Final consensus",
    "Peak rate",
]

RECOMMENDATION_ITEMS = [
    "All recommendation",
    "Highly recommended",
    "Recommended",
    "Use with caution",
    "Not recommended",
]

# Widget size constants
PLOT_SIZE = QSize(600, 400)
ICON_SIZE = QSize(28, 28)

# ---------------------------------------------------------------------------
# 3. Colour palette constants
# ---------------------------------------------------------------------------

# Table colour configs: {column_index: {value: hex_colour}}
COLOR_CONFIG_TABLE_FEASIBILITY = {
    4: {
        "High": "#1a7a2e", "Moderate": "#f5a623", "Low": "#d94f3d"
    },
    3: {
        "Low": "#1a7a2e", "Moderate": "#f5a623", "High": "#d94f3d", "NC": "#888888"
    },
    6: {
        "Insufficient ": "#d94f3d", "Cautionary": "#f5a623",
        "Acceptable": "#1a7a2e", "Suitable": "#6abf4b"
    },
}

COLOR_CONFIG_TABLE_RECOMMENDATION = {
    6: {
        "Good": "#1a7a4a", "Moderate": "#b36a00", "Low": "#c0392b"
    },
    7: {
        "Low": "#1a7a4a", "Moderate": "#b36a00", "High": "#c0392b", "NC": "#888888"
    },
    8: {
        "Not recommended": "#d94f3d", "Use with caution": "#f5a623",
        "Recommended": "#6abf4b", "Highly recommended": "#1a7a2e"
    },
}

COLOR_CONFIG_FINAL_EVALUATION = {
    8: {
        "Highly recommended": "#1a7a2e", "Recommended": "#6abf4b",
        "Use with caution": "#f5a623", "Not recommended": "#d94f3d"
    },
    9: {
        "Insufficient ": "#d94f3d", "Cautionary": "#f5a623",
        "Acceptable": "#1a7a2e", "Suitable": "#6abf4b"
    }
}

# Named colour palettes used by the colour-picker widget
PALETTES = {
    # bokeh paired 12
    'paired12': [
        '#000000', '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99',
        '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99',
        '#b15928', '#ffffff',
    ],
    # d3 category 10
    'category10': [
        '#000000', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#ffffff',
    ],
    # 17 undertones https://lospec.com/palette-list/17undertones
    '17undertones': [
        '#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970',
        '#5ebb49', '#458352', '#dcd37b', '#fffee5', '#ffd035', '#cc9245',
        '#a15c3e', '#a42f3b', '#f45b7a', '#c24998', '#81588d', '#bcb0c2',
        '#ffffff',
    ],
    'basic': [
        '#FFFFFF', '#C8D2D7', '#969682', '#323C46', '#000000', '#FFE178',
        '#FAA50A', '#FA780A', '#ED0B00', '#870A00', '#F5C8DC', '#EB78A5',
        '#AF23A5', '#641946', '#4B0500', '#CDE6EB', '#8CC3D2', '#55A0B9',
        '#006487', '#00374B', '#8CD2B4', '#55D2B4', '#1EA028', '#96B419',
        '#556E28',
    ],
}

# Sidebar background colour
SIDEBAR_BG = "#232b43"

# Colour tokens for the info/help dialog
C_TEXT           = "#1a2a4a"   # near-navy body text
C_BULLET         = "#3a6bc4"   # blue bullet arrows
C_SECTION_BG     = "#eef2fb"   # tinted section header background
C_SECTION_BORDER = "#3a6bc4"   # left border on section headers
C_SECTION_TEXT   = "#1e3a6e"   # navy section header text
C_BORDER         = "#d0d8ed"   # light separator lines

# Periwinkle / lavender-blue — sampled from the "Compute metrics" button
C_BTN_BG         = "#c5cce8"
C_BTN_HOVER      = "#aab3d8"
C_BTN_PRESSED    = "#9099c4"
C_BTN_TEXT       = "#2a3560"

# ---------------------------------------------------------------------------
# 4. Stylesheet constants
# ---------------------------------------------------------------------------

# Stylesheet for the main application window
MAIN_WINDOW_STYLESHEET = """
QPushButton#btn_close, QPushButton#btn_maximize, QPushButton#btn_minimize {
    border: none;
    background: transparent;
    border-radius: 4px;
}

QPushButton#btn_close:hover {
    background-color: rgba(255, 0, 0, 100);
}

QPushButton#btn_maximize:hover {
    background-color: rgba(85, 255, 127, 100);
}

QPushButton#btn_minimize:hover {
    background-color: rgba(255, 170, 0, 100);
}

QFrame#central_widget_frame {
    background-color: #edf1f8;
    border-radius: 22px;
}

QFrame#side_menu_frame {
    background: #325372;
    border-radius: 10px;
}

QHeaderView::section {
    padding: 0px;
    height: 20px;
    border: 0.5px solid #aeadac;
    background: #dddddd;
}

QPushButton {
    padding: 5px;
    background-color: #dddddd;
    border: 0.5px solid #aeadac;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #d6e5fb;
    border: 1px solid #234471;
}

QPushButton:pressed:active {
    background-color: #5188d8;
    border: 1px solid #7e7eff;
}

QPushButton:focus {
    border: 1px solid #234471;
}
"""

# Stylesheet for the info/help popup dialog (uses the C_* colour tokens above)
INFO_DIALOG_STYLESHEET = f"""
QDialog {{
    background-color: #ffffff;
}}

QScrollArea {{
    background: white;
    border: none;
    border-top: 1px solid {C_BORDER};
}}

QScrollBar:vertical {{
    background: #f0f3fa;
    width: 7px;
    border-radius: 3px;
    margin: 2px 1px;
}}
QScrollBar::handle:vertical {{
    background: {C_BULLET};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}

QWidget#body_widget {{
    background: white;
}}

QLabel#content_label {{
    color: {C_TEXT};
    font-size: 13px;
    background: transparent;
}}

QFrame#footer_line {{
    background-color: {C_BORDER};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

QPushButton#close_btn {{
    background-color: {C_BTN_BG};
    color: {C_BTN_TEXT};
    border: none;
    border-radius: 6px;
    padding: 7px 52px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#close_btn:hover {{
    background-color: {C_BTN_HOVER};
}}
QPushButton#close_btn:pressed {{
    background-color: {C_BTN_PRESSED};
}}
"""

# ---------------------------------------------------------------------------
# 5. Text-content constants
# ---------------------------------------------------------------------------

# Tooltip shown in the pairwise-plot page
TIPS = """<p><strong><span style="text-decoration: underline;">Tip 1</span>:</strong><br>
      Click on a plot area to select it, then choose a dataset from the table to display it there.</p>
<p><strong><span style="text-decoration: underline;">Tip 2</span>:</strong><br>
Collapse the table section by moving the horizontal splitter down—this will open the table in a separate window.</p>"""

HOW_IT_WORKS_TEXT = """\
This tool helps you evaluate and compare 2D separation space occupation in a streamlined, visual environment. Here are its main functions:

• Imports and normalizes your 1D retention data
• Automatically generates all possible 2D combinations from the dataset
• Provides visual comparisons of the candidate separations
• Evaluates orthogonality from pairs of retention data
• Uses a multi-metric approach (12 orthogonality metrics currently implemented)
• Calculates and integrates all metrics into a composite orthogonality score
• Provides a balanced assessment of 2D separation space occupation
• Ranks candidate conditions based on chromatographically relevant criteria, including orthogonality, hypothetical 2D peak capacity, and a Heinisch inspired method
• Applies filters based on practical constraints (solvent compatibility, set-up complexity, green aspects, MS compatibility)
• Assists in the final selection of optimal conditions for experimental validation\
"""

BEFORE_YOU_BEGIN_TEXT = """\
Before using the tool, preliminary experimental data must be collected. The tool is designed to evaluate and compare candidate 2D combinations based on 1D scouting results, and therefore requires retention data as input.

Required steps prior to using the tool:
· Select a set of representative compounds relevant to the target application
· Design and perform 1D scouting experiments under different chromatographic conditions (e.g., columns, mobile phase, pH, modifiers, modes)
· Extract retention data for each compound and condition (peak widths can also be included if available, but are optional)
· Calculate experimental peak capacities

Once these data are collected and organized, they can be imported into the tool for orthogonality assessment and condition ranking.

For more details on experimental design and gradient setup, please refer to the associated publication and to the documentation link in About section.\
"""

USER_GUIDE_TEXT = """\
Step-by-step workflow:
To use the tool, follow the steps below, which match the sections and subsections in the menu bar, one by one. For a practical example, you can also watch the tutorial video in the About section.

Step 1 — Data Import and Normalization
A — Data import
· Upload retention times and peak capacity data from 1D scouting runs
· Accepted formats: Excel / CSV
· Minimum requirement: retention data (other input optional)

B — Data normalization
· Scaling of retention times to harmonize the retention space
· Particularly important when different column geometries are used
· Three scaling methods are available (the default option can be used if unsure)
· Additional inputs are required when selecting the void time and wosel approaches (void time and gradient end time)

Step 2 — Visual Comparison of Paired Conditions
· Pairwise plots of conditions are available in the "Data Plotting Pairwise" section
· Enables a quick visual assessment of separation space usage between dimensions

Step 3 — Orthogonality Assessment
· Calculation of multiple orthogonality metrics
· Visualization of the results for each metric

Step 4 — Redundancy Check (Correlation Matrix)
· Identify metrics that provide overlapping information
· The cross-correlation matrix highlights relationships between metrics and groups strongly correlated ones in a summary table

Step 5 — Final Evaluation & Ranking
· Calculation of a composite orthogonality score by averaging values across metric groups
· Estimation of hypothetical practical 2D peak capacity using either the suggested score or a user-defined one
· Ranking based on orthogonality only, hypothetical practical 2D peak capacity, or a Heinisch-inspired method
· Identification of the most promising 2D combinations based on practical criteria\
"""
