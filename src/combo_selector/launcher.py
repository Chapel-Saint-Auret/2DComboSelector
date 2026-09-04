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


def _set_windows_window_icon(window, icon_path: str) -> None:
    """Set native small and large icons for a frameless Windows window."""
    if sys.platform != "win32":
        return

    user32 = ctypes.windll.user32
    load_image = user32.LoadImageW
    load_image.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_uint,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    load_image.restype = ctypes.c_void_p
    send_message = user32.SendMessageW
    send_message.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_size_t,
        ctypes.c_ssize_t,
    ]
    send_message.restype = ctypes.c_ssize_t

    image_icon = 1
    load_from_file = 0x0010
    wm_seticon = 0x0080
    icon_small = 0
    icon_big = 1

    small_handle = load_image(None, icon_path, image_icon, 16, 16, load_from_file)
    large_handle = load_image(None, icon_path, image_icon, 32, 32, load_from_file)
    window_handle = int(window.winId())

    if small_handle:
        send_message(window_handle, wm_seticon, icon_small, small_handle)
    if large_handle:
        send_message(window_handle, wm_seticon, icon_big, large_handle)

    # Keep the native handles alive for the lifetime of the window.
    window._windows_icon_handles = (small_handle, large_handle)


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
    icon_path = resource_path("icons/app_icon.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    splash = QSplashScreen(QPixmap(resource_path("icons/splash_log_ver.svg")))
    splash.show()
    app.processEvents()

    from combo_selector.main import ComboSelectorMain

    window = ComboSelectorMain()
    window.setWindowIcon(app_icon)
    _set_windows_window_icon(window, icon_path)
    window.showMaximized()
    splash.finish(window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
