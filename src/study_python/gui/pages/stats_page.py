"""学習統計ページ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.daily_activity_chart import DailyActivityChart
from study_python.gui.widgets.milestone_section import MilestoneSection
from study_python.gui.widgets.study_log_table import StudyLogEntry, StudyLogTable
from study_python.gui.widgets.today_study_banner import TodayStudyBanner
from study_python.gui.widgets.weekly_comparison_card import WeeklyComparisonCard
from study_python.services.goal_service import GoalService
from study_python.services.motivation_calculator import MotivationCalculator
from study_python.services.study_log_service import GoalStudyStats, StudyLogService
from study_python.services.study_stats_calculator import StudyStatsCalculator
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)


class SummaryCard(QFrame):
    """サマリーカード.

    アイコン・値・ラベルを表示するカード。

    Attributes:
        _value_label: 値のラベル.
    """

    def __init__(
        self,
        icon: str,
        value: str,
        label: str,
        parent: QWidget | None = None,
    ) -> None:
        """SummaryCardを初期化する.

        Args:
            icon: 表示アイコン.
            value: 値テキスト.
            label: 説明ラベル.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("summary_card")
        self.setMinimumSize(160, 100)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)

        self._value_label = QLabel(value)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self._value_label)

        desc_label = QLabel(label)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setObjectName("muted_text")
        layout.addWidget(desc_label)

    def set_value(self, value: str) -> None:
        """値を更新する.

        Args:
            value: 新しい値テキスト.
        """
        self._value_label.setText(value)


