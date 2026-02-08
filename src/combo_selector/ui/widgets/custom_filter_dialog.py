import re
import sys

from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLineEdit, QTreeView, QSpinBox,
                               QStyledItemDelegate, QLabel, QComboBox, QHeaderView,QVBoxLayout,
                               QWidget, QCheckBox, QAbstractItemView, QListView, QDialogButtonBox, )
from PySide6.QtGui import QStandardItem, QStandardItemModel

class CustomComboBox(QComboBox):
    def __init__(self, parent, items):
        super(CustomComboBox, self).__init__(parent)

        self.mode_list = items
        self.addItems(self.mode_list)

    def get_item_index(self, item):
        try:
            return self.mode_list.index(item)
        except:
            return 0


class CustomFilterDialog(QDialog):

    filter_regexp_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()

        # ------------------------------------------------------------
        # STYLE: FONT SIZE INCREASE (GLOBAL)
        # ------------------------------------------------------------
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QTreeView {
                font-size: 13px;
            }
            QListView, QCheckBox {
                font-size: 13px;
            }
            QLineEdit {
                font-size: 13px;
            }
            QPushButton {
                font-size: 13px;
                padding: 4px 10px;
            }
        """)

        self._apply_styles()


        # ------------------------------------------------------------
        # TOP TITLE LABEL (BOLD)
        # ------------------------------------------------------------
        title_top = QLabel("<b>Define chromatographic mode combinations</b>")
        main_layout.addWidget(title_top)

        # ------------------------------------------------------------
        # TREE VIEW
        # ------------------------------------------------------------
        self.data = {
            'Chromatographic mode': {
                '0': ['HILIC', 'HILIC'],
                '1': ['RPLC', 'RPLC'],
                '2': ['HILIC', 'RPLC'],
            }
        }

        self.filter_condition_tree_view = QTreeView()
        self.filter_condition_tree_view.setFixedWidth(310)
        self.filter_condition_tree_view.setMinimumHeight(220)

        self.delegate = CustomDelegate()
        self.filter_condition_tree_view.setItemDelegate(self.delegate)

        self.model = QStandardItemModel(0, 3)
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(['Condition', 'Qty', 'D1', '²D'])
        self.filter_condition_tree_view.setModel(self.model)

        self.build_tree_view_from_data()

        self.filter_condition_tree_view.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.filter_condition_tree_view.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.filter_condition_tree_view.header().setSectionResizeMode(3, QHeaderView.Stretch)
        self.filter_condition_tree_view.header().setStretchLastSection(False)

        main_layout.addWidget(self.filter_condition_tree_view)

        # ------------------------------------------------------------
        # BOTTOM SECTION TITLE LABEL (BOLD)
        # ------------------------------------------------------------
        filter_title = QLabel("<b>Select Combinations to filter</b>")
        main_layout.addWidget(filter_title)

        # ------------------------------------------------------------
        # FILTERED LISTVIEW
        # ------------------------------------------------------------
        self.filtered_listview = FilteredListView()
        self.update_combination_group()
        main_layout.addWidget(self.filtered_listview)

        # ------------------------------------------------------------
        # OK / CANCEL BUTTONS
        # ------------------------------------------------------------
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            orientation=Qt.Horizontal,
            parent=self
        )
        button_box.accepted.connect(self.selected_filter_changed)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.delegate.condition_changed.connect(self.update_condition_child_item)
        self.delegate.combination_changed.connect(self.update_combination_group)
        # self.filtered_listview.filterChanged.connect(self.selected_filter_changed)

    def _apply_styles(self):
        self.setStyleSheet("""
                QWidget {
                    font-family: Segoe UI, Arial;
                    font-size: 13px;
                }



                QLabel#TitleBar {
                    background-color: #183881;
                    color: #ffffff;
                    font-weight:bold;
                    font-size: 16px;
                                            border-top-left-radius: 10px;
                            border-top-right-radius: 10px;

                }

        QHeaderView::section {
            background-color: #d1d9fc;
            color: #1859b4;
            font-size: 12px;
            padding: 4px;
            font-weight: bold;
            border: 1px solid #d0d4da;
        }

        QTreeView {

            background-color: #F6F8FD;
            gridline-color: #D4D6EC;
            selection-background-color: #c9daf8;
            selection-color: #000000;
            font-size: 11px;
        }


        QTreeView::item:selected {
            background-color: #d8e5fc;
            color: #000000;
        }

    QTreeView::item {
        background: transparent;   /* so BackgroundRole shows */
        border: none;
        border-radius: 0px;        /* <-- force square corners */
    }

        QScrollBar:vertical {
            border: none;
            background: #bdcaf6;
            width: 10px;
            margin: 4px 0 4px 0;
        }

        QScrollBar::handle:vertical {
            background: white;
            min-height: 20px;
            border-radius: 5px;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: none;
        }

        QComboBox {
            background-color: #ffffff;
            border: 1px solid #c5d0e6;
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 14px;
        }

                QFrame#Footer {
                    background-color: #f1f3f6;
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                }

                QComboBox {
                    background-color: white;
                    border: 1px solid #ccc;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
            """)

    def selected_filter_changed(self):
        selected_filter = self.filtered_listview.get_selected_filters()


        parts = []
        for s in selected_filter:
            # extract word-like tokens, include hyphen if you want
            toks = re.findall(r'\b[A-Za-z0-9-]+\b', s)
            # ignore any 'vs' tokens in the list
            toks = [t for t in toks if t.lower() != 'vs']
            if len(toks) >= 2:
                a, b = re.escape(toks[0]), re.escape(toks[-1])
                parts.append(rf'\b{a}\b.*?vs.*?\b{b}\b')  # require literal "vs" between them
                parts.append(rf'\b{b}\b.*?vs.*?\b{a}\b')  # require literal "vs" between them


        filter_regexp = re.compile('|'.join(parts), flags=re.IGNORECASE)

        self.filter_regexp_changed.emit(filter_regexp.pattern)

        self.accept()



    def insert_parent_item(self,text):
        root_item = QStandardItem(text)
        self.model.appendRow(root_item)

    def insert_child_items(self, parent_row, child_items=None):

        # Get the item at row 2 (index 1)
        parent_item = self.model.item(parent_row)

        row_count = parent_item.rowCount()
        if child_items:
            column = 2
            while column <= 3:
                for child_text in child_items:
                    item = QStandardItem(child_text)
                    parent_item.setChild(row_count, column, item)
                    column += 1
        else:
            item1 = QStandardItem('...')
            item2 = QStandardItem('...')
            parent_item.setChild(row_count, 2, item1)
            parent_item.setChild(row_count, 3, item2)

        self.filter_condition_tree_view.setExpanded(self.model.indexFromItem(parent_item), True)

    def set_data(self, row, column, text):
        # Use the setData method to set data for an item
        index = self.model.index(row, column, QModelIndex())  # Replace with the appropriate row and column
        self.model.setData(index, text, Qt.EditRole)

    def remove_parent_item(self, row=None):

        if row:
            self.model.removeRow(row)
        else:
            last_item_index = self.model.rowCount() - 1
            self.model.removeRow(last_item_index)

    def resize_column_to_content(self):

        for i in range(self.model.columnCount()):
            self.filter_condition_tree_view.resizeColumnToContents(i)

    def build_tree_view_from_data(self):
        for row, key in enumerate(self.data):
            condition = self.data[key]
            self.insert_parent_item(text=key)
            self.set_data(row, 1, len(condition))
            for key in condition:
                index_row = condition[key]
                self.insert_child_items(parent_row=row,child_items=index_row)

        self.filter_condition_tree_view.resizeColumnToContents(0)
        self.filter_condition_tree_view.resizeColumnToContents(1)
        # self.resize_column_to_content()

    def update_condition(self):
        value = self.number_of_condition.value()

        if value > self.previous_nb_of_condition:
            for i in range(value-self.previous_nb_of_condition):
                text = f'New condition {self.model.rowCount()+1}'
                self.insert_parent_item(text=text)

        elif self.previous_nb_of_condition > value:
            # Remove the last child item from the parent_item
            for i in range(self.previous_nb_of_condition - value):
                self.remove_parent_item()

        self.previous_nb_of_condition = value

    def update_condition_child_item(self, row, previous_value, value):
        # Get the item at row 2 (index 1)
        parent_item = self.model.item(row)

        if value > previous_value:
            for i in range(value-previous_value):
                self.insert_child_items(parent_row=row)

        elif previous_value > value:
            # Remove the last child item from the parent_item
            for i in range(previous_value - value):
                last_child_index = parent_item.rowCount() - 1
                parent_item.removeRow(last_child_index)
        else:
            pass


        # for row in range(number):
        #     item1 = QStandardItem(f'Type 1')
        #     item2 = QStandardItem(f'Type 2')
        #     model.setItem(row+1, 2, item1)
        #     model.setItem(row+1, 3, item2)

    def update_combination_group(self):
        combination_group = []
        combination_count = self.model.item(0).rowCount()

        text_1 = text_2 = ''

        for row in range(combination_count):
            text_1 = self.model.item(0).child(row,2).text()
            text_2 = self.model.item(0).child(row,3).text()

            combination_group.append(text_1 +" vs " +text_2)

        self.filtered_listview.populate(combination_group)

        # self.selected_filter_changed(selected_filter=self.filtered_listview.get_selected_filters())     # self.filterChanged.emit(combination_group)
        # self.selected_filter_changed()     # self.filterChanged.emit(combination_group)


class CustomDelegate(QStyledItemDelegate):
    condition_changed = Signal(object,object, object)
    combination_changed = Signal()


    def __init__(self):
        QStyledItemDelegate.__init__(self)
        self.previous_qty_value = 0

    def createEditor(self, parent, option, index):
        editor = None
        value = index.model().data(index, Qt.EditRole)
        isParent = index.parent().row() == -1
        isCondition = index.column() in [0]
        isD1D2 = index.column() in [2,3] and not isParent
        if index.column() == 1 and isParent:
            # check if there is a value for the item
            if index.model().data(index, Qt.EditRole) is not None:
                self.previous_qty_value = index.model().data(index, Qt.EditRole)
            editor = QSpinBox(parent)
        elif (isCondition and isParent) or isD1D2:
            if index.parent().row() == 0:
                combo = CustomComboBox(parent, ['RPLC', 'HILIC', 'IEX', 'SEC', 'HIC', 'SFC'])
                combo.setCurrentIndex(combo.get_item_index(value))
                editor = combo
            elif index.parent().row() == 1:
                combo = CustomComboBox(parent, ['ACN', 'MeOH', 'EtOH', 'IpOH'])
                combo.setCurrentIndex(combo.get_item_index(value))
                editor = combo
            else:
                editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        isParent = index.parent().row() == -1
        isCondition = index.column() in [0]
        isD1D2 = index.column() in [2, 3] and not isParent
        if value:
            if index.column() == 1 and isParent:
                editor.setValue(value)
            elif (isCondition and isParent) or isD1D2:
                if index.parent().row() in [0, 1]:
                    editor.setEditText(value)
                else:
                    editor.setText(value)

    def setModelData(self, editor, model, index):
        isParent = index.parent().row() == -1
        isCondition = index.column() in [0]
        isD1D2 = index.column() in [2, 3] and not isParent

        if index.column() == 1 and isParent:
            model.setData(index, editor.value())
            self.condition_changed.emit(index.row(), int(self.previous_qty_value), editor.value())
        elif (isCondition and isParent) or isD1D2:
            if index.parent().row() in [0, 1]:
                model.setData(index, editor.currentText())
                self.combination_changed.emit()
            else:
                model.setData(index, editor.text())

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

# -------------------------------------------------------
# Checkable list view widget used in filter menu
# -------------------------------------------------------
class MultiListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            selected = self.selectedIndexes()
            for idx in selected[:-1]:
                idx = self.model().mapToSource(idx)
                item = self.model().sourceModel().itemFromIndex(idx)
                newState = (
                    Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                )
                item.setCheckState(newState)
        return super().keyPressEvent(event)

# -------------------------------------------------------
# Filter widget (checkbox list + regex lineedit)
# -------------------------------------------------------
class FilteredListView(QWidget):
    filterChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        filterLayout = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter...")
        self.regexCheckbox = QCheckBox(".*")
        self.listView = MultiListView()
        filterLayout.addWidget(self.filter)
        filterLayout.addWidget(self.regexCheckbox)
        layout.addLayout(filterLayout)
        layout.addWidget(self.listView)

        self.filters = []
        self.__data = []

        class InnerProxyModel(QSortFilterProxyModel):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.__filterStr = ""
                self.__regexMode = False

            def filterAcceptsRow(self, sourceRow, sourceParent):
                if not self.__filterStr:
                    return True
                index = self.sourceModel().index(sourceRow, 0, sourceParent)
                modelStr = self.sourceModel().data(index, Qt.DisplayRole)
                if not self.__regexMode:
                    regex = QtCore.QRegularExpression(
                        f".*{QtCore.QRegularExpression.escape(self.__filterStr)}.*",
                        QtCore.QRegularExpression.CaseInsensitiveOption,
                    )
                    return regex.match(modelStr).hasMatch()
                else:
                    regex = QtCore.QRegularExpression(
                        self.__filterStr,
                        QtCore.QRegularExpression.CaseInsensitiveOption,
                    )
                    return regex.match(modelStr).hasMatch()

            def setRegexMode(self, mode):
                self.__regexMode = bool(mode)

            def updateFilterStr(self, string):
                self.__filterStr = string
                self.invalidateFilter()

        self.model = QStandardItemModel(self)
        self.proxy = InnerProxyModel()
        self.proxy.setSourceModel(self.model)
        self.listView.setModel(self.proxy)

        self.filter.textChanged.connect(self.proxy.updateFilterStr)
        self.regexCheckbox.toggled.connect(self.proxy.setRegexMode)
        self.model.dataChanged.connect(self.update_selected_filter_list)

    def populate(self, data):
        self.model.clear()
        self.__data = data
        for d in self.__data:
            item = QStandardItem(d)
            item.setCheckable(True)
            self.model.appendRow(item)

        self.update_selected_filter_list()

    def get_selected_filters(self):
        return self.filters

    def update_selected_filter_list(self):

        self.filters = []

        for row in range(self.model.rowCount()):
            idx = self.model.index(row, 0)
            text = self.model.data(idx, Qt.DisplayRole)
            checked = self.model.data(idx, Qt.CheckStateRole)

            if checked:
                self.filters.append(text)


        self.filterChanged.emit(self.filters)

    def restoreFilters(self, filters):
        for r in range(self.model.rowCount()):
            item = self.model.item(r)
            if item.text() in filters:
                item.setCheckState(Qt.Checked)

    def clearFilters(self):
        for r in range(self.model.rowCount()):
            self.model.item(r).setCheckState(Qt.Unchecked)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CustomFilterDialog()
    # w.setFixedSize(1280, 720)
    w.show()
    app.exec()


class CustomFilterModel(QStandardItemModel):
    def __init__(self):
        super(CustomFilterModel, self).__init__()

        self.model = QStandardItemModel(0, 3)
        self.setRowCount(0)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Condition", "Qty", "D1", "²D"])

        self.data = {
            "Chromatographic mode": {
                "0": ["HILIC", "HILIC"],
                "1": ["RPLC", "RPLC"],
                "2": ["HILIC", "RPLC"],
            },
            "Organic modifier": {"0": ["MeOH", "ACN"]},
            "pH": {"0": ["pH3", "pH5.5"], "1": ["pH3", "pH8"], "2": ["pH5.5", "pH8"]},
        }

    def insert_parent_item(self, text):
        self.data[text] = {}
        root_item = QStandardItem(text)
        self.appendRow(root_item)

    def build_tree_view_from_data(self):
        for row, key in enumerate(self.data):
            condition = self.data[key]
            self.insert_parent_item(text=key)
            self.set_data(row, 1, len(condition))
            for key in condition:
                index_row = condition[key]
                self.insert_child_items(parent_row=row, child_items=index_row)
