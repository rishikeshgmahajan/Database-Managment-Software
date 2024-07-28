import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sqlite3
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFrame, QScrollArea, QLabel, QLineEdit, QPushButton
from PyQt5.QtWidgets  import QUndoCommand, QTableWidgetItem
from PyQt5.QtWidgets  import QUndoStack
from PyQt5.QtGui import QFontMetrics

class FlexibleTabBar(QTabBar):
    def tabSizeHint(self, index):
        text = self.tabText(index)
        
        font_metrics = QFontMetrics(self.font())
        width = font_metrics.width(text) + 80
        
        return QSize(width, 30)  # You can adjust the height as needed

class DeleteRowsCommand(QUndoCommand):
    def __init__(self, table_widget, rows, row_data, parent=None):
        super().__init__(parent)
        self.table_widget = table_widget
        self.rows = sorted(rows, reverse=True)
        self.row_data = row_data  # Data to restore rows if undone

    def undo(self):
        for i, row in enumerate(self.rows):
            self.table_widget.insertRow(row)
            for col, item_text in enumerate(self.row_data[i]):
                item = QTableWidgetItem(item_text)
                self.table_widget.setItem(row, col, item)

    def redo(self):
        for row in self.rows:
            self.table_widget.removeRow(row)

class DeleteColumnsCommand(QUndoCommand):
    def __init__(self, table_widget, columns, column_data, parent=None):
        super().__init__(parent)
        self.table_widget = table_widget
        self.columns = sorted(columns, reverse=True)
        self.column_data = column_data  # Data to restore columns if undone

    def undo(self):
        for i, col in enumerate(self.columns):
            self.table_widget.insertColumn(col)
            for row, item_text in enumerate(self.column_data[i]):
                item = QTableWidgetItem(item_text)
                self.table_widget.setItem(row, col, item)

    def redo(self):
        for col in self.columns:
            self.table_widget.removeColumn(col)

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vidwo - DataCord")  # Initial title when no file is opened
        self.current_file_name = None  # Variable to store the current file name
        self.setStyleSheet(myStyleSheet())

        self.centralWidget = QWidget()

        self.undo_stack = QUndoStack(self)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBar(FlexibleTabBar())
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tab_count = 0

        self.position_index = 0
        self.positions = [QTabWidget.North, QTabWidget.South]

        add_tab_button = QPushButton(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\add_tab.png"),"")
        add_tab_button.clicked.connect(self.add_tab)
        add_tab_button.setToolTip("Add one tab")
        add_tab_button.setStyleSheet("""
padding:3px;
""")
        
        close_tab_button = QPushButton(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\close_tab.png"),"")
        close_tab_button.clicked.connect(lambda: [self.tab_widget.removeTab(0) for _ in range(self.tab_widget.count())])
        close_tab_button.setToolTip("Close all tabs")
        close_tab_button.setStyleSheet("""
margin-right:3px;
padding:3px;
""")
        
        Toggle_tab_button = QPushButton(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\toggletab.png"),"")
        Toggle_tab_button.clicked.connect(self.toggle_tab_position)
        Toggle_tab_button.setToolTip("Toggle all tabs")
        Toggle_tab_button.setStyleSheet("""
margin-right:3px;
padding:3px;
""")

        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_tab_button)
        button_layout.addWidget(close_tab_button)
        button_layout.addWidget(Toggle_tab_button)
        button_container.setLayout(button_layout)
        button_layout.setContentsMargins(0, 0, 0, 0)  # Set margins to 0
        button_container.setFixedHeight(25)

        self.tab_widget.setCornerWidget(button_container)

        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        self.tab_widget.setStyleSheet("""
                                      QTabBar{
                                      padding-left:4px;
                                      padding-right:4px;
                                      }
QTabBar::tab { 
margin-top: 4px; 
padding:3px;
                                      margin-left:3px;
                                      margin-right:3px;
margin-bottom:2px;
border-radius:5px;
border:1px solid grey;
}
                                      QTabBar::tab:hover { 
margin-top: 4px; 
padding:3px;
margin-bottom:2px;
                                      margin-left:3px;
                                      margin-right:3px;

border:2px solid #820F41;
}
                                                                            QTabBar::tab:selected { 
margin-top: 4px; 
padding:3px;
margin-bottom:2px;
                                      margin-left:3px;
                                      margin-right:3px;
                                      background:#FFE6F0;

border:2px solid #820F41;
}
""")

        self.setCentralWidget(self.tab_widget)

        self.create_new_tab()

        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        self.create_widgets()

        self.create_main_toolbar()

        self.create_menu_bar()

        self.create_statusbar()

    def toggle_tab_position(self):
        # Increment the position index and wrap around if necessary
        self.position_index = (self.position_index + 1) % len(self.positions)
        # Set the new tab position
        self.tab_widget.setTabPosition(self.positions[self.position_index])

    def update_window_title(self):
        options = QFileDialog.Options()
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Open Database File", "", "SQLite Database Files (*.db *.sqlite);;All Files (*)", options=options)
        if self.file_name:
            self.setWindowTitle(f"Vidwo - DataCord : {self.file_name}")
        else:
            self.setWindowTitle("Vidwo - DataCord : No file opened")

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")

        open_file_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\opendata.png"),"Open File", self)
        open_file_action.triggered.connect(self.open_database)
        file_menu.addAction(open_file_action)

        file_menu.addSeparator()

        save_as_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\savedata.png"),"Save As", self)
        save_as_action.triggered.connect(self.save_database)
        file_menu.addAction(save_as_action)

        save_add_as_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\savadddata.png"),"Add database to existing file", self)
        save_add_as_action.triggered.connect(self.save_add_database)
        file_menu.addAction(save_add_as_action)

        file_menu.addSeparator()

        new_clear_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\clear.png"),"New/Clear", self)
        new_clear_action.triggered.connect(self.clear_table)
        file_menu.addAction(new_clear_action)

        file_menu.addSeparator()

        exit_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\exit.png"),"Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")

        search_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\search.png"),"Search", self)
        search_action.triggered.connect(self.open_search_dialog)
        edit_menu.addAction(search_action)

        # Insert Menu
        insert_menu = menubar.addMenu("Insert")

        header_label_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\addheadl.png"),"Header Label", self)
        header_label_action.triggered.connect(self.open_header_dialog)
        insert_menu.addAction(header_label_action)

        insert_data_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\adddata.png"),"Insert Data", self)
        insert_data_action.triggered.connect(self.open_add_contact_dialog)
        insert_menu.addAction(insert_data_action)

        insert_menu.addSeparator()

        add_tab_button = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\add.png"),"Add tab",self)
        add_tab_button.triggered.connect(self.add_tab)
        insert_menu.addAction(add_tab_button)

        # View Menu (Placeholder)
        view_menu = menubar.addMenu("View")

        toggle_toolbar_action = QAction("Toggle Toolbar", self)
        toggle_toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(toggle_toolbar_action)

        toggle_statusbar_action = QAction("Toggle Statusbar", self)
        toggle_statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(toggle_statusbar_action)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        menubar.setFont(QFont("Arial Rounded MT Bold", 10))

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_tab_context_menu(self, pos):
        index = self.tab_widget.tabBar().tabAt(pos)
        if index != -1:
            context_menu = QMenu(self)
            rename_action = context_menu.addAction("Rename tab")
            text_color_action = context_menu.addAction("Change text Color")
            context_menu.addSeparator()
            add_tab_action = context_menu.addAction("Add tab")
            close_tab_action = context_menu.addAction("Close all tabs")
            toggle_tab_action = context_menu.addAction("Toggle tabs")
            action = context_menu.exec_(self.tab_widget.mapToGlobal(pos))
            if action == rename_action:
                self.rename_tab(index)
            elif action == text_color_action:
                self.change_tab_text_color(index)
            elif action == add_tab_action:
                self.add_tab()
            elif action == close_tab_action:
                [self.tab_widget.removeTab(0) for _ in range(self.tab_widget.count())]  
            elif action == toggle_tab_action:
                self.toggle_tab_position()

    def rename_tab(self, index):
        current_text = self.tab_widget.tabText(index)
        new_text, ok = QInputDialog.getText(self, "Rename Tab", "Enter new tab name:", QLineEdit.Normal, current_text)
        if ok:
            self.tab_widget.setTabText(index, new_text)

    def change_tab_text_color(self, index):
        color = QColorDialog.getColor()
        if color.isValid():
            self.tab_widget.tabBar().setTabTextColor(index, color)

    def create_new_tab(self,file_name=None):
        # Increment tab count
        self.tab_count += 1

        # Create table widget for new tab
        table_widget = QTableWidget()
        table_widget.setColumnCount(3)
        table_widget.setHorizontalHeaderLabels(["ID", "Name", "Phone"])

        # Add the table widget to a new tab with dynamic name
        if file_name:
            tab_name = file_name
        elif self.tab_count == 1:
            tab_name = "Table 1"
        else:
            tab_name = f"Table {self.tab_count}"
        self.tab_widget.addTab(table_widget, tab_name)
        

    def close_tab(self, index):
        # Remove the tab at the specified index
        self.tab_widget.removeTab(index)

        # Decrement tab count
        self.tab_count -= 1

        # If all tabs are closed or only one tab remains, reset tab count to 0
        if self.tab_count <= 1:
            self.tab_count = 0

        # If the last remaining tab is named "Table 1", update its name
        if self.tab_count == 1:
            self.tab_widget.setTabText(0, "Table 1")

    def add_tab(self):
        self.create_new_tab()
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def create_statusbar(self):
        self.statusbar = self.statusBar()
        self.statusbar.setFont(QFont("Arial Rounded MT Bold", 9))
        self.statusbar.setStyleSheet("""
            background:#f5f5f5;
            font-size:15px;
            padding:3px;
            border:1px solid #bdbdbd;
            border-radius:7px;
            margin:4px;
        """)
        self.count_label = QLabel()
        self.statusbar.addWidget(self.count_label)
        self.update_status_bar()
        
        # Connect signals to update status bar
        self.contact_table.model().dataChanged.connect(self.update_status_bar)
        self.contact_table.itemChanged.connect(self.update_status_bar) 
    
    def update_status_bar(self):
        row_count = self.contact_table.rowCount()
        column_count = self.contact_table.columnCount()
        self.count_label.setText(f'Rows: {row_count}, Columns: {column_count}')

    def toggle_toolbar(self):
        state = self.main_toolbar.isVisible()
        self.main_toolbar.setVisible(not state)

    def toggle_statusbar(self):
        state = self.statusbar.isVisible()
        self.statusbar.setVisible(not state)

    def show_about_dialog(self):
        self.abtdi = QDialog(self)
        self.abtdi.setWindowIcon(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\VS_Icons\\abouticon.png"))
        self.abtdi.setGeometry(300, 300, 480, 250)
        self.abtdi.setWindowTitle("DataCord - About")
        self.abtdi.setFixedSize(470, 250)
        self.abtdi.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.abtdi.setStyleSheet("""
            background:white;
        """)

        self.topframe = QFrame(self.abtdi)
        self.topframe.resize(499, 100)
        self.topframe.setStyleSheet("""background-color:#820F41;
            border-radius:4px;
        """)

        h1layout = QHBoxLayout(self.topframe)
        vinlayout = QVBoxLayout(self.topframe)

        self.vidLabel = QLabel(self.topframe)
        self.vidLabel.setText("Vidwo")
        self.vidLabel.setFont(QFont("Arial Rounded MT Bold", 30, QFont.Bold))
        self.vidLabel.setAlignment(Qt.AlignCenter)
        self.vidLabel.setStyleSheet("""
            color:white;
            margin-left:40px;
        """)
        self.sLabel = QLabel(self.topframe)
        self.sLabel.setText("|")
        self.sLabel.setFont(QFont("Fira Mono Bold", 30))
        self.sLabel.setAlignment(Qt.AlignCenter)
        self.sLabel.setStyleSheet("""
            color:white;
        """)
        self.scLabel = QLabel(self.topframe)
        self.scLabel.setText("DataCord")
        self.scLabel.setFont(QFont("Fira Mono Bold", 20, QFont.Bold))
        self.scLabel.setAlignment(Qt.AlignCenter)
        self.scLabel.setStyleSheet("""
            margin:0px;
            color:white;
            margin-right:40px;
        """)
        self.pLabel = QLabel(self.topframe)
        self.pLabel.setText("PERSONAL")
        self.pLabel.setFont(QFont("Beware", 13))
        self.pLabel.setAlignment(Qt.AlignCenter)
        self.pLabel.setStyleSheet("""
            color:lightgrey;
            margin:0px;
            margin-right:40px;
        """)

        h1layout.addWidget(self.vidLabel)
        h1layout.addWidget(self.sLabel)

        vinlayout.addWidget(self.scLabel)
        vinlayout.addWidget(self.pLabel)
        self.setLayout(vinlayout)
        h1layout.addLayout(vinlayout)
        self.setLayout(h1layout)

        self.midframe = QFrame(self.abtdi)
        h1lay = QVBoxLayout(self.midframe)

        self.versLabel = QLabel(self.midframe)
        self.versLabel.setText("Version : 1.1.0")
        self.versLabel.setFont(QFont("Beware", 13))
        self.versLabel.setAlignment(Qt.AlignLeft)
        self.versLabel.setStyleSheet("""
            color:Black;
            margin:0px;
            margin-right:40px;
        """)

        self.statsLabel = QLabel(self.midframe)
        self.statsLabel.setText("Status : ACTIVATED ")
        self.statsLabel.setFont(QFont("Beware", 13))
        self.statsLabel.setAlignment(Qt.AlignLeft)
        self.statsLabel.setStyleSheet("""
            color:Black;
            margin:0px;
            margin-right:40px;
            background:lightgreen;
            border:1px solid green;
        """)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_flash)
        self.timer.start(1000)  # Flash every 1 second

        self.flash_on = True

        self.licLabel = QLabel(self.midframe)
        self.licLabel.setText("Developed by Rishikesh")
        self.licLabel.setFont(QFont("Beware", 13))
        self.licLabel.setAlignment(Qt.AlignLeft)
        self.licLabel.setStyleSheet("""
            color:Black;
            margin:0px;
            margin-right:40px;
        """)

        self.updtLabel = QLabel(self.midframe)
        self.updtLabel.setText("Software Update : v 1.1.0 - Up to Date")
        self.updtLabel.setFont(QFont("Beware", 13))
        self.updtLabel.setAlignment(Qt.AlignLeft)
        self.updtLabel.setStyleSheet("""
            color:Black;
            margin:0px;
            margin-right:40px;
        """)

        h1lay.addWidget(self.versLabel)
        h1lay.addWidget(self.statsLabel)
        h1lay.addWidget(self.licLabel)
        h1lay.addWidget(self.updtLabel)

        self.midframe.resize(499, 100)
        self.midframe.setStyleSheet("""background-color:lightgrey;
            border-radius:4px;
        """)
        vlayout = QVBoxLayout(self.abtdi)
        vlayout.addWidget(self.topframe)
        vlayout.addWidget(self.midframe)
        self.setLayout(vlayout)

        self.abtdi.exec()

    def toggle_flash(self):
        if self.flash_on:
            self.statsLabel.setStyleSheet("""
                color:Black;
                margin:0px;
                margin-right:40px;
                background:lightgreen;
                border:1px solid green;
            """)
            self.licLabel.setStyleSheet("""
                color:Black;
                margin:0px;
                margin-right:40px;
                background: #820F41;
                border:1px solid #820F41;
            """)
            self.flash_on = False
        else:
            self.statsLabel.setStyleSheet("""
                color:Black;
                margin:0px;
                margin-right:40px;
                background:lightgreen;
                border:1px solid green;
            """)
            self.licLabel.setStyleSheet("""
                color:Black;
                margin:0px;
                margin-right:40px;
                background: #820F41;
                border:1px solid #820F41;
            """)
            self.flash_on = True

    def create_widgets(self):
        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(3)  # Adjust column count based on headers
        self.contact_table.setHorizontalHeaderLabels(["ID", "Name", "Phone"])
        self.layout.addWidget(self.contact_table)

    def create_main_toolbar(self):
        self.main_toolbar = self.addToolBar("Main Toolbar")
        self.main_toolbar.setStyleSheet("""
        QToolButton {
            border: 1px solid grey;
            border-radius: 5px;
            padding: 3px;
            font-size: 14px;
        }
        QToolButton:hover {
            border: 1px solid #820F41;
            background: #FFE6F0;
            border-radius: 5px;
            color: #820F41;
            padding: 3px;
        }
        QToolButton:pressed {
            border: 2px solid #820F41;
            border-radius: 5px;
            padding: 3px;
        }
        """)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setColor(QtGui.QColor(136, 136, 136))
        shadow_effect.setXOffset(2)
        shadow_effect.setYOffset(2)
        self.main_toolbar.setGraphicsEffect(shadow_effect)

        self.main_toolbar.setStyleSheet("""
            background:white;
            border-radius:7px;
            margin-top:3px;
            margin-left:7px;
            margin-right:7px;
            padding:2px;
            """)
        
        open_database_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\opendata.png"),"", self)
        open_database_action.triggered.connect(self.open_database)
        self.main_toolbar.addAction(open_database_action)

        save_database_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\savedata.png"),"", self)
        save_database_action.triggered.connect(self.save_database)
        self.main_toolbar.addAction(save_database_action)

        save_add_database_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\savadddata.png"),"", self)
        save_add_database_action.triggered.connect(self.save_add_database)
        self.main_toolbar.addAction(save_add_database_action)

        self.main_toolbar.addSeparator()

        cut_cells_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\cut.png"),"", self)
        cut_cells_action.triggered.connect(self.cut_cells)
        self.main_toolbar.addAction(cut_cells_action)

        copy_cells_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\copy.png"),"", self)
        copy_cells_action.triggered.connect(self.copy_selected_cells)
        self.main_toolbar.addAction(copy_cells_action)

        paste_cells_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\paste.png"),"", self)
        paste_cells_action.triggered.connect(self.paste_cells)
        self.main_toolbar.addAction(paste_cells_action)

        self.main_toolbar.addSeparator()

        set_header_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\addheadl.png"),"", self)
        set_header_action.triggered.connect(self.open_header_dialog)
        self.main_toolbar.addAction(set_header_action)

        add_contact_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\adddata.png"),"", self)
        add_contact_action.triggered.connect(self.open_add_contact_dialog)
        self.main_toolbar.addAction(add_contact_action)

        remove_row_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\removedata.png"),"", self)
        remove_row_action.triggered.connect(self.delete_selected_row)
        self.main_toolbar.addAction(remove_row_action)

        remove_columns_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\removecolumn.png"),"", self)
        remove_columns_action.triggered.connect(self.delete_selected_columns)
        self.main_toolbar.addAction(remove_columns_action)

        self.main_toolbar.addSeparator()

        self.combo = QComboBox()
        self.combo.addItems(["Sort A to Z", "Sort Z to A", "Sort 1,2,3..."])
        self.main_toolbar.addWidget(self.combo)
        self.combo.currentIndexChanged.connect(self.sort_table)
        self.combo.setFont(QFont("Arial Rounded MT Bold", 15))
        self.combo.setStyleSheet("""
QComboBox {
                font-size: 15px;
                background-color: #FFFFFF;
                selection-background-color: #820F41;
                selection-color: white;
                border: 1px solid #CCCCCC;
                padding: 2px;
                border-radius:4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                background:white;
                image: url(C:/Users/rishi/OneDrive/Documents/DC_Icons/dda.png);
                background-size: 5px;
                background-repeat: no-repeat;
                background-position: right 10px center;
            }
""")

        self.main_toolbar.addSeparator()

        clear_contents_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\clearcontents.png"),"", self)
        clear_contents_action.triggered.connect(self.clear_table_contents)
        self.main_toolbar.addAction(clear_contents_action)

        clear_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\clear.png"),"", self)
        clear_action.triggered.connect(self.clear_table)
        self.main_toolbar.addAction(clear_action)

        self.main_toolbar.addSeparator()

        search_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\search.png"),"", self)
        search_action.triggered.connect(self.open_search_dialog)
        self.main_toolbar.addAction(search_action)

        self.copied_data = ""

    def sort_table(self):
        option = self.combo.currentText()
        current_column = self.contact_table.currentColumn()
        
        if current_column == -1:
            return  # No column selected
        
        if option == "Sort A to Z":
            self.contact_table.sortItems(current_column, Qt.AscendingOrder)
        elif option == "Sort Z to A":
            self.contact_table.sortItems(current_column, Qt.DescendingOrder)
        elif option == "Sort 1,2,3...":
            self.contact_table.sortItems(current_column, Qt.AscendingOrder)

    def cut_cells(self):
        selected_items = self.contact_table.selectedItems()
        if selected_items:
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            mime_data = QMimeData()
            text = '\n'.join([item.text() for item in selected_items])
            mime_data.setText(text)
            clipboard.setMimeData(mime_data)
            
            # Clear the content of the selected cells
            for item in selected_items:
                item.setText('')

        else:
            QMessageBox.warning(self, "Warning", "No cell selected.")

    def copy_selected_cells(self):
        clipboard = QApplication.clipboard()
        selected_ranges = self.contact_table.selectedRanges()

        if not selected_ranges:
            print("No cells selected.")
            return

        # Collect the selected cell data
        data = {}
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                if row not in data:
                    data[row] = {}
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.contact_table.item(row, col)
                    if item:
                        data[row][col] = item.text()
                    else:
                        data[row][col] = ""  # Empty cell

        # Convert the collected data into a formatted string
        rows = sorted(data.keys())
        if not rows:
            text_to_copy = ""
        else:
            cols = sorted(data[rows[0]].keys())
            text_to_copy = ""
            for row in rows:
                row_data = [data[row].get(col, "") for col in cols]
                text_to_copy += "\t".join(row_data) + "\n"

        # Store the copied data
        self.copied_data = text_to_copy.strip()
        print("Copied Data:")
        print(self.copied_data)

        # Copy to clipboard
        clipboard.setText(self.copied_data)

    def paste_cells(self):
        if not self.copied_data:
            print("No data to paste.")
            return
        
        clipboard = QApplication.clipboard()
        selected_ranges = self.contact_table.selectedRanges()

        if not selected_ranges:
            print("No cells selected.")
            return

        # Determine the range of selected cells
        selected_range = selected_ranges[0]
        start_row = selected_range.topRow()
        start_col = selected_range.leftColumn()

        # Split copied data into lines and cells
        copied_lines = self.copied_data.split('\n')
        copied_data = [line.split('\t') for line in copied_lines]

        # Ensure we do not exceed the table dimensions
        max_rows = self.contact_table.rowCount()
        max_cols = self.contact_table.columnCount()

        for r in range(len(copied_data)):
            for c in range(len(copied_data[r])):
                if r + start_row < max_rows and c + start_col < max_cols:
                    cell_text = copied_data[r][c]
                    item = self.contact_table.item(r + start_row, c + start_col)
                    if not item:
                        item = QTableWidgetItem()
                        self.contact_table.setItem(r + start_row, c + start_col, item)
                    item.setText(cell_text)
                else:
                    print(f"Skipping cell ({r + start_row}, {c + start_col}) - out of bounds.")

    def delete_selected_row(self):
        table_widget = self.contact_table  # Assuming 'contact_table' is your QTableWidget instance
        selected_indexes = table_widget.selectedIndexes()
        if selected_indexes:
            rows = set(index.row() for index in selected_indexes)
            for row in sorted(rows, reverse=True):
                table_widget.removeRow(row)
        else:
            QMessageBox.warning(self, "Warning", "No row selected.")

    def delete_selected_columns(self):
        table_widget = self.contact_table
        selected_indexes = table_widget.selectedIndexes()
        if selected_indexes:
            columns = set(index.column() for index in selected_indexes)
            for col in sorted(columns, reverse=True):
                table_widget.removeColumn(col)
        else:
            QMessageBox.warning(self, "Warning", "No column selected.")

    def save_database(self, table_name="contacts"):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Database File", "", "SQLite Database Files (*.db *.sqlite);;All Files (*)", options=options)
        
        if file_name:
            try:
                # Retrieve the currently active tab and its table widget
                current_tab_index = self.tab_widget.currentIndex()
                self.contact_table = self.tab_widget.widget(current_tab_index)

                # Get the column names and data from the QTableWidget
                column_names = [self.contact_table.horizontalHeaderItem(col).text() for col in range(self.contact_table.columnCount())]
                rows = []
                for row in range(self.contact_table.rowCount()):
                    row_data = [self.contact_table.item(row, col).text() if self.contact_table.item(row, col) else "" for col in range(self.contact_table.columnCount())]
                    rows.append(row_data)

                # Connect to the new database file and create a table
                conn = sqlite3.connect(file_name)
                cursor = conn.cursor()

                # Drop the existing table if it exists
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

                # Create the table with columns matching those in the QTableWidget
                column_defs = ", ".join([f"{col} TEXT" for col in column_names])
                cursor.execute(f"CREATE TABLE {table_name} ({column_defs});")

                # Insert the data into the table
                cursor.executemany(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join('?' * len(column_names))})", rows)
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Success", f"Data successfully saved to {file_name}")

            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"An error occurred while saving the database:\n{str(e)}")
                print(f"SQLite error: {e}")  # Debug print for console

            except Exception as ex:
                QMessageBox.warning(self, "Error", f"An unexpected error occurred:\n{str(ex)}")
                print(f"Unexpected error: {ex}")  # Debug print for console

    def save_add_database(self, table_name="contacts"):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Database File", "", "SQLite Database Files (*.db *.sqlite);;All Files (*)", options=options)
        
        if file_name:
            try:
                # Retrieve the currently active tab and its table widget
                current_tab_index = self.tab_widget.currentIndex()
                self.contact_table = self.tab_widget.widget(current_tab_index)

                # Get the column names and data from the QTableWidget
                column_names = [self.contact_table.horizontalHeaderItem(col).text() for col in range(self.contact_table.columnCount())]
                rows = []
                for row in range(self.contact_table.rowCount()):
                    row_data = [self.contact_table.item(row, col).text() if self.contact_table.item(row, col) else "" for col in range(self.contact_table.columnCount())]
                    rows.append(row_data)

                # Connect to the new database file and create a table
                conn = sqlite3.connect(file_name)
                cursor = conn.cursor()

                # Create the table with columns matching those in the QTableWidget
                column_defs = ", ".join([f"{col} TEXT" for col in column_names])
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs});")

                # Insert the data into the table
                cursor.executemany(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join('?' * len(column_names))})", rows)
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Success", f"Data successfully saved to {file_name}")

            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"An error occurred while saving the database:\n{str(e)}")

            except Exception as ex:
                QMessageBox.warning(self, "Error", f"An unexpected error occurred:\n{str(ex)}")

    def open_header_dialog(self):
        current_tab_index = self.tab_widget.currentIndex()
        table_widget = self.tab_widget.widget(current_tab_index)

        labels = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]
        dialog = HeaderDialog(self, labels)
        if dialog.exec_():
            new_labels = dialog.get_labels()
            if new_labels:
                table_widget.setColumnCount(len(new_labels))
                table_widget.setHorizontalHeaderLabels(new_labels)

    def open_add_contact_dialog(self):
        current_tab_index = self.tab_widget.currentIndex()
        table_widget = self.tab_widget.widget(current_tab_index)

        dialog = AddContactDialog(self, [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())])
        if dialog.exec_():
            data = dialog.get_data()
            if data:
                row = table_widget.rowCount()
                table_widget.insertRow(row)
                for col, value in enumerate(data):
                    table_widget.setItem(row, col, QTableWidgetItem(value))

    def open_search_dialog(self):
        dialog = SearchDialog(self)
        if dialog.exec_():
            search_text = dialog.get_search_text()
            if search_text:
                self.search_data(search_text)

    def clear_table(self):
        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to clear the whole table?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.contact_table.clear()
            self.contact_table.setRowCount(0)
            self.contact_table.setColumnCount(0)

    def clear_table_contents(self):
        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to clear the table contents?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.contact_table.clearContents()

    def search_data(self, search_text):
        for row in range(self.contact_table.rowCount()):
            for col in range(self.contact_table.columnCount()):
                item = self.contact_table.item(row, col)
                if item is not None and search_text.lower() in item.text().lower():
                    self.contact_table.selectRow(row)
                    return

    def open_database(self, table_name="contacts"):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Database File", "", "SQLite Database Files (*.db *.sqlite);;All Files (*)", options=options)
        
        if file_name:
            try:
                # Connect to the selected database
                self.setWindowTitle("Vidwo - DataCord : " + file_name)
                conn = sqlite3.connect(file_name)
                cursor = conn.cursor()

                # Check if the table exists
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                if not cursor.fetchone():
                    QMessageBox.warning(self, "Error", f"Table '{table_name}' does not exist in the database.")
                    return

                # Fetch data from the table
                cursor.execute(f"SELECT * FROM {table_name}")
                data = cursor.fetchall()

                # Get column names
                column_names = [description[0] for description in cursor.description]

                conn.close()

                # Retrieve the currently active tab and its table widget
                current_tab_index = self.tab_widget.currentIndex()
                self.contact_table = self.tab_widget.widget(current_tab_index)
                
                # Clear existing table contents
                self.contact_table.clearContents()
                self.contact_table.setRowCount(0)

                # Set column headers
                self.contact_table.setColumnCount(len(column_names))
                self.contact_table.setHorizontalHeaderLabels(column_names)

                # Populate the table with data from the database
                for row_data in data:
                    row = self.contact_table.rowCount()
                    self.contact_table.insertRow(row)
                    for col, value in enumerate(row_data):
                        self.contact_table.setItem(row, col, QTableWidgetItem(str(value)))

            except sqlite3.Error as e:
                QMessageBox.warning(self, "Error", f"An error occurred while opening the database:\n{str(e)}")

            except Exception as ex:
                QMessageBox.warning(self, "Error", f"An unexpected error occurred:\n{str(ex)}")