class GoalStatsCard(QFrame):
    """目標別統計カード.

    目標名、カラーバー、タスク別の学習統計を表示する。
    """

    def __init__(
        self,
        goal_name: str,
        goal_color: str,
        stats: GoalStudyStats,
        task_names: dict[str, str],
        parent: QWidget | None = None,
    ) -> None:
        """GoalStatsCardを初期化する.

        Args:
            goal_name: 目標名.
            goal_color: 目標の色.
            stats: 目標の学習統計.
            task_names: {task_id: task_title}のマッピング.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("goal_stats_card")
        self._setup_ui(goal_name, goal_color, stats, task_names)

    def _setup_ui(
        self,
        goal_name: str,
        goal_color: str,
        stats: GoalStudyStats,
        task_names: dict[str, str],
    ) -> None:
        """UIを構築する.

        Args:
            goal_name: 目標名.
            goal_color: 目標の色.
            stats: 目標の学習統計.
            task_names: {task_id: task_title}のマッピング.
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # 目標名ヘッダー（カラーバー付き）
        header_layout = QHBoxLayout()
        color_bar = QFrame()
        color_bar.setFixedSize(4, 24)
        color_bar.setStyleSheet(f"background-color: {goal_color}; border-radius: 2px;")
        header_layout.addWidget(color_bar)

        name_label = QLabel(goal_name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # タスク別内訳
        for ts in stats.task_stats:
            task_name = task_names.get(ts.task_id, ts.task_id)
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
        total_hours = stats.total_minutes // 60
        total_mins = stats.total_minutes % 60
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
        total_value = QLabel(f"{total_time} / {stats.total_study_days}日")
        total_value.setStyleSheet("font-weight: 600;")
        total_layout.addWidget(total_value)
        layout.addLayout(total_layout)


class StatsPage(QWidget):
    """学習統計ページ."""

    def __init__(
        self,
        goal_service: GoalService,
        task_service: TaskService,
        study_log_service: StudyLogService,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """StatsPageを初期化する.

        Args:
            goal_service: GoalService.
            task_service: TaskService.
            study_log_service: StudyLogService.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal_service = goal_service
        self._task_service = task_service
        self._study_log_service = study_log_service
        self._theme_manager = theme_manager
        self._goal_cards: list[GoalStatsCard] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ヘッダー
        title = QLabel("学習統計")
        title.setObjectName("section_title")
        layout.addWidget(title)

        desc = QLabel(
            "毎日の積み重ねが大きな成果につながります。"
            "学習の記録を振り返って、モチベーションを維持しましょう。"
        )
        desc.setObjectName("muted_text")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 今日の学習状況バナー
        self._today_banner = TodayStudyBanner(self._theme_manager)
        layout.addWidget(self._today_banner)

        # サマリーカード
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)

        self._total_time_card = SummaryCard("⏱️", "0h", "合計学習時間")
        summary_layout.addWidget(self._total_time_card)

        self._total_days_card = SummaryCard("📅", "0日", "学習日数")
        summary_layout.addWidget(self._total_days_card)

        self._goal_count_card = SummaryCard("🎯", "0個", "目標数")
        summary_layout.addWidget(self._goal_count_card)

        self._streak_card = SummaryCard("🔥", "0日", "連続学習")
        summary_layout.addWidget(self._streak_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # 週間比較 + マイルストーン（横並び）
        motivation_layout = QHBoxLayout()
        motivation_layout.setSpacing(16)

        self._weekly_card = WeeklyComparisonCard(self._theme_manager)
        motivation_layout.addWidget(self._weekly_card, 1)

        self._milestone_section = MilestoneSection(self._theme_manager)
        motivation_layout.addWidget(self._milestone_section, 1)

        layout.addLayout(motivation_layout)

        # 日別学習アクティビティチャート
        chart_title = QLabel("日別学習アクティビティ")
        chart_title.setObjectName("card_title")
        layout.addWidget(chart_title)

        self._activity_chart = DailyActivityChart(self._theme_manager)
        layout.addWidget(self._activity_chart)

        # 学習ログ履歴テーブル
        log_title = QLabel("学習ログ履歴")
        log_title.setObjectName("card_title")
        layout.addWidget(log_title)

        self._log_table = StudyLogTable(self._theme_manager)
        layout.addWidget(self._log_table)

        # スクロールエリア（目標別統計）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setSpacing(12)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll, 1)

    def refresh(self) -> None:
        """ページを更新する."""
        goals = self._goal_service.get_all_goals()
        all_logs = self._study_log_service.get_all_logs()

        # サマリー
        total_minutes = sum(log.duration_minutes for log in all_logs)
        unique_days = len({log.study_date for log in all_logs})
        hours = total_minutes // 60
        mins = total_minutes % 60
        time_text = f"{hours}h {mins:02d}min" if hours > 0 else f"{mins}min"

        self._total_time_card.set_value(time_text)
        self._total_days_card.set_value(f"{unique_days}日")
        self._goal_count_card.set_value(f"{len(goals)}個")

        # モチベーション機能
        motivation = MotivationCalculator()

        today_data = motivation.calculate_today_study(all_logs)
        self._today_banner.set_data(today_data)

        streak_data = motivation.calculate_streak(all_logs)
        self._streak_card.set_value(f"{streak_data.current_streak}日")

        milestone_data = motivation.calculate_milestones(
            all_logs, streak_data.current_streak
        )
        self._milestone_section.set_data(milestone_data)

        weekly_data = motivation.calculate_weekly_comparison(all_logs)
        self._weekly_card.set_data(weekly_data)

        # 日別アクティビティチャート
        calculator = StudyStatsCalculator()
        activity_data = calculator.calculate_daily_activity(all_logs)
        self._activity_chart.set_data(activity_data)

        # 学習ログ履歴テーブル
        all_tasks = self._task_service.get_all_tasks()
        task_name_map = {t.id: t.title for t in all_tasks}
        entries = [
            StudyLogEntry(
                study_date=log.study_date,
                task_name=task_name_map.get(log.task_id, log.task_id),
                duration_minutes=log.duration_minutes,
                memo=log.memo,
            )
            for log in sorted(all_logs, key=lambda x: x.study_date, reverse=True)
        ]
        self._log_table.set_entries(entries)

        # 目標別統計カードの再構築
        self._clear_goal_cards()

        for goal in goals:
            tasks = self._task_service.get_tasks_for_goal(goal.id)
            task_ids = [t.id for t in tasks]
            task_names = {t.id: t.title for t in tasks}
            goal_stats = self._study_log_service.get_goal_stats(goal.id, task_ids)

            card = GoalStatsCard(
                goal_name=goal.what,
                goal_color=goal.color,
                stats=goal_stats,
                task_names=task_names,
            )
            self._goal_cards.append(card)
            self._scroll_layout.addWidget(card)

    def _clear_goal_cards(self) -> None:
        """目標カードをクリアする."""
        for card in self._goal_cards:
            self._scroll_layout.removeWidget(card)
            card.deleteLater()
        self._goal_cards.clear()

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self.refresh()
