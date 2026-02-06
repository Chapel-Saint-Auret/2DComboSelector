import sys

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from combo_selector.ui.widgets import line_widget
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.utils import resource_path

stylesheet = """
	#full_menu_widget {
		background-color: #12295F;
		border-top-left-radius :10px;
        border-top-right-radius : 0px; 
        border-bottom-left-radius : 10px; 
        border-bottom-right-radius : 0px;
	}

	/* style for QPushButton */
	#full_menu_widget QPushButton {
		border:none;
		font-size: 14px;
		border-radius: 3px;
		text-align: left;
		padding: 8px 0 8px 15px;
		color: #ffffff;
		background-color:#12295F ;
	}

	#full_menu_widget QPushButton:hover {
		    background-color: #3A4B6E;  /* Slightly lighter on hover */
    color: #FFFFFF;}
    
    	#full_menu_widget QPushButton:checked {
		    background-color: #3A4B6E;  /* Slightly lighter on hover */
    color: #FFFFFF;
	}


	/* style for logo image */
	#logo_label_2 {
		padding: 5px;
		color: #fff;
	}

	/* style for APP title */
	#logo_label_3 {
		padding-right: 10px;
		color: #fff;
	}
	
    #side_bar_title QLabel{
		padding-right: 10px;
		color: w;
	}
	
	
"""

class SideBar(QWidget):

    button_clicked = Signal(int)

    def __init__(self,title = 'Unnamed'):
        super().__init__()

        self.setStyleSheet(stylesheet)
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.full_menu_widget = QFrame(self)
        self.full_menu_widget.setFixedWidth(170)
        self.full_menu_widget.setObjectName('full_menu_widget')
        self.full_menu_layout = QVBoxLayout(self.full_menu_widget)

        side_bar_title_layout = QHBoxLayout(self.full_menu_widget)
        self.side_bar_logo = QLabel()
        self.side_bar_logo.setProperty("isBold", True)
        self.side_bar_logo.setText("X")
        self.side_bar_logo.setFixedSize(20,20)
        self.side_bar_logo.setScaledContents(True)

        self.side_bar_title = QLabel()
        self.side_bar_title.setProperty("isBold", True)
        self.side_bar_title.setText(title)
        self.side_bar_title.setObjectName('side_bar_title')
        font = QFont()
        font.setPointSize(15)
        self.side_bar_title.setFont(font)

        # side_bar_title_layout.addWidget(self.side_bar_logo)
        #side_bar_title_layout.addWidget(self.side_bar_title)

        self.side_bar_button_frame = QFrame()
        self.side_bar_button_frame.setObjectName('side_bar_button_frame')
        self.side_bar_buttons_layout = QVBoxLayout(self.side_bar_button_frame)

        logo = QPushButton()
        logo.setObjectName('logo_button')
        logo.setFixedHeight(50)
        logo.setIcon(QIcon(resource_path('icons/logo.png')))
        logo.setIconSize(QSize(120,48))
        self.side_bar_buttons_layout.addWidget(logo)
        self.side_bar_buttons_layout.addWidget(LineWidget())

        self.full_menu_layout.addLayout(side_bar_title_layout)
        #side_bar_title_layout.setAlignment(Qt.AlignTop)
        self.full_menu_layout.addWidget(self.side_bar_button_frame)
        self.full_menu_layout.addStretch()


        self.content_widget = QWidget(self)
        content_widget_layout = QVBoxLayout(self.content_widget)
        content_widget_layout.setContentsMargins(0,0,0,0)
        content_widget_layout.setSpacing(0)

        top_bar_widget = QWidget()
        top_bar_layout = QHBoxLayout(top_bar_widget)

        self.hide_side_bar_btn = QPushButton('X')

        top_bar_layout.addWidget(self.hide_side_bar_btn)
        top_bar_layout.addStretch()

        self.content_qstack = QStackedWidget()

        #content_widget_layout.addWidget(top_bar_widget)
        content_widget_layout.addWidget(self.content_qstack)


        #main_layout.addWidget(self.icon_only_widget, 0, 0, 1, 1)
        main_layout.addWidget(self.full_menu_widget, 0, 1, 1, 1)
        main_layout.addWidget(self.content_widget, 0, 2, 1, 1)

    def add_side_bar_button(self,name, widget):
        button = QPushButton(name)
        button.setFixedHeight(100)
        #button.setIcon(icon)
        button.setCheckable(True)
        button.setAutoExclusive(True)
        self.side_bar_buttons_layout.addWidget(button)

        self.content_qstack.addWidget(widget)

        widget.setUpdatesEnabled(False)
        button.clicked.connect(lambda x : self.content_qstack.setCurrentWidget(widget))
        # button.clicked.connect(lambda x : self.button_clicked.emit(self.content_qstack.currentIndex()))
        widget.setUpdatesEnabled(True)


        return button

if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = QDialog()

    w.resize(950, 600)

    layout_main = QVBoxLayout(w)
    #layout_main.setContentsMargins(5, 5, 5, 5)

    SideBar = SideBar(title="2D Combo Selector")
    SideBar.add_side_bar_button('INPUT DATA', QLabel('INPUT DATA'))
    SideBar.add_side_bar_button('DATA PLOTTING\nPAIRWISE', QLabel('DATA PLOTTING\nPAIRWISE'))
    SideBar.add_side_bar_button('CALCULATION', QLabel('CALCULATION'))
    SideBar.add_side_bar_button('RESULTS', QLabel('RESULTS'))
    SideBar.add_side_bar_button('EXPORT', QLabel('EXPORT'))
    layout_main.addWidget(SideBar, 1)

    w.show()
    app.exec()