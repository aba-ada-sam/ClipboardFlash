"""
Clipboard monitoring - watches for changes and emits signals.

Uses Qt's dataChanged signal as primary detection, with a Win32
GetClipboardSequenceNumber polling fallback to catch changes that
the signal misses (broken clipboard viewer chain, etc.).
"""

import ctypes
import logging
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QClipboard, QImage
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger("ClipboardFlash")

# Win32 API for reliable clipboard change detection
_user32 = ctypes.windll.user32
_GetClipboardSequenceNumber = _user32.GetClipboardSequenceNumber
_GetClipboardSequenceNumber.restype = ctypes.c_uint

POLL_INTERVAL_MS = 250  # check every 250ms — fast feedback, negligible CPU


class ClipboardMonitor(QObject):
    """Monitors clipboard for changes and emits signals."""

    text_copied = pyqtSignal(str)
    image_copied = pyqtSignal(QImage)

    # Diagnostic signals — tray / UI can connect to these
    status_changed = pyqtSignal(dict)  # {"event", "time", "source", ...}

    def __init__(self, clipboard: QClipboard):
        super().__init__()
        self.clipboard = clipboard
        self._last_text = ""
        self._last_image_key = None
        self._active = False

        # Win32 sequence tracking
        self._last_seq = _GetClipboardSequenceNumber()

        # Polling timer (fallback)
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_clipboard)

        # Content cache — preserves content even if popup display is delayed
        self._content_cache = []  # list of (timestamp, type, content)
        self._max_cache_size = 10

        # Diagnostics
        self._signal_hits = 0
        self._poll_hits = 0
        self._last_event_time = None
        self._last_event_source = None
        self._last_event_type = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def start(self):
        """Start monitoring clipboard."""
        self._active = True
        self._last_seq = _GetClipboardSequenceNumber()
        self.clipboard.dataChanged.connect(self._on_signal_changed)
        self._poll_timer.start()
        self._emit_status("started")
        logger.info("Clipboard monitor started (signal + poll@%dms)", POLL_INTERVAL_MS)

    def stop(self):
        """Stop monitoring clipboard."""
        self._active = False
        self._poll_timer.stop()
        try:
            self.clipboard.dataChanged.disconnect(self._on_signal_changed)
        except Exception:
            pass
        self._emit_status("stopped")
        logger.info("Clipboard monitor stopped")

    def diagnostics(self) -> dict:
        """Return a snapshot of monitor health info."""
        return {
            "active": self._active,
            "signal_hits": self._signal_hits,
            "poll_hits": self._poll_hits,
            "last_event_time": self._last_event_time,
            "last_event_source": self._last_event_source,
            "last_event_type": self._last_event_type,
            "clipboard_seq": _GetClipboardSequenceNumber(),
            "cache_size": len(self._content_cache),
        }

    def get_cached_content(self):
        """Return the content cache for diagnostics or recovery."""
        return list(self._content_cache)

    # ------------------------------------------------------------------
    # Signal-driven path (primary)
    # ------------------------------------------------------------------

    def _on_signal_changed(self):
        """Qt dataChanged signal fired."""
        if not self._active:
            return
        # Update sequence so the poll timer doesn't double-fire
        self._last_seq = _GetClipboardSequenceNumber()
        self._process_clipboard("signal")

    # ------------------------------------------------------------------
    # Polling path (fallback)
    # ------------------------------------------------------------------

    def _poll_clipboard(self):
        """Timer-based check using Win32 sequence number."""
        if not self._active:
            return
        seq = _GetClipboardSequenceNumber()
        if seq != self._last_seq:
            self._last_seq = seq
            logger.info("Poll fallback caught a clipboard change (seq=%d)", seq)
            self._process_clipboard("poll")

    # ------------------------------------------------------------------
    # Shared processing
    # ------------------------------------------------------------------

    def _process_clipboard(self, source: str):
        """Read the clipboard and emit the appropriate signal."""
        try:
            mime_data = self.clipboard.mimeData()
        except Exception as exc:
            logger.warning("Failed to read clipboard mimeData: %s", exc)
            return

        if mime_data is None:
            self._record_event(source, "empty")
            return

        # Check for image first (higher priority)
        try:
            if mime_data.hasImage():
                image = self.clipboard.image()
                if not image.isNull():
                    image_key = (
                        image.width(),
                        image.height(),
                        image.pixel(0, 0)
                        if image.width() > 0 and image.height() > 0
                        else 0,
                    )
                    if image_key != self._last_image_key:
                        self._last_image_key = image_key
                        self._last_text = ""
                        self._cache_content("image", image)
                        self._record_event(source, "image")
                        self.image_copied.emit(image)
                    return
        except Exception as exc:
            logger.warning("Error reading image from clipboard: %s", exc)

        # Check for text
        try:
            if mime_data.hasText():
                text = self.clipboard.text()
                if text and text != self._last_text:
                    self._last_text = text
                    self._last_image_key = None
                    self._cache_content("text", text)
                    self._record_event(source, "text")
                    self.text_copied.emit(text)
                    return
        except Exception as exc:
            logger.warning("Error reading text from clipboard: %s", exc)

        self._record_event(source, "other")

    # ------------------------------------------------------------------
    # Content cache
    # ------------------------------------------------------------------

    def _cache_content(self, content_type: str, content):
        """Cache clipboard content for reliability on slow machines."""
        self._content_cache.append((datetime.now(), content_type, content))
        if len(self._content_cache) > self._max_cache_size:
            self._content_cache.pop(0)
        logger.debug("Cached %s content (cache size: %d)",
                      content_type, len(self._content_cache))

    # ------------------------------------------------------------------
    # Diagnostics helpers
    # ------------------------------------------------------------------

    def _record_event(self, source: str, event_type: str):
        now = datetime.now()
        if source == "signal":
            self._signal_hits += 1
        else:
            self._poll_hits += 1
        self._last_event_time = now
        self._last_event_source = source
        self._last_event_type = event_type
        logger.debug("Clipboard event: type=%s source=%s", event_type, source)
        self._emit_status(event_type)

    def _emit_status(self, event: str):
        self.status_changed.emit({
            "event": event,
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": self._last_event_source or "-",
            "signal_hits": self._signal_hits,
            "poll_hits": self._poll_hits,
        })
