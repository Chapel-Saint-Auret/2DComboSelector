"""Modern sidebar navigation menu with logo, items, and footer.

This module provides a modern, dark-themed sidebar navigation component with:
- Logo display at the top
- Customizable menu items with icons
- Badge support for notifications
- Copyright and version footer
- Custom item delegate for styling
- Rounded corners and modern aesthetics
"""

import sys

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from combo_selector.utils import get_version, resource_path

# Sidebar color scheme
SIDEBAR_BG = "#232b43"


class SidebarItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering sidebar menu items.

    Handles custom painting for:
    - Header items (section labels)
    - Regular items with icons
    - Selected item highlighting
    - Badge notifications

    Visual features:
    - Rounded background for selected items
    - Icon + text layout
    - Optional badge on the right
    """

    def paint(self, painter: QPainter, option, index) -> None:
        """Paint a sidebar item.

        Args:
            painter (QPainter): Painter to draw with.
            option (QStyleOptionViewItem): Style options.
            index (QModelIndex): Item index.
        """
        painter.save()
        rect = option.rect
        is_header = index.data(Qt.UserRole) == "header"
        selected = option.state & QStyle.State_Selected

        if is_header:
            # Draw header text (section label)
            painter.setPen(QColor("#8a99b8"))
            font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                rect.adjusted(24, 0, 0, 0),
                Qt.AlignVCenter | Qt.AlignLeft,
                index.data(Qt.DisplayRole),
            )
        else:
            # Draw selected background
            if selected:
                painter.setBrush(QColor("#4e5d78"))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(rect.adjusted(6, 4, -6, -4), 10, 10)

            # Draw icon
            icon = index.data(Qt.DecorationRole)
            icon_size = 24
            icon_padding = 10
            text_x = rect.left() + icon_padding + icon_size + 14

            if icon:
                icon_rect = QRect(
                    rect.left() + icon_padding,
                    rect.top() + (rect.height() - icon_size) // 2,
                    icon_size,
                    icon_size,
                )
                icon.paint(painter, icon_rect, Qt.AlignCenter)

            # Draw text
            painter.setPen(QColor("#fff") if selected else QColor("#bfc8e2"))
            font = QFont("Segoe UI", 10, QFont.Bold if selected else QFont.Normal)
            painter.setFont(font)
            painter.drawText(
                QRect(text_x, rect.top(), rect.width() - text_x, rect.height()),
                Qt.AlignVCenter | Qt.AlignLeft,
                index.data(Qt.DisplayRole).strip(),
            )

            # Draw badge (notification count)
            badge = index.data(Qt.UserRole + 1)
            if badge:
                badge_rect = QRect(
                    rect.right() - 44,
                    rect.top() + (rect.height() - 20) // 2,
                    36,
                    20
                )
                painter.setBrush(QColor("#5062f0"))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(badge_rect, 10, 10)
                painter.setPen(QColor("#fff"))
                painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
                painter.drawText(badge_rect, Qt.AlignCenter, str(badge))

        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        """Return the size hint for an item.

        Args:
            option (QStyleOptionViewItem): Style options.
            index (QModelIndex): Item index.

        Returns:
            QSize: Recommended size (width 200, height 36 for headers, 48 for items).
        """
        is_header = index.data(Qt.UserRole) == "header"
        return QSize(200, 36 if is_header else 48)


class SidebarLogo(QFrame):
    """Logo display widget for sidebar top section.

    Loads and displays an SVG logo with proper aspect ratio.
    Falls back gracefully if logo file is missing.
    """

    def __init__(self):
        """Initialize the logo widget."""
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 24, 0, 12)
        layout.setSpacing(0)

        try:
            logo = QSvgWidget()
            logo.load(resource_path("icons/logo.svg"))
            logo.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
            layout.addWidget(logo)
        except Exception:
            # Graceful fallback if logo not found
            pass


class SidebarFooter(QFrame):
    """Footer widget showing copyright and version information.

    Displays:
    - Copyright symbol and author name
    - Application version number
    """

    def __init__(self):
        """Initialize the footer widget."""
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(10)

        # Copyright row
        copyright_row = QHBoxLayout()
        copyright_icon = QLabel(chr(0x00A9))  # © symbol
        copyright_icon.setStyleSheet("color: white; font-size: 11px;")
        copyright_row.addWidget(copyright_icon)

        author_label = QLabel("Chapel-Saint-Auret")
        author_label.setStyleSheet("color: white; font-size: 11px;")
        copyright_row.addWidget(author_label, alignment=Qt.AlignLeft)
        copyright_row.addStretch()
        layout.addLayout(copyright_row)

        # Version label
        version_lbl = QLabel(get_version())
        version_lbl.setStyleSheet("color: white; font-size: 11px;")
        version_lbl.setAlignment(Qt.AlignLeft)
        layout.addWidget(version_lbl)


class Sidebar(QListWidget):
    """List widget for sidebar menu items.

    Provides the main navigation list with custom styling.
    Supports icons, selection, and badge indicators.

    Attributes:
        Fixed width of 240px.
        Dark blue background with light text.
    """

    def __init__(self):
        """Initialize the sidebar list widget."""
        super().__init__()

        self.setStyleSheet("""
            QListWidget {
                background: #232b43;
                border: none;
                color: #bfc8e2;
                font-family: 'Segoe UI', sans-serif;
            }
            QListWidget::item:selected {
                background: #273c75;
                color: #fff;
            }
        """)
        self.setIconSize(QSize(24, 24))
        self.setSpacing(10)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedWidth(240)

    def add_item(self, text: str, icon: str = None) -> None:
        """Add a menu item to the sidebar.

        Args:
            text (str): Display text for the item.
            icon (str, optional): Path to icon file.

        Side Effects:
            - Adds item to list widget
            - Sets icon if provided
        """
        item = QListWidgetItem(text)
        self.addItem(item)

        if icon:
            item.setIcon(QIcon(icon))


class ModernSidebar(QFrame):
    """Complete modern sidebar component with logo, menu, and footer.

    Combines all sidebar elements into a single widget:
    - Logo at the top
    - Navigation menu in the middle
    - Copyright/version footer at the bottom

    Features:
    - Dark blue theme (#232b43)
    - Rounded left corners
    - Fixed width of 200px
    - Custom item delegate for styling

    Attributes:
        sidebar_menu (Sidebar): The menu list widget.

    Example:
        >>> sidebar = ModernSidebar()
        >>> sidebar.get_menu_list().add_item("Home", "icons/home.png")
        >>> sidebar.get_menu_list().add_item("Settings", "icons/settings.png")
    """

    def __init__(self):
        """Initialize the modern sidebar."""
        super().__init__()

        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar frame
        side_bar_frame = QFrame()
        side_bar_frame.setFixedWidth(200)
        side_bar_frame.setStyleSheet(f"""
            background: {SIDEBAR_BG};
            border-top-left-radius: 20px;
            border-bottom-left-radius: 20px;
        """)

        layout = QVBoxLayout(side_bar_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add components
        layout.addWidget(SidebarLogo())
        layout.addSpacing(6)

        self.sidebar_menu = Sidebar()
        self.sidebar_menu.setItemDelegate(SidebarItemDelegate())
        layout.addWidget(self.sidebar_menu)

        layout.addWidget(SidebarFooter())

        # Content frame (for future expansion)
        self.content_frame = QFrame(self)
        content_frame_layout = QVBoxLayout(self.content_frame)
        content_frame_layout.setContentsMargins(0, 0, 0, 0)
        content_frame_layout.setSpacing(0)

        main_layout.addWidget(side_bar_frame, 0, 1, 1, 1)

    def get_menu_list(self) -> Sidebar:
        """Get the sidebar menu list widget.

        Returns:
            Sidebar: The menu list widget for adding items.
        """
        return self.sidebar_menu


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Simple usage example showing the modern sidebar."""

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("ModernSidebar Example")
    window.resize(800, 600)

    layout = QHBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create sidebar
    sidebar = ModernSidebar()

    # Add menu items
    menu = sidebar.get_menu_list()
    menu.add_item("Dashboard")
    menu.add_item("Analytics")
    menu.add_item("Projects")
    menu.add_item("Calendar")
    menu.add_item("Settings")

    # Add sidebar to layout
    layout.addWidget(sidebar)

    # Add content area
    content = QLabel("Main Content Area\n\nClick sidebar items to navigate.")
    content.setAlignment(Qt.AlignCenter)
    content.setStyleSheet("background: #edf1f8; font-size: 18px;")
    layout.addWidget(content)


    # Connect selection signal
    def on_item_clicked(item):
        content.setText(f"Selected: {item.text()}\n\nContent for {item.text()} goes here.")


    menu.itemClicked.connect(on_item_clicked)

    window.show()
    sys.exit(app.exec())