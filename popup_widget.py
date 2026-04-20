"""
Popup widget - shows brief clipboard preview near cursor with fade animation.
"""

import logging

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor, QImage, QPixmap, QGuiApplication

from config import Config

logger = logging.getLogger("ClipboardFlash")


class PopupWidget(QWidget):
    """Animated popup showing clipboard content preview."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._fade_in_anim = None
        self._fade_out_anim = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the popup UI."""
        # Window flags — same combo as splash_screen.py which renders correctly.
        # BypassWindowManagerHint was here before and prevented DWM compositing,
        # making the popup invisible when combined with WA_TranslucentBackground.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Main container with styling
        self.container = QWidget(self)
        self.container.setObjectName("popupContainer")
        self._apply_styles()

        # Content label
        self.content_label = QLabel()
        self.content_label.setObjectName("popupContent")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.addWidget(self.content_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        # Opacity effect for fade animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        # Timer for auto-hide
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._start_fade_out)

    def update_config(self):
        """Update settings from config."""
        self._apply_styles()

    def _apply_styles(self):
        """Apply dynamic styles based on config."""
        bg_color = self.config.get("popup_bg_color", "#1e1e2e")
        border_color = self.config.get("popup_border_color", "#7c3aed")
        text_color = self.config.get("popup_text_color", "#e0e0e0")
        border_width = self.config.get("popup_border_width", 1)

        self.container.setStyleSheet(f"""
            #popupContainer {{
                background-color: {bg_color};
                border: {border_width}px solid {border_color};
                border-radius: 8px;
            }}

            #popupContent {{
                color: {text_color};
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                padding: 0;
            }}
        """)

    def show_text(self, text: str):
        """Show text content in popup."""
        logger.info("show_text called, text length=%d", len(text))
        max_length = self.config.get("text_preview_length", 500)
        display_text = text[:max_length]
        if len(text) > max_length:
            display_text += "..."

        self.content_label.setPixmap(QPixmap())  # Clear any image
        self.content_label.setText(display_text)
        self._show_popup()

    def show_image(self, image: QImage):
        """Show image content in popup."""
        logger.info("show_image called, size=%dx%d", image.width(), image.height())
        max_width = self.config.get("popup_max_width", 400)
        max_height = self.config.get("popup_max_height", 300)

        # Scale image to fit
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            max_width - 24,  # Account for padding
            max_height - 40,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.content_label.setText("")  # Clear any text
        self.content_label.setPixmap(scaled)
        self._show_popup()

    def _show_popup(self):
        """Position and show the popup with animation."""
        # Stop and discard any running animations
        self.hide_timer.stop()
        self._cleanup_animations()

        # Size the popup
        max_width = self.config.get("popup_max_width", 400)
        max_height = self.config.get("popup_max_height", 300)
        self.setMaximumSize(max_width, max_height)
        self.adjustSize()

        # Position near cursor
        cursor_pos = QCursor.pos()
        offset_x = self.config.get("cursor_offset_x", 20)
        offset_y = self.config.get("cursor_offset_y", 20)

        popup_x = cursor_pos.x() + offset_x
        popup_y = cursor_pos.y() + offset_y

        # Keep on screen
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen:
            screen_geo = screen.availableGeometry()

            if popup_x + self.width() > screen_geo.right():
                popup_x = cursor_pos.x() - self.width() - offset_x
            if popup_y + self.height() > screen_geo.bottom():
                popup_y = cursor_pos.y() - self.height() - offset_y

            popup_x = max(screen_geo.left(), popup_x)
            popup_y = max(screen_geo.top(), popup_y)

        self.move(popup_x, popup_y)

        # Start fade in with a FRESH animation object
        fade_duration = self.config.get("fade_duration", 150)
        target_opacity = self.config.get("popup_opacity", 0.95)

        self.opacity_effect.setOpacity(0)
        self.show()

        self._fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in_anim.setDuration(fade_duration)
        self._fade_in_anim.setStartValue(0)
        self._fade_in_anim.setEndValue(target_opacity)
        self._fade_in_anim.start()

        logger.debug("Popup shown at (%d, %d), opacity target=%.2f", popup_x, popup_y, target_opacity)

        # Schedule fade out
        popup_duration = self.config.get("popup_duration", 1000)
        self.hide_timer.start(popup_duration)

    def _start_fade_out(self):
        """Start the fade out animation."""
        # Clean up fade-in if still around
        if self._fade_in_anim is not None:
            self._fade_in_anim.stop()
            self._fade_in_anim.deleteLater()
            self._fade_in_anim = None

        fade_duration = self.config.get("fade_duration", 150)

        self._fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out_anim.setDuration(fade_duration)
        self._fade_out_anim.setStartValue(self.opacity_effect.opacity())
        self._fade_out_anim.setEndValue(0)
        self._fade_out_anim.finished.connect(self.hide)
        self._fade_out_anim.start()

        logger.debug("Popup fade-out started")

    def _cleanup_animations(self):
        """Stop and delete any existing animation objects."""
        if self._fade_in_anim is not None:
            self._fade_in_anim.stop()
            self._fade_in_anim.deleteLater()
            self._fade_in_anim = None
        if self._fade_out_anim is not None:
            self._fade_out_anim.stop()
            self._fade_out_anim.deleteLater()
            self._fade_out_anim = None
