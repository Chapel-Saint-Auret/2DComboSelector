#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pandas-backed table model and filterable table view for PySide6.

Provides :class:`PandasModel`, a :class:`QAbstractTableModel` that wraps a
:class:`pandas.DataFrame`, and :class:`MyWindow`, a demo main window that
combines the model with a :class:`QSortFilterProxyModel` for column-based
filtering.
"""

import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets


class PandasModel(QtCore.QAbstractTableModel):
    """Qt table model backed by a :class:`pandas.DataFrame`.

    Supports display, editing, and sorting via the standard Qt model/view
    architecture.

    Attributes:
        _df (pd.DataFrame): Internal copy of the data being displayed.
    """

    def __init__(self, df=pd.DataFrame(), parent=None):
        """Initialize the model with an optional DataFrame.

        Args:
            df (pd.DataFrame): Data to display. Defaults to an empty DataFrame.
            parent (QObject | None): Optional parent object.
        """
        super().__init__(parent)
        self._df = df.copy()

    def toDataFrame(self):
        """Return a copy of the underlying DataFrame.

        Returns:
            pd.DataFrame: Copy of the internal DataFrame.
        """
        return self._df.copy()
        """Return header label for the given section and orientation.

        Args:
            section (int): Row or column index.
            orientation (Qt.Orientation): Horizontal for column headers,
                vertical for row headers.
            role (Qt.ItemDataRole): Data role; only
                :attr:`Qt.DisplayRole` is handled.

        Returns:
            str | None: Header label, or ``None`` if not applicable.
        """
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
        """Return cell data for display.

        Args:
            index (QModelIndex): Cell index.
            role (Qt.ItemDataRole): Data role; only
                :attr:`Qt.DisplayRole` is handled.

        Returns:
            str | None: String representation of the cell value, or ``None``.
        """
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """Set cell data and emit :attr:`dataChanged`.

        Args:
            index (QModelIndex): Cell index to update.
            value: New value to assign; will be cast to the column dtype.
            role (Qt.ItemDataRole): Must be :attr:`Qt.EditRole` to apply.

        Returns:
            bool: ``True`` if the value was set successfully, ``False`` otherwise.
        """
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
        """Return the number of rows in the DataFrame.

        Args:
            parent (QModelIndex): Unused; present for API compatibility.

        Returns:
            int: Number of rows.
        """
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """Return the number of columns in the DataFrame.

        Args:
            parent (QModelIndex): Unused; present for API compatibility.

        Returns:
            int: Number of columns.
        """
        return len(self._df.columns)

    def sort(self, column, order):
        """Sort the DataFrame by the specified column.

        Args:
            column (int): Column index to sort by.
            order (Qt.SortOrder): :attr:`Qt.AscendingOrder` or
                :attr:`Qt.DescendingOrder`.

        Side Effects:
            - Emits ``layoutAboutToBeChanged`` and ``layoutChanged``.
            - Resets the DataFrame index in-place.
        """
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(
            colname, ascending=(order == QtCore.Qt.AscendingOrder), inplace=True
        )
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class MyWindow(QtWidgets.QMainWindow):
    """Demo main window showcasing :class:`PandasModel` with filtering.

    Combines a :class:`QSortFilterProxyModel`, a :class:`QTableView`, a
    :class:`QLineEdit` for regex filtering, and a :class:`QComboBox` for
    column selection.
    """

    def __init__(self, parent=None):
        """Initialize the demo window and populate the table.

        Args:
            parent (QWidget | None): Optional parent widget.
        """
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
        """Load sample site data into the model and attach it to the view.

        Side Effects:
            - Creates a demo :class:`PandasModel` with four sample rows.
            - Wraps it in a :class:`QSortFilterProxyModel`.
            - Attaches the proxy model to the table view.
        """
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
        """Show a context menu with unique column values for header-click filtering.

        Args:
            logicalIndex (int): Index of the clicked header section.

        Side Effects:
            - Updates ``comboBox`` selection to match the clicked column.
            - Displays a popup menu with "All" and unique value actions.
        """
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
        """Clear the proxy filter to show all rows.

        Side Effects:
            - Resets the proxy filter regular expression to an empty string.
        """
        self.proxy.setFilterRegularExpression(QtCore.QRegularExpression(""))
        self.proxy.setFilterKeyColumn(self.logicalIndex)

    def filter_by_value(self, value):
        """Filter the table to show only rows matching a specific value.

        Args:
            value: The exact value to match in the currently selected column.

        Side Effects:
            - Updates the proxy filter to ``str(value)``.
        """
        regex = QtCore.QRegularExpression(str(value))
        self.proxy.setFilterRegularExpression(regex)
        self.proxy.setFilterKeyColumn(self.logicalIndex)

    @QtCore.Slot(str)
    def on_lineEdit_textChanged(self, text):
        """Apply a case-insensitive regex filter as the user types.

        Args:
            text (str): Current text in the search line edit.

        Side Effects:
            - Updates the proxy filter regular expression.
        """
        regex = QtCore.QRegularExpression(
            text, QtCore.QRegularExpression.CaseInsensitiveOption
        )
        self.proxy.setFilterRegularExpression(regex)

    @QtCore.Slot(int)
    def on_comboBox_currentIndexChanged(self, index):
        """Change the column used for filtering when the combo box changes.

        Args:
            index (int): New column index selected in the combo box.

        Side Effects:
            - Updates the proxy filter key column.
        """
        self.proxy.setFilterKeyColumn(index)
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main = MyWindow()
    main.resize(800, 600)
    main.show()
    sys.exit(app.exec())
