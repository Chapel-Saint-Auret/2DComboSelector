from PySide6.QtGui import QStandardItem, QStandardItemModel


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
