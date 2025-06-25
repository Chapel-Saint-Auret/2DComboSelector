from math import sqrt
from typing import Optional

import numpy as np
from matplotlib import patches, collections
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.collections import QuadMesh
from matplotlib.lines import Line2D


class PlotUtils:

    def __init__(self,fig: Figure):
        super().__init__()

        self.colorbar = None
        self.orthogonality_data = None
        self.fig = fig
        self.axe = None
        self.set_number = 'Set 1'
        self.scatter_collection = None

    def set_orthogonality_data(self,orthogonality_dict):
        self.orthogonality_data = orthogonality_dict

    def set_set_number(self,set_nb):
        self.set_number = set_nb

    def set_axe(self,axe):
        self.axe = axe

    def set_scatter_collection(self,scatter_collection):
        self.scatter_collection = scatter_collection

    def __draw_figure(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def clf(self):
        self.fig.clf()

    def clean_figure(self):
        """Clean the selected Matplotlib axis while preserving background settings."""

        # Remove colorbar
        # when you call self.colorbar.remove(), the self.colorbar object is already detached from its axes
        # or has been removed, so its .ax attribute is None.
        # This often happens if you try to remove the colorbar multiple times
        # if self.colorbar is not None and getattr(self.colorbar, 'ax', None) is not None:
        #     self.colorbar.remove()
        #     self.colorbar = None

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
        self.fig.patch.set_facecolor("white")  # Ensure the entire figure has a white background


    def plot_scatter(self,
        set_number: str = '',
        title: Optional[str] = None,
        draw=True,
        dirname: str = ""
    ):
        """
        Create or update a scatter on the given Axes, then optionally save the figure.

        Args:
            orthogonality_dict: dict mapping set numbers to dicts with keys
                'x_values', 'y_values', 'x_title', 'y_title'.
            set_nb: which key of orthogonality_dict to plot.
            fig: the matplotlib Figure to draw on.
            axe: the Axes in that Figure.
            scatter_collection: existing PathCollection (from `axes.scatter()`) or None.
            title: title text (defaults to set_nb).
            dirname: if non‐empty, directory in which to save a PNG named scatter_{set_nb}.png.

        Returns:
            (fig, axe, scatter_collection): updated or newly created.
            :param dirname:
            :param title:
            :param set_number:
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]
        x, y = data['x_values'], data['y_values']
        x_title, y_title = data['x_title'], data['y_title']
        title = title or str(set_nb)

        # 1) Update title and labels
        self.axe.set_title(title, fontdict={'fontsize': 14}, pad=16)
        self.axe.set_xlabel(x_title, fontsize=12)
        self.axe.set_ylabel(y_title, fontsize=12)

        # 2) Create or update scatter
        if self.scatter_collection is None:
            self.scatter_collection = self.axe.scatter(x,y,s=20, c='k', marker='o', alpha=0.5)
        else:
            self.scatter_collection.set_offsets(list(zip(x, y)))

        # 3) Hide legend if present
        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        # 4) Redraw and optionally save
        self.__draw_figure()
        # if dirname:
        #     os.makedirs(dirname, exist_ok=True)
        #     self.fig.savefig(os.path.join(dirname, f"scatter_{set_nb}.png"))

    def plot_percent_bin(self,set_number: str = '',) -> None:
        """
        Plot percent‐bin summary on the given Figure/Axes.

        Args:
            orthogonality_dict: your data dict with a 'percent_bin' sub‐dict.
            fig:            the Figure to draw text on.
            axe:            the Axes to draw the pcolormesh.
            set_nb:         which key in orthogonality_dict to use.
            :param set_number:
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]['percent_bin']
        H_color     = data['mask']
        percent_bin = data['value']
        sad_dev_fs  = data['sad_dev_fs']
        sad_dev     = data['sad_dev']
        sad_dev_ns  = data['sad_dev_ns']
        xedges, yedges  = data['edges']

        # define a 5×5 grid
        self.axe.pcolormesh(
            xedges, yedges, H_color,
            alpha=0.5,
            cmap=ListedColormap(['red']),
            edgecolors='k',
            linewidth=0.5
        )

        # position the stats text just to the right of the axis
        pos    = self.axe.get_position()
        x_text = pos.x1 + 0.01
        self.fig.text(x_text, 0.85, f"$\\sum dev$= {sad_dev:.2f}",    fontsize=9, ha='left')
        self.fig.text(x_text, 0.80, f"$\\sum dev_{{fs}}$= {sad_dev_fs:.2f}", fontsize=9, ha='left')
        self.fig.text(x_text, 0.75, f"$\\sum dev_{{ns}}$= {sad_dev_ns:.2f}", fontsize=9, ha='left')
        self.fig.text(x_text, 0.70, f"% BIN= {percent_bin:.2f}",      fontsize=9, ha='left')

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        self.__draw_figure()

    def plot_modeling_approach(self,
        set_number: str = '',
        erase_previous: bool = True,
        draw =  True) -> None:
        """
        Plot the bin‐box grid mask on the given Figure/Axes.

        Args:
            orthogonality_dict: your data dict with a 'bin_box'.
            fig:            the Figure for drawing.
            axe:            the Axes to draw the pcolormesh.
            set_nb:         which key in orthogonality_dict to use.
            n_boxes:        number of bins per axis.
            erase_previous: remove old grid if True.
            :param erase_previous:
            :param n_boxes:
            :param set_number:
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
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

        x = data['x_values']
        H_color = data['modeling_approach']['color_mask']
        xedges, yedges = data['modeling_approach']['edges']
        slope, intercept, r, p, se = data['linregress']


        self.axe.pcolormesh(
            xedges, yedges, H_color,
            alpha=0.5,
            cmap=ListedColormap(['red']),
            edgecolors='k',
            linewidth=0.5
        )

        # plot fitted line
        self.axe.plot(x, intercept + slope * x, 'r', label='fitted line')

        # build legend entries
        legend_elements = [
            Line2D([0], [0], marker='', color='w',
                   label=f"$y = {slope:.2f}x{'+' if intercept>=0 else ''}{intercept:.2f}$")
        ]

        # draw legend
        legend = self.axe.legend(
            handles=legend_elements,
            frameon=False,
            fontsize=9,
            handlelength=0,
            handletextpad=0.5,
            labelspacing=0.2
        )
        # style the regression‐equation entry
        legend.get_texts()[-1].set_fontweight('bold')
        legend.get_texts()[-1].set_color('navy')

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        if draw == True:
            self.__draw_figure()

    def plot_bin_box(self,
        set_number: str = '',
        erase_previous: bool = True,
        draw =  True) -> None:
        """
        Plot the bin‐box grid mask on the given Figure/Axes.

        Args:
            orthogonality_dict: your data dict with a 'bin_box'.
            fig:            the Figure for drawing.
            axe:            the Axes to draw the pcolormesh.
            set_nb:         which key in orthogonality_dict to use.
            n_boxes:        number of bins per axis.
            erase_previous: remove old grid if True.
            :param erase_previous:
            :param n_boxes:
            :param set_number:
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
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

        H_color = data['bin_box']['color_mask']
        xedges, yedges = data['bin_box']['edges']
        self.axe.pcolormesh(
            xedges, yedges, H_color,
            alpha=0.5,
            cmap=ListedColormap(['red']),
            edgecolors='k',
            linewidth=0.5
        )

        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        if draw == True:
            self.__draw_figure()

    def plot_conditional_entropy(self,
        set_number: str = '',
        erase_previous: bool = True,
        draw =  True) -> None:
        """
        Plot the bin‐box grid mask on the given Figure/Axes.

        Args:
            orthogonality_dict: your data dict with a 'bin_box'.
            fig:            the Figure for drawing.
            axe:            the Axes to draw the pcolormesh.
            set_nb:         which key in orthogonality_dict to use.
            n_boxes:        number of bins per axis.
            erase_previous: remove old grid if True.
            :param erase_previous:
            :param n_boxes:
            :param set_number:
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
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

        histogram = data['conditional_entropy']['histogram']
        xedges, yedges = data['conditional_entropy']['edges']
        colormesh = self.axe.pcolormesh(
            xedges, yedges, histogram,
            alpha=0.8,
            cmap='jet',
        )
        # self.colorbar = self.fig.colorbar(colormesh, ax=self.axe)



        leg = self.axe.get_legend()
        if leg:
            leg.set_visible(False)

        if draw == True:
            self.__draw_figure()


    def plot_asterisk(self,set_number: str = '') -> None:
        """
        Draw the asterisk‐style stability diagram on `axe`, appending new
        artists into `artist_list` and `arrow_list`.

        Mutates `artist_list` and `arrow_list` in place; returns None.
        """
        # pick the data

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]['asterisk_metrics']
        A0              = data['a0']
        Zminus, Zplus   = data['z_minus'], data['z_plus']
        Z1, Z2          = data['z1'], data['z2']
        szm, szp, sz1, sz2 = (data['sigma_sz_minus'],
                              data['sigma_sz_plus'],
                              data['sigma_sz1'],
                              data['sigma_sz2'])

        # reset axes limits
        self.axe.set_xlim(0, 1)
        self.axe.set_ylim(0, 1)

        # clear old legend entries
        if leg := self.axe.get_legend():
            for handle in leg.legend_handles:
                handle.set_label(None)


        # small helper to draw one arrow
        def draw_arrow(start, end, **kw):
            dx, dy = end[0] - start[0], end[1] - start[1]
            self.axe.arrow(
                start[0], start[1], dx, dy,
                head_width=0.01,
                length_includes_head=True,
                color='red',
                **kw
            )

        # place the four corner labels
        self.axe.text(0.16, 0.03, "$Z_-$", fontsize='medium')
        self.axe.text(0.84, 0.95, "$Z_-$", fontsize='medium')
        self.axe.text(0.51, 0.02, "$Z_1$", fontsize='medium')
        self.axe.text(0.51, 0.94, "$Z_1$", fontsize='medium')
        self.axe.text(0.10, 0.45, "$Z_2$", fontsize='medium')
        self.axe.text(0.90, 0.45, "$Z_2$", fontsize='medium')
        self.axe.text(0.84, 0.02, "$Z_+$", fontsize='medium')
        self.axe.text(0.16, 0.94, "$Z_+$", fontsize='medium')
        # compute arrow offsets
        factor = 2.5
        dszm = sqrt(2) * szm / factor
        dszp = sqrt(2) * szp / factor
        dsz1 = sqrt(2) * sz1 / factor
        dsz2 = sqrt(2) * sz2 / factor

        # draw the four sigma‐arrows + labels
        draw_arrow((0.2, 0.2 + dszm), (0.2 + dszm, 0.2))
        draw_arrow((0.2 + dszm, 0.2), (0.2, 0.2 + dszm))
        self.axe.text(0.2 + dszm, 0.17, f"$S_{{Z_-}}$:{szm:.3f}", color='red', fontsize='medium')

        draw_arrow((0.2, 0.8 - dszp), (0.2 + dszp, 0.8))
        draw_arrow((0.2 + dszp, 0.8), (0.2, 0.8 - dszp))
        self.axe.text(0.2, 0.75 - dszp, f"$S_{{Z_+}}$:{szp:.3f}", color='red', fontsize='medium')

        draw_arrow((0.5 - dsz1/2, 0.8), (0.5 + dsz1/2, 0.8))
        draw_arrow((0.5 + dsz1/2, 0.8), (0.5 - dsz1/2, 0.8))
        self.axe.text(0.61 - dsz1/2, 0.75, f"$S_{{Z_1}}$:{sz1:.3f}", color='red', fontsize='medium')

        draw_arrow((0.8, 0.5 - dsz2/2), (0.8, 0.5 + dsz2/2))
        draw_arrow((0.8, 0.5 + dsz2/2), (0.8, 0.5 - dsz2/2))
        self.axe.text(0.75, 0.45 - dsz2/2, f"$S_{{Z_2}}$:{sz2:.3f}", color='red', fontsize='medium')

        # now the diagonal & cross lines
        time = np.linspace(0, 1, 6)
        self.axe.plot(time, time,    label=f"$Z_-$: {Zminus:.3f}", color='black', linestyle='-')[0]
        self.axe.plot(time, 1-time, label=f"$Z_+$: {Zplus:.3f}", color='black', linestyle='--')[0]
        self.axe.vlines(0.5, 0, 1,  label=f"$Z_1$: {Z1:.3f}",  linestyle='-.', color='black')
        self.axe.hlines(0.5, 0, 1,  label=f"$Z_2$: {Z2:.3f}",  linestyle=':',  color='black')


        # final legend
        self.axe.legend(bbox_to_anchor=(1,1), loc="upper left")

        # redraw
        self.__draw_figure()

    def plot_linear_reg(self,set_number: str = '',) -> None:
        """
        Draws a fitted line and custom legend of regression & correlation metrics.
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        data = self.orthogonality_data[set_nb]
        x = data['x_values']
        slope, intercept, r, p, se = data['linregress']
        r     = data['pearson_r']
        rho   = data['spearman_rho']
        tau   = data['kendall_tau']

        # reset axes & clear old lines
        self.axe.set_xlim(0, 1)
        self.axe.set_ylim(0, 1)
        for line in self.axe.get_lines():
            line.remove()

        # plot fitted line
        self.axe.plot(x, intercept + slope * x, 'r', label='fitted line')

        # build legend entries
        legend_elements = [
            Line2D([0], [0], marker='', color='w', label=f'Pearson $r$: {r:.2f}'),
            Line2D([0], [0], marker='', color='w', label=f'Spearman $ρ$: {rho:.2f}'),
            Line2D([0], [0], marker='', color='w', label=f'Kendall $τ$: {tau:.2f}'),
            Line2D([0], [0], marker='', color='w',
                   label=f"$y = {slope:.2f}x{'+' if intercept>=0 else ''}{intercept:.2f}$")
        ]

        # draw legend
        legend = self.axe.legend(
            handles=legend_elements,
            frameon=False,
            fontsize=9,
            handlelength=0,
            handletextpad=0.5,
            labelspacing=0.2
        )
        # style the regression‐equation entry
        legend.get_texts()[-1].set_fontweight('bold')
        legend.get_texts()[-1].set_color('navy')

        self.__draw_figure()


    def plot_percent_fit_xy(self,set_number: str = '',) -> None:
        """
        Plots the %‐fit vs XY, updates the provided scatter collection, and prints stats.
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        data       = self.orthogonality_data[set_nb]
        x, y       = data['x_values'], data['y_values']
        x_title    = data['x_title']
        y_title    = data['y_title']
        model_xy   = data['quadratic_reg_xy']
        pct        = data['percent_fit']
        avg, sd    = pct['delta_xy_avg'], pct['delta_xy_sd']
        fit_val    = pct['value']
        coeffs     = model_xy.coeffs

        # draw quadratic fit
        xs = np.linspace(0, 10, 100)
        self.axe.plot(xs, model_xy(xs), color='red')

        # update full‐scatter offsets
        self.scatter_collection.set_offsets(list(zip(x, y)))

        # labels
        self.axe.set_xlabel(x_title, fontsize=12)
        self.axe.set_ylabel(y_title, fontsize=12)

        pos = self.axe.get_position()
        tx = pos.x1 + 0.01
        self.fig.text(tx, 0.85, f"$\\Delta xy_{{AVG}}$= {avg:.2f}", fontsize=9, ha='left')
        self.fig.text(tx, 0.80, f"$\\Delta xy_{{SD}}$= {sd:.2f}", fontsize=9, ha='left')
        self.fig.text(tx, 0.75, f"%FIT= {fit_val:.2f}",        fontsize=9, ha='left')
        eq = f"y = {coeffs[0]:.2f}x² {'+' if coeffs[1]>=0 else ''}{coeffs[1]:.2f}x {'+' if coeffs[2]>=0 else ''}{coeffs[2]:.2f}"
        self.fig.text(tx, 0.70, eq, fontdict={'fontsize': 10})

        # hide any legend
        if leg := self.axe.get_legend():
            leg.set_visible(False)

        self.__draw_figure()


    def plot_percent_fit_yx(self,set_number: str = '',) -> None:
        """
        Plots the %‐fit vs YX (swapped), updates the provided scatter collection, and prints stats.
        """

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        data       = self.orthogonality_data[set_nb]
        x, y       = data['x_values'], data['y_values']
        x_title    = data['x_title']
        y_title    = data['y_title']
        model_yx   = data['quadratic_reg_yx']
        pct        = data['percent_fit']
        avg, sd    = pct['delta_yx_avg'], pct['delta_yx_sd']
        fit_val    = pct['value']
        coeffs     = model_yx.coeffs

        xs = np.linspace(0, 10, 100)
        self.axe.plot(xs, model_yx(xs), color='red')

        self.scatter_collection.set_offsets(list(zip(y, x)))

        self.axe.set_xlabel(x_title, fontsize=12)
        self.axe.set_ylabel(y_title, fontsize=12)

        pos = self.axe.get_position()
        tx = pos.x1 + 0.01
        self.fig.text(tx, 0.85, f"$\\Delta yx_{{AVG}}$= {avg:.2f}", fontsize=9, ha='left')
        self.fig.text(tx, 0.80, f"$\\Delta yx_{{SD}}$= {sd:.2f}", fontsize=9, ha='left')
        self.fig.text(tx, 0.75, f"%FIT= {fit_val:.2f}",        fontsize=9, ha='left')
        eq = f"y = {coeffs[0]:.2f}x² {'+' if coeffs[1]>=0 else ''}{coeffs[1]:.2f}x {'+' if coeffs[2]>=0 else ''}{coeffs[2]:.2f}"
        self.fig.text(tx, 0.70, eq, fontdict={'fontsize': 10})

        if leg := self.axe.get_legend():
            leg.set_visible(False)

        self.__draw_figure()

    def plot_convex_hull(self,
        set_number: str = '',
        erase_previous: bool = True
    ) -> None:
        """
        Draws the convex hull edges on the given Axes.
        """
        # optionally clear old hull lines

        if not self.orthogonality_data:
            return

        if set_number is '':
            set_nb = self.set_number
        else:
            set_nb = set_number

        if erase_previous:
            for line in self.axe.get_lines():
                line.remove()

        hull   = self.orthogonality_data[set_nb]['convex_hull']
        subset = self.orthogonality_data[set_nb]['hull_subset']

        # draw each simplex
        if hull:
            for simplex in hull.simplices:
                self.axe.plot(subset[simplex, 0], subset[simplex, 1], 'r-')

        if leg := self.axe.get_legend():
            leg.set_visible(False)

        self.__draw_figure()

