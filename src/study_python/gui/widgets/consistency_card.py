"""学習継続率カードウィジェット."""

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
from study_python.services.motivation_calculator import ConsistencyData


logger = logging.getLogger(__name__)


class ConsistencyCard(QFrame):
    """学習の継続率を表示するカードウィジェット.

    Attributes:
        _theme_manager: テーママネージャ.
        _week_label: 今週の継続率ラベル.
        _month_label: 今月の継続率ラベル.
        _overall_label: 全体の継続率ラベル.
        _data: 継続率データ.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """ConsistencyCardを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: ConsistencyData | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("consistency_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#consistency_card {{"
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
        title_icon = QLabel("\U0001f4ca")
        title_icon.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(title_icon)
        title_label = QLabel("\u5b66\u7fd2\u306e\u7d99\u7d9a\u7387")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 今週
        self._week_label = QLabel("")
        self._week_label.setObjectName("muted_text")
        layout.addWidget(self._week_label)

        # 今月
        self._month_label = QLabel("")
        self._month_label.setObjectName("muted_text")
        layout.addWidget(self._month_label)

        # 全体
        self._overall_label = QLabel("")
        self._overall_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(self._overall_label)

        # 初期表示
        self._show_empty()

    def set_data(self, data: ConsistencyData) -> None:
        """継続率データを設定する.

        Args:
            data: 継続率データ.
        """
        self._data = data
        colors = self._theme_manager.get_colors()

        # 今週
        week_rate = (
            data.this_week_days / data.this_week_total
            if data.this_week_total > 0
            else 0.0
        )
        week_color = self._rate_color(week_rate, colors)
        self._week_label.setText(
            f"\u4eca\u9031: {data.this_week_days}/{data.this_week_total}\u65e5"
        )
        self._week_label.setStyleSheet(
            f"font-size: 13px; color: {week_color}; font-weight: 600;"
        )

        # 今月
        month_rate = (
            data.this_month_days / data.this_month_total
            if data.this_month_total > 0
            else 0.0
        )
        month_color = self._rate_color(month_rate, colors)
        self._month_label.setText(
            f"\u4eca\u6708: {data.this_month_days}/{data.this_month_total}\u65e5"
        )
        self._month_label.setStyleSheet(
            f"font-size: 13px; color: {month_color}; font-weight: 600;"
        )

        # 全体
        overall_pct = f"{data.overall_rate * 100:.0f}%"
        overall_color = self._rate_color(data.overall_rate, colors)
        self._overall_label.setText(
            f"\u5168\u4f53: {overall_pct}"
            f"\uff08{data.overall_study_days}/{data.overall_total_days}\u65e5\uff09"
        )
        self._overall_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {overall_color};"
        )

        logger.debug(
            f"Consistency card updated: "
            f"week={data.this_week_days}/{data.this_week_total}, "
            f"month={data.this_month_days}/{data.this_month_total}, "
            f"overall={data.overall_rate:.1%}"
        )

    @staticmethod
    def _rate_color(rate: float, colors: dict[str, str]) -> str:
        """継続率に応じた色を返す.

        Args:
            rate: 継続率 (0.0-1.0).
            colors: テーマカラーパレット.

        Returns:
            色コード.
        """
        if rate >= 0.8:
            return colors.get("success", "#A6E3A1")
        if rate >= 0.5:
            return colors.get("warning", "#F9E2AF")
        return colors.get("error", "#F38BA8")

    def _show_empty(self) -> None:
        """初期表示（空状態）."""
        self._week_label.setText("\u4eca\u9031: 0/0\u65e5")
        self._month_label.setText("\u4eca\u6708: 0/0\u65e5")
        self._overall_label.setText("\u5168\u4f53: 0%\uff080/0\u65e5\uff09")
