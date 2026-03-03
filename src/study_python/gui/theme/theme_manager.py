"""テーマ管理マネージャ."""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class ThemeType(Enum):
    """テーマタイプ."""

    DARK = "dark"
    LIGHT = "light"


# ダークテーマのカラーパレット（Catppuccin Mocha風）
DARK_COLORS: dict[str, str] = {
    "bg_primary": "#1E1E2E",
    "bg_secondary": "#181825",
    "bg_surface": "#313244",
    "bg_hover": "#45475A",
    "bg_card": "#2A2A3C",
    "text_primary": "#CDD6F4",
    "text_secondary": "#A6ADC8",
    "text_muted": "#6C7086",
    "accent": "#89B4FA",
    "accent_hover": "#74C7EC",
    "success": "#A6E3A1",
    "warning": "#F9E2AF",
    "error": "#F38BA8",
    "border": "#45475A",
    "scrollbar": "#585B70",
    "scrollbar_hover": "#6C7086",
}

# ライトテーマのカラーパレット（Catppuccin Latte風）
LIGHT_COLORS: dict[str, str] = {
    "bg_primary": "#EFF1F5",
    "bg_secondary": "#E6E9EF",
    "bg_surface": "#DCE0E8",
    "bg_hover": "#CCD0DA",
    "bg_card": "#FFFFFF",
    "text_primary": "#4C4F69",
    "text_secondary": "#5C5F77",
    "text_muted": "#9CA0B0",
    "accent": "#1E66F5",
    "accent_hover": "#2A7AE4",
    "success": "#40A02B",
    "warning": "#DF8E1D",
    "error": "#D20F39",
    "border": "#CCD0DA",
    "scrollbar": "#ACB0BE",
    "scrollbar_hover": "#9CA0B0",
}


def _build_stylesheet(colors: dict[str, str]) -> str:
    """カラーパレットからQSSスタイルシートを生成する.

    Args:
        colors: カラーパレット辞書.

    Returns:
        QSSスタイルシート文字列.
    """
    return f"""
/* ===== Global ===== */
QMainWindow, QDialog {{
    background-color: {colors["bg_primary"]};
    color: {colors["text_primary"]};
}}

QWidget {{
    background-color: transparent;
    color: {colors["text_primary"]};
    font-family: "Segoe UI", "Yu Gothic UI", "Meiryo", sans-serif;
    font-size: 13px;
}}

/* ===== Sidebar ===== */
QWidget#sidebar {{
    background-color: {colors["bg_secondary"]};
    border-right: 1px solid {colors["border"]};
}}

QPushButton#sidebar_button {{
    background-color: transparent;
    color: {colors["text_secondary"]};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}}

QPushButton#sidebar_button:hover {{
    background-color: {colors["bg_hover"]};
    color: {colors["text_primary"]};
}}

QPushButton#sidebar_button:checked {{
    background-color: {colors["accent"]};
    color: {colors["bg_primary"]};
    font-weight: 600;
}}

/* ===== Header Bar ===== */
QWidget#header_bar {{
    background-color: {colors["bg_secondary"]};
    border-bottom: 1px solid {colors["border"]};
}}

QPushButton#hamburger_button {{
    background: transparent;
    font-size: 20px;
    border: none;
    border-radius: 6px;
    padding: 0;
    min-height: 0;
    color: {colors["text_primary"]};
}}

QPushButton#hamburger_button:hover {{
    background-color: {colors["bg_hover"]};
}}

QLabel#header_title {{
    font-size: 16px;
    font-weight: 600;
    background: transparent;
    color: {colors["text_primary"]};
}}

/* ===== Navigation Drawer ===== */
QFrame#navigation_drawer {{
    background-color: {colors["bg_secondary"]};
    border-right: 1px solid {colors["border"]};
}}

QLabel#settings_theme_label {{
    font-size: 14px;
    color: {colors["text_secondary"]};
}}

/* ===== Cards ===== */
QFrame#goal_card {{
    background-color: {colors["bg_card"]};
    border: 1px solid {colors["border"]};
    border-radius: 12px;
    padding: 16px;
}}

QFrame#goal_card:hover {{
    border-color: {colors["accent"]};
}}

/* ===== Labels ===== */
QLabel {{
    background-color: transparent;
    color: {colors["text_primary"]};
}}

QLabel#section_title {{
    font-size: 20px;
    font-weight: 700;
    color: {colors["text_primary"]};
}}

QLabel#card_title {{
    font-size: 15px;
    font-weight: 600;
    color: {colors["text_primary"]};
}}

QLabel#card_subtitle {{
    font-size: 12px;
    color: {colors["text_secondary"]};
}}

QLabel#muted_text {{
    color: {colors["text_muted"]};
    font-size: 12px;
}}

/* ===== Buttons ===== */
QPushButton {{
    background-color: {colors["accent"]};
    color: {colors["bg_primary"]};
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {colors["accent_hover"]};
}}

QPushButton:pressed {{
    background-color: {colors["accent"]};
}}

QPushButton#danger_button {{
    background-color: {colors["error"]};
}}

QPushButton#danger_button:hover {{
    background-color: {colors["error"]};
    opacity: 0.8;
}}

QPushButton#secondary_button {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
}}

QPushButton#secondary_button:hover {{
    background-color: {colors["bg_hover"]};
}}

/* ===== Inputs ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {colors["accent"]};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {colors["accent"]};
}}

QDateEdit {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QDateEdit:focus {{
    border-color: {colors["accent"]};
}}

QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}

/* ===== ComboBox ===== */
QComboBox {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:focus {{
    border-color: {colors["accent"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    selection-background-color: {colors["accent"]};
    selection-color: {colors["bg_primary"]};
}}

/* ===== SpinBox / Slider ===== */
QSpinBox {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QSlider::groove:horizontal {{
    background-color: {colors["bg_surface"]};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {colors["accent"]};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background-color: {colors["accent"]};
    border-radius: 3px;
}}

/* ===== ScrollBar ===== */
QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {colors["scrollbar"]};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors["scrollbar_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors["scrollbar"]};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors["scrollbar_hover"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ===== Scroll Area ===== */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    background-color: {colors["bg_surface"]};
    border: none;
    border-radius: 4px;
    text-align: center;
    color: {colors["text_primary"]};
    font-size: 11px;
    max-height: 8px;
}}

QProgressBar::chunk {{
    background-color: {colors["accent"]};
    border-radius: 4px;
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    border: 1px solid {colors["border"]};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_secondary"]};
    border: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}

QTabBar::tab:selected {{
    background-color: {colors["accent"]};
    color: {colors["bg_primary"]};
    font-weight: 600;
}}

/* ===== ToolTip ===== */
QToolTip {{
    background-color: {colors["bg_surface"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ===== Graphics View ===== */
QGraphicsView {{
    background-color: {colors["bg_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
}}
"""


