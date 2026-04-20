"""
Splash screen shown on application startup.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon


def get_resource_path(filename):
    """Get path to resource, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source
        base_path = Path(__file__).parent
    return base_path / filename


class SplashScreen(QWidget):
    """Splash screen displayed on startup."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the splash screen UI."""
        # Window flags for frameless, centered popup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Fixed size
        self.setFixedSize(350, 200)
        
        # Center on screen
        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2
            )
        
        # Main container
        container = QWidget(self)
        container.setFixedSize(350, 200)
        container.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                border: 2px solid #7c3aed;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel()
        icon_path = get_resource_path("icon.png")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            scaled = pixmap.scaled(
                48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(scaled)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title = QLabel("Hello!")
        title.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            background: transparent;
            border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Message
        message = QLabel("Clipboard Flash is running\nin the system tray")
        message.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
            color: #a0a0a0;
            background: transparent;
            border: none;
        """)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        layout.addStretch()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
