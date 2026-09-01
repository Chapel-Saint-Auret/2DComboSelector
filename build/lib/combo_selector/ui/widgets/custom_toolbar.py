"""Custom Matplotlib navigation toolbar with high-DPI save support.

Extends :class:`NavigationToolbar2QT` to provide a save dialog that uses
Qt's native file picker and saves figures at 600 DPI with tight bounding box.
"""

import os

import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import QFileDialog, QMessageBox

# Scientific and Data Libraries


class CustomToolbar(NavigationToolbar):
    """Matplotlib toolbar with a Qt-native save dialog and 600 DPI export."""

    def __init__(self, canvas, parent=None):
        """Initialize the custom toolbar.

        Args:
            canvas: Matplotlib canvas to attach the toolbar to.
            parent (QWidget | None): Optional parent widget.
        """
        super(CustomToolbar, self).__init__(canvas, parent)

    def save_figure(self, *args):
        """Open a Qt file dialog and save the figure at 600 DPI.

        Overrides the default Matplotlib save action to use
        :class:`QFileDialog` and save with ``dpi=600``, ``bbox_inches="tight"``,
        and ``transparent=True``.

        Args:
            *args: Ignored positional arguments (required by Matplotlib toolbar API).

        Side Effects:
            - Opens a native save dialog.
            - Writes the figure to the chosen file path.
            - Updates ``mpl.rcParams["savefig.directory"]``.
            - Shows a critical message box on save failure.
        """
        filetypes = self.canvas.get_supported_filetypes_grouped()
        sorted_filetypes = sorted(filetypes.items())
        default_filetype = self.canvas.get_default_filetype()

        startpath = os.path.expanduser(mpl.rcParams["savefig.directory"])
        start = os.path.join(startpath, self.canvas.get_default_filename())
        filters = []
        selectedFilter = None
        for name, exts in sorted_filetypes:
            exts_list = " ".join(["*.%s" % ext for ext in exts])
            filter = f"{name} ({exts_list})"
            if default_filetype in exts:
                selectedFilter = filter
            filters.append(filter)
        filters = ";;".join(filters)

        fname, filter = QFileDialog.getSaveFileName(
            self.canvas.parent(),
            "Choose a filename to save to",
            start,
            filters,
            selectedFilter,
        )
        if fname:
            # Save dir for next time, unless empty str (i.e., use cwd).
            if startpath != "":
                mpl.rcParams["savefig.directory"] = os.path.dirname(fname)
            try:
                self.canvas.figure.savefig(
                    fname, dpi=600, bbox_inches="tight", transparent=True
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error saving file",
                    str(e),
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.NoButton,
                )
