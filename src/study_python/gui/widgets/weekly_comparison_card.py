"""週間比較カードウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.motivation_calculator import WeeklyComparisonData


logger = logging.getLogger(__name__)


class WeeklyComparisonCard(QFrame):
    """今週と先週の学習時間を比較するカードウィジェット.

    Attributes:
        _theme_manager: テーママネージャ.
        _this_week_label: 今週の学習時間ラベル.
        _last_week_label: 先週の学習時間ラベル.
        _diff_label: 差分ラベル.
        _data: 週間比較データ.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """WeeklyComparisonCardを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: WeeklyComparisonData | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("weekly_comparison_card")
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#weekly_comparison_card {{"
            f"  background-color: {bg_card};"
            f"  border: 1px solid {border};"
            f"  border-radius: 12px;"
            f"  padding: 12px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # タイトル
        title_layout = QHBoxLayout()
        title_icon = QLabel("\U0001f4ca")
        title_icon.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(title_icon)
        title_label = QLabel("\u4eca\u9031 vs \u5148\u9031")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 今週
        self._this_week_label = QLabel("\u4eca\u9031: ---")
        self._this_week_label.setObjectName("muted_text")
        layout.addWidget(self._this_week_label)

        # 先週
        self._last_week_label = QLabel("\u5148\u9031: ---")
        self._last_week_label.setObjectName("muted_text")
        layout.addWidget(self._last_week_label)

        # 区切り線
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 差分
        self._diff_label = QLabel("")
        self._diff_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        self._diff_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._diff_label)

    def set_data(self, data: WeeklyComparisonData) -> None:
        """週間比較データを設定する.

        Args:
            data: 週間比較データ.
        """
        self._data = data

        this_week_text = self._format_duration(data.this_week_minutes)
        last_week_text = self._format_duration(data.last_week_minutes)

        self._this_week_label.setText(f"\u4eca\u9031: {this_week_text}")
        self._last_week_label.setText(f"\u5148\u9031: {last_week_text}")

        self._update_diff_label(data)

        logger.debug(
            f"Weekly comparison card updated: "
            f"this={data.this_week_minutes}min, last={data.last_week_minutes}min"
        )

    def _update_diff_label(self, data: WeeklyComparisonData) -> None:
        """差分ラベルを更新する.

        Args:
            data: 週間比較データ.
        """
        colors = self._theme_manager.get_colors()
        diff_text = self._format_duration(abs(data.difference_minutes))

        if data.difference_minutes > 0:
            arrow = "\u2191"
            color = colors.get("success", "#A6E3A1")
            percent_text = (
                f" (+{data.change_percent}%)" if data.change_percent is not None else ""
            )
            self._diff_label.setText(f"{arrow} +{diff_text}{percent_text}")
        elif data.difference_minutes < 0:
            arrow = "\u2193"
            color = colors.get("error", "#F38BA8")
            percent_text = (
                f" ({data.change_percent}%)" if data.change_percent is not None else ""
            )
            self._diff_label.setText(f"{arrow} -{diff_text}{percent_text}")
        else:
            color = colors.get("text_muted", "#6C7086")
            self._diff_label.setText("\u2192 \u5909\u5316\u306a\u3057")

        self._diff_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {color};"
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
