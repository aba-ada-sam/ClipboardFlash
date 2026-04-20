"""
Main application controller - ties together all components.
"""

import logging
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject

logger = logging.getLogger("ClipboardFlash")

from clipboard_monitor import ClipboardMonitor
from tray_icon import TrayIcon
from popup_widget import PopupWidget
from viewer_dialog import ViewerDialog
from settings_dialog import SettingsDialog
from config import Config


class ClipboardFlashApp(QObject):
    """Main application controller."""

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.config = Config()

        # Create components
        self.popup = PopupWidget(self.config)
        self.viewer = ViewerDialog(self.config)
        self.settings_dialog = SettingsDialog(self.config)
        self.tray = TrayIcon(self.config)
        self.monitor = ClipboardMonitor(app.clipboard())

        # Connect signals
        self.monitor.text_copied.connect(self.on_text_copied)
        self.monitor.image_copied.connect(self.on_image_copied)
        self.monitor.status_changed.connect(self.tray.update_status)

        self.tray.show_viewer_requested.connect(self.show_viewer)
        self.tray.show_settings_requested.connect(self.show_settings)
        self.tray.exit_requested.connect(self.quit)
        
        self.settings_dialog.settings_changed.connect(self.on_settings_changed)
        
    def start(self):
        """Start the application."""
        logger.info("ClipboardFlashApp.start() called")
        self.tray.show()
        self.monitor.start()
        logger.info("All components started successfully")

    def on_text_copied(self, text: str):
        """Handle text copied to clipboard."""
        logger.info("on_text_copied: %d chars, show_popup=%s",
                     len(text), self.config.get("show_text_popup", True))
        if self.config.get("show_text_popup", True):
            self.popup.show_text(text)
        self.viewer.set_content(text=text)

    def on_image_copied(self, image):
        """Handle image copied to clipboard."""
        logger.info("on_image_copied: %dx%d, show_popup=%s",
                     image.width(), image.height(),
                     self.config.get("show_image_popup", True))
        if self.config.get("show_image_popup", True):
            self.popup.show_image(image)
        self.viewer.set_content(image=image)
        
    def show_viewer(self):
        """Show the clipboard viewer dialog."""
        self.viewer.show()
        self.viewer.raise_()
        self.viewer.activateWindow()
        
    def show_settings(self):
        """Show the settings dialog."""
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
        
    def on_settings_changed(self):
        """Handle settings changes."""
        self.popup.update_config()
        
    def quit(self):
        """Quit the application."""
        self.monitor.stop()
        self.tray.hide()
        
        # Close any open dialogs
        self.viewer.close()
        self.settings_dialog.close()
        self.popup.close()
        
        # Force quit
        self.app.quit()
        sys.exit(0)
