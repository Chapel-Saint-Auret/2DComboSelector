"""
info_popup.py
─────────────────────────────────────────────────────
Reusable InfoPopupDialog for 2DComboSelector (PySide6)
• Native OS window frame (title bar handled by the OS)
• White body with blue-grey section headers and bullet points
• Periwinkle / lavender-blue close button

Usage
-----
    from info_popup import InfoPopupDialog, HOW_IT_WORKS_TEXT

    dlg = InfoPopupDialog(
        title="How It Works",
        content=HOW_IT_WORKS_TEXT,
        parent=self
    )
    dlg.exec()
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QFrame,
)
from PySide6.QtCore import Qt


# ── Colour palette ────────────────────────────────────────────────────────────
C_TEXT           = "#1a2a4a"   # near-navy body text
C_BULLET         = "#3a6bc4"   # blue bullet arrows
C_SECTION_BG     = "#eef2fb"   # tinted section header background
C_SECTION_BORDER = "#3a6bc4"   # left border on section headers
C_SECTION_TEXT   = "#1e3a6e"   # navy section header text
C_BORDER         = "#d0d8ed"   # light separator lines

# Periwinkle / lavender-blue — sampled from your "Compute metrics" button
C_BTN_BG         = "#c5cce8"
C_BTN_HOVER      = "#aab3d8"
C_BTN_PRESSED    = "#9099c4"
C_BTN_TEXT       = "#2a3560"


STYLESHEET = f"""
QDialog {{
    background-color: #ffffff;
}}

QScrollArea {{
    background: white;
    border: none;
    border-top: 1px solid {C_BORDER};
}}

QScrollBar:vertical {{
    background: #f0f3fa;
    width: 7px;
    border-radius: 3px;
    margin: 2px 1px;
}}
QScrollBar::handle:vertical {{
    background: {C_BULLET};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{ height: 0; }}

QWidget#body_widget {{
    background: white;
}}

QLabel#content_label {{
    color: {C_TEXT};
    font-size: 13px;
    background: transparent;
}}

QFrame#footer_line {{
    background-color: {C_BORDER};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

