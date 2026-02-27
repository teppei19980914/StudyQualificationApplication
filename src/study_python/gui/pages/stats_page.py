"""学習統計ページ."""

from __future__ import annotations

import logging
from collections import defaultdict

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
from study_python.gui.widgets.activity_chart_section import ActivityChartSection
from study_python.gui.widgets.consistency_card import ConsistencyCard
from study_python.gui.widgets.goal_stats_section import (
    GoalStatsDisplayData,
    GoalStatsSection,
)
from study_python.gui.widgets.milestone_button import MilestoneButton
from study_python.gui.widgets.notification_button import NotificationButton
from study_python.gui.widgets.personal_record_card import PersonalRecordCard
from study_python.gui.widgets.study_log_table import StudyLogEntry, StudyLogTable
from study_python.gui.widgets.today_study_banner import TodayStudyBanner
from study_python.models.task import BOOK_GANTT_GOAL_ID, TaskStatus
from study_python.services.book_service import BookService
from study_python.services.goal_service import GoalService
from study_python.services.motivation_calculator import MotivationCalculator
from study_python.services.notification_service import NotificationService
from study_python.services.study_log_service import StudyLogService
from study_python.services.study_stats_calculator import (
    ActivityPeriodType,
    StudyStatsCalculator,
)
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)

_TASK_STATUS_LABELS: dict[TaskStatus, str] = {
    TaskStatus.NOT_STARTED: "未着手",
    TaskStatus.IN_PROGRESS: "実施中",
    TaskStatus.COMPLETED: "完了",
}
_DELETED_STATUS_LABEL = "削除済み"


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
        self.setMinimumHeight(100)

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


