"""
System tray icon with context menu and live status diagnostics.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal

from config import Config
from styles import Styles


def get_resource_path(filename):
    """Get path to resource, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return base_path / filename


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu and live status."""

    show_viewer_requested = pyqtSignal()
    show_settings_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._last_status = {}
        self._setup_icon()
        self._setup_menu()
        self._connect_signals()

    def _setup_icon(self):
        """Load and set the tray icon."""
        icon_path = get_resource_path("icon.ico")
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            png_path = get_resource_path("icon.png")
            if png_path.exists():
                self.setIcon(QIcon(str(png_path)))

        self.setToolTip("Clipboard Flash — starting…")

    def _setup_menu(self):
        """Create the context menu."""
        self.menu = QMenu()
        self.menu.setStyleSheet(Styles.TRAY_MENU_STYLE)

        # --- Status header (disabled, informational) ---
        self.status_action = self.menu.addAction("Monitoring: starting…")
        self.status_action.setEnabled(False)

        self.last_event_action = self.menu.addAction("Last event: –")
        self.last_event_action.setEnabled(False)

        self.stats_action = self.menu.addAction("Signal: 0 | Poll: 0")
        self.stats_action.setEnabled(False)

        self.menu.addSeparator()

        # View clipboard
        self.view_action = self.menu.addAction("View Clipboard")
        self.view_action.triggered.connect(self.show_viewer_requested.emit)

        self.menu.addSeparator()

        # Settings
        self.settings_action = self.menu.addAction("Settings")
        self.settings_action.triggered.connect(self.show_settings_requested.emit)

        self.menu.addSeparator()

        # Exit
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.triggered.connect(self.exit_requested.emit)

        self.setContextMenu(self.menu)

    def _connect_signals(self):
        """Connect tray icon signals."""
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_viewer_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_settings_requested.emit()

    # ------------------------------------------------------------------
    # Status updates from ClipboardMonitor
    # ------------------------------------------------------------------

    def update_status(self, info: dict):
        """Update tooltip and menu with live monitor status."""
        self._last_status = info
        event = info.get("event", "")
        time_str = info.get("time", "–")
        source = info.get("source", "–")
        sig = info.get("signal_hits", 0)
        poll = info.get("poll_hits", 0)

        # Tooltip (visible on hover)
        if event in ("started", "stopped"):
            tip = f"Clipboard Flash — {event}"
        else:
            tip = (
                f"Clipboard Flash\n"
                f"Last: {event} at {time_str} via {source}\n"
                f"Signal: {sig}  Poll: {poll}"
            )
        self.setToolTip(tip)

        # Menu items
        if event == "started":
            self.status_action.setText("Monitoring: active")
        elif event == "stopped":
            self.status_action.setText("Monitoring: stopped")
        else:
            self.status_action.setText("Monitoring: active")

        self.last_event_action.setText(f"Last: {event} @ {time_str} ({source})")
        self.stats_action.setText(f"Signal: {sig} | Poll fallback: {poll}")

        # Notify user when the poll fallback catches something the signal missed
        if event not in ("started", "stopped", "empty", "other") and source == "poll":
            self.showMessage(
                "Clipboard Flash",
                f"Caught a clipboard {event} via polling fallback.\n"
                "The Qt signal missed this one.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
