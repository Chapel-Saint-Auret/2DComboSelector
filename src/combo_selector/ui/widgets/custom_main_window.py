import sys, os
from PySide6 import QtCore, QtGui
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import (
    QSizeGrip, QGraphicsDropShadowEffect, QVBoxLayout, QFrame, QWidget,
    QHBoxLayout, QLabel, QPushButton, QMenu, QMainWindow, QGraphicsEffect, QMenuBar
)

from combo_selector.utils import resource_path
from combo_selector.ui.widgets.sidebar import SideBar



MainWindowStyleSheet = """

QPushButton#btn_close {
    border: none;
    background: transparent;
    border-radius: 4px;
}
QPushButton#btn_close:hover {
    background-color: rgba(255, 0, 0, 100);  /* semi-transparent red */
}

QPushButton#btn_maximize
{
    border: none;
    background: transparent;
    border-radius: 4px;
}

QPushButton#btn_maximize:hover
{
    background-color: rgba(85, 255, 127, 100);
}


QPushButton#btn_minimize
{
    border: none;
    background: transparent;
    border-radius: 4px;
}

QPushButton#btn_minimize:hover
{
    background-color: rgba(255, 170, 0, 100);
}

QPushButton#btn_close
{
    border:none;
}

QPushButton#btn_close:hover
{
    border:none;
}

QFrame#central_widget_frame
{
    background-color:#F3F3FD;
    border-radius:10px;

}



#closeButton {
    min-width: 36px;
    min-height: 36px;
    font-family: "Webdings";
    qproperty-text: "r";
    border-radius: 10px;
}

#closeButton:hover {
    color: #ccc;
    background: red;
}

QHeaderView::section {                                                   
    padding: 0px;                               
    height:20px;                                
    border: 0.5px solid #aeadac;                         
    background: #dddddd;                  
}


QTreeWidget#analysis_file_tree {
    border-radius: 10px;
    border : 1px solid grey;
    background-color: white;
}


QFrame#side_menu_frame { 

    background: #325372;
    border-radius : 10px;
}


QTableView#sidemenu {
    color:white;
    background-color: #325372;
}

QTableView#sidemenu::item:selected {
    background-color: #f2f5fc;
    border-radius : 10px;
}

QTableView#sidemenu::item:selected:!active {
    background: #f2f5fc;
    border-radius : 10px;
}

QTableView#sidemenu::item:hover {
    background: #132c4e;
    border-radius : 10px;
}    


QWidget#container[isFlat = true]
{ 
    background-color: lightgray;
}

QPushButton {
    padding: 5px;
    background-color: #dddddd;
    border: 0.5px solid #aeadac;
    border-radius: 3px;
}


QPushButton:pressed:active {
    background-color: #5188d8;
    border: 1px solid #7e7eff;
    border-radius: 3px;
}

QPushButton:focus {
    border: 1px solid #234471;
}

QPushButton:hover{
    background-color: #d6e5fb;
    border: 1px solid #234471;
}

QPushButton#make_cut{ 
    border-radius :125;
    font-size: 20px;
}   
"""

