"""
Viewer dialog - shows full clipboard contents in a larger window.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

from config import Config
from styles import Styles


class ViewerDialog(QDialog):
    """Dialog for viewing full clipboard contents."""
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._current_text = ""
        self._current_image = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the viewer UI."""
        self.setWindowTitle("Clipboard Contents")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        self.setStyleSheet(Styles.VIEWER_STYLE)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Current Clipboard Contents")
        header.setObjectName("headerLabel")
        
        # Content container
        self.container = QWidget()
        self.container.setObjectName("viewerContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Type indicator
        self.type_label = QLabel("Empty")
        self.type_label.setObjectName("headerLabel")
        container_layout.addWidget(self.type_label)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content label
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_label = QLabel()
        self.content_label.setObjectName("contentLabel")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        content_layout.addWidget(self.content_label)
        content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        container_layout.addWidget(scroll)
        
        layout.addWidget(self.container)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self._copy_content)
        button_layout.addWidget(self.copy_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("secondaryButton")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def set_content(self, text: str = None, image: QImage = None):
        """Set the viewer content."""
        if text is not None:
            self._current_text = text
            self._current_image = None
            
            # Count lines and characters
            lines = text.count('\n') + 1
            chars = len(text)
            self.type_label.setText(f"Text • {chars:,} characters • {lines:,} lines")
            
            self.content_label.setText(text)
            self.content_label.setPixmap(QPixmap())
            
        elif image is not None:
            self._current_text = ""
            self._current_image = image
            
            w, h = image.width(), image.height()
            self.type_label.setText(f"Image • {w}×{h} pixels")
            
            # Scale image to fit viewer
            pixmap = QPixmap.fromImage(image)
            max_width = self.width() - 60
            max_height = self.height() - 150
            
            if pixmap.width() > max_width or pixmap.height() > max_height:
                scaled = pixmap.scaled(
                    max_width, max_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled = pixmap
                
            self.content_label.setText("")
            self.content_label.setPixmap(scaled)
            
    def _copy_content(self):
        """Copy current content back to clipboard."""
        clipboard = QApplication.clipboard()
        
        if self._current_image is not None:
            clipboard.setImage(self._current_image)
        elif self._current_text:
            clipboard.setText(self._current_text)
            
    def resizeEvent(self, event):
        """Handle resize to rescale images."""
        super().resizeEvent(event)
        
        # Rescale image if showing one
        if self._current_image is not None:
            self.set_content(image=self._current_image)
