"""目標別統計セクションウィジェット."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

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
from study_python.services.study_log_service import GoalStudyStats


logger = logging.getLogger(__name__)


@dataclass
class GoalStatsDisplayData:
    """目標別統計カードの表示データ.

    Attributes:
        name: 目標名または書籍名.
        color: カラーコード.
        stats: 学習統計データ.
        task_names: {task_id: task_title}のマッピング.
    """

    name: str
    color: str
    stats: GoalStudyStats
    task_names: dict[str, str] = field(default_factory=dict)


_STATS_TYPE_LABELS: list[tuple[str, str]] = [
    ("goals", "目標"),
    ("books", "読書"),
]


class GoalStatsCard(QFrame):
    """目標別統計カード.

    目標名、カラーバー、タスク別の学習統計を表示する。
    """

    def __init__(
        self,
        display_data: GoalStatsDisplayData,
        parent: QWidget | None = None,
    ) -> None:
        """GoalStatsCardを初期化する.

        Args:
            display_data: 表示データ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("goal_stats_card")
        self._setup_ui(display_data)

    def _setup_ui(self, data: GoalStatsDisplayData) -> None:
        """UIを構築する.

        Args:
            data: 表示データ.
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # 目標名ヘッダー（カラーバー付き）
        header_layout = QHBoxLayout()
        color_bar = QFrame()
        color_bar.setFixedSize(4, 24)
        color_bar.setStyleSheet(f"background-color: {data.color}; border-radius: 2px;")
        header_layout.addWidget(color_bar)

        name_label = QLabel(data.name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # タスク別内訳
        for ts in data.stats.task_stats:
            task_name = data.task_names.get(ts.task_id, ts.task_id)
            hours = ts.total_minutes // 60
            mins = ts.total_minutes % 60
            time_text = f"{hours}h {mins:02d}min" if hours > 0 else f"{mins}min"

            task_layout = QHBoxLayout()
            task_label = QLabel(f"  {task_name}")
            task_label.setObjectName("muted_text")
            task_layout.addWidget(task_label)
            task_layout.addStretch()
            detail_label = QLabel(f"{time_text} / {ts.study_days}日")
            detail_label.setObjectName("muted_text")
            task_layout.addWidget(detail_label)
            layout.addLayout(task_layout)

        # 合計行
        total_hours = data.stats.total_minutes // 60
        total_mins = data.stats.total_minutes % 60
        total_time = (
            f"{total_hours}h {total_mins:02d}min"
            if total_hours > 0
            else f"{total_mins}min"
        )

        total_layout = QHBoxLayout()
        total_label = QLabel("  合計")
        total_label.setStyleSheet("font-weight: 600;")
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        total_value = QLabel(f"{total_time} / {data.stats.total_study_days}日")
        total_value.setStyleSheet("font-weight: 600;")
        total_layout.addWidget(total_value)
        layout.addLayout(total_layout)


class GoalStatsSection(QFrame):
    """プルダウン切替付き目標別統計セクション.

    「目標」「読書」をプルダウンで切り替えて統計カードを動的に表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _combo: 切替コンボボックス.
        _content_layout: カードコンテンツレイアウト.
        _goal_data: 目標統計データ.
        _book_data: 読書統計データ.
        _cards: 現在表示中のカードリスト.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """GoalStatsSectionを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._goal_data: list[GoalStatsDisplayData] = []
        self._book_data: list[GoalStatsDisplayData] = []
        self._cards: list[GoalStatsCard] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("goal_stats_section")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#goal_stats_section {{"
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

        title_icon = QLabel("\U0001f4ca")
        title_icon.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(title_icon)

        title_label = QLabel("目標別統計")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self._combo = QComboBox()
        for _key, label in _STATS_TYPE_LABELS:
            self._combo.addItem(label)
        self._combo.setCurrentIndex(0)
        self._combo.currentIndexChanged.connect(self._on_type_changed)
        header_layout.addWidget(self._combo)

        layout.addLayout(header_layout)

        # コンテンツエリア（カード動的生成）
        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(12)
        layout.addLayout(self._content_layout)

    def set_goal_data(self, data: list[GoalStatsDisplayData]) -> None:
        """目標統計データを設定する.

        Args:
            data: 目標統計表示データのリスト.
        """
        self._goal_data = data
        if self._get_current_type() == "goals":
            self._update_cards()

    def set_book_data(self, data: list[GoalStatsDisplayData]) -> None:
        """読書統計データを設定する.

        Args:
            data: 読書統計表示データのリスト.
        """
        self._book_data = data
        if self._get_current_type() == "books":
            self._update_cards()

    def _get_current_type(self) -> str:
        """現在選択中のタイプキーを返す.

        Returns:
            タイプキー文字列.
        """
        index = self._combo.currentIndex()
        if 0 <= index < len(_STATS_TYPE_LABELS):
            return _STATS_TYPE_LABELS[index][0]
        return "goals"

    def _on_type_changed(self, _index: int) -> None:
        """切替コンボボックスの変更ハンドラ.

        Args:
            _index: 新しい選択インデックス.
        """
        self._update_cards()

    def _update_cards(self) -> None:
        """現在の選択に応じてカードを再構築する."""
        self._clear_cards()

        current_type = self._get_current_type()
        data = self._goal_data if current_type == "goals" else self._book_data

        for item in data:
            card = GoalStatsCard(item)
            self._content_layout.addWidget(card)
            self._cards.append(card)

        logger.debug(
            f"GoalStatsSection updated: type={current_type}, cards={len(self._cards)}"
        )

    def _clear_cards(self) -> None:
        """表示中のカードをクリアする."""
        for card in self._cards:
            self._content_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