class CustomMainWindow(QMainWindow):

    menu_clicked = Signal(int)

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.setMinimumSize(QSize(1200, 750))
        self.globale_state = 0
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu)

        # Style Application
        self.setStyleSheet(MainWindowStyleSheet)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 100))

        # Central Widget
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.central_widget_layout = QVBoxLayout(self.central_widget)

        # Main Frame
        self.central_widget_frame = QFrame(self.central_widget)
        self.central_widget_frame.setObjectName("central_widget_frame")
        self.central_widget_frame.setFrameShape(QFrame.NoFrame)
        self.central_widget_frame.setGraphicsEffect(self.shadow)
        self.central_widget_layout.addWidget(self.central_widget_frame)
        self.central_widget_layout.setContentsMargins(0,0,0,0)

        self.main_layout = QVBoxLayout(self.central_widget_frame)
        self.main_layout.setContentsMargins(5, 0, 5, 5)


        # Title Bar
        self.title_bar_frame = QFrame()
        # self.title_bar_frame.setStyleSheet("background-color: red;")
        self.title_bar_frame.setObjectName("title_bar_frame")
        self.title_bar_frame.setFixedHeight(40)
        self.title_bar_layout = QHBoxLayout(self.title_bar_frame)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)



        self.title_frame = QFrame(self.title_bar_frame)
        self.title_frame.setObjectName("title_frame")
        self.title_label = QLabel(self.title_frame)
        self.title_label.setObjectName("label_title")
        self.title_label.setFont(QFont("Roboto", 14))
        self.title_label.setStyleSheet("color: #154E9D;")
        self.title_frame.setLayout(QHBoxLayout())
        self.title_frame.layout().addWidget(self.title_label)
        self.title_bar_layout.addWidget(self.title_frame)

        self.menu_frame = QFrame()
        self.menu_frame_layout = QHBoxLayout(self.menu_frame)
        self.menu_frame_layout.setContentsMargins(0,0,0,0)
        self.menu_frame_layout.setSpacing(0)
        # self.menu_frame.setStyleSheet("background-color: red;")
        # self.menu_frame.setFixedHeight(30)
        self.menu_bar = QMenuBar()

        # self.menu_frame_layout.addWidget(self.menu_bar)

        # Create styled status bar
        self.status_bar_frame = QFrame()
        self.status_bar_frame.setObjectName("status_bar_frame")
        self.status_bar_frame.setFixedHeight(22)
        self.status_bar_frame.setStyleSheet("""
            QFrame#status_bar_frame {
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)

        self.status_bar_layout = QHBoxLayout(self.status_bar_frame)
        self.status_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.status_bar_layout.setSpacing(0)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.status_label.setStyleSheet("color: #5c5c5c;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.status_bar_layout.addStretch()
        self.status_bar_layout.addWidget(self.status_label)


        self.main_layout.addWidget(self.title_bar_frame, alignment=Qt.AlignTop)


        # self.main_layout.addWidget(self.menu_frame, alignment=Qt.AlignTop)


        # Sidebar Menu
        self.side_bar_menu = SideBar(title="2D Combo Selector")
        self.main_layout.addWidget(self.side_bar_menu)
        self.main_layout.addWidget(self.status_bar_frame)
        # self.main_layout.addWidget(self.status_bar_frame)

        # Window Controls
        self.btns_frame = QFrame(self.title_bar_frame)
        self.btns_frame.setMaximumSize(QSize(100, 16777215))
        btn_layout = QHBoxLayout(self.btns_frame)
        self.btn_maximize = QPushButton()
        self.btn_maximize.setIcon(QIcon(resource_path('icons/maximize_window.svg')))
        self.btn_maximize.setObjectName("btn_maximize")
        self.btn_maximize.setFixedSize(16, 16)
        self.btn_minimize = QPushButton()
        self.btn_minimize.setIcon(QIcon(resource_path('icons/minimize_window.svg')))
        self.btn_minimize.setObjectName("btn_minimize")
        self.btn_minimize.setFixedSize(16, 16)

        self.btn_close = QPushButton()
        print(f"in Custom main windows, picture path is {resource_path('icons/close_window.svg')}")
        self.btn_close.setIcon(QIcon(resource_path('icons/close_window.svg')))
        self.btn_close.setFixedSize(16, 16)
        self.btn_close.setIconSize(self.btn_close.size())
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 100);  /* semi-transparent red */
            }
        """)


        # self.btn_close.setFixedSize(16, 16)
        btn_layout.addWidget(self.btn_minimize)
        btn_layout.addWidget(self.btn_maximize)
        btn_layout.addWidget(self.btn_close)
        self.title_bar_layout.addWidget(self.btns_frame)

        # Size Grip
        self.sizegrip = QSizeGrip(self.central_widget)
        self.sizegrip.setToolTip("Resize Window")

        # Signal Connections
        self.btn_maximize.clicked.connect(self.maximize_restore)
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)
        self.title_bar_frame.mouseMoveEvent = self.moveWindow

    def set_status_text(self, text):
        self.status_label.setText(text)
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def set_window_title(self,title):
        self.title_label.setText(title)
    # MOVE WINDOW
    def moveWindow(self,event):
        # RESTORE BEFORE MOVE
        if self.globale_state == 1:
            self.maximize_restore()

        # IF LEFT CLICK MOVE WINDOW
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def maximize_restore(self):

        # IF NOT MAXIMIZED
        if self.globale_state == 0:
            self.showMaximized()

            # SET GLOBAL TO 1
            self.globale_state = 1

            # IF MAXIMIZED REMOVE MARGINS AND BORDER RADIUS
            self.central_widget_layout.setContentsMargins(0, 0, 0, 0)
            # self.central_widget_frame.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(42, 44, 111, 255), stop:0.521368 rgba(28, 29, 73, 255)); border-radius: 0px;")
            self.btn_maximize.setToolTip("Restore")
        else:
            self.globale_state = 0
            self.showNormal()
            self.resize(self.width()+1, self.height()+1)
            self.central_widget_layout.setContentsMargins(10, 10, 10, 10)
            # self.central_widget_frame.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(42, 44, 111, 255), stop:0.521368 rgba(28, 29, 73, 255)); border-radius: 10px;")
            self.btn_maximize.setToolTip("Maximize")

    def right_menu(self, pos):
        self.menu = QMenu()

        # Add menu options
        import_option = self.menu.addAction('Import datas')
        exit_option = self.menu.addAction('Exit')

        # Menu option events
        exit_option.triggered.connect(lambda: exit())

        # Position
        self.menu.exec_(self.mapToGlobal(pos))
    #
    # def paintEvent(self, event):
    #     # get current window size
    #     s = self.size()
    #     qp = QPainter()
    #     qp.begin(self)
    #     qp.setRenderHint(QPainter.Antialiasing, True)
    #     qp.setPen(self.foregroundColor)
    #     qp.setBrush(self.backgroundColor)
    #     qp.drawRoundedRect(0, 0, s.width(), s.height(),
    #                        self.borderRadius, self.borderRadius)
    #     qp.end()
    def mousePressEvent(self, event):
        p = event.globalPosition()
        globalPos = p.toPoint()
        self.dragPos = globalPos


    # def mousePressEvent(self, event):
    #     if self.draggable and event.button() == Qt.LeftButton:
    #         self.__mousePressPos = event.globalPos()                # global
    #         self.__mouseMovePos = event.globalPos() - self.pos()    # local
    #     super(MainWindow, self).mousePressEvent(event)
    #
    # def mouseMoveEvent(self, event):
    #     if self.draggable and event.buttons() & Qt.LeftButton:
    #         globalPos = event.globalPos()
    #         moved = globalPos - self.__mousePressPos
    #         if moved.manhattanLength() > self.dragging_threshould:
    #             # move when user drag window more than dragging_threshould
    #             diff = globalPos - self.__mouseMovePos
    #             self.move(diff)
    #             self.__mouseMovePos = globalPos - self.pos()
    #     super(MainWindow, self).mouseMoveEvent(event)
    #
    # def mouseReleaseEvent(self, event):
    #     if self.__mousePressPos is not None:
    #         if event.button() == Qt.LeftButton:
    #             moved = event.globalPos() - self.__mousePressPos
    #             if moved.manhattanLength() > self.dragging_threshould:
    #                 # do not call click event or so on
    #                 event.ignore()
    #             self.__mousePressPos = None
    #     super(MainWindow, self).mouseReleaseEvent(event)

