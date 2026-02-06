import math
from enum import Enum

import numpy as np
import pandas as pd
from PySide6.QtCore import (QAbstractTableModel, QItemSelectionModel,
                            QModelIndex, QRegularExpression,
                            QSortFilterProxyModel, Qt)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView,
                               QLabel, QSizePolicy, QStyledItemDelegate,
                               QTableView, QVBoxLayout, QWidget)


# class syntax
class COLUMN(Enum):
    SET = 0
    TITLE = 1
    TWODPEAK = 2
    CNVX_HULL = 3
    BIN_BOX = 4
    LINEARR = 5
    PEARSON = 6
    SPEARMAN = 7
    KENDALL = 8
    ASTERIK = 9
    NNDAMEAN = 10
    NNDGMEAN = 11
    NNDHMEAN = 12
    ORTHOFACTOR = 13
    ORTHOSCORE = 14
    PRACTTWODPEAK = 15

class OrthogonalityTableModel(QAbstractTableModel):

    def __init__(self, data=None):
        super().__init__()
        self._raw_data = None
        self._formatted_data = []  # cache for display
        self.default_row_count = 0
        self._data = data if data is not None else pd.DataFrame()
        self.header_label = []
        self.proxy_model = None
        self._row_count = 0
        self._column_count = 0

    def set_default_row_count(self, row_count):
        self._row_count = row_count
        self.modelReset.emit()

    def set_header_label(self, header_label):
        self.header_label = header_label
        self._column_count = len(self.header_label)
        self.modelReset.emit()

    def get_header_label(self):
        return self.header_label

    def set_proxy(self, proxy):
        self.proxy_model = proxy

    def set_formated_data(self,data):
        self._formatted_data = data
        self.modelReset.emit()

    def set_data(self, data):
        self.beginResetModel()
        data_cast = data.astype(object)
        data_list = data_cast.values.tolist()

        self._raw_data = data_list  # <-- keep raw values

        # Cache formatted values for display
        self._formatted_data = [
            [self._format_value(val, col_idx=j) for j, val in enumerate(row)]
            for row in data_list
        ]

        self._row_count = len(data_list)
        self._column_count = len(data_list[0]) if self._row_count > 0 else 0
        self.endResetModel()

    def _format_value(self, val, col_idx=None):
        # If this is the "Practical 2D peak capacity" column, format as integer
        if col_idx is not None and self.header_label and self.header_label[col_idx] == "Practical 2D peak capacity":
            try:
                return str(int(round(float(val))))
            except Exception:
                return str(val)
        if isinstance(val, (int, np.integer)):
            return str(val)
        elif isinstance(val, (float, np.floating)):
            return f"{val:.3f}"
        elif isinstance(val, (str, tuple)):
            return str(val)
        else:
            return str(val)

    def apply_formatted_data(self, formatted_data, row_count, col_count):
        self.beginResetModel()
        self._formatted_data = formatted_data
        self._row_count = row_count
        self._column_count = col_count
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not self._formatted_data:
            return None

        r, c = index.row(), index.column()

        if role == Qt.DisplayRole:
            return self._formatted_data[r][c]  # what you currently show

        if role == Qt.UserRole:
            return self._formatted_data[r][c]  # actual numeric/NaN/None

        elif role == Qt.BackgroundRole:  # <-- add this block
            val = str(self._formatted_data[r][c]).strip().lower()

            if val == 'nan':
                return QBrush(QColor('#ff9999'))  # red background
            return None

        return None


    def rowCount(self, parent=QModelIndex()):
        return self._row_count


    def columnCount(self, parent=QModelIndex()):
        return self._column_count


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and section < len(self.header_label):
            # print('self.header_label[section]')
            # print(self.header_label[section])
            # print('self.header_label')
            # print(self.header_label)
            # print('section')
            # print(section)
            return self.header_label[section]
        return None

class SquareBackgroundDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # 1) paint a plain rectangular background if the model provided one
        brush = index.data(Qt.BackgroundRole)
        if isinstance(brush, QColor):
            brush = QBrush(brush)
        if isinstance(brush, QBrush):
            painter.save()
            painter.fillRect(option.rect, brush)  # <- square, no rounded corners
            painter.restore()

        # 2) let Qt draw text, focus, etc.
        super().paint(painter, option, index)

