"""
Clipboard monitoring - watches for changes and emits signals.

Uses Qt's dataChanged signal as primary detection, with a Win32
GetClipboardSequenceNumber polling fallback to catch changes that
the signal misses (broken clipboard viewer chain, etc.).

Contention hardening (2026-07-18)
---------------------------------
On Windows, only one process may have the clipboard OPEN at a time. When any
process holds it open, every other app's OpenClipboard() fails with error 5
("cannot open clipboard"). To the user that looks like "Ctrl+C didn't work,
try again." The more clipboard listeners are running (Clipboard History /
cbdhsvc, Chrome Remote Desktop's remoting_host, PowerToys Advanced Paste,
clipboard managers, this app), the higher the odds that at the instant of a
copy someone is mid-read and the copy is dropped. It gets worse the longer the
machine is up.

This module now:
  * Never reads the clipboard synchronously inside the change handler. Reads
    are deferred a few ms so the copying app's CloseClipboard() completes first
    and we don't race the user's next Ctrl+C.
  * Retries every read with short backoff (Windows genuinely needs this).
  * Runs a lightweight watchdog that samples GetOpenClipboardWindow() and, when
    a FOREIGN process holds the clipboard open abnormally long, logs the
    offender's PID + process name. That turns "who is stealing the clipboard?"
    from a guess into a logged fact.
This app itself uses only lock-free GetClipboardSequenceNumber polling plus
brief Qt reads; it never uses the fragile SetClipboardViewer chain and never
holds the clipboard open.
"""

import ctypes
from ctypes import wintypes
import logging
import os
import time
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QClipboard, QImage
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger("ClipboardFlash")

# ---------------------------------------------------------------------------
# Win32 clipboard introspection (all lock-free — none of these OPEN the
# clipboard, so they can never themselves cause contention).
# ---------------------------------------------------------------------------
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

_GetClipboardSequenceNumber = _user32.GetClipboardSequenceNumber
_GetClipboardSequenceNumber.restype = ctypes.c_uint

_user32.GetOpenClipboardWindow.restype = wintypes.HWND
_user32.GetClipboardOwner.restype = wintypes.HWND

_OUR_PID = os.getpid()
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# small cache so we don't reopen process handles constantly
_name_cache: dict[int, str] = {}


def _pid_of_hwnd(hwnd) -> int:
    if not hwnd:
        return 0
    pid = wintypes.DWORD(0)
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _process_name(pid: int) -> str:
    if not pid:
        return ""
    cached = _name_cache.get(pid)
    if cached is not None:
        return cached
    h = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    name = f"pid{pid}"
    if h:
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                name = buf.value.split("\\")[-1]
        finally:
            _kernel32.CloseHandle(h)
    _name_cache[pid] = name
    return name


def clipboard_open_by() -> tuple[int, str]:
    """Who currently has the clipboard OPEN (0/'' if nobody)."""
    hwnd = _user32.GetOpenClipboardWindow()
    pid = _pid_of_hwnd(hwnd)
    return pid, _process_name(pid)


def clipboard_owner() -> tuple[int, str]:
    """Who last SET the clipboard (the 'owner')."""
    hwnd = _user32.GetClipboardOwner()
    pid = _pid_of_hwnd(hwnd)
    return pid, _process_name(pid)


POLL_INTERVAL_MS = 250      # sequence-number fallback poll (lock-free, cheap)
READ_DEBOUNCE_MS = 20       # defer reads so we never race the copying app
READ_RETRIES = 8            # OpenClipboard-style backoff for our own reads
READ_RETRY_SLEEP_MS = 15
WATCHDOG_INTERVAL_MS = 40   # how often we sample who holds the clipboard open
WATCHDOG_WARN_MS = 200      # a foreign hold longer than this is logged as trouble
CONTENTION_SUMMARY_MS = 300_000  # log a rollup of top offenders every 5 min