QPushButton#close_btn {{
    background-color: {C_BTN_BG};
    color: {C_BTN_TEXT};
    border: none;
    border-radius: 6px;
    padding: 7px 52px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#close_btn:hover {{
    background-color: {C_BTN_HOVER};
}}
QPushButton#close_btn:pressed {{
    background-color: {C_BTN_PRESSED};
}}
"""


class InfoPopupDialog(QDialog):
    """
    Native-frame modal popup for displaying structured info cards.

    Parameters
    ----------
    title   : str        – window title (shown in the OS title bar)
    content : str        – body text:
                             • lines starting with "•" → blue bullet
                             • other non-empty lines   → bold section header
                             • empty lines             → spacer
    parent  : QWidget | None
    width   : int        – dialog width  in px (default 560)
    height  : int        – dialog height in px (default 500)
    """

    def __init__(
        self,
        title: str = "Information",
        content: str = "",
        parent=None,
        width: int = 560,
        height: int = 500,
    ):
        """Initialize the info pop-up dialog.

        Args:
            title (str): Window title. Defaults to ``"Information"``.
            content (str): Plain-text content rendered as styled HTML.
                Defaults to ``""``.
            parent (QWidget | None): Optional parent widget used for centering.
            width (int): Dialog width in pixels. Defaults to ``560``.
            height (int): Dialog height in pixels. Defaults to ``500``.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(width, height)
        self.setStyleSheet(STYLESHEET)
        self._build_ui(content)
        self._center_on_parent(parent)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self, content: str):
        """Build the dialog layout with a scrollable content area and close button.

        Args:
            content (str): Plain-text content to display as styled HTML.

        Side Effects:
            - Populates the dialog with scroll area, separator, and footer.
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body_widget = QWidget()
        body_widget.setObjectName("body_widget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(52, 20, 52, 12)
        body_layout.setSpacing(0)

        content_lbl = QLabel(self.make_html(content))
        content_lbl.setObjectName("content_label")
        content_lbl.setWordWrap(True)
        content_lbl.setTextFormat(Qt.RichText)
        content_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        body_layout.addWidget(content_lbl)
        body_layout.addStretch()

        scroll.setWidget(body_widget)
        root.addWidget(scroll, 1)

        # Separator
        line = QFrame()
        line.setObjectName("footer_line")
        root.addWidget(line)

        # Footer
        footer = QWidget()
        footer.setStyleSheet("background: white;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 10, 16, 12)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)

        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)
        footer_layout.addStretch()
        root.addWidget(footer)

    # ── HTML renderer ─────────────────────────────────────────────────────────

    @staticmethod
    def make_html(content: str) -> str:
        """
        Build a simple rich-text HTML string from plain text.
        Lines starting with '•' or '·' become bullet rows.
        Other non-empty lines become bold section headers.
        Empty lines add vertical spacing.
        """
        html = "<html><body>"
        for line in content.split("\n"):
            s = line.strip()
            if not s:
                html += "<p style='margin:0; padding:0; line-height:0.6;'>&nbsp;</p>"
            elif s.startswith("•") or s.startswith("·"):
                body = s[1:].strip()
                html += (
                    f"<p style='margin:4px 0; font-size:13px; color:{C_TEXT};'>"
                    f"<span style='color:{C_BULLET}; font-weight:bold;'>&#9658;</span>"
                    f"&nbsp;{body}</p>"
                )
            else:
                html += (
                    f"<p style='margin:10px 0 4px 0; font-size:13px; font-weight:bold;"
                    f" color:{C_SECTION_TEXT}; background-color:{C_SECTION_BG};"
                    f" border-left:3px solid {C_SECTION_BORDER};"
                    f" padding:6px 10px; border-radius:3px;'>{s}</p>"
                )
        html += "</body></html>"
        return html

    def _center_on_parent(self, parent):
        """Center this dialog over the parent widget.

        Args:
            parent (QWidget | None): Parent widget whose geometry is used for
                centering.  Does nothing if ``parent`` is ``None``.

        Side Effects:
            - Calls ``self.move()`` to reposition the dialog.
        """
        if parent:
            pg = parent.geometry()
            x = pg.x() + (pg.width()  - self.width())  // 2
            y = pg.y() + (pg.height() - self.height()) // 2
            self.move(x, y)


class AboutDialog(QDialog):
    """
    Dedicated About page for 2DComboSelector.
    Uses clickable hyperlinks (QLabel with OpenExternalLinks).

    Usage
    -----
        dlg = AboutDialog(parent=self)
        dlg.exec()

    Customise the URLS dict below to set real links.
    """

    # ── Fill in your real URLs here ───────────────────────────────────────────
    URLS = {
        "documentation": "https://2dcomboselector.readthedocs.io/en/latest/",          # e.g. "https://your-docs-site.com"
        "tutorial":      "#",          # e.g. YouTube link
        "publication":   "https://doi.org/10.1016/j.chroma.2025.465861",          # e.g. DOI URL
        "email":         "soraya.chapel@univ-rouen.fr",
        "github":        "https://github.com/Chapel-Saint-Auret/2DComboSelector",          # e.g. "https://github.com/yourrepo"
    }

    def __init__(self, parent=None, width: int = 580, height: int = 520):
        """Initialize the About dialog.

        Args:
            parent (QWidget | None): Optional parent widget.
            width (int): Dialog width in pixels. Defaults to ``580``.
            height (int): Dialog height in pixels. Defaults to ``520``.
        """
        super().__init__(parent)
        self.setWindowTitle("About 2DComboSelector")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(width, height)
        self.setStyleSheet(STYLESHEET + f"""
            QLabel#section_title {{
                color: {C_SECTION_TEXT};
                font-size: 13px;
                font-weight: 700;
                background-color: {C_SECTION_BG};
                border-left: 3px solid {C_SECTION_BORDER};
                padding: 6px 10px;
                border-radius: 3px;
            }}
            QLabel#body_text {{
                color: {C_TEXT};
                font-size: 13px;
                background: transparent;
            }}
            QLabel#link_label {{
                font-size: 13px;
                background: transparent;
            }}
        """)
        self._build_ui()

    def _section(self, text: str) -> QLabel:
        """Create a styled section-header label.

        Args:
            text (str): Header text to display.

        Returns:
            QLabel: Styled label with ``section_title`` object name.
        """
        lbl = QLabel(text)
        lbl.setObjectName("section_title")
        return lbl

    def _body(self, text: str) -> QLabel:
        """Create a styled body-text label with word-wrap.

        Args:
            text (str): Body text to display (may contain rich-text markup).

        Returns:
            QLabel: Styled label with ``body_text`` object name.
        """
        lbl = QLabel(text)
        lbl.setObjectName("body_text")
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        return lbl

    def _link_row(self, label: str, url: str, link_text: str) -> QWidget:
        """Create a horizontal row containing a label and a clickable hyperlink.

        Args:
            label (str): Descriptive prefix text (e.g. ``"Documentation:"``).
            url (str): URL the link points to.
            link_text (str): Visible anchor text for the hyperlink.

        Returns:
            QWidget: Container widget with the label and link side-by-side.
        """
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        prefix = QLabel(f"<span style='color:{C_TEXT}; font-size:13px;'>{label}</span>")
        prefix.setTextFormat(Qt.RichText)

        link = QLabel(f"<a href='{url}' style='color:{C_BULLET};'>{link_text}</a>")
        link.setObjectName("link_label")
        link.setTextFormat(Qt.RichText)
        link.setOpenExternalLinks(True)
        link.setCursor(Qt.PointingHandCursor)

        layout.addWidget(prefix)
        layout.addWidget(link)
        layout.addStretch()
        return row

    def _build_ui(self):
        """Build the About dialog layout with sections for info, links, and a close button.

        Side Effects:
            - Populates the dialog with scrollable about content and a footer.
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Scrollable body ───────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body_widget = QWidget()
        body_widget.setObjectName("body_widget")
        layout = QVBoxLayout(body_widget)
        layout.setContentsMargins(40, 20, 40, 16)
        layout.setSpacing(8)

        # ── App title ─────────────────────────────────────────────────────────
        title = QLabel("ABOUT 2DComboSelector")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {C_SECTION_TEXT};"
            "background: transparent;"
        )
        layout.addWidget(title)
        layout.addSpacing(4)

        # ── Description ───────────────────────────────────────────────────────
        layout.addWidget(self._body(
            "2DComboSelector is a Python-based tool designed to support the selection "
            "of suitable chromatographic condition pairs for 2D separations. It combines "
            "a structured workflow with a multi-metric orthogonality assessment to help "
            "users identify promising 2D combinations from 1D scouting data in a more "
            "systematic and time-efficient way."
        ))
        layout.addSpacing(6)

        # ── Resources ─────────────────────────────────────────────────────────
        layout.addWidget(self._section("Resources"))
        layout.addWidget(self._link_row("📄  Documentation:", self.URLS["documentation"], "2DComboSelector documentation"))
        layout.addWidget(self._link_row("🎬  Tutorial video:", self.URLS["tutorial"],      "Watch tutorial"))
        layout.addWidget(self._link_row("📖  Publication:",   self.URLS["publication"],    "https://doi.org/10.1016/j.chroma.2025.465861"))
        layout.addSpacing(2)
        layout.addWidget(self._body(
            "For details on experimental design (scouting runs, gradients, data preparation), "
            "please refer to the documentation and the associated article."
        ))
        layout.addSpacing(6)

        # ── Acknowledgements ──────────────────────────────────────────────────
        layout.addWidget(self._section("Acknowledgements"))
        layout.addWidget(self._body(
            "Developed by <b>Soraya Chapel</b> and <b>Jessy Saint-Auret</b>.<br><br>"
            "Part of this work was carried out during my time at KU Leuven. "
            "I gratefully acknowledge <b>Prof. Deirdre Cabooter</b> and "
            "<b>Dr. Marie Pardon</b> for the scientific environment and discussions "
            "that contributed to the development of this tool."
        ))
        layout.addSpacing(6)

        # ── Contact ───────────────────────────────────────────────────────────
        layout.addWidget(self._section("Contact"))
        layout.addWidget(self._link_row("✉️  Email:", self.URLS["email"],  "soraya.chapel@univ-rouen.fr"))
        layout.addWidget(self._link_row("💻  GitHub:", self.URLS["github"], "2DComboSelector"))

        layout.addStretch()
        scroll.setWidget(body_widget)
        root.addWidget(scroll, 1)

        # ── Separator + footer ────────────────────────────────────────────────
        line = QFrame()
        line.setObjectName("footer_line")
        root.addWidget(line)

        footer = QWidget()
        footer.setStyleSheet("background: white;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 10, 16, 12)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)

        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)
        footer_layout.addStretch()
        root.addWidget(footer)


