"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

from napari.utils.notifications import show_info
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from tiled.client import from_uri


class TiledBrowser(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.catalog = None
        self._current_page = 0  # Keep track of where in the catalog we are

        # Connection elements
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Enter a url")
        self.connect_button = QPushButton("Connect")
        self.connection_label = QLabel("No url connected")
        self.connection_widget = QWidget()

        # Connection layout
        connection_layout = QVBoxLayout()
        connection_layout.addWidget(self.url_entry)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.connection_label)
        connection_layout.addStretch()
        self.connection_widget.setLayout(connection_layout)

        # Navigation elements
        self.rows_per_page_label = QLabel("Rows per page: ")
        self.rows_per_page_selector = QComboBox()
        self.rows_per_page_selector.addItems(["5", "10"])
        self.rows_per_page_selector.setCurrentIndex(0)

        self.current_location_label = QLabel()
        self.previous_page = ClickableQLabel("<")
        self.next_page = ClickableQLabel(">")
        self.navigation_widget = QWidget()

        self._rows_per_page = int(self.rows_per_page_selector.currentText())

        # Navigation layout
        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.rows_per_page_label)
        navigation_layout.addWidget(self.rows_per_page_selector)
        navigation_layout.addWidget(self.current_location_label)
        navigation_layout.addWidget(self.previous_page)
        navigation_layout.addWidget(self.next_page)
        self.navigation_widget.setLayout(navigation_layout)

        # Catalog table elements
        self.catalog_table = QTableWidget(0, 1)
        self.catalog_table.setHorizontalHeaderLabels(["ID"])
        self._create_table_rows()
        self.catalog_table_widget = QWidget()

        # Catalog table layout
        catalog_table_layout = QVBoxLayout()
        catalog_table_layout.addWidget(self.catalog_table)
        catalog_table_layout.addWidget(self.navigation_widget)
        self.catalog_table_widget.setLayout(catalog_table_layout)
        self.catalog_table_widget.setVisible(False)

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Orientation.Vertical)

        self.splitter.addWidget(self.connection_widget)
        self.splitter.addWidget(self.catalog_table_widget)

        self.splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        self.connect_button.clicked.connect(self._on_connect_clicked)
        self.previous_page.clicked.connect(self._on_prev_page_clicked)
        self.next_page.clicked.connect(self._on_next_page_clicked)

        self.rows_per_page_selector.currentTextChanged.connect(
            self._on_rows_per_page_changed
        )

    # def _on_connect_clicked(self):
    #     url = self.url_entry.displayText()
    #     if not url:
    #         show_info("Please specify a url.")
    #         return
    #     try:
    #         self.catalog = from_uri(url)
    #     except Exception:
    #         show_info("Could not connect. Please check the url.")
    #         return
    #     self.connection_label.setText(f"Connected to {url}")
    #     self.catalog_table_widget.setVisible(True)
    #     self._set_current_location_label()
    #     self._populate_table()

    def _on_connect_clicked(self):
        url = self.url_entry.displayText()
        # url = "https://tiled-demo.blueskyproject.io/api"
        if not url:
            show_info("Please specify a url.")
            return
        try:
            # self.catalog = from_uri(url)["bmm"]["raw"]  # .keys()[:13]
            self.catalog = from_uri(url)
        except Exception:
            show_info("Could not connect. Please check the url.")
            return

        print(f"{self.catalog = }")
        self.connection_label.setText(f"Connected to {url}")
        self.catalog_table_widget.setVisible(True)
        self._set_current_location_label()
        self._populate_table()

    def _on_rows_per_page_changed(self, value):
        self._rows_per_page = int(value)
        self._create_table_rows()
        self._populate_table()
        self._set_current_location_label()

    def _create_table_rows(self):
        # Remove all rows first
        while self.catalog_table.rowCount() > 0:
            self.catalog_table.removeRow(0)
        # Then add new rows
        for row in range(self._rows_per_page):
            last_row_position = self.catalog_table.rowCount()
            self.catalog_table.insertRow(last_row_position)

    def _populate_table(self):
        print(f"{self.catalog_table.rowCount() = }")
        for row_index in range(self.catalog_table.rowCount()):
            node_index = self._rows_per_page * self._current_page + row_index
            print(f"{node_index = }")
            if node_index < len(self.catalog):
                if isinstance(self.catalog, list):
                    node = self.catalog[node_index]
                else:
                    # Node, CatalogOfBlueskyRuns, etc.
                    node = self.catalog.keys()[node_index]
            else:
                node = ""
            self.catalog_table.setItem(row_index, 0, QTableWidgetItem(node))

    def _on_prev_page_clicked(self):
        if self._current_page != 0:
            self._current_page -= 1
            self._populate_table()
            self._set_current_location_label()

    def _on_next_page_clicked(self):
        if (
            self._current_page * self._rows_per_page
        ) + self._rows_per_page < len(self.catalog):
            self._current_page += 1
            self._populate_table()
            self._set_current_location_label()

    def _set_current_location_label(self):
        starting_index = self._current_page * self._rows_per_page + 1
        ending_index = min(
            self._rows_per_page * (self._current_page + 1), len(self.catalog)
        )
        current_location_text = (
            f"{starting_index}-{ending_index} of {len(self.catalog)}"
        )
        self.current_location_label.setText(current_location_text)


class ClickableQLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()


# TODO: handle changing the location label/current_page when on last page and
# increasing rows per page