class ClipboardMonitor(QObject):
    """Monitors clipboard for changes and emits signals."""

    text_copied = pyqtSignal(str)
    image_copied = pyqtSignal(QImage)

    # Diagnostic signals — tray / UI can connect to these
    status_changed = pyqtSignal(dict)  # {"event", "time", "source", ...}
    # Fired when a foreign process is caught holding the clipboard too long.
    contention_detected = pyqtSignal(dict)  # {"proc", "pid", "held_ms"}

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

        # Coalescing timer — reads happen here, off the change handler, so the
        # copying app's CloseClipboard() lands first and we don't race Ctrl+C.
        self._read_timer = QTimer(self)
        self._read_timer.setSingleShot(True)
        self._read_timer.setInterval(READ_DEBOUNCE_MS)
        self._read_timer.timeout.connect(self._do_read)
        self._pending_source = None

        # Contention watchdog
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(WATCHDOG_INTERVAL_MS)
        self._watchdog.timeout.connect(self._watchdog_tick)
        self._hold_hwnd = 0
        self._hold_start = 0.0
        self._hold_logged = False
        self._contention = {}   # procname -> {"count", "total_ms", "max_ms", "warns"}
        self._last_summary = time.monotonic()

        # Content cache — preserves content even if popup display is delayed
        self._content_cache = []  # list of (timestamp, type, content)
        self._max_cache_size = 10

        # Diagnostics
        self._signal_hits = 0
        self._poll_hits = 0
        self._read_failures = 0
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
        self._watchdog.start()
        self._emit_status("started")
        logger.info(
            "Clipboard monitor started (signal + poll@%dms, watchdog@%dms, pid=%d)",
            POLL_INTERVAL_MS, WATCHDOG_INTERVAL_MS, _OUR_PID,
        )

    def stop(self):
        """Stop monitoring clipboard."""
        self._active = False
        self._poll_timer.stop()
        self._watchdog.stop()
        self._read_timer.stop()
        try:
            self.clipboard.dataChanged.disconnect(self._on_signal_changed)
        except Exception:
            pass
        self._log_contention_summary(force=True)
        self._emit_status("stopped")
        logger.info("Clipboard monitor stopped")

    def diagnostics(self) -> dict:
        """Return a snapshot of monitor health info."""
        return {
            "active": self._active,
            "signal_hits": self._signal_hits,
            "poll_hits": self._poll_hits,
            "read_failures": self._read_failures,
            "last_event_time": self._last_event_time,
            "last_event_source": self._last_event_source,
            "last_event_type": self._last_event_type,
            "clipboard_seq": _GetClipboardSequenceNumber(),
            "cache_size": len(self._content_cache),
            "contention": self.contention_report(),
        }

    def contention_report(self) -> dict:
        """Per-process summary of clipboard holds seen by the watchdog."""
        return {
            name: dict(stats) for name, stats in
            sorted(self._contention.items(), key=lambda kv: -kv[1]["max_ms"])
        }

    def get_cached_content(self):
        """Return the content cache for diagnostics or recovery."""
        return list(self._content_cache)

    # ------------------------------------------------------------------
    # Change detection -> schedule a (debounced) read
    # ------------------------------------------------------------------

    def _on_signal_changed(self):
        """Qt dataChanged signal fired."""
        if not self._active:
            return
        self._last_seq = _GetClipboardSequenceNumber()
        self._signal_hits += 1
        self._schedule_read("signal")

    def _poll_clipboard(self):
        """Timer-based check using Win32 sequence number (lock-free)."""
        if not self._active:
            return
        seq = _GetClipboardSequenceNumber()
        if seq != self._last_seq:
            self._last_seq = seq
            self._poll_hits += 1
            logger.info("Poll fallback caught a clipboard change (seq=%d)", seq)
            self._schedule_read("poll")

    def _schedule_read(self, source: str):
        """Coalesce rapid changes and read slightly later, off the hot path."""
        self._pending_source = source
        if not self._read_timer.isActive():
            self._read_timer.start()

    def _do_read(self):
        source = self._pending_source or "signal"
        self._pending_source = None
        self._process_clipboard(source)

    # ------------------------------------------------------------------
    # Contention watchdog
    # ------------------------------------------------------------------

    def _watchdog_tick(self):
        """Sample who holds the clipboard OPEN; log foreign long-holders."""
        if not self._active:
            return
        hwnd = _user32.GetOpenClipboardWindow()
        now = time.monotonic()

        if hwnd != self._hold_hwnd:
            # a hold just ended — record it
            if self._hold_hwnd:
                self._record_hold(self._hold_hwnd, (now - self._hold_start) * 1000.0)
            self._hold_hwnd = hwnd
            self._hold_start = now
            self._hold_logged = False
        elif hwnd:
            held_ms = (now - self._hold_start) * 1000.0
            pid = _pid_of_hwnd(hwnd)
            if (held_ms >= WATCHDOG_WARN_MS and not self._hold_logged
                    and pid and pid != _OUR_PID):
                name = _process_name(pid)
                self._hold_logged = True
                self._contention.setdefault(
                    name, {"count": 0, "total_ms": 0.0, "max_ms": 0.0, "warns": 0}
                )["warns"] += 1
                logger.warning(
                    "CONTENTION: %s (pid=%d) has held the clipboard OPEN for "
                    ">%dms — any Ctrl+C during this window will silently fail.",
                    name, pid, WATCHDOG_WARN_MS,
                )
                self.contention_detected.emit(
                    {"proc": name, "pid": pid, "held_ms": round(held_ms)}
                )

        if now - self._last_summary >= CONTENTION_SUMMARY_MS / 1000.0:
            self._log_contention_summary()

    def _record_hold(self, hwnd, held_ms: float):
        pid = _pid_of_hwnd(hwnd)
        if not pid or pid == _OUR_PID:
            return
        name = _process_name(pid)
        s = self._contention.setdefault(
            name, {"count": 0, "total_ms": 0.0, "max_ms": 0.0, "warns": 0}
        )
        s["count"] += 1
        s["total_ms"] += held_ms
        s["max_ms"] = max(s["max_ms"], held_ms)

    def _log_contention_summary(self, force: bool = False):
        self._last_summary = time.monotonic()
        report = self.contention_report()
        if not report:
            return
        top = list(report.items())[:5]
        parts = [
            f"{n}(x{s['count']}, max={s['max_ms']:.0f}ms, warns={s['warns']})"
            for n, s in top
        ]
        logger.info("Clipboard-hold summary (foreign holders): %s", "; ".join(parts))

    # ------------------------------------------------------------------
    # Shared processing (with retry/backoff + failure attribution)
    # ------------------------------------------------------------------

    def _process_clipboard(self, source: str):
        """Read the clipboard and emit the appropriate signal.

        Retries with short backoff because a foreign listener may momentarily
        hold the clipboard open, making the first read come back empty. If it
        stays unreadable, log WHO is holding it so the culprit is proven.
        """
        seq = _GetClipboardSequenceNumber()

        for attempt in range(READ_RETRIES):
            try:
                mime_data = self.clipboard.mimeData()
            except Exception as exc:
                mime_data = None
                logger.debug("mimeData() raised (attempt %d): %s", attempt + 1, exc)

            if mime_data is not None:
                try:
                    has_image = mime_data.hasImage()
                    has_text = mime_data.hasText()
                except Exception:
                    has_image = has_text = False

                # Image first (higher priority)
                if has_image:
                    try:
                        image = self.clipboard.image()
                        if not image.isNull():
                            self._emit_image(source, image)
                            return
                    except Exception as exc:
                        logger.debug("image() read failed (attempt %d): %s",
                                     attempt + 1, exc)

                # Then text
                if has_text:
                    try:
                        text = self.clipboard.text()
                        if text:
                            self._emit_text(source, text)
                            return
                    except Exception as exc:
                        logger.debug("text() read failed (attempt %d): %s",
                                     attempt + 1, exc)

                # Nothing readable but formats claim to exist -> transient lock;
                # if neither flag was set at all, it's genuinely a non-text/image
                # payload and retrying won't help.
                if not (has_image or has_text):
                    self._record_event(source, "other")
                    return

            time.sleep(READ_RETRY_SLEEP_MS / 1000.0)

        # Exhausted retries — attribute the failure to whoever holds it now.
        self._read_failures += 1
        open_pid, open_name = clipboard_open_by()
        set_pid, set_name = clipboard_owner()
        if open_pid and open_pid != _OUR_PID:
            logger.warning(
                "READ FAILED after %d tries (seq=%d): clipboard held OPEN by "
                "%s (pid=%d). Owner/setter=%s (pid=%d).",
                READ_RETRIES, seq, open_name, open_pid, set_name, set_pid,
            )
        else:
            logger.warning(
                "READ FAILED after %d tries (seq=%d): no foreign opener visible; "
                "last setter=%s (pid=%d).",
                READ_RETRIES, seq, set_name, set_pid,
            )
        self._record_event(source, "read_failed")

    def _emit_image(self, source, image):
        image_key = (
            image.width(),
            image.height(),
            image.pixel(0, 0) if image.width() > 0 and image.height() > 0 else 0,
        )
        if image_key != self._last_image_key:
            self._last_image_key = image_key
            self._last_text = ""
            self._cache_content("image", image)
            self._record_event(source, "image")
            self.image_copied.emit(image)

    def _emit_text(self, source, text):
        if text != self._last_text:
            self._last_text = text
            self._last_image_key = None
            self._cache_content("text", text)
            self._record_event(source, "text")
            self.text_copied.emit(text)

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
            "read_failures": self._read_failures,
        })