class OrthogonalityTableView(QTableView):
    def __init__(self, parent=None, model=None, default_column_width=100):
        super().__init__(parent)
        # Allow the view to expand and fill its layout
        self._default_column_width = 100
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Internal widgets & state
        self._proxyModel = None
        self._mainWidget = None
        self._titleLabel = None
        self._actionLayout = None
        self._toolButtonMap = {}

        self.setModel(model)

        self.setShowGrid(True)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

        horizontalHeader = self.horizontalHeader()
        horizontalHeader.setFocusPolicy(Qt.NoFocus)
        horizontalHeader.setSectionsMovable(False)
        horizontalHeader.setSectionResizeMode(QHeaderView.Interactive)
        horizontalHeader.setCascadingSectionResizes(True)
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        horizontalHeader.setDefaultAlignment(Qt.AlignBottom)
        horizontalHeader.setSortIndicatorShown(True)
        horizontalHeader.setFixedHeight(30)
        horizontalHeader.setHighlightSections(False)


        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)

        self.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.setShowGrid(True)

        self.verticalHeader().hide()

        # Horizontal header config
        header = self.horizontalHeader()
        header.setFocusPolicy(Qt.NoFocus)
        header.setSectionsMovable(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)  # last column fills extra space
        header.setSortIndicatorShown(True)
        header.setDefaultAlignment(Qt.AlignBottom)
        header.setFixedHeight(30)

        # Vertical header config
        v_header = self.verticalHeader()
        v_header.setDefaultSectionSize(22)
        v_header.setMinimumSectionSize(18)
        v_header.hide()

        # Smooth scrolling
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Apply fixed width to all but last column

    def setModel(self, model):
        self._proxyModel = OrthogonalityTableSortProxy()
        self._proxyModel.setSortRole(Qt.UserRole)
        self._proxyModel.setDynamicSortFilter(True)
        self._proxyModel.setSourceModel(model)
        self._proxyModel.invalidate()
        self._proxyModel.setFilterKeyColumn(-1)

        super(OrthogonalityTableView, self).setModel(self._proxyModel)
        # super(TableView, self).setModel(model)

    def getSelectedIndexes(self):
        return [self._proxyModel.mapToSource(index) for index in self.selectedIndexes()]

    def selectedRows(self, column=0):
        return [self._proxyModel.mapToSource(index) for index in self.selectionModel().selectedRows(column)]

    def getSourceModel(self):
        return self._proxyModel.sourceModel()

    def setSearcher(self, filterLineEdit):
        return filterLineEdit.textChanged.connect(self.filterExpChanged)

    def filterExpChanged(self, text):
        self._proxyModel.setFilterRegularExpression(QRegularExpression(text))
        self._proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def getProxyModel(self):
        return self._proxyModel

    def getIndex(self, proxyIndex):
        return self._proxyModel.mapToSource(proxyIndex)

    def stopCellEditing(self):
        index = self.currentIndex()
        self.currentChanged(index, index)

    def setWidget(self):
        if self._mainWidget is not None:
            return

        self._mainWidget = QWidget(None)
        self._mainWidget.setObjectName("WhiteBackground")
        headerWidget = QWidget(self._mainWidget)
        headerWidget.setObjectName("WhiteBackground")
        self._titleLabel = QLabel(headerWidget)
        self._titleLabel.setObjectName("Bold_14")
        self._titleLabel.setScaledContents(True)

        self._actionLayout = QHBoxLayout(headerWidget)
        self._actionLayout.setContentsMargins(10, 0, 10, 0)
        self._actionLayout.addWidget(self._titleLabel)
        self._actionLayout.addStretch(100)
        self._actionLayout.setSpacing(10)
        headerWidget.setLayout(self._actionLayout)

        mainLayout = QVBoxLayout(self._mainWidget)
        mainLayout.setContentsMargins(10, 0, 10, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(headerWidget)
        mainLayout.addWidget(self)
        self.setParent(self._mainWidget)
        self._mainWidget.setLayout(mainLayout)
        headerWidget.setFixedHeight(30)

    def getWidget(self, parentWidget):
        self.setWidget()
        self._mainWidget.setParent(parentWidget)
        return self._mainWidget

    def setTitle(self, title):
        self.setWidget()
        self._titleLabel.setText(title)

    def addActions(self, actions):
        for action in actions:
            self.addAction(action)

    # def addAction(self, action):
    #     if action is not None:
    #         self.setWidget()
    #         toolButton = QToolButton(action)
    #         toolButton.setDefaultIconButton()
    #         self._actionLayout.addWidget(toolButton)
    #         self._toolButtonMap[action] = toolButton

    def removeAction(self, action):
        toolButton = self._toolButtonMap.get(action, None)
        if toolButton is not None:
            self._toolButtonMap.pop(action)
            self._actionLayout.removeWidget(toolButton)

    def selectNodes(self, nodes):
        for node in nodes:
            self.selectionModel().select(self.getSourceModel().getIndex(node), QItemSelectionModel.Select)

    def getSingleSelectedNode(self):
        indexes = self.getSelectedIndexes()
        if not indexes:
            return None

        firstIndex = indexes[0]
        for i in range(1, len(indexes)):
            if indexes[i].row() != firstIndex.row():
                return None
        return firstIndex.internalPointer()


class OrthogonalityTableSortProxy(QSortFilterProxyModel):
        def __init__(self):
            super(OrthogonalityTableSortProxy,self).__init__()

        def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
            # Get the data from the model as strings
            left_data = self.sourceModel().data(left, Qt.DisplayRole)
            right_data = self.sourceModel().data(right, Qt.DisplayRole)

            def norm(v):
                # None or NaN → +inf so they always go last
                if v is None:
                    return math.inf
                try:
                    f = float(v)
                    return f if not math.isnan(f) else math.inf
                except (ValueError, TypeError):
                    # not numeric, fallback to string comparison
                    return v

            return norm(left_data) < norm(right_data)

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if orientation == Qt.Vertical and role == Qt.DisplayRole:
                return str(section + 1)  # Fixed sequential order for vertical headers
            return super().headerData(section, orientation, role)

        def mapToSourceRow(self, proxy_row):
            return self.mapToSource(self.index(proxy_row, 0)).row()