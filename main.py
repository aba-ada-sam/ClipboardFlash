#!/usr/bin/env python3
"""
Clipboard Flash - A beautiful clipboard monitor for Windows
Shows a brief preview of clipboard content near cursor when copied.
"""

import logging
import logging.handlers
import os
import sys
import socket
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer

from splash_screen import SplashScreen
from app import ClipboardFlashApp


# Port for single instance check
SINGLE_INSTANCE_PORT = 47923


def setup_logging():
    """Set up file + console logging so the user can see what happened."""
    log_dir = Path(os.environ.get("APPDATA", "")) / "ClipboardFlash"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "clipboard_flash.log"

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=512_000, backupCount=2, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))

    root = logging.getLogger("ClipboardFlash")
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler())
    root.info("--- Clipboard Flash starting (pid=%d) ---", os.getpid())


def check_single_instance():
    """Check if another instance is already running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        sock.listen(1)
        return sock
    except socket.error:
        return None


def main():
    setup_logging()

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Clipboard Flash")
    app.setOrganizationName("ClipboardFlash")

    # Check for existing instance
    instance_lock = check_single_instance()
    if instance_lock is None:
        QMessageBox.information(
            None,
            "Clipboard Flash",
            "Clipboard Flash is already running.\n\n"
            "Look for the clipboard icon in your system tray."
        )
        sys.exit(0)

    # Show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Create main application and start monitoring IMMEDIATELY
    # (don't wait for splash — copies during the splash were silently lost)
    clipboard_app = ClipboardFlashApp(app)
    clipboard_app.start()

    # Close splash after a brief display (purely cosmetic)
    QTimer.singleShot(2000, splash.close)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
