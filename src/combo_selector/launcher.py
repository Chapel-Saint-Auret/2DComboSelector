"""Lightweight application launcher.

Only Qt's startup classes are imported before the splash is displayed.  The
full application (and its heavier scientific dependencies) is loaded while
the splash is already visible.
"""

import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen


APP_USER_MODEL_ID = "ChapelSaintAuret.2DComboSelector"


def _resource_path(relative_path: str) -> str:
    """Resolve a resource in both source and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / "resources" / relative_path)


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
    app.setWindowIcon(QIcon(_resource_path("icons/app_icon.ico")))

    splash = QSplashScreen(QPixmap(_resource_path("icons/splash_log_ver.svg")))
    splash.show()
    app.processEvents()

    from combo_selector.main import ComboSelectorMain

    window = ComboSelectorMain()
    window.showMaximized()
    splash.finish(window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
