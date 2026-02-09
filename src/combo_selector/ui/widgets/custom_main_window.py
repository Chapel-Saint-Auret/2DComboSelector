"""Custom frameless main window with modern UI and neumorphism effects.

This module provides a custom main window with:
- Frameless design with custom title bar
- Min/max/close window controls
- Sidebar navigation with stacked widget pages
- Draggable window
- Status bar with auto-clear messages
- Neumorphism shadow effect (OutsideNeumorphismEffect)
"""

import sys

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QRadialGradient,
    QConicalGradient,
    QPainter,
    QPainterPath,
    QPixmap,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from combo_selector.ui.widgets.modern_side_menu import ModernSidebar
from combo_selector.utils import resource_path


# =============================================================================
# Main Window Stylesheet
# =============================================================================

MAIN_WINDOW_STYLESHEET = """
QPushButton#btn_close, QPushButton#btn_maximize, QPushButton#btn_minimize {
    border: none;
    background: transparent;
    border-radius: 4px;
}

QPushButton#btn_close:hover {
    background-color: rgba(255, 0, 0, 100);
}

QPushButton#btn_maximize:hover {
    background-color: rgba(85, 255, 127, 100);
}

QPushButton#btn_minimize:hover {
    background-color: rgba(255, 170, 0, 100);
}

QFrame#central_widget_frame {
    background-color: #edf1f8;
    border-radius: 22px;
}

QFrame#side_menu_frame {
    background: #325372;
    border-radius: 10px;
}

QHeaderView::section {
    padding: 0px;
    height: 20px;
    border: 0.5px solid #aeadac;
    background: #dddddd;
}

QPushButton {
    padding: 5px;
    background-color: #dddddd;
    border: 0.5px solid #aeadac;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #d6e5fb;
    border: 1px solid #234471;
}

QPushButton:pressed:active {
    background-color: #5188d8;
    border: 1px solid #7e7eff;
}

QPushButton:focus {
    border: 1px solid #234471;
}
"""


