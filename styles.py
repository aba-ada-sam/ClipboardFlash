"""
Application styles and themes.
"""


class Styles:
    """Application stylesheets."""
    
    # Colors
    DARK_BG = "#1e1e2e"
    DARK_SURFACE = "#2a2a3e"
    DARK_BORDER = "#3a3a4e"
    DARK_TEXT = "#e0e0e0"
    DARK_TEXT_DIM = "#a0a0a0"
    ACCENT = "#7c3aed"
    ACCENT_HOVER = "#8b5cf6"
    
    POPUP_STYLE = """
        #popupContainer {
            background-color: rgba(30, 30, 46, 0.98);
            border: 1px solid rgba(124, 58, 237, 0.5);
            border-radius: 8px;
        }
        
        #popupContent {
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            padding: 0;
        }
    """
    
    DIALOG_STYLE = """
        QDialog {
            background-color: #1e1e2e;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
        }
        
        QLabel {
            color: #e0e0e0;
            font-size: 12px;
        }
        
        QLabel#titleLabel {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px 0;
        }
        
        QLabel#sectionLabel {
            font-size: 13px;
            font-weight: 600;
            color: #a0a0a0;
            padding-top: 10px;
        }
        
        QPushButton {
            background-color: #7c3aed;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #8b5cf6;
        }
        
        QPushButton:pressed {
            background-color: #6d28d9;
        }
        
        QPushButton#secondaryButton {
            background-color: #3a3a4e;
        }
        
        QPushButton#secondaryButton:hover {
            background-color: #4a4a5e;
        }
        
        QSpinBox, QDoubleSpinBox {
            background-color: #2a2a3e;
            color: #ffffff;
            border: 1px solid #3a3a4e;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 13px;
            min-height: 20px;
        }
        
        QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #7c3aed;
        }
        
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
            background-color: #3a3a4e;
            border: none;
            width: 16px;
            subcontrol-origin: border;
        }
        
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #a0a0a0;
            width: 0;
            height: 0;
        }
        
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #a0a0a0;
            width: 0;
            height: 0;
        }
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover,
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #4a4a5e;
        }
        
        QCheckBox {
            color: #e0e0e0;
            font-size: 12px;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid #3a3a4e;
            background-color: #2a2a3e;
        }
        
        QCheckBox::indicator:checked {
            background-color: #7c3aed;
            border-color: #7c3aed;
        }
        
        QCheckBox::indicator:hover {
            border-color: #7c3aed;
        }
        
        QSlider::groove:horizontal {
            height: 6px;
            background-color: #3a3a4e;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background-color: #7c3aed;
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background-color: #8b5cf6;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: #2a2a3e;
            width: 10px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4a4a5e;
            border-radius: 5px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #5a5a6e;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
    """
    
    VIEWER_STYLE = """
        QDialog {
            background-color: #1e1e2e;
        }
        
        #viewerContainer {
            background-color: #2a2a3e;
            border: 1px solid #3a3a4e;
            border-radius: 8px;
        }
        
        #contentLabel {
            color: #e0e0e0;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            padding: 15px;
        }
        
        #headerLabel {
            color: #a0a0a0;
            font-size: 11px;
            padding: 10px 15px;
            background-color: #252535;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        
        QPushButton {
            background-color: #7c3aed;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #8b5cf6;
        }
    """
    
    TRAY_MENU_STYLE = """
        QMenu {
            background-color: #2a2a3e;
            color: #e0e0e0;
            border: 1px solid #3a3a4e;
            border-radius: 8px;
            padding: 5px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
        }
        
        QMenu::item {
            padding: 8px 30px 8px 15px;
            border-radius: 4px;
        }
        
        QMenu::item:selected {
            background-color: #7c3aed;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #3a3a4e;
            margin: 5px 10px;
        }
    """
