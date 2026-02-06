import os
import sys

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QItemSelectionModel, QModelIndex, QSize, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
                               QGraphicsDropShadowEffect, QGroupBox,
                               QHBoxLayout, QHeaderView, QLabel, QScrollArea,
                               QSizePolicy, QSplitter, QVBoxLayout)

from combo_selector.ui.widgets.custom_toolbar import CustomToolbar
from combo_selector.ui.widgets.line_widget import LineWidget
from combo_selector.ui.widgets.neumorphism import *
from combo_selector.ui.widgets.orthogonality_table import \
    OrthogonalityTableView
from combo_selector.ui.widgets.style_table import StyledTable
from combo_selector.utils import resource_path

PLOT_SIZE = QSize(600, 400)

drop_down_icon_path = resource_path('icons/drop_down_arrow.png').replace("\\", "/")
print("LOOKING FOR ICON:", drop_down_icon_path, "EXISTS:", os.path.exists(drop_down_icon_path))

class PlotPairWisePage(QFrame):
    def __init__(self, model=None, title='Unnamed'):
        super().__init__()

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.update_blink)
        self.blink_step = 0
        self.blink_ax = None
        self.animations = []
        self.highlighted_ax = None
        self.selected_scatter_collection = None
        self.selected_axe = None
        self.full_scatter_collection = None
        self.selected_set = 'Set 1'
        self.orthogonality_dict = None
        self.model = model

        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        top_frame = QFrame()

        top_frame_layout = QHBoxLayout(top_frame)
        top_frame_layout.setContentsMargins(50, 50, 50, 50)
        top_frame_layout.setSpacing(80)

        input_title = QLabel("Input")
        input_title.setFixedHeight(30)
        input_title.setObjectName("TitleBar")
        input_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        input_title.setContentsMargins(10, 0, 0, 0)
        input_title.setStyleSheet("""
            background-color: #183881;
            color: white;
            font-weight:bold;
            font-size: 16px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)

        user_input_scroll_area = QScrollArea()
        user_input_scroll_area.setObjectName("userScroll")

        user_input_scroll_area.setFixedWidth(290)
        user_input_scroll_area.setWidgetResizable(True)
        user_input_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        user_input_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        user_input_frame = QFrame()

        user_input_frame.setFixedWidth(290)
        user_input_frame_layout = QVBoxLayout(user_input_frame)
        user_input_frame_layout.setContentsMargins(20, 20, 20, 20)

        user_input_scroll_area.setWidget(user_input_frame)

        input_section = QFrame()
        input_section.setFixedWidth(290)
        input_layout = QVBoxLayout(input_section)
        input_layout.setSpacing(0)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(input_title)
        input_layout.addWidget(user_input_scroll_area)

        info_group = QGroupBox("Info")
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
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
            QLabel {
                background-color: transparent;
                color: #3f4c5a;
            }
        """)

        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Number of conditions:"))
        self.condition_label = QLabel("---")
        info_layout.addWidget(self.condition_label)
        info_layout.addWidget(QLabel("Number of combinations:"))
        self.combination_label = QLabel("---")
        info_layout.addWidget(self.combination_label)
        info_group.setLayout(info_layout)

        data_selection_group = QGroupBox("Dataset selection")
        data_selection_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
                border: 1px solid #d0d4da;
                border-radius: 12px;
                margin-top: 25px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px;
                margin-top: -8px;
            }}
            QLabel {{
                background-color: transparent;
                color: #2C3E50;
                font-family: "Segoe UI";
                font-weight: bold;
            }}

            QComboBox::drop-down {{
                border:none;
            }}

            QComboBox::down-arrow {{
                image: url("{drop_down_icon_path}");
            }}
        """)

        self.data_selection_layout = QVBoxLayout()
        self.data_selection_layout.setSpacing(6)

        self.data_selection_layout.addWidget(QLabel("Number of data set to compare:"))
        self.compare_number = QComboBox()
        self.compare_number.addItems(["1", "2", "3", "4"])
        self.data_selection_layout.addWidget(self.compare_number)
        self.data_selection_layout.addSpacing(20)

        self.dataset_selector1 = QComboBox()
        self.dataset_selector2 = QComboBox()
        self.dataset_selector3 = QComboBox()
        self.dataset_selector4 = QComboBox()

        self.dataset_selector2.setDisabled(True)
        self.dataset_selector3.setDisabled(True)
        self.dataset_selector4.setDisabled(True)

        self.add_dataset_selector("Select data set 1:", self.dataset_selector1)
        self.add_dataset_selector("Select data set 2:", self.dataset_selector2)
        self.add_dataset_selector("Select data set 3:", self.dataset_selector3)
        self.add_dataset_selector("Select data set 4:", self.dataset_selector4)

        self.dataset_selector_list = [
            self.dataset_selector1,
            self.dataset_selector2,
            self.dataset_selector3,
            self.dataset_selector4
        ]

        self.dataset_selector_map = {
            '0': {'selector': self.dataset_selector1, 'axe': None, 'scatter_collection': None},
            '1': {'selector': self.dataset_selector2, 'axe': None, 'scatter_collection': None},
            '2': {'selector': self.dataset_selector3, 'axe': None, 'scatter_collection': None},
            '3': {'selector': self.dataset_selector4, 'axe': None, 'scatter_collection': None}
        }

        data_selection_group.setLayout(self.data_selection_layout)

        page_tips_group = QGroupBox("Tips")
        page_tips_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                background-color: #e7e7e7;
                color: #154E9D;
                border-radius: 12px;
                margin-top: 25px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px;
                margin-top: -10px;
            }
            QLabel {
                background-color: transparent;
                color: #3f4c5a;
            }
        """)

        page_tips_layout = QVBoxLayout()
        page_tips_group.setLayout(page_tips_layout)

        self.textEdit = QLabel()
        self.textEdit.setTextFormat(Qt.RichText)
        self.textEdit.setWordWrap(True)
        self.textEdit.setText(
            '<p><strong><span style="text-decoration: underline;">Tip 1</span>:</strong><br>'
            'Click on a plot area to select it, then choose a dataset from the table to display it there.</p>'
            '<p><strong><span style="text-decoration: underline;">Tip 2</span>:</strong><br>'
            'Collapse the table section by moving the horizontal splitter down—this will open the table in a separate window.</p>'
        )
        page_tips_layout.addWidget(self.textEdit)

        user_input_frame_layout.addWidget(data_selection_group)
        user_input_frame_layout.addWidget(LineWidget('Horizontal'))
        user_input_frame_layout.addWidget(info_group)
        user_input_frame_layout.addWidget(LineWidget('Horizontal'))
        user_input_frame_layout.addWidget(page_tips_group)

        # Plot Section
        plot_frame = QFrame()
        plot_frame.setFrameShape(QFrame.StyledPanel)
        plot_frame.setFrameShadow(QFrame.Raised)
        plot_frame.setStyleSheet("""
            background-color: #e7e7e7;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)

        plot_frame_layout = QVBoxLayout(plot_frame)
        plot_frame_layout.setContentsMargins(0, 0, 0, 0)

        plot_title = QLabel("2D Dataset visualization")
        plot_title.setFixedHeight(30)
        plot_title.setObjectName("TitleBar")
        plot_title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        plot_title.setContentsMargins(10, 0, 0, 0)
        plot_title.setStyleSheet("""
            background-color: #183881;
            color: white;
            font-weight:bold;
            font-size: 16px;
            font-weight: bold;
            padding: 6px 12px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)

        self.fig = Figure(figsize=(15,15))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = CustomToolbar(self.canvas)

        self._ax = self.canvas.figure.add_subplot(1, 1, 1)
        self._ax.set_box_aspect(1)


        plot_frame_layout.addWidget(plot_title)
        plot_frame_layout.addWidget(self.toolbar)
        plot_frame_layout.addWidget(self.canvas)

        top_frame_layout.addWidget(input_section)
        top_frame_layout.addWidget(plot_frame)

        self.top_frame_shadow = BoxShadow()
        top_frame.setGraphicsEffect(self.top_frame_shadow)

        # ====== NORMALIZED TABLE SECTION (optional below) ======
        table_frame = QWidget()
        table_frame_layout = QHBoxLayout(table_frame)
        table_frame_layout.setContentsMargins(20, 20, 20, 20)

        self.styled_table = StyledTable('2D combination table')
        self.styled_table.set_header_label([
            "Set #", "2D Combination", "Number of peaks","Hypothetical 2D peak capacity"
        ])
        self.styled_table.set_default_row_count(10)

        self.table_view_dialog = TableViewDialog(
            self,
            self.styled_table.get_table_view(),
            self.styled_table.get_model()
        )

        table_frame_layout.addWidget(self.styled_table)

        self.table_frame_shadow = BoxShadow()
        self.styled_table.setGraphicsEffect(self.table_frame_shadow)

        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.main_splitter.addWidget(top_frame)
        self.main_splitter.addWidget(table_frame)

        self.main_splitter.setSizes([486, 204])

        self.main_layout.addWidget(self.main_splitter)

        # Connect dataset count selector to update combo states
        self.compare_number.currentTextChanged.connect(self.update_dataset_selector_state)

        # Connect dataset combo changes to update selection map
        for index, data in self.dataset_selector_map.items():
            data["selector"].currentTextChanged.connect(lambda _, k=index: self.on_selector_changed(k))

        # Matplotlib canvas click event
        self.canvas.figure.canvas.mpl_connect("button_press_event", self.on_click)

        # Splitter collapsed state event
        self.main_splitter.splitterMoved.connect(self.table_collapsed)

        # Table selection event
        self.styled_table.selectionChanged.connect(self.data_set_selection_changed_from_table)

        # Individual dataset combo selector change event
        for index, data in self.dataset_selector_map.items():
            data["selector"].currentTextChanged.connect(self.data_set_selection_changed_from_combobox)


    def init_page(self):
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        self.update_data_set_table()
        self.populate_data_set_selectors()

        self.condition_label.setText(str(self.model.get_number_of_condition()))
        self.combination_label.setText(str(self.model.get_number_of_combination()))

        self.update_dataset_selector_state()

        #at page initialization , the current set selector is the number one
        # self.selected_set = self.dataset_selector_map['0']["selector"].currentText()
        # self.selected_axe = self.dataset_selector_map['0']["axe"]
        # self.selected_scatter_collection = self.dataset_selector_map['0']["scatter_collection"]
        #
        # self.update_figure()

    # Helper to reduce redundancy
    def add_dataset_selector(self,label_text, combobox):
        container = QVBoxLayout()
        container.setSpacing(2)
        container.addWidget(QLabel(label_text))
        container.addWidget(combobox)
        self.data_selection_layout.addLayout(container)

    def table_collapsed(self):

        if self.main_splitter.sizes()[1] == 0:
            self.table_view_dialog.show()
        else:
            self.table_view_dialog.close()

    def update_dataset_selector_state(self):
        number_of_selectors = int(self.compare_number.currentText())

        [self.dataset_selector_list[i].setDisabled(False) if i<number_of_selectors
         else self.dataset_selector_list[i].setDisabled(True) for i,selector in enumerate(self.dataset_selector_list)]

        self.update_plot_layout()


        [self.on_selector_changed(str(i)) for i in range(number_of_selectors)]


    def update_plot_layout(self):
        #get the number of plot to compare
        number_of_selectors = self.compare_number.currentText()

        #create a key string based on the compare number value in order to know which ploy layout to select
        plot_key = number_of_selectors+'PLOT'


        # plot layout map that contains the list of plot layout to display based on the compare number
        plot_layout_map = {'1PLOT':[111],
                       '2PLOT':[121,122],
                       '3PLOT':[221,222,223],
                       '4PLOT':[221,222,223,224]}

        #get list of layout
        layout_list = plot_layout_map[plot_key]

        self.fig.clear()

        for i,layout in enumerate(layout_list):
            index = str(i)
            axe = self.canvas.figure.add_subplot(layout)
            self.canvas.figure.subplots_adjust(wspace=.5, hspace=.5)
            axe.set_box_aspect(1)
            axe.set_xlim(0, 1)
            axe.set_ylim(0, 1)

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

            #initialize selector axe and scatter point selection
            self.dataset_selector_map[index]['axe'] = axe
            self.dataset_selector_map[index]['scatter_collection'] = axe.scatter([], [],s=20, c='k', marker='o', alpha=0.5)


    def on_selector_changed(self, index):
        """Handle combobox text change and get the corresponding axe."""
        selector = self.dataset_selector_map[index]["selector"]
        self.selected_set = selector.currentText()
        self.selected_axe = self.dataset_selector_map[index]["axe"]
        self.selected_scatter_collection = self.dataset_selector_map[index]["scatter_collection"]

        self.update_figure()


    def populate_data_set_selectors(self):
        """
        Updates the dataset selection combo box and figure list with the available data sets.

        - Retrieves the list of available data sets from `self.orthogonality_dict`.
        - Updates `self.set_combo` with the new dataset options.
        - Ensures signals are blocked during updates to prevent unwanted UI triggers.

        Notes:
        - This method should be called after loading new data.
        - If no data sets are available, the combo boxes remain unchanged.
        """
        if not self.orthogonality_dict:
            return  # No data available, prevent unnecessary UI updates

        data_sets_list = list(self.orthogonality_dict.keys())

        for key in self.dataset_selector_map:
            selector = self.dataset_selector_map[key]['selector']

            selector.blockSignals(True)  # Prevent UI signal loops

            selector.clear()

            selector.addItems(data_sets_list)

            selector.blockSignals(False)

    def update_table_peak_data(self):
        self.orthogonality_dict = self.model.get_orthogonality_dict()
        self.update_data_set_table()

    def update_data_set_table(self):
        """
        Updates the table view with orthogonality metrics for multiple datasets.

        - Retrieves the latest orthogonality metrics from the model.
        - Updates the table model with the new data.
        - Connects the table model to the proxy model for filtering/sorting.
        - Adjusts column sizes for better readability.

        Notes:
        - This method should be called after loading or modifying dataset metrics.
        - Ensures that the displayed data stays synchronized with the model.
        """
        data = self.model.get_combination_df()
        self.styled_table.async_set_table_data(data)


        self.styled_table.set_table_proxy()
        # self.table_view_dialog.set_proxy(self.table_view.getProxyModel())



    def data_sets_change(self, data_set: str = None) -> None:
        """
        Handles dataset selection from the dropdown menu and updates the UI accordingly.

        - Updates the current dataset based on the selection.
        - Highlights the corresponding row in the table view.
        - Refreshes the displayed figure to reflect the new dataset.

        Parameters:
            data_set (str, optional): The dataset name to switch to.
                                      If None, it is retrieved from `self.set_combo`.

        Notes:
        - If triggered by the dropdown, `data_set` is None, so the function retrieves the selected value.
        - Updates both the dropdown and table selection to stay synchronized.
        - Calls `update_figure()` to refresh the visualization.
        """
        if data_set is None:
            self.selected_set = self.select_set_combo.currentText()
            index_at_row = self.get_index_from()

            # Prevent unnecessary signal emissions while selecting the row
            self.styled_table.get_table_view().blockSignals(True)
            self.styled_table.get_table_view().selectionModel().blockSignals(True)
            self.styled_table.get_table_view().selectRow(index_at_row)
            self.styled_table.get_table_view().blockSignals(False)
            self.styled_table.get_table_view().selectionModel().blockSignals(False)
        else:
            self.selected_set = data_set
            self.select_set_combo.blockSignals(True)
            self.select_set_combo.setCurrentText(self.selected_set)
            self.select_set_combo.blockSignals(False)

        # Refresh the displayed figure
        self.update_figure()

    def update_figure(self) -> None:
        """
        Updates the current visualization based on the selected set.

        - Checks the model's status to determine if data is available for plotting.

        """

        if self.model.get_status() in ['loaded','peak_capacity_loaded']:
            self.plot_scatter()
        else:
            return


    def update_blink(self):
        """Smoothly fade the border in and out, then reset."""
        if self.blink_ax:
            alpha = abs(np.sin(self.blink_step * np.pi / 10))  # Create smooth fade effect
            self.blink_ax.patch.set_edgecolor((1, 0, 0, alpha))  # Red with varying alpha
            self.canvas.figure.canvas.draw_idle()  # Force redraw

            self.blink_step += 1
            if self.blink_step >= 10:  # Stop after one blink
                self.blink_timer.stop()
                self.blink_ax.patch.set_edgecolor("black")  # Reset to default
                self.canvas.figure.canvas.draw_idle()  # Ensure final redraw

    def on_click(self, event):
        """Detect which subplot was clicked and trigger a brief highlight."""
        if event.inaxes:
            self.selected_axe = event.inaxes

            # Reset previous highlighted axis
            if self.highlighted_ax:
                self.highlighted_ax.patch.set_edgecolor("black")  # Reset border

            # Apply initial highlight
            self.selected_axe.patch.set_linewidth(1)

            # Start the smooth blink effect
            self.blink_ax = self.selected_axe
            self.blink_step = 0
            self.blink_timer.start(25)  # Adjust speed of blink

            self.highlighted_ax = self.selected_axe  # Store the selected axe


    def plot_scatter(self, set_nb=None, dirname=""):
        """
        Plots scatter points on the main axis.

        - Sets the plot stack index to 0.
        - Retrieves X and Y values along with their labels from the orthogonality dictionary.
        - Updates or creates a scatter plot with the retrieved data.
        - Hides the legend for cleaner visualization.

        Parameters:
            set_nb (str, optional): The dataset number to plot. Defaults to the current dataset.
            dirname (str, optional): Directory name for saving plots.

        Notes:
        - If the scatter plot already exists, its offsets are updated.
        - Otherwise, a new scatter plot is created.
        """

        # if no axe is ready leave function
        if self.selected_axe is None:
            return

        if set_nb is None:
            set_number = self.selected_set
        else:
            set_number = set_nb

        x = self.orthogonality_dict[set_number]['x_values']
        y = self.orthogonality_dict[set_number]['y_values']
        x_title = self.orthogonality_dict[set_number]['x_title']
        y_title = self.orthogonality_dict[set_number]['y_title']
        self.selected_axe.set_title(set_number, fontdict={'fontsize': 10}, pad=13)

        # Set axis labels
        self.selected_axe.set_xlabel(x_title, fontsize=11)
        self.selected_axe.set_ylabel(y_title, fontsize=11)

        # Update scatter plot if it already exists
        self.selected_scatter_collection.set_offsets(list(zip(x, y)))


        # self._ax.legend().set_visible(False)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def get_index_from(self) -> int:
        """
        Retrieves the row index corresponding to the currently selected dataset.

        - Iterates through the table model to find a match with `self.selected_set`.
        - Uses the proxy model to access the displayed data.

        Returns:
            int: The row index of the selected dataset, or -1 if not found.

        Notes:
        - This function assumes that dataset names are stored in the first column.
        - If no match is found, returns -1 to indicate failure.
        """
        row_count = self.styled_table.get_row_count()

        for row in range(row_count):
            model_index = self.styled_table.get_proxy_model().index(row, 0)  # Column 0 assumed to contain dataset names
            if f"Set {model_index.data()}" == self.selected_set:
                return row

        return -1  # Explicitly return -1 if no match is found

    def table_item_clicked(self, index: QModelIndex) -> None:
        """
        Handles table row selection and updates the dataset accordingly.

        - Retrieves the dataset name from the selected row.
        - Calls `data_sets_change()` to synchronize the dropdown selection.

        Parameters:
            index (QModelIndex): The index of the clicked item (not used in current logic).

        Notes:
        - Only the first selected row is considered if multiple rows are selected.
        - Assumes dataset names are stored in the first column.
        """
        model_index_list = self.styled_table.get_selected_rows()

        if not model_index_list:
            return  # No selection, exit early

        self.data_sets_change(f"Set {model_index_list[0].data()}")

    def data_set_selection_changed_from_combobox(self) -> None:
        """
        Handles dataset selection changes from the combo box.

        - Updates the current dataset name.
        - Selects the corresponding row in the table view.
        - Refreshes the figure to display the selected dataset.

        Notes:
        - This function ensures synchronization between the combo box selection and the table view.
        - Calls `get_index_from()` to retrieve the correct row index.
        - If no matching row is found, no row selection is applied.
        """
        index_at_row = self.get_index_from()

        if index_at_row != -1:
            self.styled_table.select_row(index=index_at_row)
            self.table_view_dialog.get_table_view().selectRow(index_at_row)


        # Refresh the figure to reflect the selected dataset
        self.update_figure()

    def data_set_selection_changed_from_table(self) -> None:
        """
        Handles dataset selection changes from the table view.

        - Retrieves the selected dataset from the table view.
        - Synchronizes the combo box with the selected dataset.
        - Updates the visualization based on the current tab.

        Notes:
        - Only the first selected row is considered if multiple rows are selected.
        - The combo box is blocked during updates to prevent signal loops.
        - If the "Calculations" tab is active, the selected dataset blinks on the orthogonality plot.
        - Otherwise, the standard figure update is triggered.
        """
        model_index_list = self.styled_table.get_selected_rows()

        if not model_index_list:
            return  # No selection, exit early

        proxy_model = self.styled_table.get_proxy_model()
        model_index = proxy_model.mapToSource(model_index_list[0])
        self.selected_set = f"Set {model_index.data()}"


        # find the index of  data set selector assocciated to the given selected axe
        index = [index for index, val in self.dataset_selector_map.items() if val['axe'] == self.selected_axe]

        # index is a list, but I just need the index value inside (string)
        index = index[0]
        selector = self.dataset_selector_map[index]["selector"]
        self.selected_axe = self.dataset_selector_map[index]["axe"]
        self.selected_scatter_collection = self.dataset_selector_map[index]["scatter_collection"]

        selector.blockSignals(True)
        selector.setCurrentText(self.selected_set)
        selector.blockSignals(False)

        self.update_figure()

