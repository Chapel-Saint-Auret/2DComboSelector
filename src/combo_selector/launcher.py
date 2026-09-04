"""Lightweight application launcher.

Only Qt's startup classes are imported before the splash is displayed.  The
full application (and its heavier scientific dependencies) is loaded while
the splash is already visible.
"""

import ctypes
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from combo_selector.resource_utils import resource_path


APP_USER_MODEL_ID = "ChapelSaintAuret.2DComboSelector"


def main() -> int:
    """Display the splash first, then load and run the full application."""
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app_icon = QIcon(resource_path("icons/app_icon.ico"))
    app.setWindowIcon(app_icon)

    splash = QSplashScreen(QPixmap(resource_path("icons/splash_log_ver.svg")))
    splash.show()
    app.processEvents()

    from combo_selector.main import ComboSelectorMain

    window = ComboSelectorMain()
    window.setWindowIcon(app_icon)
    window.showMaximized()
    splash.finish(window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
