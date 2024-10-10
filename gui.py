from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QProgressBar, QTextEdit, QLabel, 
                             QLineEdit, QFrame, QScrollArea, QDesktopWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QFont, QIcon, QFontDatabase
from workers import SortByLocThread, FlattenFolderThread, SortByTimeThread

class ModernButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(150)
        
        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding-left: 15px;
                padding-right: 40px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton::icon {
                position: absolute;
                left: 15px;  /* Position of the icon */
            }
        """)

class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 20px;
            }
        """)

class MediaGPSExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PinPoint')
        self.setWindowIcon(QIcon('assets/icons/app_icon.png'))
        self.setGeometry(100, 100, 800, 500)
        self.center()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        content_card = CardWidget()
        card_layout = QVBoxLayout(content_card)

        header = QLabel("PinPoint")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 28px;
            color: #ecf0f1;
            margin-bottom: 20px;
            font-weight: bold;
        """)
        card_layout.addWidget(header)

        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder")
        folder_layout.addWidget(self.folder_input)
        
        # Browse Folder button
        browse_button = ModernButton('Browse', 'assets/icons/folder_icon.png')
        browse_button.clicked.connect(self.browse_folder)
        browse_button.setToolTip("Select a folder containing files")
        folder_layout.addWidget(browse_button)
        
        card_layout.addLayout(folder_layout)

        button_layout = QHBoxLayout()

        # Location Sort button
        location_button = ModernButton('Location Sort', 'assets/icons/play_icon.png')
        location_button.clicked.connect(self.sort_by_loc)
        location_button.setToolTip("Sort files by place taken")
        button_layout.addWidget(location_button)

        # Time Sort button
        time_button = ModernButton('Time Sort', 'assets/icons/clock_icon.png')
        time_button.clicked.connect(self.sort_by_time)
        time_button.setToolTip("Sort files by creation time")
        button_layout.addWidget(time_button)

        # Flatten Folder button
        flatten_button = ModernButton('Flatten Folder', 'assets/icons/flatten_icon.png')
        flatten_button.clicked.connect(self.flatten_folder)
        flatten_button.setToolTip("Flatten the selected folder")
        button_layout.addWidget(flatten_button)

        card_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #465c71;
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 5px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #bdc3c7; margin-top: 5px;")
        card_layout.addWidget(self.status_label)

        output_scroll = QScrollArea()
        output_scroll.setWidgetResizable(True)
        output_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #34495e;
            }
        """)
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont('Inter', 12))
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: none;
                padding: 10px;
            }
        """)
        output_scroll.setWidget(self.output_area)
        card_layout.addWidget(output_scroll)

        main_layout.addWidget(content_card)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #34495e;
            }
            QLineEdit {
                background-color: #465c71;
                color: #ecf0f1;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QToolTip {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 5px;
            }
        """)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.folder_input.setText(folder)

    def sort_by_loc(self):
        folder_path = self.folder_input.text()
        if not folder_path:
            self.show_error("Please select a folder")
            return

        self.output_area.clear()
        self.output_area.append("Sorting files...")
        self.status_label.setText("Sorting")
        self.status_label.setStyleSheet("color: #f39c12; margin-top: 5px;")

        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(1000)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(0)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.progress_animation.start()

        self.worker = SortByLocThread(folder_path)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_output.connect(self.update_output)
        self.worker.finished.connect(self.sort_loc_finished)
        self.worker.start()

    def flatten_folder(self):
        folder_path = self.folder_input.text()
        if not folder_path:
            self.show_error("Please select a folder")
            return

        self.output_area.clear()
        self.output_area.append("Flattening folder...")
        self.status_label.setText("Flattening")
        self.status_label.setStyleSheet("color: #f39c12; margin-top: 5px;")

        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(1000)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(0)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.progress_animation.start()

        self.flatten_worker = FlattenFolderThread(folder_path)
        self.flatten_worker.update_progress.connect(self.update_progress)
        self.flatten_worker.update_output.connect(self.update_output)
        self.flatten_worker.finished.connect(self.flatten_finished)
        self.flatten_worker.start()

    def sort_by_time(self):
        folder_path = self.folder_input.text()
        if not folder_path:
            self.show_error("Please select a folder")
            return

        self.output_area.clear()
        self.output_area.append("Sorting files...")
        self.status_label.setText("Sorting")
        self.status_label.setStyleSheet("color: #f39c12; margin-top: 5px;")

        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(1000)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(0)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.progress_animation.start()

        self.sort_time_worker = SortByTimeThread(folder_path)
        self.sort_time_worker.update_progress.connect(self.update_progress)
        self.sort_time_worker.update_output.connect(self.update_output)
        self.sort_time_worker.finished.connect(self.sort_time_finished)
        self.sort_time_worker.start()

    def update_progress(self, value):
        self.progress_animation.setEndValue(value)
        self.progress_animation.start()

    def update_output(self, message):
        self.output_area.append(message)

    def sort_loc_finished(self):
        self.output_area.append("Sorting completed")
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: #2ecc71; margin-top: 5px;")

    def flatten_finished(self):
        self.output_area.append("Flattening completed")
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: #2ecc71; margin-top: 5px;")

    def sort_time_finished(self):
        self.output_area.append("Sorting completed")
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("color: #2ecc71; margin-top: 5px;")

    def show_error(self, message):
        self.output_area.append(f"<span style='color: #e74c3c;'>{message}</span>")