class CustomMainWindow(QMainWindow):
    """Custom frameless main window with sidebar navigation.

    Provides a modern, frameless window design with:
    - Custom title bar with min/max/close buttons
    - Sidebar navigation with icon-based menu
    - Stacked widget for page content
    - Draggable window functionality
    - Status bar with auto-clearing messages
    - Context menu support

    Signals:
        menu_clicked(int): Emitted when a menu item is clicked (unused).

    Attributes:
        page_index_map (dict): Maps page names to stacked widget indices.
        globale_state (int): 0=normal, 1=maximized.
        side_bar_menu (ModernSidebar): Sidebar navigation widget.
        content_qstack (QStackedWidget): Stacked widget for page content.
        status_label (QLabel): Status message label.

    Example:
        >>> window = CustomMainWindow()
        >>> window.add_side_bar_item("Home", home_page, "icons/home.png")
        >>> window.add_side_bar_item("Settings", settings_page, "icons/settings.png")
        >>> window.show()
    """

    menu_clicked = Signal(int)

    def __init__(self):
        """Initialize the custom main window."""
        super().__init__()

        self.page_index_map = {}
        self.globale_state = 0  # 0=normal, 1=maximized

        # --- Window configuration ---
        self.setMinimumSize(QSize(1200, 750))
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu)
        self.setStyleSheet(MAIN_WINDOW_STYLESHEET)

        # --- Central widget ---
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)

        self.central_widget_layout = QVBoxLayout(self.central_widget)
        self.central_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.central_widget_frame = QFrame(self.central_widget)
        self.central_widget_frame.setObjectName("central_widget_frame")
        self.central_widget_frame.setFrameShape(QFrame.NoFrame)
        self.central_widget_layout.addWidget(self.central_widget_frame)

        self.main_layout = QHBoxLayout(self.central_widget_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Title bar ---
        self.title_bar_frame = self._create_title_bar()

        # --- Sidebar menu ---
        self.side_bar_menu = ModernSidebar()
        self.main_layout.addWidget(self.side_bar_menu)

        # --- Status bar ---
        self.status_bar_frame = self._create_status_bar()

        # --- Content area ---
        self.content_qstack = QStackedWidget()
        content_frame = self._create_content_frame()
        self.main_layout.addWidget(content_frame)

        # --- Size grip ---
        self.sizegrip = QSizeGrip(self.central_widget)
        self.sizegrip.setToolTip("Resize Window")
        self.main_layout.addWidget(
            self.sizegrip, alignment=Qt.AlignBottom | Qt.AlignRight
        )

        # --- Signal connections ---
        self.btn_maximize.clicked.connect(self.maximize_restore)
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)
        self.title_bar_frame.mouseMoveEvent = self.moveWindow
        self.side_bar_menu.get_menu_list().itemClicked.connect(self.page_change)

    def _create_title_bar(self) -> QFrame:
        """Create the custom title bar with window controls.

        Returns:
            QFrame: Title bar frame with min/max/close buttons.
        """
        title_bar_frame = QFrame()
        title_bar_frame.setObjectName("title_bar_frame")
        title_bar_frame.setFixedHeight(25)

        title_bar_layout = QHBoxLayout(title_bar_frame)
        title_bar_layout.setSpacing(0)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Window control buttons
        btns_frame = QFrame(title_bar_frame)
        btns_frame.setMaximumSize(QSize(100, 16777215))
        btn_layout = QHBoxLayout(btns_frame)
        btn_layout.setContentsMargins(0, 5, 10, 0)
        btn_layout.setSpacing(10)

        self.btn_minimize = QPushButton()
        self.btn_minimize.setIcon(QIcon(resource_path("icons/minimize_window.svg")))
        self.btn_minimize.setObjectName("btn_minimize")
        self.btn_minimize.setFixedSize(16, 16)
        self.btn_minimize.setToolTip("Minimize")

        self.btn_maximize = QPushButton()
        self.btn_maximize.setIcon(QIcon(resource_path("icons/maximize_window.svg")))
        self.btn_maximize.setObjectName("btn_maximize")
        self.btn_maximize.setFixedSize(16, 16)
        self.btn_maximize.setToolTip("Maximize")

        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon(resource_path("icons/close_window.svg")))
        self.btn_close.setFixedSize(16, 16)
        self.btn_close.setIconSize(self.btn_close.size())
        self.btn_close.setToolTip("Close")

        btn_layout.addWidget(self.btn_minimize)
        btn_layout.addWidget(self.btn_maximize)
        btn_layout.addWidget(self.btn_close)
        title_bar_layout.addWidget(btns_frame, alignment=Qt.AlignRight)

        return title_bar_frame

    def _create_status_bar(self) -> QFrame:
        """Create the status bar at the bottom of the window.

        Returns:
            QFrame: Status bar frame with status label.
        """
        status_bar_frame = QFrame()
        status_bar_frame.setObjectName("status_bar_frame")
        status_bar_frame.setFixedHeight(10)
        status_bar_frame.setStyleSheet("""
            QFrame#status_bar_frame {
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)

        status_bar_layout = QHBoxLayout(status_bar_frame)
        status_bar_layout.setContentsMargins(0, 0, 0, 0)
        status_bar_layout.setSpacing(0)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.status_label.setStyleSheet("color: #5c5c5c;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.status_label)

        return status_bar_frame

    def _create_content_frame(self) -> QFrame:
        """Create the content frame with title bar, content, and status bar.

        Returns:
            QFrame: Content frame containing all main UI elements.
        """
        qstack_frame = QFrame()
        qstack_layout = QHBoxLayout()
        qstack_frame.setLayout(qstack_layout)
        qstack_layout.addWidget(self.content_qstack)
        qstack_layout.setContentsMargins(0, 0, 0, 0)
        qstack_layout.setSpacing(0)

        content_frame = QFrame()
        content_frame_layout = QVBoxLayout()
        content_frame_layout.setContentsMargins(0, 0, 0, 0)
        content_frame_layout.setSpacing(0)
        content_frame.setLayout(content_frame_layout)

        content_frame_layout.addWidget(self.title_bar_frame, alignment=Qt.AlignTop)
        content_frame_layout.addWidget(qstack_frame)
        content_frame_layout.addWidget(self.status_bar_frame, alignment=Qt.AlignBottom)

        return content_frame

    def set_status_text(self, text: str) -> None:
        """Set status bar text that auto-clears after 3 seconds.

        Args:
            text (str): Status message to display.

        Side Effects:
            - Sets status label text
            - Schedules text clear after 3000ms
        """
        self.status_label.setText(text)
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def add_side_bar_item(self, text: str, widget: QWidget, icon: str = None) -> None:
        """Add a page to the sidebar navigation.

        Args:
            text (str): Display text for the menu item.
            widget (QWidget): Page widget to display when selected.
            icon (str, optional): Path to icon image file.

        Side Effects:
            - Adds widget to stacked widget
            - Adds menu item to sidebar
            - Updates page index map
        """
        self.content_qstack.addWidget(widget)
        self.side_bar_menu.get_menu_list().add_item(text, icon)

        widget_index = self.content_qstack.indexOf(widget)
        self.page_index_map[text] = {"index": widget_index}

    def page_change(self, item_clicked) -> None:
        """Handle page change when sidebar item is clicked.

        Args:
            item_clicked (QListWidgetItem): The clicked menu item.

        Side Effects:
            - Changes current page in stacked widget
        """
        page_name = item_clicked.text()
        page_index = self.page_index_map[page_name]["index"]
        self.content_qstack.setCurrentIndex(page_index)

    def moveWindow(self, event) -> None:
        """Handle window dragging via title bar.

        Args:
            event (QMouseEvent): Mouse move event.

        Side Effects:
            - Restores window if maximized
            - Moves window to new position
        """
        if self.globale_state == 1:
            self.maximize_restore()

        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def maximize_restore(self) -> None:
        """Toggle between maximized and normal window state.

        Side Effects:
            - Toggles window state
            - Updates margins and tooltips
        """
        if self.globale_state == 0:
            # Maximize
            self.showMaximized()
            self.globale_state = 1
            self.central_widget_layout.setContentsMargins(0, 0, 0, 0)
            self.btn_maximize.setToolTip("Restore")
        else:
            # Restore
            self.globale_state = 0
            self.showNormal()
            self.resize(self.width() + 1, self.height() + 1)
            self.central_widget_layout.setContentsMargins(10, 10, 10, 10)
            self.btn_maximize.setToolTip("Maximize")

    def right_menu(self, pos) -> None:
        """Show context menu on right-click.

        Args:
            pos (QPoint): Position where menu was requested.

        Side Effects:
            - Displays context menu with Import/Exit options
        """
        menu = QMenu()
        import_option = menu.addAction("Import data")
        exit_option = menu.addAction("Exit")
        exit_option.triggered.connect(lambda: exit())
        menu.exec(self.mapToGlobal(pos))

    def mousePressEvent(self, event) -> None:
        """Track mouse press position for window dragging.

        Args:
            event (QMouseEvent): Mouse press event.

        Side Effects:
            - Stores drag position
        """
        self.dragPos = event.globalPosition().toPoint()


# =============================================================================
# Neumorphism Graphics Effect (simplified for brevity)
# =============================================================================

class OutsideNeumorphismEffect(QGraphicsEffect):
    """Neumorphism-style outer shadow effect for widgets.

    Creates a soft, raised appearance with light and shadow gradients
    on all sides and corners of the widget.

    Note: Implementation details omitted for brevity. This class creates
    soft shadows with gradients to achieve a neumorphic design aesthetic.
    """

    _cornerShift = (
        Qt.TopLeftCorner,
        Qt.TopLeftCorner,
        Qt.BottomRightCorner,
        Qt.BottomLeftCorner,
    )

    def __init__(
        self,
        distance: int = 4,
        lightColor: QColor = QColor("#FFFFFF"),
        darkColor: QColor = QColor("#7d7d7d"),
        clipRadius: int = 4,
        origin: Qt.Corner = Qt.TopLeftCorner,
    ):
        """Initialize the neumorphism effect."""
        super().__init__()
        # Implementation details omitted for brevity
        pass

    def boundingRectFor(self, rect):
        """Calculate bounding rect including shadow distance."""
        pass

    def draw(self, qp: QPainter) -> None:
        """Draw the neumorphism effect."""
        pass


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing the custom main window."""

    app = QApplication(sys.argv)

    # Create main window
    window = CustomMainWindow()
    window.setWindowTitle("Custom Main Window Example")

    # Create sample pages
    page1 = QLabel("Home Page\n\nThis is the home page content.")
    page1.setAlignment(Qt.AlignCenter)
    page1.setStyleSheet("font-size: 18px; background: white; padding: 20px;")

    page2 = QLabel("Settings Page\n\nThis is the settings page content.")
    page2.setAlignment(Qt.AlignCenter)
    page2.setStyleSheet("font-size: 18px; background: white; padding: 20px;")

    page3 = QLabel("About Page\n\nThis is the about page content.")
    page3.setAlignment(Qt.AlignCenter)
    page3.setStyleSheet("font-size: 18px; background: white; padding: 20px;")

    # Add pages to sidebar (icons optional - will work without them)
    try:
        window.add_side_bar_item("Home", page1, "icons/home_icon.png")
        window.add_side_bar_item("Settings", page2, "icons/settings_icon.png")
        window.add_side_bar_item("About", page3, "icons/info_icon.png")
    except:
        # Fallback without icons if resource_path fails
        window.add_side_bar_item("Home", page1)
        window.add_side_bar_item("Settings", page2)
        window.add_side_bar_item("About", page3)

    # Show status message
    window.set_status_text("Application ready!")

    window.show()
    sys.exit(app.exec())