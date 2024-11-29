from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLineEdit, QPushButton, QProgressBar, QTextEdit,
                           QFileDialog, QLabel, QSpinBox, QScrollArea, QStyle,
                           QStyleOptionSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread
from scraper import DocScraper
import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import QPointF

class ScraperThread(QThread):
    def __init__(self, scraper, method_to_run=None, method_args=None):
        super().__init__()
        self.scraper = scraper
        self.method_to_run = method_to_run
        self.method_args = method_args or []

    def run(self):
        if self.method_to_run:
            self.method_to_run(*self.method_args)
        else:
            self.scraper.discover_links()  # Default to discover_links if no method specified

class MaterialSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                color: #2c3e50;
                min-width: 80px;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3498db;
                border: none;
                width: 20px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #2980b9;
            }
            
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #2473a6;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create style option
        opt = QStyleOptionSpinBox()
        opt.initFrom(self)
        
        # Get button rectangles
        up_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            opt,
            QStyle.SubControl.SC_SpinBoxUp,
            self
        )
        
        down_rect = self.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            opt,
            QStyle.SubControl.SC_SpinBoxDown,
            self
        )

        # Draw arrows
        painter.setPen(QPen(QColor("white"), 2))
        
        # Up arrow
        up_center_x = up_rect.center().x()
        up_center_y = up_rect.center().y()
        painter.drawLine(up_center_x - 4, up_center_y + 2,
                        up_center_x, up_center_y - 2)
        painter.drawLine(up_center_x + 4, up_center_y + 2,
                        up_center_x, up_center_y - 2)
        
        # Down arrow
        down_center_x = down_rect.center().x()
        down_center_y = down_rect.center().y()
        painter.drawLine(down_center_x - 4, down_center_y - 2,
                        down_center_x, down_center_y + 2)
        painter.drawLine(down_center_x + 4, down_center_y - 2,
                        down_center_x, down_center_y + 2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Scraper")
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # URL input section
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to scrape...")
        url_layout.addWidget(self.url_input)
        
        # Thread control with better layout
        thread_layout = QHBoxLayout()
        thread_layout.setSpacing(10)
        
        thread_label = QLabel("Threads:")
        thread_label.setMinimumWidth(60)
        
        self.thread_spinner = MaterialSpinBox()
        self.thread_spinner.setRange(1, 10)
        self.thread_spinner.setValue(5)
        self.thread_spinner.setToolTip("Number of concurrent threads to use for scraping")
        self.thread_spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thread_spinner.setSuffix(" threads")
        
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_spinner)
        thread_layout.addStretch()
        
        # Add discover button
        self.discover_button = QPushButton("Discover Links")
        self.discover_button.clicked.connect(self.discover_links)
        thread_layout.addWidget(self.discover_button)
        
        # Add layouts to main layout
        main_layout.addLayout(url_layout)
        main_layout.addLayout(thread_layout)
        
        # Progress bar (moved here)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v/%m)")
        self.progress_bar.hide()  # Hidden by default
        main_layout.addWidget(self.progress_bar)
        
        # Scroll area for checkboxes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)
        
        # Container for checkboxes
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.scroll_area.setWidget(self.checkbox_container)
        
        # Select/Deselect buttons
        self.select_buttons_widget = QWidget()
        select_buttons_layout = QHBoxLayout(self.select_buttons_widget)
        select_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all)
        
        select_buttons_layout.addWidget(self.select_all_button)
        select_buttons_layout.addWidget(self.deselect_all_button)
        select_buttons_layout.addStretch()
        
        # Start button
        self.start_button = QPushButton("Start Scraping Selected")
        self.start_button.clicked.connect(self.start_scraping)
        self.start_button.hide()
        select_buttons_layout.addWidget(self.start_button)
        
        # Add selection controls and scroll area
        main_layout.addWidget(self.select_buttons_widget)
        main_layout.addWidget(self.scroll_area)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(100)
        main_layout.addWidget(self.log_output)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize scraper
        self.scraper = None
        self.scraper_thread = None
        self.checkboxes = []

    def discover_links(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_message("Please enter a URL")
            return
            
        self.discover_button.setEnabled(False)
        self.url_input.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        
        # Initialize scraper
        self.scraper = DocScraper(url, self.thread_spinner.value())
        
        # Connect signals
        self.scraper.status_updated.connect(self.log_message)
        self.scraper.error_occurred.connect(self.log_message)
        self.scraper.links_discovered.connect(self.show_link_selection)
        
        # Start discovery in separate thread
        self.scraper_thread = ScraperThread(self.scraper)  # Uses default discover_links
        self.scraper_thread.start()

    def show_link_selection(self, links):
        # Clear previous checkboxes
        for checkbox in self.checkboxes:
            self.checkbox_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.checkboxes.clear()
        
        # Add new checkboxes
        for link in sorted(links):
            checkbox = QCheckBox(link)
            checkbox.setChecked(True)
            self.checkboxes.append(checkbox)
            self.checkbox_layout.addWidget(checkbox)
        
        # Show selection UI
        self.scroll_area.show()
        self.select_buttons_widget.show()
        self.start_button.show()
        self.discover_button.hide()
        
        self.discover_button.setEnabled(True)
        self.url_input.setEnabled(True)
        self.statusBar().showMessage("Select links to scrape")

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def start_scraping(self):
        selected_urls = [
            checkbox.text()
            for checkbox in self.checkboxes
            if checkbox.isChecked()
        ]
        
        if not selected_urls:
            self.log_message("Please select at least one URL to scrape")
            return
            
        self.start_button.setEnabled(False)
        self.scroll_area.setEnabled(False)
        self.select_buttons_widget.setEnabled(False)
        
        # Connect remaining signals
        self.scraper.progress_updated.connect(self.update_progress)
        self.scraper.scraping_completed.connect(self.handle_completion)
        
        # Start scraping in separate thread
        self.scraper_thread = ScraperThread(
            self.scraper,
            method_to_run=self.scraper.scrape_selected,
            method_args=[selected_urls]
        )
        self.scraper_thread.finished.connect(self.scraping_finished)
        self.scraper_thread.start()

    def update_progress(self, current, total):
        percentage = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(percentage)
        self.statusBar().showMessage(f"Processing: {current}/{total} pages")

    def log_message(self, message):
        self.log_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def handle_completion(self, content):
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"scrape_{timestamp}"
        
        # Save JSON
        json_path = output_dir / f"{base_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        # Save TXT
        txt_path = output_dir / f"{base_name}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            for item in content:
                f.write(f"Title: {item['title']}\n")
                f.write(f"URL: {item['url']}\n\n")
                f.write(item['content'])
                f.write("\n\n" + "=" * 80 + "\n\n")
        
        self.log_message(f"Files saved:\n{json_path}\n{txt_path}")

    def scraping_finished(self):
        self.start_button.setEnabled(True)
        self.scroll_area.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.deselect_all_button.setEnabled(True)
        self.discover_button.show()
        self.statusBar().showMessage("Scraping completed")

    def update_thread_label(self, value):
        """Update the thread count when spinner value changes"""
        self.thread_spinner.setSuffix(f" thread{'s' if value > 1 else ''}")
        self.log_message(f"Thread count set to {value}") 