#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df.copy()

    def toDataFrame(self):
        return self._df.copy()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except IndexError:
                return None
        elif orientation == QtCore.Qt.Vertical:
            try:
                return str(self._df.index.tolist()[section])
            except IndexError:
                return None

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        dtype = self._df[col].dtype
        try:
            if dtype != object and value != "":
                value = dtype.type(value)
        except Exception:
            return False
        self._df.loc[row, col] = value
        self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(
            colname, ascending=(order == QtCore.Qt.AscendingOrder), inplace=True
        )
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.centralwidget = QtWidgets.QWidget(self)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.view = QtWidgets.QTableView(self.centralwidget)
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.label = QtWidgets.QLabel("Regex Filter", self.centralwidget)

        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.comboBox, 0, 2, 1, 1)
        self.gridLayout.addWidget(self.view, 1, 0, 1, 3)
        self.setCentralWidget(self.centralwidget)

        self.load_sites()
        self.comboBox.addItems([f"{col}" for col in self.model._df.columns])

        self.lineEdit.textChanged.connect(self.on_lineEdit_textChanged)
        self.comboBox.currentIndexChanged.connect(self.on_comboBox_currentIndexChanged)
        self.horizontalHeader = self.view.horizontalHeader()
        self.horizontalHeader.sectionClicked.connect(
            self.on_view_horizontalHeader_sectionClicked
        )

    def load_sites(self):
        df = pd.DataFrame(
            {
                "site_codes": ["01", "02", "03", "04"],
                "status": ["open", "open", "open", "closed"],
                "Location": ["east", "north", "south", "east"],
                "data_quality": ["poor", "moderate", "high", "high"],
            }
        )
        self.model = PandasModel(df)
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.view.setModel(self.proxy)
        self.view.resizeColumnsToContents()

    @QtCore.Slot(int)
    def on_view_horizontalHeader_sectionClicked(self, logicalIndex):
        self.logicalIndex = logicalIndex
        self.menuValues = QtWidgets.QMenu(self)

        self.comboBox.blockSignals(True)
        self.comboBox.setCurrentIndex(self.logicalIndex)
        self.comboBox.blockSignals(False)

        valuesUnique = sorted(self.model._df.iloc[:, self.logicalIndex].unique())

        actionAll = QtWidgets.QAction("All", self)
        actionAll.triggered.connect(self.on_actionAll_triggered)
        self.menuValues.addAction(actionAll)
        self.menuValues.addSeparator()

        for value in valuesUnique:
            action = QtWidgets.QAction(str(value), self)
            action.triggered.connect(
                lambda checked=False, v=value: self.filter_by_value(v)
            )
            self.menuValues.addAction(action)

        headerPos = self.view.mapToGlobal(self.horizontalHeader.pos())
        posY = headerPos.y() + self.horizontalHeader.height()
        posX = headerPos.x() + self.horizontalHeader.sectionPosition(self.logicalIndex)
        self.menuValues.exec(QtCore.QPoint(posX, posY))

    @QtCore.Slot()
    def on_actionAll_triggered(self):
        self.proxy.setFilterRegularExpression(QtCore.QRegularExpression(""))
        self.proxy.setFilterKeyColumn(self.logicalIndex)

    def filter_by_value(self, value):
        regex = QtCore.QRegularExpression(str(value))
        self.proxy.setFilterRegularExpression(regex)
        self.proxy.setFilterKeyColumn(self.logicalIndex)

    @QtCore.Slot(str)
    def on_lineEdit_textChanged(self, text):
        regex = QtCore.QRegularExpression(
            text, QtCore.QRegularExpression.CaseInsensitiveOption
        )
        self.proxy.setFilterRegularExpression(regex)

    @QtCore.Slot(int)
    def on_comboBox_currentIndexChanged(self, index):
        self.proxy.setFilterKeyColumn(index)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main = MyWindow()
    main.resize(800, 600)
    main.show()
    sys.exit(app.exec())
