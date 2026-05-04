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

    def set_annotation(self, annotation) -> None:
        """Set the matplotlib Annotation for plotting.
        Args:
        """

        self.annotation = annotation

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

        x = self.orthogonality_result_data['Consensus Ranking']
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

    def plot_peak_capacity_vs_elution(self):
        self.fig.clear()

        x = self.orthogonality_result_data['Hypothetical 2D Peak Capacity']
        y = self.orthogonality_result_data['Elution Composition Space Area']

        x_is_numeric = (x != 'Not available').any()
        y_is_numeric = (y != 'Not available').any()

        if x_is_numeric and y_is_numeric:

            final_rank = self.orthogonality_result_data['Final Rank']
            consensus_rank = self.orthogonality_result_data['Consensus Ranking']
            n = len(final_rank)

            final_rank_pct = (final_rank / n) * 100  # controls which points are shown
            consensus_rank_pct = (consensus_rank / n) * 100  # controls point color

            def get_color(pct):
                if pct >= 99:
                    return '#1A3A9E'
                elif pct >= 95:
                    return '#A0379A'
                elif pct >= 90:
                    return '#E64981'
                elif pct >= 75:
                    return '#FF7C64'
                else:
                    return '#F9F871'

            colors = np.array([get_color(p) for p in consensus_rank_pct])  # color from consensus

            panels = {
                'All': np.ones(n, dtype=bool),
                'Top 50%': final_rank_pct >= 50,  # filter from final_rank
                'Top 20%': final_rank_pct >= 80,
                'Top 10%': final_rank_pct >= 90,
            }

            x_min, x_max = x.min() * 0.8, x.max() * 1.2
            y_min, y_max = y.min() * 0.8, y.max() * 1.2

            gs = GridSpec(2, 2, figure=self.fig, hspace=0.45, wspace=0.35,
                          left=0.1, right=0.82, top=0.92, bottom=0.1)

            for i, (title, mask) in enumerate(panels.items()):
                self.axe = self.fig.add_subplot(gs[i // 2, i % 2])

                x_data = x[mask]
                y_data = y[mask]

                self.axe.scatter(x_data, y_data,
                           c=colors[mask], s=15, edgecolors='k', alpha=0.85, linewidths=0.3, picker=5)

                self.axe.set_xscale('log')
                self.axe.set_yscale('log')
                self.axe.set_xlim(x_data.min() * 0.8, x_data.max() * 1.2)
                self.axe.set_ylim(y_data.min() * 0.8, y_data.max() * 1.2)
                self.axe.set_title(title, fontsize=9)
                self.axe.tick_params(labelsize=7)
                self.axe.xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
                # ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f'{val:.0f}'))
                # ax.yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
                # ax.yaxis.set_major_formatter(ticker.LogFormatterMathtext())
                self.axe.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.5)

                if i in (0, 2):
                    self.axe.set_ylabel('Elution-composition space area', fontsize=7)
                if i in (2, 3):
                   self.axe.set_xlabel('Hypothetical 2D peak capacity', fontsize=7)

            legend_elements = [
                patches.Patch(color='#1A3A9E', label='Top 1%'),
                patches.Patch(color='#A0379A', label='Top 5%'),
                patches.Patch(color='#E64981', label='Top 10%'),
                patches.Patch(color='#FF7C64', label='Top 25%'),
                patches.Patch(color='#F9F871', label='> 25%'),
            ]
            leg = self.fig.legend(handles=legend_elements,
                                  title="Percentile\nd'orthogonalité",
                                  loc='center right',
                                  bbox_to_anchor=(1.0, 0.5),
                                  fontsize=8,
                                  title_fontsize=8,
                                  frameon=True,
                                  edgecolor='gray')
            leg.get_frame().set_linewidth(0.5)

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def plot_elution_area_vs_peak_rate(self):
        self.fig.clear()

        x = self.orthogonality_result_data['Elution Composition Space Area']
        y = self.orthogonality_result_data['Peak Detection Rate (%)']

        x_is_numeric = (x != 'Not available').any()
        y_is_numeric = (y != 'Not available').any()

        if x_is_numeric and y_is_numeric:

            final_rank = self.orthogonality_result_data['Final Rank']
            consensus_rank = self.orthogonality_result_data['Consensus Ranking']
            n = len(final_rank)

            final_rank_pct = (final_rank / n) * 100  # controls which points are shown
            consensus_rank_pct = (consensus_rank / n) * 100  # controls point color

            def get_color(pct):
                if pct >= 99:
                    return '#1A3A9E'
                elif pct >= 95:
                    return '#A0379A'
                elif pct >= 90:
                    return '#E64981'
                elif pct >= 75:
                    return '#FF7C64'
                else:
                    return '#F9F871'

            colors = np.array([get_color(p) for p in consensus_rank_pct])  # color from consensus

            panels = {
                'All': np.ones(n, dtype=bool),
                'Top 50%': final_rank_pct >= 50,  # filter from final_rank
                'Top 20%': final_rank_pct >= 80,
                'Top 10%': final_rank_pct >= 90,
            }

            x_min, x_max = x.min() * 0.8, x.max() * 1.2
            y_min, y_max = y.min() * 0.8, y.max() * 1.2

            gs = GridSpec(2, 2, figure=self.fig, hspace=0.45, wspace=0.35,
                          left=0.1, right=0.82, top=0.92, bottom=0.1)

            for i, (title, mask) in enumerate(panels.items()):
                self.axe = self.fig.add_subplot(gs[i // 2, i % 2])

                x_data = x[mask]
                y_data = y[mask]

                self.axe.scatter(x_data, y_data,
                           c=colors[mask], s=15, edgecolors='k', alpha=0.85, linewidths=0.3, picker=5)

                self.axe.set_xscale('log')
                self.axe.set_yscale('log')
                self.axe.set_xlim(x_data.min() * 0.8, x_data.max() * 1.2)
                self.axe.set_ylim(y_data.min() * 0.8, y_data.max() * 1.2)
                self.axe.set_title(title, fontsize=9)
                self.axe.tick_params(labelsize=7)
                self.axe.xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
                # ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f'{val:.0f}'))
                # ax.yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
                # ax.yaxis.set_major_formatter(ticker.LogFormatterMathtext())
                self.axe.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.5)

                if i in (0, 2):
                    self.axe.set_ylabel('Peak Detection Rate (%)', fontsize=7)
                if i in (2, 3):
                    self.axe.set_xlabel('Elution Composition Space Area', fontsize=7)

            legend_elements = [
                patches.Patch(color='#1A3A9E', label='Top 1%'),
                patches.Patch(color='#A0379A', label='Top 5%'),
                patches.Patch(color='#E64981', label='Top 10%'),
                patches.Patch(color='#FF7C64', label='Top 25%'),
                patches.Patch(color='#F9F871', label='> 25%'),
            ]
            leg = self.fig.legend(handles=legend_elements,
                                  title="Percentile\nd'orthogonalité",
                                  loc='center right',
                                  bbox_to_anchor=(1.0, 0.5),
                                  fontsize=8,
                                  title_fontsize=8,
                                  frameon=True,
                                  edgecolor='gray')
            leg.get_frame().set_linewidth(0.5)

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def plot_median_rank_score_heatmap(self):

        self.fig.clear()

        median_df = self.model.get_median_rank_score_table()

        peak_col = "Peak Detection Rate (%)"
        rank_df = median_df.drop(columns=[peak_col])
        peak_df = median_df[[peak_col]]

        n_rows, n_rank_cols = rank_df.shape

        rank_cmap = LinearSegmentedColormap.from_list(
            "rank_cmap", ["#2166ac", "#f7f7f7", "#fddbc7"], N=256
        )
        peak_cmap = LinearSegmentedColormap.from_list(
            "peak_cmap", ["#fff7bc", "#fdae61", "#d7191c"], N=256
        )

        gs = GridSpec(
            1, 3,
            figure=self.fig,
            width_ratios=[n_rank_cols + 1, 0.07, 0.07],
            left=0.16,
            right=0.84,  # pull grid left to create gap
            top=0.62,
            bottom=0.28,
            wspace=0.35  # more space between heatmap and colorbars
        )

        ax_main = self.fig.add_subplot(gs[0, 0])
        cax_rank = self.fig.add_subplot(gs[0, 1])
        cax_peak = self.fig.add_subplot(gs[0, 2])

        im_rank = ax_main.imshow(
            rank_df.values.astype(float),
            cmap=rank_cmap,
            aspect="auto",
            extent=[-0.5, n_rank_cols - 0.5, n_rows - 0.5, -0.5],
            vmin=rank_df.values.min(),
            vmax=rank_df.values.max()
        )

        im_peak = ax_main.imshow(
            peak_df.values.astype(float),
            cmap=peak_cmap,
            aspect="auto",
            extent=[n_rank_cols - 0.5, n_rank_cols + 0.5, n_rows - 0.5, -0.5],
            vmin=0,
            vmax=1
        )

        ax_main.set_xlim(-0.5, n_rank_cols + 0.5)
        ax_main.set_ylim(n_rows - 0.5, -0.5)

        all_labels = [c.replace(" ", "\n") for c in rank_df.columns] + ["Peak rate\n(value)"]
        ax_main.set_xticks(range(n_rank_cols + 1))
        ax_main.set_xticklabels(all_labels, fontsize=5, fontweight="bold")

        ax_main.set_yticks(range(n_rows))
        ax_main.set_yticklabels(rank_df.index, fontsize=5, fontweight="bold")

        ax_main.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False, length=0)

        ax_main.set_xticks(np.arange(-0.5, n_rank_cols + 1, 1), minor=True)
        ax_main.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
        ax_main.grid(which="minor", color="white", linewidth=1.5)
        ax_main.tick_params(which="minor", length=0)

        for r in range(n_rows):
            for c in range(n_rank_cols):
                ax_main.text(
                    c, r, f"{rank_df.iloc[r, c]:.0f}",
                    ha="center", va="center", fontsize=7, color="black"
                )

        for r in range(n_rows):
            ax_main.text(
                n_rank_cols, r, f"{peak_df.iloc[r, 0]:.2f}",
                ha="center", va="center", fontsize=7, color="black"
            )

        cbar_rank = self.fig.colorbar(im_rank, cax=cax_rank)
        cbar_rank.ax.tick_params(labelsize=6)
        cbar_rank.set_label("Median rank\n(Lower = better)", fontsize=6, labelpad=2)
        # move label to right side so it doesn't overlap ticks
        cbar_rank.ax.yaxis.set_label_position('right')
        cbar_rank.ax.yaxis.tick_left()  # keep ticks on left

        cbar_peak = self.fig.colorbar(im_peak, cax=cax_peak)
        cbar_peak.ax.tick_params(labelsize=6)
        cbar_peak.set_label("Peak rate\n(raw value)", fontsize=6, labelpad=2)

        self.fig.suptitle(
            "A. Median rank heatmap by chromatographic mode",
            fontsize=9, fontweight="bold", x=0.16, ha="left"
        )

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_rank_score_distribution_by_mode(self):
        self.fig.clear()

        df = self.model.get_rank_score_grouped_by_chrom_mode_table()

        metrics = [
            ("Consensus Ranking", "Orthogonality"),
            ("Elution Composition Space Area Rank", "Elution-composition space area"),
            ("Hypothetical 2D Peak Capacity Rank", "Hypothetical 2D peak capacity"),
            ("Final Rank", "Final consensus rank"),
            ("Peak Detection Rate (%)", "Peak rate"),
        ]

        gs = GridSpec(
            2, 3,
            figure=self.fig,
            hspace=0.55,
            wspace=0.35,
            left=0.08,
            right=0.96,
            top=0.86,
            bottom=0.16
        )

        positions = [
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 1),
        ]

        colors = [
            "#E41A1C",
            "#377EB8",
            "#4DAF4A",
            "#984EA3",
            "#FF7F00",
            "#00A6A6",
        ]

        for i, ((column_name, title), position) in enumerate(zip(metrics, positions)):

            self.axe = self.fig.add_subplot(gs[position[0], position[1]])

            labels = []
            values = []

            for mode, group in df:
                labels.append(mode)
                values.append(group[column_name].dropna().values)

            box = self.axe.boxplot(
                values,
                patch_artist=True,
                widths=0.55,
                showfliers=False
            )

            for patch, color in zip(box["boxes"], colors):
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

            for j, y_data in enumerate(values, start=1):
                x_data = np.random.normal(j, 0.04, size=len(y_data))

                self.axe.scatter(
                    x_data,
                    y_data,
                    s=10,
                    color=colors[j - 1],
                    edgecolors="k",
                    linewidths=0.2,
                    alpha=0.75,
                    picker=5
                )

            self.axe.set_title(title, fontsize=9, fontweight="bold")
            self.axe.set_ylabel("Rank score", fontsize=8)
            # self.axe.set_ylim(0, 100)

            self.axe.set_xticks(range(1, len(labels) + 1))
            self.axe.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)

            self.axe.tick_params(axis="y", labelsize=7)
            self.axe.grid(
                True,
                axis="y",
                linestyle="--",
                linewidth=0.4,
                alpha=0.5
            )

        self.fig.suptitle(
            "Example 1 — Rank score distribution by chromatographic mode",
            fontsize=13,
            fontweight="bold",
            y=0.96
        )

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_recommendation_distribution(self):
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        df = self.model.get_recommendation_distribution_group_table()

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

        mode_labels = []
        data = {cat: [] for cat in CATEGORY_ORDER}

        for mode, group in df:
            mode_labels.append(mode)
            recommendations = group.values
            for cat in CATEGORY_ORDER:
                data[cat].append((recommendations == cat).sum())

        x = range(len(mode_labels))
        bar_width = 0.5
        bottoms = [0] * len(mode_labels)

        for cat in CATEGORY_ORDER:
            values = data[cat]
            bars = self.axe.bar(x, values, bar_width, bottom=bottoms,
                          color=COLORS[cat], label=cat)

            for bar, val, bot in zip(bars, values, bottoms):
                if val > 0:
                    self.axe.text(
                        bar.get_x() + bar.get_width() / 2,
                        bot + val / 2,
                        f"{val:,}",
                        ha="center", va="center",
                        fontsize=7, fontweight="bold", color="white",
                    )

            bottoms = [b + v for b, v in zip(bottoms, values)]

        # Total on top
        for i, total in enumerate(bottoms):
            self.axe.text(
                i, total + max(bottoms) * 0.01,
                f"{total:,}",
                ha="center", va="bottom",
                fontsize=7, fontweight="bold", color="#2c2c2a",
            )

        self.axe.set_xticks(list(x))
        self.axe.set_xticklabels(mode_labels, fontsize=7, rotation=15, ha="right")
        self.axe.set_xlabel("Chromatographic mode", fontsize=8)
        self.axe.set_ylabel("Number of combinations", fontsize=8)
        self.axe.set_title("Recommendation distribution", fontsize=9, fontweight="bold")
        self.axe.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
        self.axe.tick_params(axis="both", labelsize=7)
        self.axe.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        self.axe.set_axisbelow(True)
        self.axe.spines[["top", "right"]].set_visible(False)

        self.axe.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, -0.35),
            ncol=2,
            fontsize=7,
            frameon=True,
            edgecolor="#cccccc",
        )

        # Reserve space for the legend below the axes
        self.fig.subplots_adjust(left=0.12, right=0.97, top=0.92, bottom=0.28)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_feasibility_decision_map(self) -> None:
        """Plot a feasibility decision map colored by final recommendation.

        One point = one combination.

        - X-axis: Final Rank (lower = better), normalized to percentile.
        - Y-axis: Peak Detection Rate (%).
        - Point color: Final Recommendation.
        - Marker shape: Chromatographic Mode.

        This version does NOT use background traffic-light zones, because
        the final recommendation already incorporates rank, peak rate,
        compatibility, and complexity.

        Side Effects:
            - Clears and redraws ``self.fig``.
            - Updates ``self.axe``.
            - Redraws the figure canvas.
        """
        self.fig.clear()
        self.axe = self.fig.add_subplot(111)

        df = self.orthogonality_result_data.copy()

        if df is None or df.empty:
            return

        # Resolve the rank column to use
        rank_col = (
            "Final Rank"
            if "Final Rank" in df.columns
            and pd.to_numeric(df["Final Rank"], errors="coerce").notna().any()
            else "Consensus Ranking"
        )

        rank_numeric = pd.to_numeric(df[rank_col], errors="coerce")
        peak_rate = pd.to_numeric(df["Peak Detection Rate (%)"], errors="coerce")

        valid_mask = rank_numeric.notna() & peak_rate.notna()
        df = df.loc[valid_mask].copy()
        rank_numeric = rank_numeric.loc[valid_mask]
        peak_rate = peak_rate.loc[valid_mask]

        if df.empty:
            return

        # Normalize rank to percentile (1–100)
        rank_max = rank_numeric.max()
        x_pct = (rank_numeric / rank_max) * 100 if rank_max else rank_numeric

        # Recommendation colors
        recommendation_colors = {
            "Highly recommended": "#1a7a2e",
            "Recommended": "#6abf4b",
            "Use with caution": "#f5a623",
            "Not recommended": "#d94f3d",
        }

        recommendation_order = [
            "Highly recommended",
            "Recommended",
            "Use with caution",
            "Not recommended",
        ]

        # Marker styles per chromatographic mode
        mode_markers = {
            "HILIC HILIC": "o",
            "HILIC RPLC": "s",
            "RPLC HILIC": "^",
            "RPLC RPLC": "D",
            "SFC RPLC": "v",
            "SFC HILIC": "h",
        }
        fallback_markers = ["o", "s", "^", "D", "v", "h", "p", "*"]

        unique_modes = list(df["Chromatographic Mode"].dropna().unique())
        mode_to_marker = {
            mode: mode_markers.get(mode, fallback_markers[i % len(fallback_markers)])
            for i, mode in enumerate(unique_modes)
        }

        # Plot by recommendation, then by mode
        for rec_label in recommendation_order:
            rec_mask = df["Final Recommendation"] == rec_label
            if not rec_mask.any():
                continue

            for mode in unique_modes:
                mask = rec_mask & (df["Chromatographic Mode"] == mode)
                if not mask.any():
                    continue

                self.axe.scatter(
                    x_pct[mask],
                    peak_rate[mask],
                    s=22,
                    marker=mode_to_marker[mode],
                    color=recommendation_colors.get(rec_label, "#aaaaaa"),
                    edgecolors="k",
                    linewidths=0.3,
                    alpha=0.88,
                    zorder=5,
                )

        # Axes formatting
        self.axe.set_xlim(1, 100)
        self.axe.set_ylim(0, 100)
        self.axe.set_xticks([1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        self.axe.set_xlabel("Final consensus rank (lower = better)", fontsize=8)
        self.axe.set_ylabel("Peak rate (%)", fontsize=8)
        self.axe.set_title(
            "Overall feasibility decision map\none point = one combination",
            fontsize=9,
            fontweight="bold",
            loc="left",
            pad=8,
        )
        self.axe.tick_params(axis="both", labelsize=7)
        self.axe.grid(True, linestyle="--", linewidth=0.4, alpha=0.4)
        self.axe.spines[["top", "right"]].set_visible(False)

        # Recommendation legend
        rec_handles = [
            patches.Patch(
                facecolor=recommendation_colors[label],
                edgecolor="k",
                linewidth=0.4,
                label=label,
            )
            for label in recommendation_order
            if label in df["Final Recommendation"].values
        ]
        rec_legend = self.axe.legend(
            handles=rec_handles,
            title="Final recommendation",
            title_fontsize=7,
            loc="lower left",
            bbox_to_anchor=(0.01, 0.01),
            fontsize=6,
            frameon=True,
            framealpha=0.92,
            edgecolor="#aaaaaa",
        )
        self.axe.add_artist(rec_legend)

        # Mode legend
        from matplotlib.lines import Line2D

        mode_handles = [
            Line2D(
                [0],
                [0],
                marker=mode_to_marker[mode],
                color="w",
                markerfacecolor="#555555",
                markeredgecolor="k",
                markeredgewidth=0.3,
                markersize=5,
                label=mode.replace(" ", "×"),
            )
            for mode in unique_modes
        ]
        self.axe.legend(
            handles=mode_handles,
            title="Chromatographic mode",
            title_fontsize=7,
            loc="upper right",
            bbox_to_anchor=(0.99, 0.99),
            fontsize=6,
            frameon=True,
            framealpha=0.92,
            edgecolor="#aaaaaa",
        )

        self.fig.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.12)
        self.fig.canvas.draw()
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