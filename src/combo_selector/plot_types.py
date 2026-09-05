"""Plot availability for public and internal application editions."""

from combo_selector import edition


ALL_PLOT_TYPES = [
    "Orthogonality Space",
    "Metric Removal Impact On Orthogonality Rank",
    "Metric Removal Impact On Practical Peak Capacity Rank",
    "Multi-Criteria Space",
    "Chromatographic Mode Performance",
    "Recommendation Distribution",
    "Feasibility Profile",
    "Final Rank vs Recommendation",
    "Final Rank Shift Scatter",
    "Final Rank Shift Distribution",
    "Rank Shift by Combination",
    "Top Rank Overlap",
    "Practical Peak Capacity Rank vs Final Consensus Rank",
    "Detected Compound Mode Distribution",
    "Detected Compound Combination Mode Distribution",
    "Metric Agreement Combination Mode Distribution",
]

PUBLIC_PLOT_TYPES = [
    "Multi-Criteria Space",
    "Metric Removal Impact On Orthogonality Rank",
    "Chromatographic Mode Performance",
    "Recommendation Distribution",
    "Feasibility Profile",
]


def get_plot_types() -> list[str]:
    """Return the plots exposed by the currently selected edition."""
    if edition.is_internal_edition():
        return ALL_PLOT_TYPES.copy()
    return PUBLIC_PLOT_TYPES.copy()


__all__ = ["ALL_PLOT_TYPES", "PUBLIC_PLOT_TYPES", "get_plot_types"]
