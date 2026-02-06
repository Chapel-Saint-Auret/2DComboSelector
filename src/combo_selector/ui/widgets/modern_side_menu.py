import sys

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from combo_selector.utils import get_version, resource_path

SIDEBAR_BG = "#232b43"  # Use your preferred dark blue


class SidebarItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        rect = option.rect
        is_header = index.data(Qt.UserRole) == "header"
        selected = option.state & QStyle.State_Selected

        if is_header:
            painter.setPen(QColor("#8a99b8"))
            font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                rect.adjusted(24, 0, 0, 0),
                Qt.AlignVCenter | Qt.AlignLeft,
                index.data(Qt.DisplayRole),
            )
        else:
            # Draw background for selected item
            if selected:
                painter.setBrush(QColor("#4e5d78"))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(rect.adjusted(6, 4, -6, -4), 10, 10)

            # Draw icon
            icon = index.data(Qt.DecorationRole)
            icon_size = 24
            icon_padding = 10  # More space to the left
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

            # Draw badge if needed
            badge = index.data(Qt.UserRole + 1)
            if badge:
                badge_rect = QRect(
                    rect.right() - 44, rect.top() + (rect.height() - 20) // 2, 36, 20
                )
                painter.setBrush(QColor("#5062f0"))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(badge_rect, 10, 10)
                painter.setPen(QColor("#fff"))
                painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
                painter.drawText(badge_rect, Qt.AlignCenter, str(badge))
        painter.restore()

    def sizeHint(self, option, index):
        is_header = index.data(Qt.UserRole) == "header"
        return QSize(200, 36 if is_header else 48)  # Increase item height here


class SidebarLogo(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 24, 0, 12)
        layout.setSpacing(0)
        logo = QLabel()
        # Draw a simple logo (replace with your own SVG or PNG if available)
        pixmap = QPixmap(resource_path("icons/logo.png"))

        logo = QSvgWidget()
        logo.load(resource_path("icons/logo.svg"))
        logo.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        # logo.setPixmap(pixmap)
        # logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)


class SidebarFooter(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(10)

        # Footer text
        copyright_row = QHBoxLayout()
        copyright_icon = QLabel(chr(0x00A9))
        copyright_icon.setStyleSheet("color: white; font-size: 11px;")
        copyright_row.addWidget(copyright_icon)
        author_label = QLabel("Chapel-Saint-Auret")
        author_label.setStyleSheet("color: white; font-size: 11px;")
        copyright_row.addWidget(author_label, alignment=Qt.AlignLeft)
        copyright_row.addStretch()
        layout.addLayout(copyright_row)

        version_lbl = QLabel(get_version())
        version_lbl.setStyleSheet("color: white; font-size: 11px;")
        version_lbl.setAlignment(Qt.AlignLeft)
        layout.addWidget(version_lbl)


class Sidebar(QListWidget):
    def __init__(self):
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
        # self.populate()

    def add_item(self, text, icon):

        item = QListWidgetItem(text)
        self.addItem(item)

        if icon:
            item.setIcon(QIcon(icon))

    def populate(self):
        # Main navigation section
        nav_header = QListWidgetItem("Navigation")
        nav_header.setFlags(Qt.NoItemFlags)
        nav_header.setData(Qt.UserRole, "header")
        # self.addItem(nav_header)

        dashboards = QListWidgetItem("  Dashboards")
        # dashboards.setIcon(QIcon.fromTheme("view-dashboard"))
        # dashboards.setData(Qt.UserRole + 1)
        self.addItem(dashboards)
        self.addItem(QListWidgetItem("    Default"))
        self.addItem(QListWidgetItem("    Analytics"))
        self.addItem(QListWidgetItem("    SaaS"))
        self.addItem(QListWidgetItem("    Social"))
        self.addItem(QListWidgetItem("    Crypto"))

        # # Apps section
        # apps_header = QListWidgetItem("Apps")
        # apps_header.setFlags(Qt.NoItemFlags)
        # apps_header.setData(Qt.UserRole, "header")
        # self.addItem(apps_header)
        #
        # ecommerce = QListWidgetItem("  E-Commerce")
        # ecommerce.setIcon(QIcon.fromTheme("cart"))
        # self.addItem(ecommerce)
        # projects = QListWidgetItem("  Projects")
        # projects.setIcon(QIcon.fromTheme("folder"))
        # self.addItem(projects)
        # chat = QListWidgetItem("  Chat")
        # chat.setIcon(QIcon.fromTheme("chat"))
        # self.addItem(chat)
        # file_manager = QListWidgetItem("  File Manager")
        # file_manager.setIcon(QIcon.fromTheme("folder"))
        # file_manager.setData(Qt.UserRole + 1, "New")
        # self.addItem(file_manager)
        # calendar = QListWidgetItem("  Calendar")
        # calendar.setIcon(QIcon.fromTheme("calendar"))
        # self.addItem(calendar)
        # email = QListWidgetItem("  Email")
        # email.setIcon(QIcon.fromTheme("mail"))
        # email.setData(Qt.UserRole + 1, "New")
        # self.addItem(email)
        # tasks = QListWidgetItem("  Tasks")
        # tasks.setIcon(QIcon.fromTheme("task-complete"))
        # self.addItem(tasks)

        # # Pages section
        # pages_header = QListWidgetItem("Pages")
        # pages_header.setFlags(Qt.NoItemFlags)
        # pages_header.setData(Qt.UserRole, "header")
        # self.addItem(pages_header)
        # self.addItem(QListWidgetItem("  Pages"))


class ModernSidebar(QFrame):
    def __init__(self):
        super().__init__()

        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        side_bar_frame = QFrame()
        side_bar_frame.setFixedWidth(200)
        side_bar_frame.setStyleSheet(f"""background: {SIDEBAR_BG};
            border-top-left-radius:20px;
    border-bottom-left-radius:20px;
""")
        layout = QVBoxLayout(side_bar_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo at the top
        layout.addWidget(SidebarLogo())
        layout.addSpacing(6)

        # Menu with custom delegate
        self.sidebar_menu = Sidebar()

        # self.sidebar_menu.setStyleSheet(f"background: {SIDEBAR_BG};")
        self.sidebar_menu.setItemDelegate(
            SidebarItemDelegate()
        )  # <-- Apply your custom delegate here
        layout.addWidget(self.sidebar_menu)

        # layout.addStretch(1)
        layout.addWidget(SidebarFooter())

        self.content_frame = QFrame(self)
        content_frame_layout = QVBoxLayout(self.content_frame)
        content_frame_layout.setContentsMargins(0, 0, 0, 0)
        content_frame_layout.setSpacing(0)

        # main_layout.addWidget(self.icon_only_widget, 0, 0, 1, 1)
        main_layout.addWidget(side_bar_frame, 0, 1, 1, 1)
        # main_layout.addWidget(self.content_frame, 0, 2, 1, 1)

        # self.sidebar_menu.itemClicked.connect(self.page_change)

    def get_menu_list(self):
        return self.sidebar_menu
