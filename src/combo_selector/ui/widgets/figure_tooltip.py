import numpy as np
import matplotlib.pyplot as plt


class HoverPopup:
    """
    Attache un popup matplotlib à un scatter plot existant.

    Quand la souris survole un point du scatter, une fenêtre secondaire
    s'affiche avec le contenu défini par `popup_func`.

    Paramètres
    ----------
    ax : Axes
        L'axes matplotlib contenant le scatter à surveiller.
    scatter : PathCollection
        L'objet retourné par ax.scatter(...).
    popup_func : callable(ax_popup, ind) -> None
        Fonction appelée à chaque nouveau point survolé.
        Elle reçoit l'axes vide du popup et l'index du point survolé.
        C'est là que tu dessines ce que tu veux afficher.
    popup_size : tuple, optional
        Taille de la fenêtre popup en pouces (largeur, hauteur).
    hover_radius_px : int, optional
        Distance en pixels pour déclencher le hover.

    Exemple
    -------
        sc = ax.scatter(x, y)

        def mon_popup(ax_popup, ind):
            ax_popup.scatter(sub_x[ind], sub_y[ind])
            ax_popup.set_title(f"Point {ind}")

        HoverPopup(ax, sc, mon_popup)
    """

    def __init__(self, ax, scatter, popup_func,
                 popup_size=(4, 3.5), hover_radius_px=10):
        self._ax = ax
        self._scatter = scatter
        self._popup_func = popup_func
        self._hover_radius_px = hover_radius_px
        self._current = None  # index du point actuellement survolé

        # ── Fenêtre popup ─────────────────────────────────────────────────────
        self._fig_popup = plt.figure(figsize=popup_size)
        self._ax_popup = self._fig_popup.add_subplot(111)
        self._fig_popup.canvas.manager.set_window_title("Popup")

        self._win = self._fig_popup.canvas.manager.window
        self._hide()

        # Repasser le focus sur la figure principale
        plt.figure(self._ax.figure.number)

        # ── Connexion de l'événement ──────────────────────────────────────────
        self._cid = ax.figure.canvas.mpl_connect(
            "motion_notify_event", self._on_motion
        )

    # ── API publique ──────────────────────────────────────────────────────────

    def detach(self):
        """Déconnecte le handler et ferme la popup."""
        self._ax.figure.canvas.mpl_disconnect(self._cid)
        plt.close(self._fig_popup)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _on_motion(self, event):
        if event.inaxes is not self._ax:
            if self._current is not None:
                self._current = None
                self._hide()
            return

        # Coordonnées pixel de tous les points du scatter
        xy_data = self._scatter.get_offsets()  # shape (N, 2)
        pts_px = self._ax.transData.transform(xy_data)
        mouse = np.array([event.x, event.y])
        dists = np.linalg.norm(pts_px - mouse, axis=1)
        nearest = int(np.argmin(dists))

        if dists[nearest] <= self._hover_radius_px:
            if self._current != nearest:
                self._current = nearest
                self._update_popup(nearest, event)
        else:
            if self._current is not None:
                self._current = None
                self._hide()

    def _update_popup(self, ind, event):
        """Redessine le popup et le positionne à droite du curseur."""
        self._ax_popup.cla()
        self._popup_func(self._ax_popup, ind)
        self._fig_popup.tight_layout(pad=1.2)
        self._fig_popup.canvas.draw_idle()

        sx, sy = self._cursor_to_screen(event)
        self._show_at(sx, sy)

    def _cursor_to_screen(self, event):
        """Convertit les coords canvas matplotlib → coords écran."""
        canvas = self._ax.figure.canvas
        cx = int(event.x)
        cy = int(canvas.height() - event.y)  # flip Y (mpl=bas, Qt=haut)
        try:
            from PyQt5.QtCore import QPoint
            gp = canvas.mapToGlobal(QPoint(cx, cy))
            return gp.x(), gp.y()
        except ImportError:
            pass
        try:
            from PyQt6.QtCore import QPoint
            gp = canvas.mapToGlobal(QPoint(cx, cy))
            return gp.x(), gp.y()
        except ImportError:
            pass
        return cx, cy  # Tk : coords déjà en espace écran

    def _show_at(self, sx, sy):
        POPUP_W, POPUP_H = (
            int(self._fig_popup.get_figwidth() * self._fig_popup.dpi),
            int(self._fig_popup.get_figheight() * self._fig_popup.dpi),
        )
        x = sx + 20  # 20 px à droite du curseur
        y = sy  # bord haut aligné avec le curseur
        try:
            self._win.wm_geometry(f"+{x}+{y}")
            self._win.deiconify()
            self._win.lift()
        except AttributeError:
            self._win.setGeometry(x, y, POPUP_W, POPUP_H)
            self._win.show()
            self._win.raise_()

    def _hide(self):
        try:
            self._win.withdraw()
        except AttributeError:
            self._win.hide()