class OutsideNeumorphismEffect(QGraphicsEffect):
    _cornerShift = (
    Qt.TopLeftCorner, Qt.TopLeftCorner, Qt.BottomRightCorner, Qt.BottomLeftCorner)

    def __init__(self, distance= 4, lightColor= QColor("#FFFFFF"),
                 darkColor= QColor("#7d7d7d"), clipRadius= 4,
                 origin= Qt.TopLeftCorner):
        super().__init__()

        self._leftGradient = QtGui.QLinearGradient(1, 0, 0, 0)
        self._leftGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self._topGradient = QtGui.QLinearGradient(0, 1, 0, 0)
        self._topGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)

        self._rightGradient = QtGui.QLinearGradient(0, 0, 1, 0)
        self._rightGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self._bottomGradient = QtGui.QLinearGradient(0, 0, 0, 1)
        self._bottomGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)

        self._radial = QtGui.QRadialGradient(.5, .5, .5)
        self._radial.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self._conical = QtGui.QConicalGradient(.5, .5, 0)
        self._conical.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)

        self._origin = origin
        distance = max(0, distance)
        self._clipRadius = min(distance, max(0, clipRadius))
        self._setColors(lightColor, darkColor)
        self._setDistance(distance)

    def setColors(self, color1, color2):
        if isinstance(color1, QtCore.Qt.GlobalColor) and isinstance(color2, QtCore.Qt.GlobalColor):
            color1 = QtGui.QColor(color1)
            color2 = QtGui.QColor(color2)

            self._setColors(color1, color2)

            self._setDistance(self._distance)
            self.update()

    def _setColors(self, color1, color2):

        self._baseStart = color1
        self._baseStop = QtGui.QColor(color1)
        self._baseStop.setAlpha(0)
        self._shadowStart = color2
        self._shadowStop = QtGui.QColor(color2)
        self._shadowStop.setAlpha(0)

        self.lightSideStops = [(0, self._baseStart), (1, self._baseStop)]
        self.shadowSideStops = [(0, self._shadowStart), (1, self._shadowStop)]
        self.cornerStops = [(0, self._shadowStart), (.25, self._shadowStop),
                            (.75, self._shadowStop), (1, self._shadowStart)]

        self._setOrigin(self._origin)

    def distance(self):
        return self._distance

    def setDistance(self, distance):
        if distance == self._distance:
            return

        self._setDistance(distance)
        self.updateBoundingRect()

    def _getCornerPixmap(self, rect, grad1, grad2=None):
        pm = QtGui.QPixmap(self._distance + self._clipRadius, self._distance + self._clipRadius)
        pm.fill(QtCore.Qt.transparent)
        qp = QtGui.QPainter(pm)
        if self._clipRadius > 1:
            path = QtGui.QPainterPath()
            path.addRect(rect)
            size = self._clipRadius * 2 - 1
            mask = QtCore.QRectF(0, 0, size, size)
            mask.moveCenter(rect.center())
            path.addEllipse(mask)
            qp.setClipPath(path)
        qp.fillRect(rect, grad1)
        if grad2:
            qp.setCompositionMode(qp.CompositionMode_SourceAtop)
            qp.fillRect(rect, grad2)
        qp.end()
        return pm

    def _setDistance(self, distance):
        distance = max(1, distance)
        self._distance = distance
        if self._clipRadius > distance:
            self._clipRadius = distance
        distance += self._clipRadius
        r = QtCore.QRectF(0, 0, distance * 2, distance * 2)

        lightSideStops = self.lightSideStops[:]
        shadowSideStops = self.shadowSideStops[:]

        if self._clipRadius:
            gradStart = self._clipRadius / (self._distance + self._clipRadius)
            lightSideStops[0] = (gradStart, lightSideStops[0][1])
            shadowSideStops[0] = (gradStart, shadowSideStops[0][1])

        # create the 4 corners as if the light source was top-left
        self._radial.setStops(lightSideStops)
        topLeft = self._getCornerPixmap(r, self._radial)

        self._conical.setAngle(359.9)
        self._conical.setStops(self.cornerStops)
        topRight = self._getCornerPixmap(r.translated(-distance, 0), self._radial, self._conical)

        self._conical.setAngle(270)
        self._conical.setStops(self.cornerStops)
        bottomLeft = self._getCornerPixmap(r.translated(0, -distance), self._radial, self._conical)

        self._radial.setStops(shadowSideStops)
        bottomRight = self._getCornerPixmap(r.translated(-distance, -distance), self._radial)

        # rotate the images according to the actual light source
        images = topLeft, topRight, bottomRight, bottomLeft
        shift = self._cornerShift.index(self._origin)
        if shift:
            transform = QtGui.QTransform().rotate(shift * 90)
            for img in images:
                img.swap(img.transformed(transform, QtCore.Qt.SmoothTransformation))

        # and reorder them if required
        self.topLeft, self.topRight, self.bottomRight, self.bottomLeft = images[-shift:] + images[:-shift]

    def origin(self):
        return self._origin

    def setOrigin(self, origin):
        origin = QtCore.Qt.Corner(origin)
        if origin == self._origin:
            return
        self._setOrigin(origin)
        self._setDistance(self._distance)
        self.update()

    def _setOrigin(self, origin):
        self._origin = origin

        gradients = self._leftGradient, self._topGradient, self._rightGradient, self._bottomGradient
        stops = self.lightSideStops, self.lightSideStops, self.shadowSideStops, self.shadowSideStops

        # assign color stops to gradients based on the light source position
        shift = self._cornerShift.index(self._origin)
        for grad, stops in zip(gradients, stops[-shift:] + stops[:-shift]):
            grad.setStops(stops)

    def clipRadius(self):
        return self._clipRadius

    def setClipRadius(self, radius):
        if radius == self._clipRadius:
            return
        self._setClipRadius(radius)
        self.update()

    def _setClipRadius(self, radius):
        radius = min(self._distance, max(0, int(radius)))
        self._clipRadius = radius
        self._setDistance(self._distance)

    def boundingRectFor(self, rect):
        d = self._distance
        return rect.adjusted(-d, -d, d, d)

    def draw(self, qp):
        restoreTransform = qp.worldTransform()

        qp.setPen(QtCore.Qt.NoPen)
        x, y, width, height = self.sourceBoundingRect(QtCore.Qt.DeviceCoordinates).getRect()
        right = x + width
        bottom = y + height
        clip = self._clipRadius
        doubleClip = clip * 2

        if self._clipRadius:
            path = QtGui.QPainterPath()
            source = self.sourcePixmap(QtCore.Qt.DeviceCoordinates)
            sourceBoundingRect = self.sourceBoundingRect(QtCore.Qt.DeviceCoordinates)
            qp.save()
            qp.setTransform(QtGui.QTransform())
            path.addRoundedRect(sourceBoundingRect.x(), sourceBoundingRect.y(), sourceBoundingRect.width(),
                                sourceBoundingRect.height(), self._clipRadius, self._clipRadius)
            qp.setClipPath(path)
            qp.drawPixmap(sourceBoundingRect.x() - self._distance, sourceBoundingRect.y() - self._distance, source)
            qp.restore()
        else:
            path = QtGui.QPainterPath()
            source = self.sourcePixmap(QtCore.Qt.DeviceCoordinates)
            sourceBoundingRect = self.sourceBoundingRect(QtCore.Qt.DeviceCoordinates)
            qp.save()
            qp.setTransform(QtGui.QTransform())
            path.addRect(sourceBoundingRect.x(), sourceBoundingRect.y(), sourceBoundingRect.width(),
                         sourceBoundingRect.height())
            qp.setClipPath(path)
            qp.drawPixmap(sourceBoundingRect.x() - self._distance, sourceBoundingRect.y() - self._distance, source)
            qp.restore()

        qp.setWorldTransform(QtGui.QTransform())
        leftRect = QtCore.QRectF(x - self._distance, y + clip, self._distance, height - doubleClip)
        qp.setBrush(self._leftGradient)
        qp.drawRect(leftRect)

        topRect = QtCore.QRectF(x + clip, y - self._distance, width - doubleClip, self._distance)
        qp.setBrush(self._topGradient)
        qp.drawRect(topRect)

        rightRect = QtCore.QRectF(right, y + clip, self._distance, height - doubleClip)
        qp.setBrush(self._rightGradient)
        qp.drawRect(rightRect)

        bottomRect = QtCore.QRectF(x + clip, bottom, width - doubleClip, self._distance)
        qp.setBrush(self._bottomGradient)
        qp.drawRect(bottomRect)

        qp.drawPixmap(x - self._distance, y - self._distance, self.topLeft)
        qp.drawPixmap(right - clip, y - self._distance, self.topRight)
        qp.drawPixmap(right - clip, bottom - clip, self.bottomRight)
        qp.drawPixmap(x - self._distance, bottom - clip, self.bottomLeft)

        qp.setWorldTransform(restoreTransform)

