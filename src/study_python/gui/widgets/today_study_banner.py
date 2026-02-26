"""今日の学習状況バナーウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.motivation_calculator import TodayStudyData


logger = logging.getLogger(__name__)


class TodayStudyBanner(QFrame):
    """今日の学習状況を表示するバナーウィジェット.

    学習済みの場合はsuccess色、未学習の場合はwarning色で表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _icon_label: アイコンラベル.
        _message_label: メッセージラベル.
        _detail_label: 詳細ラベル.
        _data: 今日の学習状況データ.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """TodayStudyBannerを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: TodayStudyData | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setFixedHeight(60)
        self.setObjectName("today_study_banner")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self._icon_label)

        self._message_label = QLabel()
        self._message_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._message_label)

        self._detail_label = QLabel()
        self._detail_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self._detail_label)

        layout.addStretch()

        self._apply_not_studied_style()

    def set_data(self, data: TodayStudyData) -> None:
        """今日の学習状況データを設定する.

        Args:
            data: 今日の学習状況データ.
        """
        self._data = data

        if data.studied:
            self._apply_studied_style()
            self._icon_label.setText("\u2705")
            self._message_label.setText(
                "\u4eca\u65e5\u3082\u5b66\u7fd2\u3057\u307e\u3057\u305f\uff01"
            )
            time_text = self._format_duration(data.total_minutes)
            session_text = f"{data.session_count}\u30bb\u30c3\u30b7\u30e7\u30f3"
            self._detail_label.setText(f"{time_text}\uff08{session_text}\uff09")
        else:
            self._apply_not_studied_style()
            self._icon_label.setText("\U0001f4dd")
            self._message_label.setText(
                "\u4eca\u65e5\u306f\u307e\u3060\u5b66\u7fd2\u3057\u3066\u3044\u307e\u305b\u3093"
            )
            self._detail_label.setText("")

        logger.debug(f"Today study banner updated: studied={data.studied}")

    def _apply_studied_style(self) -> None:
        """学習済みスタイルを適用する."""
        colors = self._theme_manager.get_colors()
        success = colors.get("success", "#A6E3A1")
        bg = colors.get("bg_primary", "#1E1E2E")
        self.setStyleSheet(
            f"QFrame#today_study_banner {{"
            f"  background-color: {success};"
            f"  border-radius: 8px;"
            f"}}"
            f"QLabel {{ color: {bg}; background-color: transparent; }}"
        )

    def _apply_not_studied_style(self) -> None:
        """未学習スタイルを適用する."""
        colors = self._theme_manager.get_colors()
        warning = colors.get("warning", "#F9E2AF")
        bg = colors.get("bg_primary", "#1E1E2E")
        self.setStyleSheet(
            f"QFrame#today_study_banner {{"
            f"  background-color: {warning};"
            f"  border-radius: 8px;"
            f"}}"
            f"QLabel {{ color: {bg}; background-color: transparent; }}"
        )

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """学習時間をフォーマットする.

        Args:
            minutes: 学習時間（分）.

        Returns:
            フォーマット済み文字列.
        """
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins:02d}min"
        return f"{mins}min"
