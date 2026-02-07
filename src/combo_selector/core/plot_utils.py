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
from matplotlib import collections, patches
from matplotlib.collections import QuadMesh
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D


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

    def __init__(self, fig: Figure):
        """Initialize the PlotUtils with a matplotlib Figure.

        Args:
            fig (Figure): Matplotlib Figure object to use for all plotting operations.
        """
        super().__init__()

        self.orthogonality_data = None
        self.fig = fig
        self.axe = None
        self.set_number = "Set 1"
        self.scatter_collection = None

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
            [text.remove() for text in self.axe.texts]
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
        self.axe.set_title(title, fontdict={"fontsize": 14}, pad=16)
        self.axe.set_xlabel(x_title, fontsize=12)
        self.axe.set_ylabel(y_title, fontsize=12)

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