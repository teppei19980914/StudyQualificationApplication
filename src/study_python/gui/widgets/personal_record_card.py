"""自己ベスト記録カードウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.motivation_calculator import PersonalRecordData


logger = logging.getLogger(__name__)


class PersonalRecordCard(QFrame):
    """自己ベスト記録を表示するカードウィジェット.

    Attributes:
        _theme_manager: テーママネージャ.
        _best_day_label: 1日最長ラベル.
        _best_week_label: 週間最長ラベル.
        _longest_streak_label: 最長連続ラベル.
        _total_label: 累計ラベル.
        _data: 自己ベスト記録データ.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """PersonalRecordCardを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: PersonalRecordData | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("personal_record_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#personal_record_card {{"
            f"  background-color: {bg_card};"
            f"  border: 1px solid {border};"
            f"  border-radius: 12px;"
            f"}}"
        )

        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # タイトル
        title_layout = QHBoxLayout()
        title_icon = QLabel("\U0001f3c5")
        title_icon.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(title_icon)
        title_label = QLabel("\u81ea\u5df1\u30d9\u30b9\u30c8")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 1日最長
        self._best_day_label = QLabel("")
        self._best_day_label.setObjectName("muted_text")
        layout.addWidget(self._best_day_label)

        # 週間最長
        self._best_week_label = QLabel("")
        self._best_week_label.setObjectName("muted_text")
        layout.addWidget(self._best_week_label)

        # 最長連続
        self._longest_streak_label = QLabel("")
        self._longest_streak_label.setObjectName("muted_text")
        layout.addWidget(self._longest_streak_label)

        # 累計
        self._total_label = QLabel("")
        self._total_label.setObjectName("muted_text")
        layout.addWidget(self._total_label)

        # 初期表示
        self._show_empty()

    def set_data(self, data: PersonalRecordData) -> None:
        """自己ベスト記録データを設定する.

        Args:
            data: 自己ベスト記録データ.
        """
        self._data = data
        colors = self._theme_manager.get_colors()
        success_color = colors.get("success", "#A6E3A1")
        record_style = f"font-size: 13px; color: {success_color}; font-weight: 600;"

        if data.best_day_date is not None:
            day_time = self._format_duration(data.best_day_minutes)
            date_str = data.best_day_date.isoformat()
            self._best_day_label.setText(
                f"\U0001f551 1\u65e5\u6700\u9577: {day_time}\uff08{date_str}\uff09"
            )
            self._best_day_label.setStyleSheet(record_style)
        else:
            self._best_day_label.setText("\U0001f551 1\u65e5\u6700\u9577: ---")
            self._best_day_label.setStyleSheet("")

        if data.best_week_start is not None:
            week_time = self._format_duration(data.best_week_minutes)
            week_str = data.best_week_start.isoformat()
            self._best_week_label.setText(
                f"\U0001f4c5 \u9031\u9593\u6700\u9577: {week_time}\uff08{week_str}\u9031\uff09"
            )
            self._best_week_label.setStyleSheet(record_style)
        else:
            self._best_week_label.setText("\U0001f4c5 \u9031\u9593\u6700\u9577: ---")
            self._best_week_label.setStyleSheet("")

        self._longest_streak_label.setText(
            f"\U0001f525 \u6700\u9577\u9023\u7d9a: {data.longest_streak}\u65e5"
        )
        if data.longest_streak > 0:
            self._longest_streak_label.setStyleSheet(record_style)
        else:
            self._longest_streak_label.setStyleSheet("")

        self._total_label.setText(
            f"\u23f1\ufe0f \u7d2f\u8a08: {data.total_hours}h / "
            f"{data.total_study_days}\u65e5"
        )
        if data.total_study_days > 0:
            self._total_label.setStyleSheet(record_style)
        else:
            self._total_label.setStyleSheet("")

        logger.debug(
            f"Personal record card updated: "
            f"best_day={data.best_day_minutes}min, "
            f"best_week={data.best_week_minutes}min, "
            f"longest_streak={data.longest_streak}"
        )

    def _show_empty(self) -> None:
        """初期表示（空状態）."""
        self._best_day_label.setText("\U0001f551 1\u65e5\u6700\u9577: ---")
        self._best_week_label.setText("\U0001f4c5 \u9031\u9593\u6700\u9577: ---")
        self._longest_streak_label.setText(
            "\U0001f525 \u6700\u9577\u9023\u7d9a: 0\u65e5"
        )
        self._total_label.setText("\u23f1\ufe0f \u7d2f\u8a08: 0.0h / 0\u65e5")

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
