STYLE_SHEET = """
QMainWindow {
    background-color: #ffffff;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #2c3e50;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 20px;
    border-radius: 6px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2473a6;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}

QLineEdit {
    padding: 8px 12px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    background-color: white;
    color: #2c3e50;
    selection-background-color: #3498db;
}

QLineEdit:focus {
    border-color: #3498db;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    text-align: center;
    background-color: #f0f0f0;
    color: #2c3e50;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #2ecc71;
    border-radius: 4px;
}

QStatusBar {
    background-color: #f8f9fa;
    color: #2c3e50;
    padding: 4px;
}

QTextEdit {
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    background-color: white;
    color: #2c3e50;
    padding: 8px;
    selection-background-color: #3498db;
}

QLabel {
    color: #2c3e50;
}

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
    border-radius: 3px;
    margin: 2px;
    min-width: 20px;
    subcontrol-origin: border;
}

QSpinBox::up-button {
    subcontrol-position: top right;
}

QSpinBox::down-button {
    subcontrol-position: bottom right;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #2980b9;
}

QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
    background-color: #2473a6;
}

/* Material Design Arrows using Unicode characters */
QSpinBox::up-arrow {
    image: none;
    width: 10px;
    height: 10px;
}

QSpinBox::up-arrow:after {
    content: "⌃";
    color: white;
    font-size: 16px;
    font-weight: bold;
    position: absolute;
}

QSpinBox::down-arrow {
    image: none;
    width: 10px;
    height: 10px;
}

QSpinBox::down-arrow:after {
    content: "⌄";
    color: white;
    font-size: 16px;
    font-weight: bold;
    position: absolute;
}

/* Remove the default arrow buttons */
QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off,
QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off {
    image: none;
}

QScrollArea {
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    background-color: white;
}

QScrollArea QWidget {
    background-color: white;
}

QCheckBox {
    spacing: 8px;
    color: #2c3e50;
    background-color: transparent;
    padding: 2px 4px;
    margin: 0px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    margin-right: 4px;
}

QScrollBar:vertical {
    border: none;
    background-color: #f0f0f0;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
    width: 8px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollArea QScrollBar:vertical {
    width: 12px;
}

QScrollArea QScrollBar:vertical {
    background: transparent;
}
""" 