class ThemeManager:
    """テーマの管理と切替を行うマネージャ.

    Attributes:
        current_theme: 現在のテーマタイプ.
    """

    def __init__(self, settings_path: Path | None = None) -> None:
        """ThemeManagerを初期化する.

        Args:
            settings_path: 設定ファイルのパス.
        """
        self._settings_path = settings_path or Path("data/settings.json")
        self.current_theme = self._load_theme_preference()

    def get_stylesheet(self, theme: ThemeType | None = None) -> str:
        """テーマのQSSスタイルシートを取得する.

        Args:
            theme: テーマタイプ。Noneの場合は現在のテーマ.

        Returns:
            QSSスタイルシート文字列.
        """
        target = theme or self.current_theme
        colors = DARK_COLORS if target == ThemeType.DARK else LIGHT_COLORS
        return _build_stylesheet(colors)

    def get_colors(self, theme: ThemeType | None = None) -> dict[str, str]:
        """テーマのカラーパレットを取得する.

        Args:
            theme: テーマタイプ。Noneの場合は現在のテーマ.

        Returns:
            カラーパレット辞書.
        """
        target = theme or self.current_theme
        if target == ThemeType.DARK:
            return DARK_COLORS.copy()
        return LIGHT_COLORS.copy()

    def toggle_theme(self) -> ThemeType:
        """テーマを切り替える.

        Returns:
            切り替え後のテーマタイプ.
        """
        if self.current_theme == ThemeType.DARK:
            self.current_theme = ThemeType.LIGHT
        else:
            self.current_theme = ThemeType.DARK
        self._save_theme_preference()
        logger.info(f"Theme switched to: {self.current_theme.value}")
        return self.current_theme

    def set_theme(self, theme: ThemeType) -> None:
        """テーマを設定する.

        Args:
            theme: 設定するテーマタイプ.
        """
        self.current_theme = theme
        self._save_theme_preference()

    def _load_theme_preference(self) -> ThemeType:
        """設定ファイルからテーマ設定を読み込む.

        Returns:
            保存されたテーマタイプ。ファイルが無い場合はDARK.
        """
        try:
            if self._settings_path.exists():
                data: dict[str, Any] = json.loads(
                    self._settings_path.read_text(encoding="utf-8")
                )
                return ThemeType(data.get("theme", "dark"))
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        return ThemeType.DARK

    def _save_theme_preference(self) -> None:
        """テーマ設定を保存する."""
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            data: dict[str, Any] = {}
            if self._settings_path.exists():
                data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            data["theme"] = self.current_theme.value
            self._settings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:  # pragma: no cover
            logger.error(f"Failed to save theme preference: {e}")
