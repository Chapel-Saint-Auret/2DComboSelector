"""Section help button with Markdown-rendered popup dialog.

Provides a small clickable info icon (ℹ) that opens a non-modal floating
dialog displaying help content loaded from a Markdown (.md) file.

Features:
- Small QToolButton that sits in the top-right corner of any QGroupBox
- Renders Markdown files natively via QTextBrowser (no extra dependencies)
- One shared dialog per window — lightweight and non-intrusive
- Repositions automatically to stay within screen bounds
- Falls back gracefully if the help file is missing

Usage:
    # After building your group box normally, attach a help button:
    group = self._create_ranking_group()
    SectionHelpButton.for_group(group, "Ranking", "help/ranking.md")
"""

import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from combo_selector.utils import resource_path


# =============================================================================
# Help Dialog
# =============================================================================

class HelpDialog(QDialog):
    """Floating non-modal dialog that renders Markdown help content.

    Positioned next to the button that opened it. Uses QTextBrowser's
    native Markdown rendering (Qt 6), so no extra dependencies are needed.

    Attributes:
        _title_label (QLabel): Section title shown in the dialog header.
        _browser (QTextBrowser): Renders the Markdown content as HTML.

    Example:
        >>> dialog = HelpDialog(parent=window)
        >>> dialog.show_for("Ranking", "help/ranking.md", anchor=btn)
    """

    def __init__(self, parent: QWidget = None):
        """Initialize the help dialog.

        Args:
            parent (QWidget, optional): Parent window. Used for modality
                scoping and screen geometry calculations.
        """
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose, False)  # reuse instance
        self.setFixedWidth(360)
        self.setMaximumHeight(480)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #c5d0e6;
                border-radius: 10px;
            }
            QTextBrowser {
                background-color: transparent;
                border: none;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                color: #2c3e50;
            }
            QPushButton#close_btn {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 13px;
                padding: 0px;
            }
            QPushButton#close_btn:hover {
                color: #183881;
            }
        """)

        # --- Layout -------------------------------------------------------
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        # Title row: label on the left, close button on the right
        title_row = QHBoxLayout()
        self._title_label = QLabel()
        self._title_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #183881;"
        )
        title_row.addWidget(self._title_label)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(self.close)
        title_row.addWidget(close_btn)
        outer.addLayout(title_row)

        # Thin separator line
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #e0e6f0;")
        outer.addWidget(sep)

        # Scrollable Markdown browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer.addWidget(self._browser)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_for(self, title: str, markdown_path: str, anchor: QWidget) -> None:
        """Load Markdown content and show the dialog next to *anchor*.

        Args:
            title (str): Section name displayed in the dialog header.
            markdown_path (str): Resource-relative path to the ``.md`` file,
                e.g. ``"help/ranking.md"``.
            anchor (QWidget): The button that triggered the dialog. Used to
                compute the dialog's screen position.
        """
        self._title_label.setText(title)
        self._load_markdown(markdown_path)
        self._reposition(anchor)
        self.show()
        self.raise_()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_markdown(self, markdown_path: str) -> None:
        """Read a Markdown file and render it inside the browser.

        Uses ``QTextBrowser.setMarkdown()`` which is available natively
        in Qt 6. Falls back to a plain error message if the file is missing.

        Args:
            markdown_path (str): Resource-relative path to the ``.md`` file.
        """
        full_path = resource_path(markdown_path)
        try:
            with open(full_path, encoding="utf-8") as f:
                md_text = f.read()
            self._browser.setMarkdown(md_text)
        except FileNotFoundError:
            self._browser.setHtml(
                f"<p style='color:#c0392b;'>"
                f"Help file not found:<br><code>{full_path}</code>"
                f"</p>"
            )

    def _reposition(self, anchor: QWidget) -> None:
        """Place the dialog to the right of *anchor*, keeping it on-screen.

        If there is not enough space to the right, the dialog flips to the
        left of the anchor. Vertical position is clamped to the screen.

        Args:
            anchor (QWidget): Reference widget for positioning.
        """
        global_pos: QPoint = anchor.mapToGlobal(anchor.rect().topRight())
        x = global_pos.x() + 6
        y = global_pos.y()

        screen = anchor.screen().availableGeometry()
        if x + self.width() > screen.right():
            x = global_pos.x() - self.width() - 6
        if y + self.height() > screen.bottom():
            y = screen.bottom() - self.height()

        self.move(x, y)


# =============================================================================
# Section Help Button
# =============================================================================

class SectionHelpButton(QToolButton):
    """Small info icon button that opens a Markdown help dialog for a section.

    Designed to be injected into the title area of a ``QGroupBox`` via the
    :meth:`for_group` factory method. Clicking the button opens a
    :class:`HelpDialog` positioned next to it.

    A single ``HelpDialog`` instance is shared across all buttons in the
    same top-level window, keeping memory usage minimal.

    Attributes:
        _title (str): Section title passed to the dialog header.
        _markdown_path (str): Resource path to the ``.md`` help file.
        _dialog (HelpDialog): Class-level shared dialog (lazy-created).

    Example:
        >>> group = QGroupBox("Ranking")
        >>> SectionHelpButton.for_group(group, "Ranking", "help/ranking.md")
    """

    # One shared dialog reused across all buttons in the same window
    _dialog: HelpDialog = None

    def __init__(
        self,
        title: str,
        markdown_path: str,
        parent: QWidget = None,
    ):
        """Initialise the help button.

        Args:
            title (str): Human-readable section name shown in the dialog.
            markdown_path (str): Resource-relative path to the Markdown file.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self._title = title
        self._markdown_path = markdown_path

        # self.setFixedSize(35, 35)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Help: {title}")
        self.setFocusPolicy(Qt.NoFocus)

        # Try the project's info icon; fall back to a unicode character
        try:
            self.setIcon(QIcon(resource_path("icons/info_icon.png")))
        except Exception:
            self.setText("ℹ")

        self.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                color: #7a90b8;
                font-size: 13px;
            }
            QToolButton:hover {
                color: #183881;
            }
        """)

        self.clicked.connect(self._on_clicked)

    # ------------------------------------------------------------------
    # Class-level factory helper
    # ------------------------------------------------------------------

    @classmethod
    def for_group(
            cls,
            group: QGroupBox,
            title: str,
            markdown_path: str,
    ) -> "SectionHelpButton":
        """Create a help button anchored inside a :class:`QGroupBox` title bar.

        Instantiates the button, attaches a resize listener to keep it
        positioned correctly, and returns it.

        Args:
            group (QGroupBox): The group box whose title bar hosts the button.
            title (str): Title displayed in the help pop-up.
            markdown_path (str): Path to the Markdown file for the help content.

        Returns:
            SectionHelpButton: The newly created and positioned button.
        """
        btn = cls(title, markdown_path, parent=group)

        def _place_button():
            """Reposition the button within the group box title bar.

            Computes the correct ``(x, y)`` coordinates based on the group box
            font metrics and title margin, then calls ``btn.move(x, y)``.
            """
            # font height gives us the text cap height; we center the button on it.
            font_height = group.fontMetrics().height()  # actual title text height
            margin_top = 25  # must match your stylesheet
            title_center_y = (margin_top - font_height) // 2  # vertical center of band

            # Center the button on that same line
            y = title_center_y + (font_height - btn.height()) // 2
            x = group.width() - btn.width() - 8

            btn.move(x, y)
            btn.raise_()

        _place_button()
        group.resizeEvent = lambda event, orig=group.resizeEvent: (
            orig(event), _place_button()
        )

        btn.show()
        return btn

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _on_clicked(self) -> None:
        """Open the shared help dialog positioned next to this button."""
        window = self.window()
        if (
            SectionHelpButton._dialog is None
            or SectionHelpButton._dialog.parent() is not window
        ):
            SectionHelpButton._dialog = HelpDialog(parent=window)

        SectionHelpButton._dialog.show_for(
            self._title, self._markdown_path, anchor=self
        )


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    """Standalone example showing SectionHelpButton attached to two group boxes.

    Run this file directly to preview the widget:
        python section_help_button.py

    Two groups are shown side by side:
    - "Ranking" uses an inline Markdown string written to a temp file.
    - "Orthogonality Score" demonstrates the missing-file fallback message.
    """

    import os
    import tempfile

    app = QApplication(sys.argv)

    # --- Write a temporary .md file so the example works without the full
    #     resource tree. In the real app these live in resources/help/.
    tmp_dir = tempfile.mkdtemp()
    ranking_md = os.path.join(tmp_dir, "ranking.md")
    with open(ranking_md, "w", encoding="utf-8") as f:
        f.write(
            "# Ranking\n\n"
            "Controls how 2D combinations are ordered in the result table.\n\n"
            "## Options\n\n"
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| **Suggested score** | Pre-computed score recommended by the tool. |\n"
            "| **Computed score** | Score from the *Orthogonality assessment* step. |\n\n"
            "## Tips\n\n"
            "- Switch modes at any time and re-run the ranking.\n"
            "- If no computed score is available, only **Suggested score** works.\n"
        )

    # Monkey-patch resource_path so the example resolves the temp .md file
    # without needing the full application resource bundle.
    import combo_selector.ui.widgets.section_help_button as _mod

    _original_resource_path = _mod.resource_path

    def _patched_resource_path(rel_path: str) -> str:
        """Return a patched resource path for demo mode.

        Looks for the resource basename in the temp directory first;
        falls back to the original :func:`resource_path` if not found.

        Args:
            rel_path (str): Relative resource path (e.g. ``"icons/help.svg"``).

        Returns:
            str: Absolute path to the resource file.
        """
        if os.path.exists(candidate):
            return candidate
        return _original_resource_path(rel_path)

    _mod.resource_path = _patched_resource_path

    # ------------------------------------------------------------------
    # Build the demo window
    # ------------------------------------------------------------------
    window = QWidget()
    window.setWindowTitle("SectionHelpButton — live example")
    window.setMinimumWidth(500)
    window.setStyleSheet("background-color: #e7e7e7;")

    root_layout = QVBoxLayout(window)
    root_layout.setContentsMargins(30, 30, 30, 30)
    root_layout.setSpacing(20)

    # --- Group 1: Ranking (has a real .md file) ---
    ranking_group = QGroupBox("Ranking")
    ranking_group.setStyleSheet("""
        QGroupBox {
            font-size: 14px;
            font-weight: bold;
            color: #154E9D;
            background-color: #e7e7e7;
            border: 1px solid #d0d4da;
            border-radius: 12px;
            margin-top: 25px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0px;
            margin-top: -8px;
        }
        QLabel { background: transparent; color: #2c3e50; font-weight: bold; }
    """)
    ranking_layout = QVBoxLayout()
    ranking_layout.setContentsMargins(10, 10, 10, 10)
    ranking_layout.addWidget(QLabel("Ranking based on:"))
    from PySide6.QtWidgets import QComboBox
    combo = QComboBox()
    combo.addItems(["Suggested score", "Computed score", "Practical 2D peak capacity"])
    ranking_layout.addWidget(combo)
    ranking_group.setLayout(ranking_layout)

    # Attach help button — click ℹ to open the dialog
    SectionHelpButton.for_group(
        ranking_group,
        title="Ranking",
        markdown_path="ranking.md",  # resolved via patched resource_path above
    )

    # --- Group 2: Orthogonality Score (missing .md → shows fallback message) ---
    score_group = QGroupBox("Orthogonality Score Calculation")
    score_group.setStyleSheet(ranking_group.styleSheet())
    score_layout = QVBoxLayout()
    score_layout.setContentsMargins(10, 10, 10, 10)
    score_layout.addWidget(QLabel("Practical 2D peak capacity Calculation:"))
    from PySide6.QtWidgets import QRadioButton
    score_layout.addWidget(QRadioButton("Use suggested score"))
    score_layout.addWidget(QRadioButton("Use computed score"))
    score_group.setLayout(score_layout)

    # Attach help button — click ℹ to see the missing-file fallback
    SectionHelpButton.for_group(
        score_group,
        title="Orthogonality Score Calculation",
        markdown_path="orthogonality_score.md",  # intentionally missing
    )

    root_layout.addWidget(ranking_group)
    root_layout.addWidget(score_group)
    root_layout.addStretch()

    hint = QLabel(
        "Click the <b>ℹ</b> icon in the top-right of each group to open its help dialog."
    )
    hint.setWordWrap(True)
    hint.setStyleSheet("color: #555; font-size: 12px;")
    root_layout.addWidget(hint)

    window.show()
    sys.exit(app.exec())