class AddContactDialog(QDialog):
    def __init__(self, parent=None, header_labels=None):
        super().__init__(parent)
        self.setWindowTitle("Add Contact")
        self.setGeometry(100, 100, 500, 300)

        self.layout = QVBoxLayout()

        self.frame = QFrame()
        self.frame_layout = QVBoxLayout(self.frame)
        

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.frame)

        self.layout.addWidget(self.scroll_area)

        self.header_labels = header_labels or []

        self.create_labels_input()

        self.add_data_button = QPushButton(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\add.png"),"")
        self.add_data_button.clicked.connect(self.add_data)
        self.layout.addWidget(self.add_data_button)

        self.setLayout(self.layout)

    def create_labels_input(self):
        for label in self.header_labels:
            label_text = QLabel(label)
            line_edit = QLineEdit()
            self.frame_layout.addWidget(label_text)
            self.frame_layout.addWidget(line_edit)

    def get_data(self):
        data = []
        for i in range(1, self.frame_layout.count(), 2):  # Skip label widgets
            item = self.frame_layout.itemAt(i)
            if item and isinstance(item.widget(), QLineEdit):
                data.append(item.widget().text())
        return tuple(data)

    def add_data(self):
        data = self.get_data()
        if data:
            self.accept()



class HeaderDialog(QDialog):
    def __init__(self, parent=None, existing_labels=None):
        super().__init__(parent)
        self.setWindowTitle("Set Header Labels")
        self.setGeometry(100, 100, 500, 300)

        self.layout = QVBoxLayout()

        self.frame = QFrame()
        self.frame_layout = QVBoxLayout(self.frame)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.frame)

        self.layout.addWidget(self.scroll_area)

        self.existing_labels = existing_labels or []

        self.create_labels_input()

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("""
        QToolButton {
            border: 1px solid grey;
            border-radius: 5px;
            margin: 3px;
            font-size: 14px;
        }
        QToolButton:hover {
            border: 1px solid #820F41;
            background: #FFE6F0;
            border-radius: 5px;
            color: #820F41;
        }
        QToolButton:pressed {
            border: 2px solid #820F41;
            border-radius: 5px;
        }
        """)

        add_label_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\addleb.png"),"", self)
        add_label_action.triggered.connect(self.add_label)
        self.toolbar.addAction(add_label_action)

        delete_label_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\delleb.png"),"", self)
        delete_label_action.triggered.connect(self.delete_label)
        self.toolbar.addAction(delete_label_action)

        delete_all_labels_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\deleteall.png"),"", self)
        delete_all_labels_action.triggered.connect(self.delete_all_labels)
        self.toolbar.addAction(delete_all_labels_action)

        update_action = QAction(QtGui.QIcon("C:\\Users\\rishi\\OneDrive\\Documents\\DC_Icons\\updleb.png"),"", self)
        update_action.triggered.connect(self.handle_update_action)
        self.toolbar.addAction(update_action)

        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

    def create_labels_input(self):
        for label in self.existing_labels:
            label_input = QLineEdit(label)
            label_input.setMinimumHeight(25)  # Set minimum height for each line edit
            self.frame_layout.addWidget(label_input)

    def add_label(self):
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, QLineEdit):
            label_input = QLineEdit()
            label_input.setMinimumHeight(25)  # Set minimum height for each new line edit
            index = self.frame_layout.indexOf(focus_widget)
            if index >= 0:
                self.frame_layout.insertWidget(index + 1, label_input)

    def delete_label(self):
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, QLineEdit):
            focus_widget.deleteLater()

    def delete_all_labels(self):
        while self.frame_layout.count() > 0:
            item = self.frame_layout.takeAt(0)
            widget = item.widget()
            if widget:  # Check if the item is a widget
                widget.deleteLater()

    def get_labels(self):
        labels = []
        for i in range(self.frame_layout.count()):
            item = self.frame_layout.itemAt(i)
            if isinstance(item.widget(), QLineEdit):
                labels.append(item.widget().text())
        return labels

    def handle_update_action(self):
        new_labels = self.get_labels()
        if new_labels:
            self.accept()



class SearchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Search Contact")
        self.setGeometry(200, 200, 300, 100)

        layout = QVBoxLayout(self)

        self.search_lineedit = QLineEdit()
        layout.addWidget(self.search_lineedit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Search")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def get_search_text(self):
        return self.search_lineedit.text()


def myStyleSheet():
    return """

QLineEdit{
border-radius:5px;
background:white;
font-size:15px;
padding:2px;
}
QLineEdit:focus{
border:2px solid #820F41;
}
QLineEdit:hover{
border:2px solid #820F41;
}
    
    QMenuBar
{
margin-top:7px;
margin-left:7px;
margin-right:7px;
margin-bottom:3px;
border-radius:5px;
background: #820F41;
font-size:15px;
width:50px;
color:white;
padding:3px;
}
            QMenuBar::item {
border-radius:5px;
font-size:20px;

            }
            QMenuBar::item:selected {
            border-radius:5px;
            background-color:#5F0B30;
            }
            QMenu {
background-color: white;
                margin:4px;
                padding:4px;
                        }
            QMenu::item {
            }
            QMenu::item:selected {
                background-color: lightgrey;
                color:black;
                border-radius:5px;
            }

QMenuBar:hover{
font-size:15px bold;
}
    QMainWindow {
        background: #f5f5f5;
        color: black;
        font-size: 15px;
    }

    QTableWidget {
        background: #f5f5f5;
        border: 1px solid lightgrey;
        gridline-color: lightgrey;
        border-radius:8px;
    }

    QTableWidget::item {
        border-radius:5px;
    }

    QTableWidget::item:selected {
        background: #D1AFBE;
        border-radius:0px;
        border:1px solid #f5f5f5;
        color:black;
    }

    QHeaderView::section {
        background-color: lightgrey;
        color: black;
        padding: 1px;
        margin:1px;
        border-radius: 3px;
    }

QHeaderView::section:selected {
    background-color: lightgrey;
    color: black;
    padding: 1px;
    margin:3px;
    border-bottom:2px solid #820F41;
    border-radius: 3px;
}

    QStatusBar {
        background: #f5f5f5;
        color: black;
    }
QPushButton{
border:1px solid grey;
border-radius:5px;
padding:3px;
font-size:14px;
}
QPushButton:hover{
border:1px solid #820F41;
background:#FFE6F0;
border-radius:5px;
color:#820F41;
padding:3px;
}
QPushButton:pressed{
border:2px solid #820F41;
border-radius:5px;
padding:3px;
}
    """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.showMaximized()
    sys.exit(app.exec_())
