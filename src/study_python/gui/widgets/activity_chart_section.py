"""学習アクティビティチャートセクションウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.daily_activity_chart import DailyActivityChart
from study_python.services.study_stats_calculator import (
    ActivityChartData,
    ActivityPeriodType,
)


logger = logging.getLogger(__name__)

_PERIOD_LABELS: list[tuple[ActivityPeriodType, str]] = [
    (ActivityPeriodType.DAILY, "日別"),
    (ActivityPeriodType.WEEKLY, "週別"),
    (ActivityPeriodType.MONTHLY, "月別"),
    (ActivityPeriodType.YEARLY, "年別"),
]


class ActivityChartSection(QFrame):
    """学習アクティビティチャートセクション.

    プルダウンで年別/月別/週別/日別を切り替えて
    チャートを動的に更新する複合ウィジェット。

    Attributes:
        _theme_manager: テーママネージャ.
        _combo: 期間切替コンボボックス.
        _chart: アクティビティチャート.
        _all_data: 全期間のチャートデータ.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """ActivityChartSectionを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._all_data: dict[ActivityPeriodType, ActivityChartData] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("activity_chart_section")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#activity_chart_section {{"
            f"  background-color: {bg_card};"
            f"  border: 1px solid {border};"
            f"  border-radius: 12px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # ヘッダー（タイトル + コンボボックス）
        header_layout = QHBoxLayout()

        title_icon = QLabel("\U0001f4c8")
        title_icon.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(title_icon)

        title_label = QLabel("学習アクティビティ")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self._combo = QComboBox()
        for _period_type, label in _PERIOD_LABELS:
            self._combo.addItem(label)
        # デフォルト: 日別 (index 0)
        self._combo.setCurrentIndex(0)
        self._combo.currentIndexChanged.connect(self._on_period_changed)
        header_layout.addWidget(self._combo)

        layout.addLayout(header_layout)

        # チャート
        self._chart = DailyActivityChart(self._theme_manager)
        layout.addWidget(self._chart)

    def set_all_data(self, data: dict[ActivityPeriodType, ActivityChartData]) -> None:
        """全期間のチャートデータを一括設定する.

        Args:
            data: 期間種別→チャートデータのマップ.
        """
        self._all_data = data
        self._update_chart()

    def _on_period_changed(self, _index: int) -> None:
        """期間切替コンボボックスの変更ハンドラ.

        Args:
            _index: 新しい選択インデックス.
        """
        self._update_chart()

    def _update_chart(self) -> None:
        """現在選択中の期間に応じてチャートを更新する."""
        current_index = self._combo.currentIndex()
        if current_index < 0 or current_index >= len(_PERIOD_LABELS):
            return

        period_type = _PERIOD_LABELS[current_index][0]
        chart_data = self._all_data.get(period_type)
        if chart_data is not None:
            self._chart.set_activity_data(chart_data)

        logger.debug(f"Activity chart section updated: period={period_type.value}")
