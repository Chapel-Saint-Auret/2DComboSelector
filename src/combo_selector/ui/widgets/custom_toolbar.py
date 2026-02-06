import os

import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import QFileDialog, QMessageBox

# Scientific and Data Libraries


class CustomToolbar(NavigationToolbar):
    def __init__(self, canvas, parent=None):
        super(CustomToolbar, self).__init__(canvas, parent)

    def save_figure(self, *args):
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