# ── Pre-defined content strings ───────────────────────────────────────────────

HOW_IT_WORKS_TEXT = """\
This tool helps you evaluate and compare 2D separation space occupation in a streamlined, visual environment. Here are its main functions:

• Imports and normalizes your 1D retention data
• Automatically generates all possible 2D combinations from the dataset
• Provides visual comparisons of the candidate separations
• Evaluates orthogonality from pairs of retention data
• Uses a multi-metric approach (12 orthogonality metrics currently implemented)
• Calculates and integrates all metrics into a composite orthogonality score
• Provides a balanced assessment of 2D separation space occupation
• Ranks candidate conditions based on chromatographically relevant criteria, including orthogonality, hypothetical 2D peak capacity, and a Heinisch inspired method
• Applies filters based on practical constraints (solvent compatibility, set-up complexity, green aspects, MS compatibility)
• Assists in the final selection of optimal conditions for experimental validation\
"""

BEFORE_YOU_BEGIN_TEXT = """\
Before using the tool, preliminary experimental data must be collected. The tool is designed to evaluate and compare candidate 2D combinations based on 1D scouting results, and therefore requires retention data as input.

Required steps prior to using the tool:
· Select a set of representative compounds relevant to the target application
· Design and perform 1D scouting experiments under different chromatographic conditions (e.g., columns, mobile phase, pH, modifiers, modes)
· Extract retention data for each compound and condition (peak widths can also be included if available, but are optional)
· Calculate experimental peak capacities

Once these data are collected and organized, they can be imported into the tool for orthogonality assessment and condition ranking.

For more details on experimental design and gradient setup, please refer to the associated publication and to the documentation link in About section.\
"""

