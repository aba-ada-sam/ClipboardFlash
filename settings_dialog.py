"""
Settings dialog - configure popup behavior, appearance, and startup.
"""

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QDoubleSpinBox, QCheckBox,
    QWidget, QScrollArea, QFrame, QColorDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from config import Config
from styles import Styles


class ColorButton(QPushButton):
    """Button that displays a color and opens color picker on click."""
    
    color_changed = pyqtSignal(str)
    
    def __init__(self, color: str = "#ffffff"):
        super().__init__()
        self._color = color
        self.setFixedSize(60, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._pick_color)
        self._update_style()
        
    def _update_style(self):
        """Update button appearance to show current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #3a3a4e;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #7c3aed;
            }}
        """)
        
    def _pick_color(self):
        """Open color dialog."""
        color = QColorDialog.getColor(
            QColor(self._color),
            self,
            "Select Color"
        )
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)
            
    def get_color(self) -> str:
        """Get current color as hex string."""
        return self._color
        
    def set_color(self, color: str):
        """Set color from hex string."""
        self._color = color
        self._update_style()


class SettingsDialog(QDialog):
    """Settings configuration dialog."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """Set up the settings UI."""
        self.setWindowTitle("Clipboard Flash Settings")
        self.setMinimumWidth(450)
        self.setStyleSheet(Styles.DIALOG_STYLE)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title = QLabel("Settings")
        title.setObjectName("titleLabel")
        main_layout.addWidget(title)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        scroll_layout.setSpacing(20)
        
        # Popup Settings Section
        popup_section = self._create_section("Popup Behavior")
        popup_layout = popup_section.layout()
        
        # Duration
        duration_row = self._create_setting_row(
            "Display Duration",
            "How long the popup stays visible (milliseconds)"
        )
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(200, 10000)
        self.duration_spin.setSingleStep(100)
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setFixedWidth(100)
        self.duration_spin.setFixedHeight(32)
        duration_row.layout().addWidget(self.duration_spin)
        popup_layout.addWidget(duration_row)
        
        # Fade duration
        fade_row = self._create_setting_row(
            "Fade Duration",
            "Animation speed for fade in/out (milliseconds)"
        )
        self.fade_spin = QSpinBox()
        self.fade_spin.setRange(0, 1000)
        self.fade_spin.setSingleStep(25)
        self.fade_spin.setSuffix(" ms")
        self.fade_spin.setFixedWidth(100)
        self.fade_spin.setFixedHeight(32)
        fade_row.layout().addWidget(self.fade_spin)
        popup_layout.addWidget(fade_row)
        
        # Opacity
        opacity_row = self._create_setting_row(
            "Popup Opacity",
            "Transparency level of the popup"
        )
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setSingleStep(0.05)
        self.opacity_spin.setDecimals(2)
        self.opacity_spin.setFixedWidth(100)
        self.opacity_spin.setFixedHeight(32)
        opacity_row.layout().addWidget(self.opacity_spin)
        popup_layout.addWidget(opacity_row)
        
        scroll_layout.addWidget(popup_section)
        
        # Size & Position Section
        size_section = self._create_section("Size & Position")
        size_layout = size_section.layout()
        
        # Max width
        width_row = self._create_setting_row(
            "Maximum Width",
            "Maximum popup width in pixels"
        )
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 1000)
        self.width_spin.setSingleStep(25)
        self.width_spin.setSuffix(" px")
        self.width_spin.setFixedWidth(100)
        self.width_spin.setFixedHeight(32)
        width_row.layout().addWidget(self.width_spin)
        size_layout.addWidget(width_row)
        
        # Max height
        height_row = self._create_setting_row(
            "Maximum Height",
            "Maximum popup height in pixels"
        )
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 800)
        self.height_spin.setSingleStep(25)
        self.height_spin.setSuffix(" px")
        self.height_spin.setFixedWidth(100)
        self.height_spin.setFixedHeight(32)
        height_row.layout().addWidget(self.height_spin)
        size_layout.addWidget(height_row)
        
        # Cursor offset X
        offset_x_row = self._create_setting_row(
            "Horizontal Offset",
            "Distance from cursor (pixels)"
        )
        self.offset_x_spin = QSpinBox()
        self.offset_x_spin.setRange(-100, 200)
        self.offset_x_spin.setSingleStep(5)
        self.offset_x_spin.setSuffix(" px")
        self.offset_x_spin.setFixedWidth(100)
        self.offset_x_spin.setFixedHeight(32)
        offset_x_row.layout().addWidget(self.offset_x_spin)
        size_layout.addWidget(offset_x_row)
        
        # Cursor offset Y
        offset_y_row = self._create_setting_row(
            "Vertical Offset",
            "Distance from cursor (pixels)"
        )
        self.offset_y_spin = QSpinBox()
        self.offset_y_spin.setRange(-100, 200)
        self.offset_y_spin.setSingleStep(5)
        self.offset_y_spin.setSuffix(" px")
        self.offset_y_spin.setFixedWidth(100)
        self.offset_y_spin.setFixedHeight(32)
        offset_y_row.layout().addWidget(self.offset_y_spin)
        size_layout.addWidget(offset_y_row)
        
        scroll_layout.addWidget(size_section)
        
        # Content Section
        content_section = self._create_section("Content")
        content_layout = content_section.layout()
        
        # Text preview length
        preview_row = self._create_setting_row(
            "Text Preview Length",
            "Maximum characters to show in popup"
        )
        self.preview_spin = QSpinBox()
        self.preview_spin.setRange(50, 2000)
        self.preview_spin.setSingleStep(50)
        self.preview_spin.setFixedWidth(100)
        self.preview_spin.setFixedHeight(32)
        preview_row.layout().addWidget(self.preview_spin)
        content_layout.addWidget(preview_row)
        
        # Show text popup
        self.show_text_check = QCheckBox("Show popup for text content")
        content_layout.addWidget(self.show_text_check)
        
        # Show image popup
        self.show_image_check = QCheckBox("Show popup for image content")
        content_layout.addWidget(self.show_image_check)
        
        scroll_layout.addWidget(content_section)
        
        # Appearance Section
        appearance_section = self._create_section("Appearance")
        appearance_layout = appearance_section.layout()
        
        # Background color
        bg_color_row = self._create_setting_row(
            "Background Color",
            "Popup background color"
        )
        self.bg_color_btn = ColorButton()
        bg_color_row.layout().addWidget(self.bg_color_btn)
        appearance_layout.addWidget(bg_color_row)
        
        # Border color
        border_color_row = self._create_setting_row(
            "Border Color",
            "Popup border color"
        )
        self.border_color_btn = ColorButton()
        border_color_row.layout().addWidget(self.border_color_btn)
        appearance_layout.addWidget(border_color_row)
        
        # Text color
        text_color_row = self._create_setting_row(
            "Text Color",
            "Popup text color"
        )
        self.text_color_btn = ColorButton()
        text_color_row.layout().addWidget(self.text_color_btn)
        appearance_layout.addWidget(text_color_row)
        
        # Border width
        border_width_row = self._create_setting_row(
            "Border Width",
            "Popup border thickness in pixels"
        )
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(0, 10)
        self.border_width_spin.setSingleStep(1)
        self.border_width_spin.setSuffix(" px")
        self.border_width_spin.setFixedWidth(100)
        self.border_width_spin.setFixedHeight(32)
        border_width_row.layout().addWidget(self.border_width_spin)
        appearance_layout.addWidget(border_width_row)
        
        scroll_layout.addWidget(appearance_section)
        
        # System Section
        system_section = self._create_section("System")
        system_layout = system_section.layout()
        
        # Run on startup
        self.startup_check = QCheckBox("Run on Windows startup")
        self.startup_check.toggled.connect(self._on_startup_toggled)
        system_layout.addWidget(self.startup_check)
        
        scroll_layout.addWidget(system_section)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self._reset_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
        
    def _create_section(self, title: str) -> QWidget:
        """Create a settings section with title."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        label = QLabel(title)
        label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #b0b0c0;
            padding-top: 10px;
        """)
        layout.addWidget(label)
        
        return section
        
    def _create_setting_row(self, title: str, description: str) -> QWidget:
        """Create a setting row with label and description."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 500;
            background: transparent;
        """)
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            color: #a0a0b0;
            font-size: 11px;
            background: transparent;
        """)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return row
        
    def _load_settings(self):
        """Load current settings into controls."""
        self.duration_spin.setValue(self.config.get("popup_duration", 1000))
        self.fade_spin.setValue(self.config.get("fade_duration", 150))
        self.opacity_spin.setValue(self.config.get("popup_opacity", 0.95))
        self.width_spin.setValue(self.config.get("popup_max_width", 400))
        self.height_spin.setValue(self.config.get("popup_max_height", 300))
        self.offset_x_spin.setValue(self.config.get("cursor_offset_x", 20))
        self.offset_y_spin.setValue(self.config.get("cursor_offset_y", 20))
        self.preview_spin.setValue(self.config.get("text_preview_length", 500))
        self.show_text_check.setChecked(self.config.get("show_text_popup", True))
        self.show_image_check.setChecked(self.config.get("show_image_popup", True))
        self.startup_check.setChecked(self._check_startup_enabled())
        # Appearance
        self.bg_color_btn.set_color(self.config.get("popup_bg_color", "#1e1e2e"))
        self.border_color_btn.set_color(self.config.get("popup_border_color", "#7c3aed"))
        self.text_color_btn.set_color(self.config.get("popup_text_color", "#e0e0e0"))
        self.border_width_spin.setValue(self.config.get("popup_border_width", 1))
        
    def _save_settings(self):
        """Save settings and close dialog."""
        self.config.set("popup_duration", self.duration_spin.value())
        self.config.set("fade_duration", self.fade_spin.value())
        self.config.set("popup_opacity", self.opacity_spin.value())
        self.config.set("popup_max_width", self.width_spin.value())
        self.config.set("popup_max_height", self.height_spin.value())
        self.config.set("cursor_offset_x", self.offset_x_spin.value())
        self.config.set("cursor_offset_y", self.offset_y_spin.value())
        self.config.set("text_preview_length", self.preview_spin.value())
        self.config.set("show_text_popup", self.show_text_check.isChecked())
        self.config.set("show_image_popup", self.show_image_check.isChecked())
        # Appearance
        self.config.set("popup_bg_color", self.bg_color_btn.get_color())
        self.config.set("popup_border_color", self.border_color_btn.get_color())
        self.config.set("popup_text_color", self.text_color_btn.get_color())
        self.config.set("popup_border_width", self.border_width_spin.value())
        
        self.config.save()
        self.settings_changed.emit()
        self.close()
        
    def _reset_defaults(self):
        """Reset all settings to defaults."""
        self.config.reset_to_defaults()
        self._load_settings()
        
    def _on_startup_toggled(self, checked: bool):
        """Handle startup checkbox toggle."""
        if checked:
            self._enable_startup()
        else:
            self._disable_startup()
            
    def _get_startup_path(self) -> Path:
        """Get the Windows startup folder shortcut path."""
        startup_folder = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        return startup_folder / "ClipboardFlash.lnk"
        
    def _check_startup_enabled(self) -> bool:
        """Check if startup is enabled."""
        return self._get_startup_path().exists()
        
    def _enable_startup(self):
        """Enable run on startup using PowerShell (no extra dependencies)."""
        import subprocess

        startup_path = str(self._get_startup_path())
        working_dir = str(Path(__file__).parent)

        if getattr(sys, 'frozen', False):
            target = sys.executable
            arguments = ""
        else:
            # Always use pythonw (no console) with launch.pyw
            target = str(Path(sys.executable).parent / "pythonw.exe")
            arguments = f'"{Path(__file__).parent / "launch.pyw"}"'

        # Use PowerShell to create the .lnk — always available on Windows
        ps_script = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{startup_path}'); "
            f"$s.TargetPath = '{target}'; "
            f"$s.Arguments = '{arguments}'; "
            f"$s.WorkingDirectory = '{working_dir}'; "
            "$s.Description = 'Clipboard Flash'; "
            "$s.Save()"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, timeout=10,
            )
        except Exception:
            # Last-resort fallback: .bat file
            bat_path = self._get_startup_path().with_suffix('.bat')
            script_path = Path(__file__).parent / "main.py"
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\n')
                f.write(f'pythonw "{script_path}"\n')
                
    def _disable_startup(self):
        """Disable run on startup."""
        # Try both .lnk and .bat
        for suffix in ['.lnk', '.bat']:
            path = self._get_startup_path().with_suffix(suffix)
            if path.exists():
                try:
                    path.unlink()
                except:
                    pass