class TableViewDialog(QDialog):

    def __init__(self,parent,parent_table_view = None, model = None ):
        super().__init__(parent)

        self.setWindowTitle("Data set table")
        self.setGeometry(50, 50, 500, 400)
        self.parent_table_view = parent_table_view  # Store reference
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.table_model = model
        self.table_view = OrthogonalityTableView(self,model)

        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)


        main_layout.addWidget(self.table_view)

        # ✅ Sync sorting between both tables
        header = self.table_view.horizontalHeader()
        header.sectionClicked.connect(self.sync_sorting)


        # # ✅ Sync sorting in both directions
        # self.table_view.horizontalHeader().sectionClicked.connect(self.sync_sorting)
        self.parent_table_view.horizontalHeader().sectionClicked.connect(self.sync_sorting)

        # ✅ Manually sync selection changes
        self.table_view.selectionModel().selectionChanged.connect(self.sync_selection)

    def get_table_view(self):
        return self.table_view

    def set_proxy(self,proxy):
        self.table_model.set_proxy(proxy)

    def sync_sorting(self, column):
        """Synchronize sorting between dialog and main layout."""
        sender_table = self.sender().parent()  # Get the sender's table view

        # Get sorting order from the correct table
        current_order = sender_table.horizontalHeader().sortIndicatorOrder()

        # ✅ Apply sorting to the shared model instead of just a view
        self.parent_table_view.model().sort(column, current_order)
        self.table_view.model().sort(column, current_order)

    def sync_selection(self, selected, deselected):
        """Synchronize row selection from dialog to main layout"""
        parent_selection_model = self.parent_table_view.selectionModel()

        # Clear previous selection in the main table
        parent_selection_model.clearSelection()

        for index in selected.indexes():
            row = index.row()

            # Select the same row in the parent table
            parent_index = self.parent_table_view.model().index(row, 0)  # Select the first column
            parent_selection_model.select(parent_index, QItemSelectionModel.Select | QItemSelectionModel.Rows)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotPairWisePage()
    window.show()
    sys.exit(app.exec())