USER_GUIDE_TEXT = """\
Step-by-step workflow:
To use the tool, follow the steps below, which match the sections and subsections in the menu bar, one by one. For a practical example, you can also watch the tutorial video in the About section.

Step 1 — Data Import and Normalization
A — Data import
· Upload retention times and peak capacity data from 1D scouting runs
· Accepted formats: Excel / CSV
· Minimum requirement: retention data (other input optional)

B — Data normalization
· Scaling of retention times to harmonize the retention space
· Particularly important when different column geometries are used
· Three scaling methods are available (the default option can be used if unsure)
· Additional inputs are required when selecting the void time and wosel approaches (void time and gradient end time)

Step 2 — Visual Comparison of Paired Conditions
· Pairwise plots of conditions are available in the "Data Plotting Pairwise" section
· Enables a quick visual assessment of separation space usage between dimensions

Step 3 — Orthogonality Assessment
· Calculation of multiple orthogonality metrics
· Visualization of the results for each metric

Step 4 — Redundancy Check (Correlation Matrix)
· Identify metrics that provide overlapping information
· The cross-correlation matrix highlights relationships between metrics and groups strongly correlated ones in a summary table

Step 5 — Final Evaluation & Ranking
· Calculation of a composite orthogonality score by averaging values across metric groups
· Estimation of hypothetical practical 2D peak capacity using either the suggested score or a user-defined one
· Ranking based on orthogonality only, hypothetical practical 2D peak capacity, or a Heinisch-inspired method
· Identification of the most promising 2D combinations based on practical criteria\
"""


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QHBoxLayout, QWidget, QPushButton
    )

    app = QApplication(sys.argv)

    win = QMainWindow()
    win.setWindowTitle("2DComboSelector – popup demo")
    win.setFixedSize(900, 600)
    win.setStyleSheet("background-color: #f0f3fa;")

    central = QWidget()
    layout = QHBoxLayout(central)
    layout.setContentsMargins(80, 220, 80, 80)
    layout.setSpacing(24)

    btn_style = """
        QPushButton {
            background-color: #1e3a6e;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 20px 12px;
        }
        QPushButton:hover { background-color: #3a6bc4; }
    """

    cards = [
        ("HOW IT WORKS?",     HOW_IT_WORKS_TEXT),
        ("BEFORE YOU BEGIN?", BEFORE_YOU_BEGIN_TEXT),
        ("USER GUIDE",        USER_GUIDE_TEXT),
    ]

    for label, content in cards:
        btn = QPushButton(label)
        btn.setStyleSheet(btn_style)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(100)
        btn.clicked.connect(
            lambda checked, l=label, c=content:
                InfoPopupDialog(title=l, content=c, parent=win).exec()
        )
        layout.addWidget(btn)

    about_btn = QPushButton("ABOUT")
    about_btn.setStyleSheet(btn_style)
    about_btn.setCursor(Qt.PointingHandCursor)
    about_btn.setFixedHeight(100)
    about_btn.clicked.connect(lambda: AboutDialog(parent=win).exec())
    layout.addWidget(about_btn)

    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec())