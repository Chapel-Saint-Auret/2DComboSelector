"""Plotting utilities for visualizing orthogonality metrics in 2D chromatography.

This module provides the PlotUtils class which handles all visualization tasks including:
- Scatter plots of retention time distributions
- Convex hull visualizations
- Bin box counting grids
- Linear and quadratic regression plots
- Asterisk stability diagrams
- Conditional entropy heatmaps
- Percent fit and percent bin visualizations
"""

from math import sqrt
from typing import Optional

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QDialog,QVBoxLayout
from matplotlib import collections, patches, ticker
from matplotlib.gridspec import GridSpec
from matplotlib.collections import QuadMesh
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as ticker
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from combo_selector.ui.widgets.custom_toolbar import CustomToolbar

SUBSET_THRESHOLDS = {
    "All": 100,
    "Top 50%": 50,
    "Top 20%": 20,
    "Top 10%": 10,
}

CRITERIA_COLUMN_MAP = {
    "All criteria":    None,
    "Orthogonality":   ("Orthogonality Rank",       "Orthogonality"),
    "Elution Domain":  ("Elution Domain Rank",       "Elution Domain"),
    "Peak Capacity":   ("Peak Capacity Rank",        "Peak Capacity"),
    "Final consensus": ("Final Rank",                "Final Consensus Rank"),
    "Peak rate":       ("Peak Detection Rate (%)",   "Peak rate (%)"),
}


CATEGORY_ORDER = [
    "Highly recommended",
    "Recommended",
    "Use with caution",
    "Not recommended",
]
COLORS = {
    "Highly recommended": "#1a7a2e",
    "Recommended": "#6abf4b",
    "Use with caution": "#f5a623",
    "Not recommended": "#d94f3d",
}

class PlotUtils:
    """Utility class for creating and managing orthogonality metric visualizations.

    This class encapsulates all plotting functionality for the 2DComboSelector application,
    providing methods to visualize various orthogonality metrics on matplotlib figures.

    Attributes:
        color bar: Matplotlib color bar object (currently unused).
        orthogonality_data (dict): Dictionary containing orthogonality metrics for all sets.
        fig (Figure): The matplotlib Figure object to draw on.
        axe (Axes): The matplotlib Axes object for plotting.
        set_number (str): Currently selected set identifier (e.g., 'Set 1').
        scatter_collection (PathCollection): Scatter plot collection for updating points.
    """

    def __init__(self, fig: Figure,model=None):
        """Initialize the PlotUtils with a matplotlib Figure.

        Args:
            fig (Figure): Matplotlib Figure object to use for all plotting operations.
        """
        super().__init__()

        self.model = model
        self.orthogonality_data = None
        self.fig = fig
        self.axe = None
        self.set_number = "Set 1"
        self.scatter_collection = None

    def set_orthogonality_result_data(self, orthogonality_result_df: pd.DataFrame) -> None:
        self.orthogonality_result_data = orthogonality_result_df

    def set_orthogonality_data(self, orthogonality_dict: dict) -> None:
        """Set the orthogonality data dictionary for plotting.

        Args:
            orthogonality_dict (dict): Dictionary mapping set identifiers to their
                                      orthogonality metric data.
        """
        self.orthogonality_data = orthogonality_dict

    def set_set_number(self, set_nb: str) -> None:
        """Set the current set number to plot.

        Args:
            set_nb (str): Set identifier (e.g., 'Set 1', 'Set 2').
        """
        self.set_number = set_nb

    def set_axe(self, axe) -> None:
        """Set the matplotlib Axes object for plotting.

        Args:
            axe (Axes): Matplotlib Axes object to draw on.
        """
        self.axe = axe

    def set_scatter_collection(self, scatter_collection) -> None:
        """Set the scatter plot collection for efficient updates.

        Args:
            scatter_collection (PathCollection): Existing scatter plot collection
                                                from axes.scatter().
        """
        self.scatter_collection = scatter_collection

    def __draw_figure(self) -> None:
        """Redraw the figure canvas and flush events.

        Private method to update the display after plotting operations.
        """

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def clf(self) -> None:
        """Clear the entire figure.

        Removes all axes, plots, and text from the figure.
        """
        self.fig.clf()

    def clean_axe(self) -> None:
        """Clear the entire axe.

        Removes everything (data, labels, titles) and resets the axis to default settings.
        """
        self.axe.clear()

    def clean_figure(self) -> None:
        """Clean the selected matplotlib axis while preserving background settings.

        Removes all plot elements (texts, lines, arrows, meshes, legends) while
        maintaining the white background and axis structure.

        Side Effects:
            - Removes all text annotations from axes and figure
            - Removes all lines and arrows
            - Removes all QuadMesh objects (heatmaps/colormeshes)
            - Clears legend labels
            - Resets background to white
        """
        # Remove texts and lines
        if self.axe:
            [text.remove() for text in self.axe.texts if text not in [self.annotation]]
            [line.remove() for line in self.axe.get_lines()]

        # Remove figure-level texts
        for text in self.fig.texts[:]:
            try:
                text.remove()
            except ValueError:
                pass

        for artist in self.axe.get_children():
            # Remove FancyArrowPatch (arrows)
            if isinstance(artist, patches.FancyArrow):
                artist.remove()

            if isinstance(artist, collections.LineCollection):
                artist.remove()

        # Remove additional lines and QuadMesh objects
        [line.remove() for line in self.axe.get_lines()]
        [quadmesh.remove() for quadmesh in self.axe.findobj(QuadMesh)]

        # Remove legend labels but keep handles
        handles, labels = self.axe.get_legend_handles_labels()
        for handle in handles:
            handle.set_label(None)

        # Force the background color back to white
        self.axe.set_facecolor("white")
        self.fig.patch.set_facecolor("white")

    def plot_scatter(
            self,
            set_number: str = "",
            title: Optional[str] = None,
            draw: bool = True,
            dirname: str = "",
    ) -> None:
        """Create or update a scatter plot of retention time data.

        Plots normalized retention times as a scatter plot with x and y values
        from the specified set's chromatography data.

        Args:
            set_number (str, optional): Set identifier to plot. If empty, uses
                                       self.set_number. Defaults to "".
            title (str, optional): Custom title for the plot. If None, uses set_number.
                                  Defaults to None.
            draw (bool, optional): Whether to redraw the figure. Defaults to True.
            dirname (str, optional): Directory path for saving (currently unused).
                                    Defaults to "".

        Side Effects:
            - Updates or creates scatter plot on self.axe
            - Sets axis title and labels
            - Updates self.scatter_collection
            - Redraws figure if draw=True

        Note:
            The scatter plot uses black circles (marker='o') with 50% transparency.
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]
        x, y = data["x_values"], data["y_values"]
        x_title, y_title = data["x_title"], data["y_title"]
        title = title or str(set_nb)

        # 1) Update title and labels
        self.axe.set_title(title, fontdict={"fontsize": 10}, pad=13)
        self.axe.set_xlabel(x_title, fontsize=11)
        self.axe.set_ylabel(y_title, fontsize=11)

        # 2) Create or update scatter
        if self.scatter_collection is None:
            self.scatter_collection = self.axe.scatter(
                x, y, s=20, c="k", marker="o", alpha=0.5
            )
        else:
            self.scatter_collection.set_offsets(list(zip(x, y)))

        # 3) Hide legend if present
        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        # 4) Redraw
        self.__draw_figure()

    def plot_percent_bin(
            self,
            set_number: str = "",
    ) -> None:
        """Plot the percent bin (%BIN) metric visualization with statistics.

        Displays a 5×5 grid showing occupied bins in red, along with statistics:
        - Sum of deviations
        - Sum of deviations for full spread
        - Sum of deviations for no spread
        - Final %BIN value

        Args:
            set_number (str, optional): Set identifier to plot. If empty, uses
                                       self.set_number. Defaults to "".

        Side Effects:
            - Draws colored mesh on axes showing occupied bins
            - Adds statistical text annotations to the figure
            - Hides legend if present
            - Redraws figure
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]["percent_bin"]
        H_color = data["mask"]
        percent_bin = data["value"]
        sad_dev_fs = data["sad_dev_fs"]
        sad_dev = data["sad_dev"]
        sad_dev_ns = data["sad_dev_ns"]
        xedges, yedges = data["edges"]

        # define a 5×5 grid
        self.axe.pcolormesh(
            xedges,
            yedges,
            H_color,
            alpha=0.5,
            cmap=ListedColormap(["red"]),
            edgecolors="k",
            linewidth=0.5,
        )

        # position the stats text just to the right of the axis
        pos = self.axe.get_position()
        x_text = pos.x1 + 0.01
        self.fig.text(
            x_text, 0.85, f"$\\sum dev$= {sad_dev:.2f}", fontsize=9, ha="left"
        )
        self.fig.text(
            x_text, 0.80, f"$\\sum dev_{{fs}}$= {sad_dev_fs:.2f}", fontsize=9, ha="left"
        )
        self.fig.text(
            x_text, 0.75, f"$\\sum dev_{{ns}}$= {sad_dev_ns:.2f}", fontsize=9, ha="left"
        )
        self.fig.text(x_text, 0.70, f"% BIN= {percent_bin:.2f}", fontsize=9, ha="left")

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        self.__draw_figure()

    def plot_modeling_approach(
            self, set_number: str = "", erase_previous: bool = True, draw: bool = True
    ) -> None:
        """Plot the modeling approach metric with bin grid and regression line.

        Displays occupied bins and overlays a linear regression line showing
        the relationship between dimensions.

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".
            erase_previous (bool, optional): Whether to remove old plot elements
                                            before drawing. Defaults to True.
            draw (bool, optional): Whether to redraw the figure. Defaults to True.

        Side Effects:
            - Removes old lines and meshes if erase_previous=True
            - Draws colored mesh showing occupied bins
            - Plots regression line in red
            - Adds legend with regression equation
            - Redraws figure if draw=True
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]

        if erase_previous:
            # remove old lines and QuadMesh objects
            for line in self.axe.get_lines():
                line.remove()
            for mesh in self.axe.findobj(QuadMesh):
                mesh.remove()

        x = data["x_values"]
        H_color = data["modeling_approach"]["color_mask"]
        xedges, yedges = data["modeling_approach"]["edges"]
        slope, intercept, r, p, se = data["linregress"]

        self.axe.pcolormesh(
            xedges,
            yedges,
            H_color,
            alpha=0.5,
            cmap=ListedColormap(["red"]),
            edgecolors="k",
            linewidth=0.5,
        )

        # plot fitted line
        self.axe.plot(x, intercept + slope * x, "r", label="fitted line")

        # build legend entries
        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="",
                color="w",
                label=f"$y = {slope:.2f}x{'+' if intercept >= 0 else ''}{intercept:.2f}$",
            )
        ]

        # draw legend
        legend = self.axe.legend(
            handles=legend_elements,
            frameon=False,
            fontsize=9,
            handlelength=0,
            handletextpad=0.5,
            labelspacing=0.2,
        )
        # style the regression equation entry
        legend.get_texts()[-1].set_fontweight("bold")
        legend.get_texts()[-1].set_color("navy")

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        if draw:
            self.__draw_figure()

    def plot_bin_box(
            self, set_number: str = "", erase_previous: bool = True, draw: bool = True
    ) -> None:
        """Plot the bin box counting grid overlay.

        Displays a grid showing which bins contain at least one peak, used for
        the bin box counting orthogonality metric.

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".
            erase_previous (bool, optional): Whether to remove old plot elements.
                                            Defaults to True.
            draw (bool, optional): Whether to redraw the figure. Defaults to True.

        Side Effects:
            - Removes old lines and meshes if erase_previous=True
            - Draws colored mesh showing occupied bins in red
            - Hides legend if present
            - Redraws figure if draw=True
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]

        if erase_previous:
            # remove old lines and QuadMesh objects
            for line in self.axe.get_lines():
                line.remove()
            for mesh in self.axe.findobj(QuadMesh):
                mesh.remove()

        H_color = data["bin_box"]["color_mask"]
        xedges, yedges = data["bin_box"]["edges"]
        self.axe.pcolormesh(
            xedges,
            yedges,
            H_color,
            alpha=0.5,
            cmap=ListedColormap(["red"]),
            edgecolors="k",
            linewidth=0.5,
        )

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        if draw:
            self.__draw_figure()

    def plot_conditional_entropy(
            self, set_number: str = "", erase_previous: bool = True, draw: bool = True
    ) -> None:
        """Plot the conditional entropy heatmap.

        Displays a 2D histogram showing the distribution of peaks, colored by
        density using the 'jet' colormap. Used for visualizing the conditional
        entropy metric H(Y|X).

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".
            erase_previous (bool, optional): Whether to remove old plot elements.
                                            Defaults to True.
            draw (bool, optional): Whether to redraw the figure. Defaults to True.

        Side Effects:
            - Removes old lines and meshes if erase_previous=True
            - Draws density heatmap using 'jet' colormap
            - Hides legend if present
            - Redraws figure if draw=True
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]

        if erase_previous:
            # remove old lines and QuadMesh objects
            for line in self.axe.get_lines():
                line.remove()
            for mesh in self.axe.findobj(QuadMesh):
                mesh.remove()

        histogram = data["conditional_entropy"]["histogram"]
        xedges, yedges = data["conditional_entropy"]["edges"]
        colormesh = self.axe.pcolormesh(
            xedges,
            yedges,
            histogram,
            alpha=0.8,
            cmap="jet",
        )
        # self.colorbar = self.fig.colorbar(colormesh, ax=self.axe)

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        if draw:
            self.__draw_figure()

    def plot_asterisk(self, set_number: str = "") -> None:
        """Draw the asterisk stability diagram for orthogonality visualization.

        Creates a specialized plot showing:
        - Diagonal and cross lines representing Z-, Z+, Z1, Z2 metrics
        - Arrows showing standard deviations in different directions
        - Labels with metric values

        This visualization helps assess the stability and spread of peaks
        along different axes and diagonals.

        Args:
            set_number (str, optional): Set identifier to plot. If empty, uses
                                       self.set_number. Defaults to "".

        Side Effects:
            - Resets axes limits to [0, 1]
            - Draws diagonal lines, cross lines, and arrows
            - Adds text labels for Z metrics and sigma values
            - Creates legend with metric values
            - Redraws figure

        Note:
            The asterisk metrics include:
            - Z-: Diagonal stability (bottom-left to top-right)
            - Z+: Anti-diagonal stability (top-left to bottom-right)
            - Z1: Vertical stability
            - Z2: Horizontal stability
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]["asterisk_metrics"]
        z_minus, z_plus = data["z_minus"], data["z_plus"]
        Z1, Z2 = data["z1"], data["z2"]
        szm, szp, sz1, sz2 = (
            data["sigma_sz_minus"],
            data["sigma_sz_plus"],
            data["sigma_sz1"],
            data["sigma_sz2"],
        )

        # reset axes limits
        self.axe.set_xlim(0, 1)
        self.axe.set_ylim(0, 1)

        # clear old legend entries
        if leg := self.axe.get_legend():
            for handle in leg.legend_handles:
                handle.set_label(None)

        # small helper to draw one arrow
        def draw_arrow(start: tuple, end: tuple, **kw) -> None:
            """Draw an arrow from start to end coordinates.

            Args:
                start (tuple): (x, y) start coordinates.
                end (tuple): (x, y) end coordinates.
                **kw: Additional keyword arguments for arrow styling.
            """
            dx, dy = end[0] - start[0], end[1] - start[1]
            self.axe.arrow(
                start[0],
                start[1],
                dx,
                dy,
                head_width=0.01,
                length_includes_head=True,
                color="red",
                **kw,
            )

        # place the four corner labels
        self.axe.text(0.16, 0.03, "$Z_-$", fontsize="medium")
        self.axe.text(0.84, 0.95, "$Z_-$", fontsize="medium")
        self.axe.text(0.51, 0.02, "$Z_1$", fontsize="medium")
        self.axe.text(0.51, 0.94, "$Z_1$", fontsize="medium")
        self.axe.text(0.10, 0.45, "$Z_2$", fontsize="medium")
        self.axe.text(0.90, 0.45, "$Z_2$", fontsize="medium")
        self.axe.text(0.84, 0.02, "$Z_+$", fontsize="medium")
        self.axe.text(0.16, 0.94, "$Z_+$", fontsize="medium")

        # compute arrow offsets
        factor = 2.5
        dszm = sqrt(2) * szm / factor
        dszp = sqrt(2) * szp / factor
        dsz1 = sqrt(2) * sz1 / factor
        dsz2 = sqrt(2) * sz2 / factor

        # draw the four sigma arrows + labels
        draw_arrow((0.2, 0.2 + dszm), (0.2 + dszm, 0.2))
        draw_arrow((0.2 + dszm, 0.2), (0.2, 0.2 + dszm))
        self.axe.text(
            0.2 + dszm, 0.17, f"$S_{{Z_-}}$:{szm:.3f}", color="red", fontsize="medium"
        )

        draw_arrow((0.2, 0.8 - dszp), (0.2 + dszp, 0.8))
        draw_arrow((0.2 + dszp, 0.8), (0.2, 0.8 - dszp))
        self.axe.text(
            0.2, 0.75 - dszp, f"$S_{{Z_+}}$:{szp:.3f}", color="red", fontsize="medium"
        )

        draw_arrow((0.5 - dsz1 / 2, 0.8), (0.5 + dsz1 / 2, 0.8))
        draw_arrow((0.5 + dsz1 / 2, 0.8), (0.5 - dsz1 / 2, 0.8))
        self.axe.text(
            0.61 - dsz1 / 2,
            0.75,
            f"$S_{{Z_1}}$:{sz1:.3f}",
            color="red",
            fontsize="medium",
        )

        draw_arrow((0.8, 0.5 - dsz2 / 2), (0.8, 0.5 + dsz2 / 2))
        draw_arrow((0.8, 0.5 + dsz2 / 2), (0.8, 0.5 - dsz2 / 2))
        self.axe.text(
            0.75,
            0.45 - dsz2 / 2,
            f"$S_{{Z_2}}$:{sz2:.3f}",
            color="red",
            fontsize="medium",
        )

        # now the diagonal & cross lines
        time = np.linspace(0, 1, 6)
        dummy_1 = self.axe.plot(
            time, time, label=f"$Z_-$: {z_minus:.3f}", color="black", linestyle="-"
        )[0]
        dummy_2 = self.axe.plot(
            time, 1 - time, label=f"$Z_+$: {z_plus:.3f}", color="black", linestyle="--"
        )[0]
        self.axe.vlines(
            0.5, 0, 1, label=f"$Z_1$: {Z1:.3f}", linestyle="-.", color="black"
        )
        self.axe.hlines(
            0.5, 0, 1, label=f"$Z_2$: {Z2:.3f}", linestyle=":", color="black"
        )

        # final legend
        self.axe.legend(bbox_to_anchor=(1, 1), loc="upper left")

        # redraw
        self.__draw_figure()

    def plot_linear_reg(
            self,
            set_number: str = "",
    ) -> None:
        """Draw linear regression line with correlation statistics.

        Plots the fitted regression line and displays correlation coefficients:
        - Pearson r (linear correlation)
        - Spearman ρ (rank correlation)
        - Kendall τ (ordinal correlation)
        - Regression equation

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".

        Side Effects:
            - Clears old lines from axes
            - Plots red regression line
            - Adds legend with correlation statistics
            - Redraws figure
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]
        x = data["x_values"]
        slope, intercept, r, p, se = data["linregress"]
        r = data["pearson_r"]
        rho = data["spearman_rho"]
        tau = data["kendall_tau"]

        # reset axes & clear old lines
        self.axe.set_xlim(0, 1)
        self.axe.set_ylim(0, 1)
        for line in self.axe.get_lines():
            line.remove()

        # plot fitted line
        self.axe.plot(x, intercept + slope * x, "r", label="fitted line")

        # build legend entries
        legend_elements = [
            Line2D([0], [0], marker="", color="w", label=f"Pearson $r$: {r:.2f}"),
            Line2D([0], [0], marker="", color="w", label=f"Spearman $ρ$: {rho:.2f}"),
            Line2D([0], [0], marker="", color="w", label=f"Kendall $τ$: {tau:.2f}"),
            Line2D(
                [0],
                [0],
                marker="",
                color="w",
                label=f"$y = {slope:.2f}x{'+' if intercept >= 0 else ''}{intercept:.2f}$",
            ),
        ]

        # draw legend
        legend = self.axe.legend(
            handles=legend_elements,
            frameon=False,
            fontsize=9,
            handlelength=0,
            handletextpad=0.5,
            labelspacing=0.2,
        )
        # style the regression equation entry
        legend.get_texts()[-1].set_fontweight("bold")
        legend.get_texts()[-1].set_color("navy")

        self.__draw_figure()

    def plot_percent_fit_xy(
            self,
            set_number: str = "",
    ) -> None:
        """Plot %FIT metric with X vs Y quadratic regression.

        Displays quadratic curve fit for predicting Y from X, along with:
        - ΔXY average deviation
        - ΔXY standard deviation
        - Overall %FIT value
        - Quadratic equation

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".

        Side Effects:
            - Plots red quadratic curve
            - Updates scatter collection with (x, y) data
            - Adds statistical text annotations
            - Sets axis labels
            - Hides legend
            - Redraws figure
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]
        x, y = data["x_values"], data["y_values"]
        x_title = data["x_title"]
        y_title = data["y_title"]
        model_xy = data["quadratic_reg_xy"]
        pct = data["percent_fit"]
        avg, sd = pct["delta_xy_avg"], pct["delta_xy_sd"]
        fit_val = pct["value"]
        coeffs = model_xy.coeffs

        # draw quadratic fit
        xs = np.linspace(0, 10, 100)
        self.axe.plot(xs, model_xy(xs), color="red")

        # update scatter offsets
        self.scatter_collection.set_offsets(list(zip(x, y)))

        # labels
        self.axe.set_xlabel(x_title, fontsize=12)
        self.axe.set_ylabel(y_title, fontsize=12)

        pos = self.axe.get_position()
        tx = pos.x1 + 0.01
        self.fig.text(
            tx, 0.85, f"$\\Delta xy_{{AVG}}$= {avg:.2f}", fontsize=9, ha="left"
        )
        self.fig.text(tx, 0.80, f"$\\Delta xy_{{SD}}$= {sd:.2f}", fontsize=9, ha="left")
        self.fig.text(tx, 0.75, f"%FIT= {fit_val:.2f}", fontsize=9, ha="left")
        eq = f"y = {coeffs[0]:.2f}x² {'+' if coeffs[1] >= 0 else ''}{coeffs[1]:.2f}x {'+' if coeffs[2] >= 0 else ''}{coeffs[2]:.2f}"
        self.fig.text(tx, 0.70, eq, fontdict={"fontsize": 10})

        # hide any legend
        if leg := self.axe.get_legend():
            leg.set_visible(False)

        self.__draw_figure()

    def plot_percent_fit_yx(
            self,
            set_number: str = "",
    ) -> None:
        """Plot %FIT metric with Y vs X quadratic regression (axes swapped).

        Displays quadratic curve fit for predicting X from Y, along with:
        - ΔYX average deviation
        - ΔYX standard deviation
        - Overall %FIT value
        - Quadratic equation

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".

        Side Effects:
            - Plots red quadratic curve
            - Updates scatter collection with (y, x) data (swapped)
            - Adds statistical text annotations
            - Sets axis labels
            - Hides legend
            - Redraws figure

        Note:
            This is the reverse direction compared to plot_percent_fit_xy,
            useful for assessing bidirectional correlation.
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]
        x, y = data["x_values"], data["y_values"]
        x_title = data["x_title"]
        y_title = data["y_title"]
        model_yx = data["quadratic_reg_yx"]
        pct = data["percent_fit"]
        avg, sd = pct["delta_yx_avg"], pct["delta_yx_sd"]
        fit_val = pct["value"]
        coeffs = model_yx.coeffs

        xs = np.linspace(0, 10, 100)
        self.axe.plot(xs, model_yx(xs), color="red")

        self.scatter_collection.set_offsets(list(zip(y, x)))

        self.axe.set_xlabel(x_title, fontsize=12)
        self.axe.set_ylabel(y_title, fontsize=12)

        pos = self.axe.get_position()
        tx = pos.x1 + 0.01
        self.fig.text(
            tx, 0.85, f"$\\Delta yx_{{AVG}}$= {avg:.2f}", fontsize=9, ha="left"
        )
        self.fig.text(tx, 0.80, f"$\\Delta yx_{{SD}}$= {sd:.2f}", fontsize=9, ha="left")
        self.fig.text(tx, 0.75, f"%FIT= {fit_val:.2f}", fontsize=9, ha="left")
        eq = f"y = {coeffs[0]:.2f}x² {'+' if coeffs[1] >= 0 else ''}{coeffs[1]:.2f}x {'+' if coeffs[2] >= 0 else ''}{coeffs[2]:.2f}"
        self.fig.text(tx, 0.70, eq, fontdict={"fontsize": 10})

        if leg := self.axe.get_legend():
            leg.set_visible(False)

        self.__draw_figure()

    def plot_convex_hull(
            self, set_number: str = "", erase_previous: bool = True
    ) -> None:
        """Draw the convex hull boundary around retention time data points.

        Visualizes the smallest convex polygon that contains all data points,
        used for the convex hull orthogonality metric.

        Args:
            set_number (str, optional): Set identifier to plot. Defaults to "".
            erase_previous (bool, optional): Whether to remove old lines before
                                            drawing. Defaults to True.

        Side Effects:
            - Removes old lines if erase_previous=True
            - Plots red lines connecting hull vertices
            - Hides legend if present
            - Redraws figure

        Note:
            The convex hull is computed using scipy.spatial.ConvexHull and
            stored in the orthogonality_data dictionary.
        """
        if not self.orthogonality_data:
            return

        if set_number == "":
            set_nb = self.set_number
        else:
            set_nb = set_number

        if erase_previous:
            for line in self.axe.get_lines():
                line.remove()

        hull = self.orthogonality_data[set_nb]["convex_hull"]
        subset = self.orthogonality_data[set_nb]["hull_subset"]

        # draw each simplex
        if hull:
            for simplex in hull.simplices:
                self.axe.plot(subset[simplex, 0], subset[simplex, 1], "r-")

        if leg := self.axe.get_legend():
            leg.set_visible(False)

        self.__draw_figure()

    def plot_coverage_vs_distribution(self):

        x = self.orthogonality_result_data['Coverage Score']
        y = self.orthogonality_result_data['Distribution Score']

        self.axe.set_xlabel('Coverage Score', fontsize=12)
        self.axe.set_ylabel('Distribution Score', fontsize=12)


        # 2) Create or update scatter
        self.scatter_collection = self.axe.scatter(
                x, y, s=20, c="k", marker="o", alpha=0.5
            )

        # 3) Hide legend if present
        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_peak_capacity_vs_consensus_score(self):

        x = self.orthogonality_result_data['Practical 2D Peak Capacity']
        y = self.orthogonality_result_data['Consensus Score']

        self.axe.set_xlabel('Practical 2D Peak Capacity', fontsize=12)
        self.axe.set_ylabel('Consensus Score', fontsize=12)

        # 2) Create or update scatter

        self.scatter_collection = self.axe.scatter(
                x, y, s=20, c="k", marker="o", alpha=0.5
            )

        # 3) Hide legend if present
        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_top_ranked_combination(self,number_of_rank_to_show):

        if number_of_rank_to_show == 'all':
            index = None
        else:
            index = int(number_of_rank_to_show)

        x = self.orthogonality_result_data['Orthogonality Rank']
        y = self.orthogonality_result_data['2D Combination']

        sorted_x = x.sort_values()

        sorted_x_index = list(sorted_x.index)

        sorted_y = y[sorted_x_index]

        sorted_x = sorted_x[0:index-1]
        sorted_y = sorted_y[0:index-1]

        self.axe.barh(sorted_y, sorted_x)

        # 3) Hide legend if present
        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_orthogonality_space(self, subset: str = "All"):

        self.fig.clear()
        self.axe = self.fig.add_subplot(111)
        self.axe.set_box_aspect(1)
        self.set_annotation()

        df = self.model.get_filtered_result_df().copy()
        n = self.model.get_number_of_combination()

        final_rank = pd.to_numeric(df['Final Rank'], errors='coerce')
        orthogonality_rank = pd.to_numeric(df['Orthogonality Rank'], errors='coerce')

        final_rank_pct = (final_rank / n) * 100          # controls which points are shown
        orthogonality_rank_pct = (orthogonality_rank / n) * 100  # controls point color

        # ------------------------------------------------------------------
        # Subset filter — same logic as plot_multi_criteria_space
        # ------------------------------------------------------------------
        threshold = SUBSET_THRESHOLDS.get(subset, 0)
        mask = final_rank_pct <= threshold

        df_filtered = df[mask]
        orthogonality_rank_pct_filtered = orthogonality_rank_pct[mask]

        if df_filtered.empty:
            self._show_missing_data()
            return

        x = pd.to_numeric(df_filtered['Coverage Score'], errors='coerce')
        y = pd.to_numeric(df_filtered['Distribution Score'], errors='coerce')

        valid = x.notna() & y.notna()
        x = x[valid]
        y = y[valid]
        orthogonality_rank_pct_filtered = orthogonality_rank_pct_filtered[valid]

        # ------------------------------------------------------------------
        # Color by Orthogonality rank percentile
        # Same palette as plot_multi_criteria_space
        # ------------------------------------------------------------------
        def get_color(pct):
            if pct <= 1:
                return '#1A3A9E'   # Top 1%
            elif pct <= 5:
                return '#A0379A'   # Top 5%
            elif pct <= 10:
                return '#E64981'   # Top 10%
            elif pct <= 25:
                return '#FF7C64'   # Top 25%
            else:
                return '#F9F871'   # > 25%

        colors = np.array([get_color(p) for p in orthogonality_rank_pct_filtered])

        self.axe.scatter(x, y,
                         c=colors, s=15,
                         edgecolors='k', alpha=0.85,
                         linewidths=0.3, picker=5)

        # ------------------------------------------------------------------
        # Legend — only show tiers present in the filtered data
        # ------------------------------------------------------------------
        tier_defs = [
            (1, '#1A3A9E', 'Top 1%'),
            (5, '#A0379A', 'Top 5%'),
            (10,'#E64981', 'Top 10%'),
            (25,'#FF7C64', 'Top 25%'),
            (100,'#F9F871', '> 25%'),
        ]

        max_pct = orthogonality_rank_pct_filtered.max() \
            if len(orthogonality_rank_pct_filtered) > 0 else 0

        legend_elements = [
            patches.Patch(facecolor=color, edgecolor='gray', linewidth=0.5, label=label)
            for thresh, color, label in tier_defs
            if max_pct >= thresh
        ]

        # ------------------------------------------------------------------
        # Axes formatting
        # ------------------------------------------------------------------
        subtitle = f"Showing: {subset}" if subset != "All" else "All combinations"

        if subset == "All":
            self.axe.set_xlim(0, 1)
            self.axe.set_ylim(0, 1)
        else:
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()

            x_pad = max((x_max - x_min) * 0.08, 0.02)
            y_pad = max((y_max - y_min) * 0.08, 0.02)

            self.axe.set_xlim(max(0, x_min - x_pad), min(1, x_max + x_pad))
            self.axe.set_ylim(max(0, y_min - y_pad), min(1, y_max + y_pad))

        self.axe.set_box_aspect(1)
        self.axe.set_xlabel('Coverage Score', fontsize=12)
        self.axe.set_ylabel('Distribution Score', fontsize=12)
        self.axe.tick_params(axis='both', labelsize=11)
        self.axe.grid(True, linestyle=':', linewidth=0.9, alpha=0.5)
        self.axe.set_axisbelow(True)

        self.axe.text(0.5, 1.13, 'Orthogonality Space',
                      transform=self.axe.transAxes, ha='center', va='bottom',
                      fontsize=22, fontweight='bold')
        self.axe.text(0.5, 1.06, subtitle,
                      transform=self.axe.transAxes, ha='center', va='bottom',
                      fontsize=11, style='italic', color='0.45')

        self.fig.legend(handles=legend_elements,
                        title='Orthogonality rank\npercentile',
                        loc='center right',
                        bbox_to_anchor=(1.0, 0.5),
                        fontsize=10, title_fontsize=10,
                        frameon=True, edgecolor='gray')

        self.fig.subplots_adjust(left=0.11, right=0.80, bottom=0.12, top=0.80)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_metric_removal_impact(self):
        """Plot the impact of removing each metric on orthogonality rank.

        Displays a horizontal bar chart where each bar corresponds to one removed
        metric and its associated median orthogonality rank.

        Expected data columns:
            - "Metric Removed"
            - "Median Orthogonality Rank"
        """
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        impact_df = self.model.get_metric_removal_impact_on_orthogonality_rank_df()

        if impact_df is None or impact_df.empty:
            self._show_missing_data()
            return

        plot_df = impact_df.copy()

        if "Metric Removed" not in plot_df.columns or "Median Orthogonality Rank Difference" not in plot_df.columns:
            self._show_missing_data()
            return

        plot_df["Median Orthogonality Rank Difference"] = pd.to_numeric(
            plot_df["Median Orthogonality Rank Difference"], errors="coerce"
        )
        plot_df = plot_df.dropna(subset=["Median Orthogonality Rank Difference"])

        if plot_df.empty:
            self._show_missing_data()
            return

        plot_df = plot_df.sort_values("Median Orthogonality Rank Difference", ascending=True)

        y = plot_df["Metric Removed"]
        x = plot_df["Median Orthogonality Rank Difference"].round(1)

        bars = self.axe.barh(y, x, color="#4C78A8", edgecolor="#2F4B6E", alpha=0.9)

        for bar, value in zip(bars, x):
            self.axe.text(
                value + (x.max() * 0.01 if x.max() > 0 else 0.1),
                bar.get_y() + bar.get_height() / 2,
                f"{value:.2f}",
                va="center",
                ha="left",
                fontsize=8,
                color="#333333",
            )

        self.axe.set_xlabel("Median Rank Shift (% of total combinations)", fontsize=10)
        self.axe.set_ylabel("Metric Removed", fontsize=10)
        self.axe.tick_params(axis="both", labelsize=8)
        self.axe.grid(True, axis="x", linestyle="--", linewidth=0.4, alpha=0.5)
        self.axe.set_axisbelow(True)
        self.axe.spines[["top", "right"]].set_visible(False)

        self.axe.text(
            0.5, 1.08,
            "Metric Removal Impact",
            transform=self.axe.transAxes,
            ha="center", va="bottom",
            fontsize=16, fontweight="bold"
        )
        self.axe.text(
            0.5, 1.02,
            "Median orthogonality rank difference after removing each metric",
            transform=self.axe.transAxes,
            ha="center", va="bottom",
            fontsize=9, style="italic", color="dimgray"
        )

        self.fig.subplots_adjust(left=0.34, right=0.95, top=0.84, bottom=0.12)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_multi_criteria_space(self, subset: str = "All", axis_scale: str = "Auto"):

        self.fig.clear()
        self.axe = self.fig.add_subplot(111)
        self.axe.set_box_aspect(1)
        self.set_annotation()

        df = self.orthogonality_result_data.copy()

        peak_capacity = df['Hypothetical 2D Peak Capacity']
        elution_domain = df['Elution Domain']

        peak_capacity_available = pd.to_numeric(peak_capacity, errors='coerce').notna().any()
        elution_domain_available = pd.to_numeric(elution_domain, errors='coerce').notna().any()

        full_criteria = peak_capacity_available and elution_domain_available
        reduced_criteria = peak_capacity_available ^ elution_domain_available  # XOR: only one available

        if not full_criteria and not reduced_criteria:
            self._show_missing_data()
            return

        # ------------------------------------------------------------------
        # Shared: rank-based subset filtering + coloring
        # ------------------------------------------------------------------
        final_rank = pd.to_numeric(df['Final Rank'], errors='coerce')
        orthogonality_rank = pd.to_numeric(df['Orthogonality Rank'], errors='coerce')
        n = len(df)

        final_rank_pct = (final_rank / n) * 100
        orthogonality_rank_pct = (orthogonality_rank / n) * 100

        threshold = SUBSET_THRESHOLDS.get(subset, 0)
        mask = final_rank_pct <= threshold

        df = df[mask]
        final_rank_pct = final_rank_pct[mask]
        orthogonality_rank_pct = orthogonality_rank_pct[mask]

        if df.empty:
            self._show_missing_data()
            return

        def get_color(pct):
            if pct <= 1:
                return '#1A3A9E'   # Top 1%
            elif pct <= 5:
                return '#A0379A'   # Top 5%
            elif pct <= 10:
                return '#E64981'   # Top 10%
            elif pct <= 25:
                return '#FF7C64'   # Top 25%
            else:
                return '#F9F871'   # > 25%

        colors = np.array([get_color(p) for p in orthogonality_rank_pct])

        # ------------------------------------------------------------------
        # Near-identical peak rate detection + jitter (reduced criteria only)
        # ------------------------------------------------------------------
        def _is_near_identical(series):
            """Return True if value range < 1% (non-informative for visualization)."""
            clean = pd.to_numeric(series, errors='coerce').dropna()
            if len(clean) == 0:
                return False
            return (clean.max() - clean.min()) < 1.0

        def _apply_jitter(series):
            """Add small vertical jitter for visibility; seed fixed for reproducibility."""
            pr_range = series.max() - series.min()
            amplitude = max(pr_range * 0.5, 0.15)
            np.random.seed(42)
            return series + np.random.normal(0, amplitude, size=len(series))

        # ------------------------------------------------------------------
        # Axis scale helper
        # ------------------------------------------------------------------
        def apply_scale(ax, subset: str, scale: str):

            if subset == "All":
                self.axe.set_xlim(0, 1)
                self.axe.set_ylim(0, 1)
            else:
                x_min, x_max = x.min(), x.max()
                y_min, y_max = y.min(), y.max()

                x_pad = max((x_max - x_min) * 0.08, 0.02)
                y_pad = max((y_max - y_min) * 0.08, 0.02)

                self.axe.set_xlim(max(0, x_min - x_pad), min(1, x_max + x_pad))
                self.axe.set_ylim(max(0, y_min - y_pad), min(1, y_max + y_pad))

            s = 'log' if scale == 'Auto' else scale.lower()
            ax.set_xscale(s)
            ax.set_yscale(s)
            if s == 'log':
                ax.xaxis.set_major_formatter(
                    ticker.FuncFormatter(lambda val, _: f"{int(val):,}")
                )
                ax.xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=5))
                ax.xaxis.set_minor_locator(ticker.NullLocator())
                ax.tick_params(axis="x", labelsize=6)   # smaller to avoid overlap


        # ------------------------------------------------------------------
        # Full Criteria — both Hypothetical 2D Peak Capacity & Elution Domain
        # ------------------------------------------------------------------
        jitter_applied = False   # default; only relevant in reduced criteria

        if full_criteria:
            x = pd.to_numeric(df['Hypothetical 2D Peak Capacity'], errors='coerce')
            y = pd.to_numeric(df['Elution Domain'], errors='coerce')

            valid = x.notna() & y.notna()
            x, y, colors_plot = x[valid], y[valid], colors[valid.values]

            self.axe.scatter(x, y,
                             c=colors_plot, s=15,
                             edgecolors='k', alpha=0.85,
                             linewidths=0.3, picker=5)

            apply_scale(self.axe, subset, axis_scale)
            self.axe.tick_params(axis='y', labelsize=8)

            if x.notna().any():
                self.axe.set_xlim(x.min() * 0.8, x.max() * 1.2)
            if y.notna().any():
                self.axe.set_ylim(y.min() * 0.8, y.max() * 1.2)

            self.axe.set_xlabel('Hypothetical 2D Peak Capacity', fontsize=10)
            self.axe.set_ylabel('Elution Domain (%)', fontsize=10)

            plot_title = 'Multi-Criteria Space'
            plot_subtitle = f'Hypothetical peak capacity vs elution domain · {subset}'

        # ------------------------------------------------------------------
        # Reduced Criteria — only one of the two columns available
        # ------------------------------------------------------------------
        elif reduced_criteria:
            if elution_domain_available:
                x = pd.to_numeric(df['Elution Domain'], errors='coerce')
                x_label = 'Elution Domain'
            else:
                x = pd.to_numeric(df['Hypothetical 2D Peak Capacity'], errors='coerce')
                x_label = 'Hypothetical 2D Peak Capacity'

            y_raw = pd.to_numeric(df['Peak Detection Rate (%)'], errors='coerce')

            valid = x.notna() & y_raw.notna()
            x = x[valid]
            y_raw = y_raw[valid]
            colors_plot = colors[valid.values]

            # ← Detect near-identical peak rate and apply jitter if needed
            jitter_applied = _is_near_identical(y_raw)
            if jitter_applied:
                y_display = _apply_jitter(y_raw)
            else:
                y_display = y_raw.copy()
            y = y_display
            self.axe.scatter(x, y_display,
                             c=colors_plot, s=15,
                             edgecolors='k', alpha=0.85,
                             linewidths=0.3, picker=5)

            apply_scale(self.axe,subset , axis_scale)
            self.axe.tick_params(axis='y', labelsize=8)

            if x.notna().any():
                self.axe.set_xlim(x.min() * 0.8, x.max() * 1.2)

            # ← If jittered, zoom y-axis around true peak rate center
            if jitter_applied:
                pr_center = y_raw.mean()
                pr_spread = max(y_display.max() - y_display.min(), 0.5)
                self.axe.set_ylim(pr_center - pr_spread * 2.5,
                                  pr_center + pr_spread * 2.5)
            elif y_raw.notna().any():
                self.axe.set_ylim(y_raw.min() * 0.8, y_raw.max() * 1.2)

            self.axe.set_xlabel(x_label, fontsize=10)
            self.axe.set_ylabel('Peak Detection Rate (%)', fontsize=10)

            plot_title = 'Multi-Criteria Space — Reduced Criteria'

            if elution_domain_available:
                self.axe.set_xlim(0,100)
                self.axe.set_ylim(0,100)
            # ← Subtitle warns about jitter when applied
            if jitter_applied:
                plot_subtitle = (
                    'Vertical jitter added for visibility; peak rate values are near-identical.'
                )
            else:
                plot_subtitle = f'{x_label} vs peak detection rate · {subset}'

        # ------------------------------------------------------------------
        # Shared: grid, titles, legend
        # ------------------------------------------------------------------
        self.axe.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.5)

        self.axe.text(0.5, 1.10, plot_title,
                      transform=self.axe.transAxes,
                      ha='center', va='bottom',
                      fontsize=16, fontweight='bold')

        self.axe.text(0.5, 1.04, plot_subtitle,
                      transform=self.axe.transAxes,
                      ha='center', va='bottom',
                      fontsize=9,
                      style='italic',
                      color='#b05000' if jitter_applied else 'dimgray')

        legend_elements = [
            patches.Patch(color='#1A3A9E', label='Top 1%'),
            patches.Patch(color='#A0379A', label='Top 5%'),
            patches.Patch(color='#E64981', label='Top 10%'),
            patches.Patch(color='#FF7C64', label='Top 25%'),
            patches.Patch(color='#F9F871', label='> 25%'),
        ]
        self.fig.legend(handles=legend_elements,
                        title="Orthogonality rank\npercentile",
                        loc='center right',
                        bbox_to_anchor=(1.0, 0.5),
                        fontsize=8, title_fontsize=8,
                        frameon=True, edgecolor='gray')

        self.fig.subplots_adjust(left=0.12, right=0.82, top=0.84, bottom=0.12)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_chroma_mode_performance(self, view: str = "Heatmap", criteria: str = None):
        self.fig.clear()

        # ------------------------------------------------------------------
        # Availability checks
        # ------------------------------------------------------------------
        peak_capacity_available = pd.to_numeric(
            self.orthogonality_result_data['Hypothetical 2D Peak Capacity'], errors='coerce'
        ).notna().any()

        elution_domain_available = pd.to_numeric(
            self.orthogonality_result_data['Elution Domain'], errors='coerce'
        ).notna().any()

        # ------------------------------------------------------------------
        # HEATMAP
        # ------------------------------------------------------------------
        if view == "Heatmap":
            median_df = self.model.get_median_rank_score_table()

            # Drop unavailable rank columns
            cols_to_drop = []
            if not elution_domain_available and "Elution Domain Rank" in median_df.columns:
                cols_to_drop.append("Elution Domain Rank")
            if not peak_capacity_available and "Peak Capacity Rank" in median_df.columns:
                cols_to_drop.append("Peak Capacity Rank")
            median_df = median_df.drop(columns=cols_to_drop)

            peak_col = "Peak Detection Rate (%)"

            if median_df.empty or len(median_df.columns) == 0:
                self._show_missing_data()
                return

            rank_df = median_df.drop(columns=[peak_col], errors='ignore').copy()
            peak_df = median_df[[peak_col]].copy() if peak_col in median_df.columns else None

            n_rows, n_rank_cols = rank_df.shape

            rank_min = float(rank_df.values.min())
            rank_max = float(rank_df.values.max())
            # rank_score = (
            #     ((rank_df - rank_min) / (rank_max - rank_min)) * 100.0
            #     if rank_max > rank_min
            #     else rank_df * 0.0
            # )

            rank_cmap = LinearSegmentedColormap.from_list(
                "rank_cmap",
                ["#fff7bc", "#d9ef8b", "#7fcdbb", "#41b6c4", "#225ea8"],
                N=256
            )

            n_total_cols = n_rank_cols + (1 if peak_df is not None else 0)

            gs = GridSpec(
                2, 1, figure=self.fig,
                height_ratios=[12, 1.6],
                left=0.17, right=0.76, top=0.70, bottom=0.15, hspace=0.35
            )
            ax_main = self.fig.add_subplot(gs[0, 0])
            cax_rank = self.fig.add_subplot(gs[1, 0])

            im_rank = ax_main.imshow(
                rank_df.values.astype(float),
                cmap=rank_cmap, aspect="auto",
                extent=[-0.5, n_rank_cols - 0.5, n_rows - 0.5, -0.5],
                vmin=rank_min, vmax=rank_max
            )

            if peak_df is not None:
                peak_cmap = mcolors.ListedColormap(["#d73027", "#f46d43", "#fee08b", "#66bd63"])
                peak_values = peak_df.astype(float).copy()
                if peak_values.max().iloc[0] <= 1.0:
                    peak_values[peak_col] = peak_values[peak_col] * 100.0

                im_peak = ax_main.imshow(
                    peak_values.values.astype(float),
                    cmap=peak_cmap, aspect="auto",
                    extent=[n_rank_cols - 0.5, n_rank_cols + 0.5, n_rows - 0.5, -0.5]
                )

            ax_main.set_xlim(-0.5, n_total_cols - 0.5)
            ax_main.set_ylim(n_rows - 0.5, -0.5)

            all_labels = [c.replace(" ", "\n") for c in rank_df.columns]
            if peak_df is not None:
                all_labels += ["Peak rate"]
            ax_main.set_xticks(range(n_total_cols))
            ax_main.set_xticklabels(all_labels, fontsize=8, fontweight="bold")
            ax_main.set_yticks(range(n_rows))
            ax_main.set_yticklabels(rank_df.index, fontsize=10, fontweight="bold")
            ax_main.tick_params(
                top=True, bottom=False, labeltop=True, labelbottom=False, length=0, pad=4
            )

            ax_main.set_xticks(np.arange(-0.5, n_total_cols, 1), minor=True)
            ax_main.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
            ax_main.grid(which="minor", color="white", linewidth=2.0)
            ax_main.tick_params(which="minor", length=0)

            for r in range(n_rows):
                for c in range(n_rank_cols):
                    val = rank_df.iloc[r, c]
                    ax_main.text(c, r, f"{val:.0f}", ha="center", va="center",
                                 fontsize=10, color='black')

            if peak_df is not None:
                for r in range(n_rows):
                    val = peak_values.iloc[r, 0]
                    ax_main.text(n_rank_cols, r, f"{val:.0f}", ha="center", va="center",
                                 fontsize=10, color='black')

            ax_main.text(0.5, 1.36, "Chromatographic Mode Performance",
                         transform=ax_main.transAxes, ha="center", va="bottom",
                         fontsize=16, fontweight="bold")
            ax_main.text(0.5, 1.28, "Median Rank Heatmap by Chromatographic Mode",
                         transform=ax_main.transAxes, ha="center", va="bottom",
                         fontsize=11, style="italic", color="dimgray")

            cbar_rank = self.fig.colorbar(im_rank, cax=cax_rank, orientation="horizontal")
            cbar_rank.ax.tick_params(labelsize=8)
            cbar_rank.set_label("Median rank score", fontsize=9, labelpad=4)
            cbar_rank.ax.xaxis.set_label_position("top")

            if peak_df is not None:
                heatmap_pos = ax_main.get_position()
                cax_peak = self.fig.add_axes([
                    heatmap_pos.x1 + 0.015, heatmap_pos.y0,
                    0.014, heatmap_pos.height
                ])
                cbar_peak = self.fig.colorbar(im_peak, cax=cax_peak, ticks=[20, 50, 70, 90])
                cbar_peak.ax.set_yticklabels(["<40%", "40–60%", "60–80%", ">80%"])
                cbar_peak.ax.tick_params(labelsize=8)
                cbar_peak.set_label("Peak rate", fontsize=9, labelpad=6)

        # ------------------------------------------------------------------
        # BOXPLOT
        # ------------------------------------------------------------------
        else:
            grouped_df = list(self.model.get_rank_score_grouped_by_chrom_mode_table())

            if not grouped_df:
                self._show_missing_data()
                return

            if criteria not in CRITERIA_COLUMN_MAP:
                self._show_missing_data()
                return

            BOXPLOT_COLORS = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00", "#00A6A6"]

            # ------------------------------------------------------------------
            # Near-identical peak rate detection helper
            # ------------------------------------------------------------------
            def _is_near_identical(values_list):
                """Return True if peak rate range across all groups < 1%."""
                all_vals = np.concatenate([v for v in values_list if len(v) > 0]) \
                    if any(len(v) > 0 for v in values_list) else np.array([])
                if len(all_vals) == 0:
                    return False
                return (all_vals.max() - all_vals.min()) < 1.0

            def _apply_jitter(y_data):
                """Add small vertical jitter for near-identical peak rate visibility."""
                pr_range = y_data.max() - y_data.min() if len(y_data) > 1 else 0.0
                amplitude = max(pr_range * 0.5, 0.15)
                np.random.seed(42)
                return y_data + np.random.normal(0, amplitude, size=len(y_data))

            def _draw_single_boxplot(ax, col_name, title, show_title=True):
                labels, values = [], []
                for mode, group in grouped_df:
                    labels.append(mode)
                    values.append(group[col_name].dropna().values)

                # ← Detect near-identical peak rate for this specific column
                is_peak_rate_col = col_name == "Peak Detection Rate (%)"
                jitter_applied = is_peak_rate_col and _is_near_identical(values)

                box = ax.boxplot(values, patch_artist=True, widths=0.55, showfliers=False)

                for patch, color in zip(box["boxes"], BOXPLOT_COLORS):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.25)
                    patch.set_edgecolor(color)
                    patch.set_linewidth(1.0)

                for median in box["medians"]:
                    median.set_color("black")
                    median.set_linewidth(1.2)

                for whisker in box["whiskers"]:
                    whisker.set_linewidth(0.8)

                for cap in box["caps"]:
                    cap.set_linewidth(0.8)

                all_display_vals = []
                np.random.seed(42)
                for j, y_data in enumerate(values, start=1):
                    x_jitter = np.random.normal(j, 0.04, size=len(y_data))

                    # ← Apply vertical jitter only when peak rate is near-identical
                    if jitter_applied and len(y_data) > 0:
                        y_plot = _apply_jitter(y_data)
                    else:
                        y_plot = y_data

                    all_display_vals.extend(y_plot)

                    ax.scatter(x_jitter, y_plot, s=10,
                               color=BOXPLOT_COLORS[j - 1],
                               edgecolors="k", linewidths=0.2,
                               alpha=0.75, picker=5)

                if show_title:
                    ax.set_title(title, fontsize=9, fontweight="bold")

                # ← Y-label and y-axis zoom when jitter applied
                if jitter_applied:
                    ax.set_ylabel("Peak rate (%) †", fontsize=8)
                    if all_display_vals:
                        disp = np.array(all_display_vals)
                        margin = (disp.max() - disp.min()) * 0.3 or 0.5
                        ax.set_ylim(disp.min() - margin, disp.max() + margin)
                    # ← Small note at bottom of subplot
                    ax.text(0.5, -0.02,
                            "† Jitter added; values are near-identical",
                            transform=ax.transAxes,
                            ha="center", va="top",
                            fontsize=6, style="italic", color="#b05000")
                else:
                    if title in "Peak rate (%)":
                        ax.set_ylabel("Peak rate", fontsize=8)
                    else:
                        ax.set_ylabel("Rank", fontsize=8)

                ax.set_xticks(range(1, len(labels) + 1))
                ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
                ax.tick_params(axis="y", labelsize=7)
                ax.grid(True, axis="y", linestyle="--", linewidth=0.4, alpha=0.5)
                ax.set_axisbelow(True)

            col_name_value = CRITERIA_COLUMN_MAP[criteria]

            # ------------------------------------------------------------------
            # All criteria — multi-panel
            # ------------------------------------------------------------------
            if col_name_value is None:
                metrics = [
                    ("Orthogonality Rank", "Orthogonality"),
                    ("Final Rank", "Final Consensus Rank"),
                    ("Peak Detection Rate (%)", "Peak rate (%)"),
                ]
                if elution_domain_available:
                    metrics.insert(1, ("Elution Domain Rank", "Elution Domain"))
                if peak_capacity_available:
                    metrics.insert(2, ("Peak Capacity Rank", "Peak Capacity"))

                n = len(metrics)
                ncols = min(3, n)
                nrows = int(np.ceil(n / ncols))

                gs = GridSpec(nrows, ncols, figure=self.fig,
                              hspace=0.65, wspace=0.35,
                              left=0.08, right=0.96, top=0.78, bottom=0.16)

                created_axes = []
                for i, (col_name, title) in enumerate(metrics):
                    self.axe = self.fig.add_subplot(gs[i // ncols, i % ncols])
                    created_axes.append(self.axe)
                    _draw_single_boxplot(self.axe, col_name, title)

                # Hide unused grid cells
                for i in range(n, nrows * ncols):
                    self.fig.add_subplot(gs[i // ncols, i % ncols]).axis("off")

                if created_axes:
                    title_ax = created_axes[min(1, len(created_axes) - 1)]
                    title_ax.text(0.5, 1.34, "Chromatographic Mode Performance",
                                  transform=title_ax.transAxes, ha="center", va="bottom",
                                  fontsize=16, fontweight="bold")
                    title_ax.text(0.5, 1.20, "Rank Distribution by Chromatographic Mode — All Criteria",
                                  transform=title_ax.transAxes, ha="center", va="bottom",
                                  fontsize=11, style="italic", color="dimgray")

            # ------------------------------------------------------------------
            # Single criteria
            # ------------------------------------------------------------------
            else:
                col_name, title = col_name_value

                # Availability guard for optional columns
                if criteria == "Elution Domain" and not elution_domain_available:
                    self._show_missing_data()
                    return
                if criteria == "Peak Capacity" and not peak_capacity_available:
                    self._show_missing_data()
                    return

                self.axe = self.fig.add_subplot(111)
                _draw_single_boxplot(self.axe, col_name, title, show_title=False)

                self.axe.text(0.5, 1.10, "Chromatographic Mode Performance",
                              transform=self.axe.transAxes, ha="center", va="bottom",
                              fontsize=16, fontweight="bold")
                self.axe.text(0.5, 1.04, f"{title} distribution by chromatographic mode",
                              transform=self.axe.transAxes, ha="center", va="bottom",
                              fontsize=9, style="italic", color="dimgray")

                self.fig.subplots_adjust(left=0.12, right=0.95, top=0.82, bottom=0.22)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_feasibility_profile(self, grouping: str = "Global", axis_scale: str = "Auto",chrom_mode: str = 'All mode'):
        self.fig.clear()

        def apply_scale(ax, scale: str):
            if scale == "Auto":
                return
            s = scale.lower()
            ax.set_xscale(s)
            ax.set_yscale(s)
            if scale == "Log":
                ax.xaxis.set_major_formatter(
                    ticker.FuncFormatter(lambda val, _: f"{int(val):,}")
                )
                ax.xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=5))
                ax.tick_params(axis="x", labelsize=6)  # smaller font for log ticks

        # ------------------------------------------------------------------
        # GLOBAL — single plot
        # ------------------------------------------------------------------
        if grouping == "Global":
            self.axe = self.fig.add_subplot(111)

            df = self.orthogonality_result_data.copy()

            if df is None or df.empty:
                self._show_missing_data()
                return

            rank_col = (
                "Final Rank"
                if "Final Rank" in df.columns
                   and pd.to_numeric(df["Final Rank"], errors="coerce").notna().any()
                else "Orthogonality Rank"
            )

            rank_numeric = pd.to_numeric(df[rank_col], errors="coerce")
            peak_rate = pd.to_numeric(df["Peak Detection Rate (%)"], errors="coerce")

            valid_mask = rank_numeric.notna() & peak_rate.notna()
            df = df.loc[valid_mask].copy()
            rank_numeric = rank_numeric.loc[valid_mask]
            peak_rate = peak_rate.loc[valid_mask]

            if df.empty:
                self._show_missing_data()
                return

            # rank_max = rank_numeric.max()
            # x_pct = (rank_numeric / rank_max) * 100 if rank_max else rank_numeric

            recommendation_colors = {
                "Highly recommended": "#1a7a2e",
                "Recommended": "#6abf4b",
                "Use with caution": "#f5a623",
                "Not recommended": "#d94f3d",
            }
            recommendation_order = list(recommendation_colors.keys())

            _marker_pool = ["o", "s", "^", "D", "v", "h", "p", "*", "<", ">", "X"]
            unique_modes = self.model.get_chromatographic_mode_list()
            mode_to_marker = {
                mode: _marker_pool[i % len(_marker_pool)]
                for i, mode in enumerate(unique_modes)
            }

            for rec_label in recommendation_order:
                rec_mask = df["Final Recommendation"] == rec_label
                if not rec_mask.any():
                    continue
                for mode in unique_modes:
                    mask = rec_mask & (df["Chromatographic Mode"] == mode)
                    if not mask.any():
                        continue
                    self.axe.scatter(
                        rank_numeric[mask], peak_rate[mask],
                        s=15,
                        marker=mode_to_marker[mode],
                        color=recommendation_colors.get(rec_label, "#aaaaaa"),
                        edgecolors="k", linewidths=0.3,
                        alpha=0.88, zorder=5, picker=5
                    )

            apply_scale(self.axe, axis_scale)

            self.axe.set_xlabel("Final consensus rank (lower = better)", fontsize=8)
            self.axe.set_ylabel("Peak rate (%)", fontsize=8)
            self.axe.tick_params(axis="both", labelsize=7)
            self.axe.grid(True, linestyle="--", linewidth=0.4, alpha=0.4)
            self.axe.spines[["top", "right"]].set_visible(False)

            self.axe.text(0.5, 1.08, "Feasibility Profile",
                          transform=self.axe.transAxes, ha="center", va="bottom",
                          fontsize=16, fontweight="bold")
            self.axe.text(0.5, 1.02, "Overall feasibility decision map · Global",
                          transform=self.axe.transAxes, ha="center", va="bottom",
                          fontsize=9, style="italic", color="dimgray")

            # ------------------------------------------------------------------
            # Legends — side by side at the bottom (same pattern as by mode)
            # ------------------------------------------------------------------
            rec_handles = [
                patches.Patch(facecolor=recommendation_colors[label],
                              edgecolor="k", linewidth=0.4, label=label)
                for label in recommendation_order
                if label in df["Final Recommendation"].values
            ]
            mode_handles = [
                Line2D([0], [0], marker=mode_to_marker[mode], color="w",
                       markerfacecolor="#555555", markeredgecolor="k",
                       markeredgewidth=0.3, markersize=5,
                       label=mode.replace(" ", "×"))
                for mode in unique_modes
            ]

            rec_legend = self.fig.legend(
                handles=rec_handles,
                title="Final recommendation", title_fontsize=7,
                loc="lower center", bbox_to_anchor=(0.30, 0.01),
                ncol=1, fontsize=7,
                frameon=True, framealpha=0.92, edgecolor="#aaaaaa"
            )
            self.fig.add_artist(rec_legend)

            self.fig.legend(
                handles=mode_handles,
                title="Chromatographic mode", title_fontsize=7,
                loc="lower center", bbox_to_anchor=(0.72, -0.03),
                ncol=1, fontsize=7,
                frameon=True, framealpha=0.92, edgecolor="#aaaaaa"
            )

            self.fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.30)

        # ------------------------------------------------------------------
        # BY MODE — faceted
        # ------------------------------------------------------------------
        else:
            grouped_df = list(self.model.get_rank_score_grouped_by_chrom_mode_table())

            if not grouped_df:
                self._show_missing_data()
                return

            recommendation_colors = {
                "Highly recommended": "#1a7a4a",
                "Recommended": "#6abf4b",
                "Use with caution": "#f0a11a",
                "Not recommended": "#d9534f",
            }
            mode_markers = ["o", "s", "^", "D", "v", "p", "X", "<", ">"]

            if chrom_mode == "All mode":
                n_modes = len(grouped_df)
                ncols = min(3, n_modes)
                nrows = int(np.ceil(n_modes / ncols))

                gs = GridSpec(nrows, ncols, figure=self.fig,
                              hspace=0.55, wspace=0.28,
                              left=0.08, right=0.98, top=0.82, bottom=0.28)

                for i, (mode, group) in enumerate(grouped_df):
                    self.axe = self.fig.add_subplot(gs[i // ncols, i % ncols])
                    marker = mode_markers[i % len(mode_markers)]

                    for recommendation, color in recommendation_colors.items():
                        subset = group[group["Final Recommendation"] == recommendation]
                        if subset.empty:
                            continue
                        self.axe.scatter(
                            subset["Final Rank"].astype(float),
                            subset["Peak Detection Rate (%)"].astype(float),
                            s=15, c=color, marker=marker,
                            edgecolors="black", linewidths=0.3, alpha=0.85, picker=5
                        )

                        apply_scale(self.axe, axis_scale)

                        self.axe.set_title(mode, fontsize=10, fontweight="bold")
                        self.axe.grid(True, linestyle="--", linewidth=0.4, alpha=0.4)
                        self.axe.tick_params(axis="both", labelsize=8)
                        self.axe.set_xlabel("Final consensus rank)", fontsize=8)
                        self.axe.set_ylabel("Peak rate (%)" if i % ncols == 0 else "", fontsize=8)
                        self.axe.spines[["top", "right"]].set_visible(False)

                    # Hide unused grid cells
                    for j in range(n_modes, nrows * ncols):
                        self.fig.add_subplot(gs[j // ncols, j % ncols]).axis("off")

                    legend_handles = [
                        patches.Patch(facecolor="#1a7a4a", edgecolor="none", label="Highly recommended"),
                        patches.Patch(facecolor="#6abf4b", edgecolor="none", label="Recommended"),
                        patches.Patch(facecolor="#f0a11a", edgecolor="none", label="Use with caution"),
                        patches.Patch(facecolor="#d9534f", edgecolor="none", label="Not recommended"),
                    ]
                    self.fig.legend(
                        handles=legend_handles,
                        loc="lower center", ncol=2,
                        frameon=True, fancybox=True, framealpha=0.95,
                        bbox_to_anchor=(0.5, 0.01),
                        fontsize=9, columnspacing=1.8, handlelength=1.8
                    )

                    # Titles — suptitle high, subtitle clearly below it
                    self.fig.suptitle("Feasibility Profile",
                                      fontsize=16, fontweight="bold", y=0.97)
                    self.fig.text(0.5, 0.89,  # ← was 0.93, now lower
                                  "Faceted feasibility maps by chromatographic mode",
                                  ha="center", fontsize=9, style="italic", color="dimgray")

            # ------------------------------------------------------------------
            # Single mode
            # ------------------------------------------------------------------
            else:
                self.axe = self.fig.add_subplot(111)

                chrom_mode_list = self.model.get_chromatographic_mode_list()
                i = chrom_mode_list.index(chrom_mode)
                marker = mode_markers[i % len(mode_markers)]

                chrom_mode_df = self.model.get_rank_score_grouped_by_chrom_mode_table().get_group(chrom_mode)
                for recommendation, color in recommendation_colors.items():
                    subset = chrom_mode_df[chrom_mode_df["Final Recommendation"] == recommendation]
                    if subset.empty:
                        continue
                    if not chrom_mode_df[chrom_mode_df["Final Recommendation"] == recommendation].any().any():
                        continue
                    self.axe.scatter(
                        subset["Final Rank"].astype(float),
                        subset["Peak Detection Rate (%)"].astype(float),
                        s=15, c=color, marker=marker,
                        edgecolors="black", linewidths=0.3, alpha=0.85, picker=5
                    )

                    apply_scale(self.axe, axis_scale)

                    self.axe.set_title(chrom_mode, fontsize=10, fontweight="bold")
                    self.axe.grid(True, linestyle="--", linewidth=0.4, alpha=0.4)
                    self.axe.tick_params(axis="both", labelsize=8)
                    self.axe.set_xlabel("Final consensus rank", fontsize=8)
                    self.axe.set_ylabel("Peak rate (%)", fontsize=8)
                    self.axe.spines[["top", "right"]].set_visible(False)

                # # Hide unused grid cells
                # for j in range(n_modes, nrows * ncols):
                #     self.fig.add_subplot(gs[j // ncols, j % ncols]).axis("off")

                legend_handles = [
                    patches.Patch(facecolor="#1a7a4a", edgecolor="none", label="Highly recommended"),
                    patches.Patch(facecolor="#6abf4b", edgecolor="none", label="Recommended"),
                    patches.Patch(facecolor="#f0a11a", edgecolor="none", label="Use with caution"),
                    patches.Patch(facecolor="#d9534f", edgecolor="none", label="Not recommended"),
                ]
                self.fig.legend(
                    handles=legend_handles,
                    loc="lower center", ncol=2,
                    frameon=True, fancybox=True, framealpha=0.95,
                    bbox_to_anchor=(0.5, 0.015),
                    fontsize=9, columnspacing=1.8, handlelength=1.8
                )

                # Titles — suptitle high, subtitle clearly below it
                self.fig.suptitle("Feasibility Profile",
                                  fontsize=16, fontweight="bold", y=0.97)
                self.fig.text(0.5, 0.89,  # ← was 0.93, now lower
                              chrom_mode,
                              ha="center", fontsize=9, style="italic", color="dimgray")

                self.fig.subplots_adjust(left=0.12, right=0.95, top=0.82, bottom=0.22)



        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def plot_recommendation_distribution(self, grouping: str = "Global"):
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        # ------------------------------------------------------------------
        # GLOBAL — one single stacked bar
        # ------------------------------------------------------------------
        if grouping == "Global":
            recommendations = self.orthogonality_result_data.copy()['Final Recommendation']

            if recommendations.empty:
                self._show_missing_data()
                return

            counts = recommendations.value_counts()
            total = counts.sum()
            bottom = 0
            present_cats = []

            for cat in CATEGORY_ORDER:
                val = counts.get(cat, 0)
                if val == 0:
                    continue
                present_cats.append(cat)
                bar = self.axe.bar(
                    ["All combinations"], [val],
                    bottom=bottom,
                    color=COLORS[cat],
                    label=cat,
                    width=0.4
                )
                self.axe.text(
                    bar[0].get_x() + bar[0].get_width() / 2,
                    bottom + val / 2,
                    f"{val:,}",
                    ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white"
                )
                bottom += val

            # ← Total label removed for Global view

        # ------------------------------------------------------------------
        # BY MODE — one stacked bar per chromatographic mode
        # ------------------------------------------------------------------
        else:
            df = self.model.get_recommendation_distribution_group_table()

            mode_labels = []
            data = {cat: [] for cat in CATEGORY_ORDER}

            for mode, group in df:
                mode_labels.append(mode)
                recommendations = group.values
                for cat in CATEGORY_ORDER:
                    data[cat].append((recommendations == cat).sum())

            if not mode_labels:
                self._show_missing_data()
                return

            x = range(len(mode_labels))
            bar_width = 0.5
            bottoms = [0] * len(mode_labels)
            present_cats = []

            for cat in CATEGORY_ORDER:
                values = data[cat]
                if sum(values) == 0:
                    continue
                present_cats.append(cat)
                bars = self.axe.bar(x, values, bar_width,
                                    bottom=bottoms,
                                    color=COLORS[cat],
                                    label=cat)
                for bar, val, bot in zip(bars, values, bottoms):
                    if val > 0:
                        self.axe.text(
                            bar.get_x() + bar.get_width() / 2,
                            bot + val / 2,
                            f"{val:,}",
                            ha="center", va="center",
                            fontsize=7, fontweight="bold", color="white"
                        )
                bottoms = [b + v for b, v in zip(bottoms, values)]

            # ← Total on top of each bar (original style)
            max_total = max(bottoms) if bottoms else 1
            for i, total in enumerate(bottoms):
                self.axe.text(
                    i, total + max_total * 0.01,
                    f"{total:,}",
                    ha="center", va="bottom",
                    fontsize=7, fontweight="bold", color="#2c2c2a"
                )

            self.axe.set_xticks(list(x))
            self.axe.set_xticklabels(mode_labels, fontsize=7, rotation=15, ha="right")

        # ------------------------------------------------------------------
        # Shared formatting
        # ------------------------------------------------------------------
        self.axe.set_ylabel("Number of combinations", fontsize=8)
        self.axe.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda v, _: f"{int(v):,}")
        )
        self.axe.tick_params(axis="both", labelsize=7)
        self.axe.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        self.axe.set_axisbelow(True)
        self.axe.spines[["top", "right"]].set_visible(False)

        subtitle = "All combinations" if grouping == "Global" else "By chromatographic mode"
        self.axe.text(0.5, 1.10, "Recommendation Distribution",
                      transform=self.axe.transAxes, ha="center", va="bottom",
                      fontsize=16, fontweight="bold")
        self.axe.text(0.5, 1.03, subtitle,
                      transform=self.axe.transAxes, ha="center", va="bottom",
                      fontsize=9, style="italic", color="dimgray")

        legend_handles = [
            patches.Patch(facecolor=COLORS[cat], label=cat)
            for cat in present_cats
        ]
        self.axe.legend(
            handles=legend_handles,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.38),
            ncol=2, fontsize=7,
            frameon=True, edgecolor="#cccccc"
        )

        self.fig.subplots_adjust(left=0.14, right=0.90, top=0.70, bottom=0.30)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_final_rank_by_recommendation_class(self,recommendation: str = 'All recommendation'):
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        grouped_df = list(self.model.get_rank_score_grouped_by_recommendation_table())

        if not grouped_df:
            self._show_missing_data()
            return

        recommendation_order = [
            "Highly recommended",
            "Recommended",
            "Use with caution",
            "Not recommended",
        ]
        recommendation_colors = {
            "Highly recommended": "#1a7a2e",
            "Recommended": "#6abf4b",
            "Use with caution": "#f5a623",
            "Not recommended": "#d94f3d",
        }

        mode_order = self.model.get_chromatographic_mode_list()
        mode_markers = ["o", "s", "^", "D", "v", "p", "X", "<", ">"]
        mode_to_marker = {
            mode: mode_markers[i % len(mode_markers)]
            for i, mode in enumerate(mode_order)
        }


        available_groups = {label: group for label, group in grouped_df}
        plot_labels = [label for label in recommendation_order if label in available_groups]

        if not plot_labels:
            self._show_missing_data()
            return

        if recommendation == 'All recommendation':
            values = [
                available_groups[label]["Final Rank"].dropna().astype(float).to_numpy()
                for label in plot_labels
            ]
            positions = np.arange(1, len(plot_labels) + 1)

            # ------------------------------------------------------------------
            # Boxplot
            # ------------------------------------------------------------------
            box = self.axe.boxplot(
                values,
                positions=positions,
                widths=0.46,
                patch_artist=True,
                showfliers=False
            )

            for patch, label in zip(box["boxes"], plot_labels):
                color = recommendation_colors[label]
                patch.set_facecolor(color)
                patch.set_alpha(0.25)
                patch.set_edgecolor(color)
                patch.set_linewidth(1.2)

            for median, label in zip(box["medians"], plot_labels):
                median.set_color(recommendation_colors[label])
                median.set_linewidth(2.0)

            for whisker in box["whiskers"]:
                whisker.set_color("#666666")
                whisker.set_linewidth(1.0)

            for cap in box["caps"]:
                cap.set_color("#666666")
                cap.set_linewidth(1.0)

            # ------------------------------------------------------------------
            # Jittered scatter points per mode
            # ------------------------------------------------------------------
            seen_modes = []

            for xpos, label in zip(positions, plot_labels):
                group = available_groups[label]
                point_color = recommendation_colors[label]

                if "Chromatographic Mode" in group.columns:
                    for mode, mode_group in group.groupby("Chromatographic Mode"):
                        if mode not in seen_modes:
                            seen_modes.append(mode)

                        marker = mode_to_marker.get(mode, "o")
                        y = mode_group["Final Rank"].dropna().astype(float).to_numpy()
                        if len(y) == 0:
                            continue

                        self.axe.scatter(
                            np.random.normal(loc=xpos, scale=0.06, size=len(y)), y,
                            s=24, color=point_color, marker=marker,
                            edgecolors="white", linewidths=0.35,
                            alpha=0.95, zorder=3, picker=5
                        )
                else:
                    y = group["Final Rank"].dropna().astype(float).to_numpy()
                    if len(y) > 0:
                        self.axe.scatter(
                            np.random.normal(loc=xpos, scale=0.06, size=len(y)), y,
                            s=24, color=point_color, marker="o",
                            edgecolors="white", linewidths=0.35,
                            alpha=0.95, zorder=3, picker=5
                        )

            # ------------------------------------------------------------------
            # Axes formatting
            # ------------------------------------------------------------------
            plot_labels
            self.axe.set_xticks(positions)
            self.axe.set_xticklabels(plot_labels, fontsize=9)
            self.axe.set_ylabel("Final consensus rank", fontsize=10)
            self.axe.tick_params(axis="both", labelsize=8)
            self.axe.grid(True, axis="y", linestyle="--", linewidth=0.4, alpha=0.35)
            self.axe.set_axisbelow(True)
            self.axe.spines[["top", "right"]].set_visible(False)
            self.axe.spines[["left", "bottom"]].set_linewidth(1.0)

        else:

            if recommendation not in available_groups:
                self._show_missing_data()
                return

            value = available_groups[recommendation]["Final Rank"].dropna().astype(float).to_numpy()

            position = [1]
            # ------------------------------------------------------------------
            # Boxplot (Single recommendation)
            # ------------------------------------------------------------------
            box = self.axe.boxplot(
                value,
                widths=0.46,
                patch_artist=True,
                showfliers=False
            )

            patch = box["boxes"][0]
            color = recommendation_colors[recommendation]
            patch.set_facecolor(color)
            patch.set_alpha(0.25)
            patch.set_edgecolor(color)
            patch.set_linewidth(1.2)

            median = box["medians"][0]
            median.set_color(recommendation_colors[recommendation])
            median.set_linewidth(2.0)

            whisker = box["whiskers"][0]
            whisker.set_color("#666666")
            whisker.set_linewidth(1.0)

            cap = box["caps"][0]
            cap.set_color("#666666")
            cap.set_linewidth(1.0)

            # ------------------------------------------------------------------
            # Jittered scatter points per mode
            # ------------------------------------------------------------------
            seen_modes = []

            group = available_groups[recommendation]
            point_color = recommendation_colors[recommendation]

            if "Chromatographic Mode" in group.columns:
                for mode, mode_group in group.groupby("Chromatographic Mode"):
                    if mode not in seen_modes:
                        seen_modes.append(mode)

                    marker = mode_to_marker.get(mode, "o")
                    y = mode_group["Final Rank"].dropna().astype(float).to_numpy()
                    if len(y) == 0:
                        continue

                    self.axe.scatter(
                        np.random.normal(loc=position, scale=0.06, size=len(y)), y,
                        s=24, color=point_color, marker=marker,
                        edgecolors="white", linewidths=0.35,
                        alpha=0.95, zorder=3, picker=5
                    )
            else:
                y = group["Final Rank"].dropna().astype(float).to_numpy()
                if len(y) > 0:
                    self.axe.scatter(
                        np.random.normal(loc=position, scale=0.06, size=len(y)), y,
                        s=24, color=point_color, marker="o",
                        edgecolors="white", linewidths=0.35,
                        alpha=0.95, zorder=3, picker=5
                    )

            # ------------------------------------------------------------------
            # Axes formatting
            # ------------------------------------------------------------------
            self.axe.set_xticks(position)
            self.axe.set_xticklabels([recommendation], fontsize=9)
            self.axe.set_ylabel("Final consensus rank", fontsize=10)
            self.axe.tick_params(axis="both", labelsize=8)
            self.axe.grid(True, axis="y", linestyle="--", linewidth=0.4, alpha=0.35)
            self.axe.set_axisbelow(True)
            self.axe.spines[["top", "right"]].set_visible(False)
            self.axe.spines[["left", "bottom"]].set_linewidth(1.0)

        # ------------------------------------------------------------------
        # Mode legend
        # ------------------------------------------------------------------
        legend_handles = [
            Line2D([0], [0], marker=mode_to_marker.get(mode, "o"), color="w",
                   label=mode, markerfacecolor="#666666", markeredgecolor="#666666",
                   markersize=6, linewidth=0)
            for mode in seen_modes
        ]
        if legend_handles:
            self.axe.legend(
                handles=legend_handles,
                title="Chromatographic mode",
                loc="lower center", bbox_to_anchor=(0.5, -0.32),
                ncol=min(3, len(legend_handles)),  # up to 3 per row
                frameon=True, framealpha=0.92,
                edgecolor="#aaaaaa",
                fontsize=8, title_fontsize=9,
                handletextpad=0.6, columnspacing=1.2
            )

        # ------------------------------------------------------------------
        # Titles
        # ------------------------------------------------------------------
        self.axe.text(0.5, 1.08, "Final Rank vs Recommendation",
                      transform=self.axe.transAxes, ha="center", va="bottom",
                      fontsize=16, fontweight="bold")
        self.axe.text(0.5, 1.02, "Final consensus rank distribution by recommendation class",
                      transform=self.axe.transAxes, ha="center", va="bottom",
                      fontsize=9, style="italic", color="dimgray")

        self.fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.30)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_rank_shift_scatter(self, color_by: str = "Chromatographic Mode"):
        """Scatter plot of Old Rank vs New Rank (Utility) with y=x diagonal.

        Points below the diagonal → combination moves up in the new ranking.
        Points above the diagonal → combination moves down.

        Args:
            color_by (str): Column used to color points.
                            One of 'Chromatographic Mode', 'Hypothetical 2D Peak Capacity',
                            'Elution Domain'. Defaults to 'Chromatographic Mode'.

        Side Effects:
            - Clears the figure and redraws from scratch.
            - Draws scatter + diagonal + legend.
        """
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        df = self.orthogonality_result_data.copy()

        old_rank = pd.to_numeric(df.get("Final Rank"), errors="coerce")
        new_rank = pd.to_numeric(df.get("Final Rank (Utility)"), errors="coerce")

        valid = old_rank.notna() & new_rank.notna()
        if not valid.any():
            self._show_missing_data()
            return

        df = df[valid]
        x = old_rank[valid]
        y = new_rank[valid]

        # ------------------------------------------------------------------
        # Coloring strategy
        # ------------------------------------------------------------------
        if color_by == "Chromatographic Mode":
            modes = df["Chromatographic Mode"].fillna("Unknown")
            unique_modes = list(modes.unique())
            palette = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                "#bcbd22", "#17becf",
            ]
            mode_color = {m: palette[i % len(palette)] for i, m in enumerate(unique_modes)}
            colors = [mode_color[m] for m in modes]

            legend_handles = [
                patches.Patch(facecolor=mode_color[m], edgecolor="k",
                              linewidth=0.4, label=m)
                for m in unique_modes
            ]
            legend_title = "Chromatographic Mode"

        else:
            # Continuous colormap — Peak Capacity or Elution Domain
            col_values = pd.to_numeric(df.get(color_by, pd.Series(dtype=float)),
                                       errors="coerce")
            cmap = (
                "plasma" if color_by == "Hypothetical 2D Peak Capacity" else "viridis"
            )
            sc = self.axe.scatter(
                x, y,
                c=col_values, cmap=cmap,
                s=18, edgecolors="k", linewidths=0.3,
                alpha=0.80, picker=5
            )
            cbar = self.fig.colorbar(sc, ax=self.axe, pad=0.02, shrink=0.85)
            cbar.set_label(color_by, fontsize=9)
            cbar.ax.tick_params(labelsize=8)
            colors = None  # already plotted above

        # ------------------------------------------------------------------
        # Scatter (categorical color_by only — continuous path already drawn)
        # ------------------------------------------------------------------
        if colors is not None:
            self.axe.scatter(
                x, y,
                c=colors,
                s=18, edgecolors="k", linewidths=0.3,
                alpha=0.80, picker=5
            )
            self.axe.legend(
                handles=legend_handles,
                title=legend_title,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.38),
                ncol=min(3, len(legend_handles)),
                fontsize=8, title_fontsize=9,
                frameon=True, edgecolor="#aaaaaa"
            )

        # ------------------------------------------------------------------
        # Diagonal y = x  (no change line)
        # ------------------------------------------------------------------
        rank_min = min(x.min(), y.min())
        rank_max = max(x.max(), y.max())
        diag = np.linspace(rank_min, rank_max, 200)
        self.axe.plot(
            diag, diag,
            color="#999999", linewidth=1.0,
            linestyle="--", zorder=0,
            label="No change (y = x)"
        )

        # ------------------------------------------------------------------
        # Annotations
        # ------------------------------------------------------------------
        x_center = (rank_min + rank_max) / 2
        pad = (rank_max - rank_min) * 0.04

        self.axe.text(
            x_center, x_center - pad * 2.5,
            "▼ moves up",
            ha="center", va="top",
            fontsize=7, color="#1a7a2e", style="italic",
            rotation=-42
        )
        self.axe.text(
            x_center, x_center + pad * 2.5,
            "▲ moves down",
            ha="center", va="bottom",
            fontsize=7, color="#d94f3d", style="italic",
            rotation=-42
        )

        # ------------------------------------------------------------------
        # Axes formatting
        # ------------------------------------------------------------------
        self.axe.set_xlabel("Old Rank  (Final Rank)", fontsize=11)
        self.axe.set_ylabel("New Rank  (Utility)", fontsize=11)
        self.axe.tick_params(axis="both", labelsize=9)
        self.axe.grid(True, linestyle=":", linewidth=0.8, alpha=0.5)
        self.axe.set_axisbelow(True)
        self.axe.set_box_aspect(1)
        self.axe.spines[["top", "right"]].set_visible(False)

        self.axe.text(
            0.5, 1.10, "Rank Shift Analysis",
            transform=self.axe.transAxes, ha="center", va="bottom",
            fontsize=16, fontweight="bold"
        )
        self.axe.text(
            0.5, 1.03,
            f"Old Rank vs New Rank (Utility)  ·  colored by {color_by}",
            transform=self.axe.transAxes, ha="center", va="bottom",
            fontsize=9, style="italic", color="dimgray"
        )

        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.84, bottom=0.30)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_rank_shift_distribution(self, view: str = "Boxplot"):
        """Distribution of Rank Gain = Old Rank − New Rank (Utility).

        Positive gain → combination moves up.
        Negative gain → combination moves down.

        Args:
            view (str): 'Histogram' for a global distribution,
                        'Boxplot' for one box per chromatographic mode.

        Side Effects:
            - Clears the figure and redraws from scratch.
        """
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        df = self.orthogonality_result_data.copy()
        old_rank = pd.to_numeric(df.get("Final Rank"), errors="coerce")
        new_rank = pd.to_numeric(df.get("Final Rank (Utility)"), errors="coerce")

        valid = old_rank.notna() & new_rank.notna()
        if not valid.any():
            self._show_missing_data()
            return

        df = df[valid].copy()
        rank_gain = (old_rank[valid] - new_rank[valid])
        df["Rank Gain"] = rank_gain.values

        # ------------------------------------------------------------------
        # HISTOGRAM — global distribution
        # ------------------------------------------------------------------
        if view == "Histogram":
            n_bins = max(20, int(np.sqrt(len(rank_gain))))

            pos_mask = rank_gain >= 0
            neg_mask = rank_gain < 0

            if pos_mask.any():
                self.axe.hist(
                    rank_gain[pos_mask], bins=n_bins,
                    color="#1a7a2e", alpha=0.75, edgecolor="white",
                    linewidth=0.4, label="Moves up (gain ≥ 0)"
                )
            if neg_mask.any():
                self.axe.hist(
                    rank_gain[neg_mask], bins=n_bins,
                    color="#d94f3d", alpha=0.75, edgecolor="white",
                    linewidth=0.4, label="Moves down (gain < 0)"
                )

            self.axe.axvline(0, color="#555555", linewidth=1.2, linestyle="--", zorder=5)
            self.axe.axvline(
                rank_gain.median(),
                color="#f5a623", linewidth=1.2, linestyle="-.",
                label=f"Median gain = {rank_gain.median():.0f}", zorder=5
            )

            self.axe.set_xlabel("Rank Gain  (Old − New)", fontsize=11)
            self.axe.set_ylabel("Number of combinations", fontsize=11)
            self.axe.legend(fontsize=8, frameon=True, edgecolor="#cccccc")
            subtitle = "Global rank gain distribution"

        # ------------------------------------------------------------------
        # BOXPLOT — one box per chromatographic mode
        # ------------------------------------------------------------------
        else:
            if "Chromatographic Mode" not in df.columns:
                self._show_missing_data()
                return

            mode_order = self.model.get_chromatographic_mode_list()
            palette = [
                "#E41A1C", "#377EB8", "#4DAF4A", "#984EA3",
                "#FF7F00", "#00A6A6", "#A65628", "#F781BF",
            ]

            labels, values = [], []
            for mode in mode_order:
                group = df[df["Chromatographic Mode"] == mode]["Rank Gain"].dropna()
                if group.empty:
                    continue
                labels.append(mode)
                values.append(group.values)

            if not labels:
                self._show_missing_data()
                return

            box = self.axe.boxplot(
                values, patch_artist=True,
                widths=0.55, showfliers=False
            )
            for patch, color in zip(box["boxes"], palette):
                patch.set_facecolor(color)
                patch.set_alpha(0.25)
                patch.set_edgecolor(color)
                patch.set_linewidth(1.0)
            for median in box["medians"]:
                median.set_color("black")
                median.set_linewidth(1.2)

            # jittered points
            np.random.seed(42)
            for j, (y_data, color) in enumerate(zip(values, palette), start=1):
                x_jitter = np.random.normal(j, 0.05, size=len(y_data))
                self.axe.scatter(
                    x_jitter, y_data,
                    s=10, color=color,
                    edgecolors="k", linewidths=0.2,
                    alpha=0.70, picker=5
                )

            self.axe.axhline(0, color="#555555", linewidth=1.0, linestyle="--", zorder=0)
            self.axe.set_xticks(range(1, len(labels) + 1))
            self.axe.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
            self.axe.set_ylabel("Rank Gain  (Old − New)", fontsize=11)
            subtitle = "Rank gain by chromatographic mode"

        # ------------------------------------------------------------------
        # Shared formatting
        # ------------------------------------------------------------------
        self.axe.tick_params(axis="both", labelsize=9)
        self.axe.grid(True, axis="y", linestyle="--", linewidth=0.4, alpha=0.5)
        self.axe.set_axisbelow(True)
        self.axe.spines[["top", "right"]].set_visible(False)

        self.axe.text(
            0.5, 1.10, "Rank Shift Distribution",
            transform=self.axe.transAxes, ha="center", va="bottom",
            fontsize=16, fontweight="bold"
        )
        self.axe.text(
            0.5, 1.03, subtitle,
            transform=self.axe.transAxes, ha="center", va="bottom",
            fontsize=9, style="italic", color="dimgray"
        )

        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.84, bottom=0.28)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_rank_shift_by_combination(self):
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        df = self.orthogonality_result_data.copy()
        required_cols = {"Final Rank", "Final Rank (Utility)"}
        if not required_cols.issubset(df.columns):
            self._show_missing_data()
            return

        old_rank = pd.to_numeric(df["Final Rank"], errors="coerce")
        new_rank = pd.to_numeric(df["Final Rank (Utility)"], errors="coerce")

        if old_rank.notna().sum() == 0 or new_rank.notna().sum() == 0:
            self._show_missing_data()
            return

        valid = old_rank.notna() & new_rank.notna()
        if not valid.any():
            self._show_missing_data()
            return

        plot_df = pd.DataFrame({
            "Old Rank": old_rank[valid],
            "Rank Shift": (new_rank[valid] - old_rank[valid])
        }).sort_values("Old Rank")

        x = np.arange(1, len(plot_df) + 1)
        y = plot_df["Rank Shift"].to_numpy()
        colors = np.where(y > 0, "#f39c12", "#2471a3")

        self.axe.vlines(x, 0, y, colors=colors, linewidth=1.3, alpha=0.9, zorder=2)
        self.axe.scatter(x, y, c=colors, s=28, zorder=3)
        self.axe.axhline(0, color="black", linewidth=1.1, zorder=1)

        self.axe.set_title("Rank Shift by Combination", fontsize=14, fontweight="bold")
        self.axe.set_xlabel("Combination (sorted by old rank)", fontsize=11)
        self.axe.set_ylabel("Rank shift (New Rank − Old Rank)", fontsize=11)
        self.axe.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.5)
        self.axe.set_xlim(0.5, len(plot_df) + 0.5)
        self.axe.spines[["top", "right"]].set_visible(False)

        legend_handles = [
            Line2D([0], [0], marker="o", color="#2471a3", markersize=7, linestyle="None",
                   label="Negative = improved rank"),
            Line2D([0], [0], marker="o", color="#f39c12", markersize=7, linestyle="None",
                   label="Positive = worsened rank"),
        ]
        self.axe.legend(handles=legend_handles, fontsize=9, frameon=True, edgecolor="#cccccc")

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_top_rank_overlap(self):
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        df = self.orthogonality_result_data.copy()
        required_cols = {"Final Rank", "Final Rank (Utility)"}
        if not required_cols.issubset(df.columns):
            self._show_missing_data()
            return

        old_rank = pd.to_numeric(df["Final Rank"], errors="coerce")
        new_rank = pd.to_numeric(df["Final Rank (Utility)"], errors="coerce")

        if old_rank.notna().sum() == 0 or new_rank.notna().sum() == 0:
            self._show_missing_data()
            return

        valid = old_rank.notna() & new_rank.notna()
        if not valid.any():
            self._show_missing_data()
            return

        rank_df = pd.DataFrame({
            "Old Rank": old_rank[valid],
            "New Rank": new_rank[valid],
        })

        top_ks = [k for k in [10, 50, 100, 200, 500, 1000] if k <= len(rank_df)]
        if not top_ks:
            self._show_missing_data()
            return

        palette = ["#2471a3", "#1e8449", "#6c3483", "#b7770d", "#117a65", "#922b21"]
        color_map = {k: palette[i % len(palette)] for i, k in enumerate(top_ks)}
        overlaps, percentages = [], []
        for k in top_ks:
            old_top = rank_df.nsmallest(k, "Old Rank").index.to_numpy()
            new_top = rank_df.nsmallest(k, "New Rank").index.to_numpy()
            overlap_count = int(np.sum(old_top == new_top))
            overlaps.append(overlap_count)
            percentages.append((overlap_count / k) * 100)

        x = np.arange(len(top_ks))
        bar_colors = [color_map[k] for k in top_ks]
        bars = self.axe.bar(x, overlaps, color=bar_colors, width=0.6, zorder=3)

        self.axe.set_xticks(x)
        self.axe.set_xticklabels([f"Top {k}" for k in top_ks], fontsize=11)
        self.axe.set_ylabel("Overlap (shared combinations)", fontsize=11)
        self.axe.text(
            0.5, 1.10, "Overlap of Top Ranked Combinations",
            transform=self.axe.transAxes, ha="center", va="bottom",
            fontsize=14, fontweight="bold"
        )
        self.axe.text(
            0.5, 1.03, "Shared combinations between old and new top-k lists",
            transform=self.axe.transAxes, ha="center", va="bottom",
            fontsize=9, style="italic", color="dimgray"
        )

        max_overlap = max(overlaps)
        y_max = max(5, max_overlap) * 1.25
        self.axe.set_ylim(0, y_max)
        self.axe.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        self.axe.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.5, zorder=0)
        self.axe.spines[["top", "right"]].set_visible(False)

        # Reduce font size by 1pt for each bar beyond 3 so annotations don't overlap, floor at 8pt
        annot_fs = max(8, 11 - max(0, len(top_ks) - 3))
        label_offset = max(1, max_overlap) * 0.01
        for bar, k, count, pct, color in zip(bars, top_ks, overlaps, percentages, bar_colors):
            self.axe.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + label_offset,
                f"{count}/{k}\n({pct:.0f}%)",
                ha="center", va="bottom", fontsize=annot_fs, color=color, fontweight="bold"
            )

        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.72, bottom=0.12)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _show_missing_data(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.axis('off')
        ax.text(
            0.5, 0.5,
            'Missing data',
            transform=ax.transAxes,
            ha='center', va='center',
            fontsize=18, color='#c0c0c0',
            fontweight='bold'
        )
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def set_annotation(self,annotation = None):

        if annotation:
            self.annotation = annotation
        else:
            self.annotation = self.axe.annotate("", xy=(0, 0), xytext=(10, 10),
                                                                         fontsize='x-small',
                                                                          textcoords="offset points",
                                                                          bbox=dict(boxstyle="round", fc="white",
                                                                                    ec="gray"),
                                                                          arrowprops=dict(arrowstyle="->"))

            self.annotation.set_visible(False)

    def on_pick(self,event,subset):
        axe = event.artist.axes

        xy_data = axe.collections[0].get_offsets()

        extracted_x = xy_data[:, 0]
        extracted_y = xy_data[:, 1]

        ind = event.ind[0]

        df_filtered = self.model.get_filtered_result_df()
        n = self.model.get_number_of_combination()
        final_rank = pd.to_numeric(df_filtered['Final Rank'], errors='coerce')

        final_rank_pct = (final_rank / n) * 100

        if subset:
            threshold = SUBSET_THRESHOLDS.get(subset, 0)
            mask = final_rank_pct <= threshold

            df_filtered = df_filtered[mask]

        # convert panda series into list to reset the serie index which has been held even after filtering the data
        # when filtering panda dataframe or series, the index stays unchanged
        combination = list(df_filtered['2D Combination'])[ind]
        combination_number = list(df_filtered['Combination #'])[ind]

        x = extracted_x[ind]
        y = extracted_y[ind]

        self.annotation.xy = (extracted_x[ind], extracted_y[ind])
        self.annotation.set_text(f"Combination # {combination_number}\n{combination}\n(x, y) = ({x:.2f}, {y:.2f})")
        self.annotation.set_visible(True)

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def open_in_window(self):
        self._plot_dialog = QDialog()
        self._plot_dialog.setWindowTitle("Multi-Criteria Space")
        self._plot_dialog.resize(1000, 700)

        layout = QVBoxLayout(self._plot_dialog)

        canvas = FigureCanvas(self.fig)
        toolbar = CustomToolbar(canvas, self._plot_dialog)

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self._plot_dialog.show()