class StatsPage(QWidget):
    """学習統計ページ."""

    def __init__(
        self,
        goal_service: GoalService,
        task_service: TaskService,
        study_log_service: StudyLogService,
        theme_manager: ThemeManager,
        book_service: BookService | None = None,
        notification_service: NotificationService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """StatsPageを初期化する.

        Args:
            goal_service: GoalService.
            task_service: TaskService.
            study_log_service: StudyLogService.
            theme_manager: テーママネージャ.
            book_service: BookService（読書統計用、省略可）.
            notification_service: 通知サービス.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal_service = goal_service
        self._task_service = task_service
        self._study_log_service = study_log_service
        self._theme_manager = theme_manager
        self._book_service = book_service
        self._notification_service = notification_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ページ全体のスクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 24, 32, 24)
        container_layout.setSpacing(16)

        # ヘッダー（タイトル + 実績ボタン）
        header_layout = QHBoxLayout()
        title = QLabel("学習統計")
        title.setObjectName("section_title")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._milestone_button = MilestoneButton(self._theme_manager)
        header_layout.addWidget(self._milestone_button)

        self._notification_button = NotificationButton(
            self._theme_manager, self._notification_service
        )
        header_layout.addWidget(self._notification_button)

        container_layout.addLayout(header_layout)

        desc = QLabel(
            "毎日の積み重ねが大きな成果につながります。"
            "学習の記録を振り返って、モチベーションを維持しましょう。"
        )
        desc.setObjectName("muted_text")
        desc.setWordWrap(True)
        container_layout.addWidget(desc)

        # 今日の学習状況バナー
        self._today_banner = TodayStudyBanner(self._theme_manager)
        container_layout.addWidget(self._today_banner)

        # サマリーカード（均等幅）
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)

        self._total_time_card = SummaryCard("⏱️", "0h", "合計学習時間")
        summary_layout.addWidget(self._total_time_card, 1)

        self._total_days_card = SummaryCard("📅", "0日", "学習日数")
        summary_layout.addWidget(self._total_days_card, 1)

        self._goal_count_card = SummaryCard("🎯", "0個", "目標数")
        summary_layout.addWidget(self._goal_count_card, 1)

        self._streak_card = SummaryCard("🔥", "0日", "連続学習")
        summary_layout.addWidget(self._streak_card, 1)

        container_layout.addLayout(summary_layout)

        # 自己ベスト記録
        self._personal_record_card = PersonalRecordCard(self._theme_manager)
        container_layout.addWidget(self._personal_record_card)

        # 学習実施率
        self._consistency_card = ConsistencyCard(self._theme_manager)
        container_layout.addWidget(self._consistency_card)

        # 学習アクティビティチャート
        self._activity_chart_section = ActivityChartSection(self._theme_manager)
        container_layout.addWidget(self._activity_chart_section)

        # 目標別統計（プルダウン切替）
        self._goal_stats_section = GoalStatsSection(self._theme_manager)
        container_layout.addWidget(self._goal_stats_section)

        # 学習ログ履歴テーブル（最下部）
        log_title = QLabel("学習ログ履歴")
        log_title.setObjectName("card_title")
        container_layout.addWidget(log_title)

        self._log_table = StudyLogTable(self._theme_manager)
        container_layout.addWidget(self._log_table)

        container_layout.addStretch()
        scroll.setWidget(container)
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
        self._milestone_button.set_data(milestone_data)

        if self._notification_service is not None:
            self._notification_service.check_and_create_achievement_notifications(
                milestone_data
            )
            unread = self._notification_service.get_unread_count()
            self._notification_button.update_badge(unread)

        record_data = motivation.calculate_personal_records(all_logs)
        self._personal_record_card.set_data(record_data)

        consistency_data = motivation.calculate_consistency(all_logs)
        self._consistency_card.set_data(consistency_data)

        # 学習アクティビティチャート
        calculator = StudyStatsCalculator()
        all_chart_data = {
            pt: calculator.calculate_activity(all_logs, pt) for pt in ActivityPeriodType
        }
        self._activity_chart_section.set_all_data(all_chart_data)

        # 学習ログ履歴テーブル
        all_tasks = self._task_service.get_all_tasks()
        task_name_map = {t.id: t.title for t in all_tasks}
        task_status_map = {t.id: t.status for t in all_tasks}

        # 既存ログのtask_nameバックフィル（タスク削除後も名前を表示するため）
        backfilled = self._study_log_service.backfill_task_names(task_name_map)
        if backfilled > 0:
            all_logs = self._study_log_service.get_all_logs()

        entries = [
            StudyLogEntry(
                study_date=log.study_date,
                task_name=task_name_map.get(log.task_id, log.task_name or log.task_id),
                duration_minutes=log.duration_minutes,
                memo=log.memo,
                task_status=self._resolve_task_status(log.task_id, task_status_map),
            )
            for log in sorted(all_logs, key=lambda x: x.study_date, reverse=True)
        ]
        self._log_table.set_entries(entries)

        # 目標別統計（目標データ）
        goal_display_data = []
        for goal in goals:
            tasks = self._task_service.get_tasks_for_goal(goal.id)
            task_ids = [t.id for t in tasks]
            task_names = {t.id: t.title for t in tasks}
            goal_stats = self._study_log_service.get_goal_stats(goal.id, task_ids)
            goal_display_data.append(
                GoalStatsDisplayData(
                    name=goal.what,
                    color=goal.color,
                    stats=goal_stats,
                    task_names=task_names,
                )
            )
        self._goal_stats_section.set_goal_data(goal_display_data)

        # 読書統計データ
        book_display_data = self._build_book_stats_data(task_name_map)
        self._goal_stats_section.set_book_data(book_display_data)

    def _build_book_stats_data(
        self, task_name_map: dict[str, str]
    ) -> list[GoalStatsDisplayData]:
        """読書統計データを構築する.

        Args:
            task_name_map: タスクID→タスク名のマッピング.

        Returns:
            読書統計表示データのリスト.
        """
        if self._book_service is None:
            return []

        book_tasks = self._task_service.get_tasks_for_goal(BOOK_GANTT_GOAL_ID)
        if not book_tasks:
            return []

        books = self._book_service.get_all_books()
        book_name_map = {b.id: b.title for b in books}

        # book_idでタスクをグループ化
        tasks_by_book: dict[str, list] = defaultdict(list)
        for task in book_tasks:
            book_id = task.book_id or "unknown"
            tasks_by_book[book_id].append(task)

        # 書籍アクセントカラー
        accent_color = "#CBA6F7"

        result: list[GoalStatsDisplayData] = []
        for book_id, tasks in tasks_by_book.items():
            book_name = book_name_map.get(book_id, book_id)
            task_ids = [t.id for t in tasks]
            task_names = {t.id: task_name_map.get(t.id, t.title) for t in tasks}
            book_stats = self._study_log_service.get_goal_stats(book_id, task_ids)
            result.append(
                GoalStatsDisplayData(
                    name=book_name,
                    color=accent_color,
                    stats=book_stats,
                    task_names=task_names,
                )
            )

        return result

    @staticmethod
    def _resolve_task_status(
        task_id: str,
        task_status_map: dict[str, TaskStatus],
    ) -> str:
        """タスクIDからステータスラベルを解決する.

        Args:
            task_id: タスクID.
            task_status_map: タスクID→ステータスのマップ.

        Returns:
            ステータスラベル文字列.
        """
        if task_id in task_status_map:
            status = task_status_map[task_id]
            return _TASK_STATUS_LABELS.get(status, status.value)
        return _DELETED_STATUS_LABEL

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self.refresh()
