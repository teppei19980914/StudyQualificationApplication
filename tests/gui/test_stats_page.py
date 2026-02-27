"""StatsPageのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.pages.stats_page import (
    StatsPage,
    SummaryCard,
)
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.goal_stats_section import (
    GoalStatsCard,
    GoalStatsDisplayData,
)
from study_python.models.goal import WhenType
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository
from study_python.repositories.study_log_repository import StudyLogRepository
from study_python.repositories.task_repository import TaskRepository
from study_python.services.goal_service import GoalService
from study_python.services.notification_service import NotificationService
from study_python.services.study_log_service import (
    GoalStudyStats,
    StudyLogService,
    TaskStudyStats,
)
from study_python.services.task_service import TaskService


@pytest.fixture
def stats_services(tmp_path: Path):
    goal_storage = JsonStorage(tmp_path / "goals.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    log_storage = JsonStorage(tmp_path / "study_logs.json")
    goal_repo = GoalRepository(goal_storage)
    task_repo = TaskRepository(task_storage)
    log_repo = StudyLogRepository(log_storage)
    goal_service = GoalService(goal_repo, task_repo)
    task_service = TaskService(task_repo)
    study_log_service = StudyLogService(log_repo)
    theme_manager = ThemeManager(tmp_path / "settings.json")
    notification_storage = JsonStorage(tmp_path / "notifications.json")
    notification_repo = NotificationRepository(notification_storage)
    notification_service = NotificationService(notification_repo)
    return (
        goal_service,
        task_service,
        study_log_service,
        theme_manager,
        notification_service,
    )


class TestSummaryCard:
    """SummaryCardのテスト."""

    def test_create_card(self, qtbot):
        card = SummaryCard("⏱️", "10h", "合計学習時間")
        qtbot.addWidget(card)
        assert card._value_label.text() == "10h"

    def test_set_value(self, qtbot):
        card = SummaryCard("📅", "0日", "学習日数")
        qtbot.addWidget(card)
        card.set_value("15日")
        assert card._value_label.text() == "15日"


class TestGoalStatsCard:
    """GoalStatsCardのテスト."""

    def test_create_card(self, qtbot):
        stats = GoalStudyStats(
            goal_id="goal-1",
            task_stats=[
                TaskStudyStats(
                    task_id="task-1", total_minutes=90, study_days=3, log_count=5
                ),
                TaskStudyStats(
                    task_id="task-2", total_minutes=60, study_days=2, log_count=3
                ),
            ],
            total_minutes=150,
            total_study_days=4,
        )
        data = GoalStatsDisplayData(
            name="AWS資格",
            color="#4A9EFF",
            stats=stats,
            task_names={"task-1": "Udemy学習", "task-2": "問題集"},
        )
        card = GoalStatsCard(data)
        qtbot.addWidget(card)
        assert card.objectName() == "goal_stats_card"

    def test_card_with_no_tasks(self, qtbot):
        stats = GoalStudyStats(
            goal_id="goal-1",
            task_stats=[],
            total_minutes=0,
            total_study_days=0,
        )
        data = GoalStatsDisplayData(
            name="テスト",
            color="#FF0000",
            stats=stats,
            task_names={},
        )
        card = GoalStatsCard(data)
        qtbot.addWidget(card)
        assert card is not None


class TestStatsPage:
    """StatsPageのテスト."""

    def test_create_page(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        assert page is not None

    def test_refresh_empty(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "0min"
        assert page._total_days_card._value_label.text() == "0日"
        assert page._goal_count_card._value_label.text() == "0個"

    def test_refresh_with_data(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        # データ作成
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 60)
        sls.add_study_log(task.id, date(2026, 3, 2), 90)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "2h 30min"
        assert page._total_days_card._value_label.text() == "2日"
        assert page._goal_count_card._value_label.text() == "1個"
        assert len(page._goal_stats_section._cards) == 1

    def test_refresh_clears_old_cards(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)

        # 1回目のリフレッシュ
        gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page.refresh()
        assert len(page._goal_stats_section._cards) == 1

        # 2回目のリフレッシュ（カードが重複しないこと）
        page.refresh()
        assert len(page._goal_stats_section._cards) == 1

    def test_theme_changed(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.on_theme_changed()  # エラーなく実行

    def test_hours_format_over_1_hour(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 75)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "1h 15min"

    def test_minutes_only_format(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 45)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "45min"

    def test_refresh_populates_activity_chart_section(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date.today(), 60)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert len(page._activity_chart_section._all_data) == 4

    def test_refresh_populates_log_table(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 60, "メモA")
        sls.add_study_log(task.id, date(2026, 3, 2), 30, "メモB")

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._log_table._table.rowCount() == 2
        # 日付降順 → 最初の行は3/2
        assert page._log_table._table.item(0, 0).text() == "2026-03-02"
        assert page._log_table._table.item(0, 1).text() == "タスク1"
        # ステータス列（未着手）
        assert page._log_table._table.item(0, 2).text() == "未着手"

    def test_refresh_shows_deleted_status(self, qtbot, stats_services):
        """タスク削除後にステータスが「削除済み」と表示される."""
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="削除対象タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 60, task_name="削除対象タスク")
        ts.delete_task(task.id)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._log_table._table.rowCount() == 1
        assert page._log_table._table.item(0, 1).text() == "削除対象タスク"
        assert page._log_table._table.item(0, 2).text() == "削除済み"

    def test_refresh_uses_stored_task_name_when_deleted(self, qtbot, stats_services):
        """タスク削除後に保存済みtask_nameが表示される."""
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="保存テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 30, task_name="保存テスト")
        ts.delete_task(task.id)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        # UUID ではなく保存済みタスク名が表示される
        assert page._log_table._table.item(0, 1).text() == "保存テスト"

    def test_refresh_backfills_task_name_for_old_logs(self, qtbot, stats_services):
        """task_nameが空の既存ログにタスク名がバックフィルされる."""
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="バックフィル対象",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        # task_name未設定で記録（旧バージョンのログを模倣）
        sls.add_study_log(task.id, date(2026, 3, 1), 30)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        # バックフィルされてタスク名が表示される
        assert page._log_table._table.item(0, 1).text() == "バックフィル対象"

    def test_refresh_backfill_then_delete_shows_name(self, qtbot, stats_services):
        """バックフィル後にタスクを削除してもタスク名が表示される."""
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="削除前バックフィル",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        # task_name未設定で記録
        sls.add_study_log(task.id, date(2026, 3, 1), 30)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        # 1回目のrefreshでバックフィル
        page.refresh()
        assert page._log_table._table.item(0, 1).text() == "削除前バックフィル"

        # タスクを削除
        ts.delete_task(task.id)
        # 2回目のrefresh
        page.refresh()
        # バックフィル済みのため、タスク名が表示される
        assert page._log_table._table.item(0, 1).text() == "削除前バックフィル"
        assert page._log_table._table.item(0, 2).text() == "削除済み"

    def test_refresh_shows_task_status_labels(self, qtbot, stats_services):
        """各ステータスのラベルが正しく表示される."""
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="進捗タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date(2026, 3, 1), 30)
        # 進捗率を変更（ステータスは自動決定される）
        ts.update_progress(task.id, 50)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._log_table._table.item(0, 2).text() == "実施中"

    def test_refresh_empty_chart_and_table(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert len(page._activity_chart_section._all_data) == 4
        assert page._log_table._table.rowCount() == 0

    def test_refresh_populates_today_banner(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date.today(), 45)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._today_banner._data is not None
        assert page._today_banner._data.studied is True
        assert page._today_banner._data.total_minutes == 45

    def test_refresh_populates_streak_card(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._streak_card._value_label.text() == "0日"

    def test_refresh_populates_milestone_button(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._milestone_button._data is not None

    def test_refresh_with_study_today_shows_streak(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        # 今日と昨日に学習 → ストリーク2日
        from datetime import timedelta

        sls.add_study_log(task.id, date.today(), 30)
        sls.add_study_log(task.id, date.today() - timedelta(days=1), 30)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._streak_card._value_label.text() == "2日"

    def test_refresh_populates_personal_record_card(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._personal_record_card._data is not None
        assert page._personal_record_card._data.total_study_days == 0

    def test_refresh_populates_consistency_card(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()
        assert page._consistency_card._data is not None
        assert page._consistency_card._data.overall_rate == 0.0

    def test_refresh_with_data_populates_new_cards(self, qtbot, stats_services):
        gs, ts, sls, tm, ns = stats_services
        goal = gs.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS",
            how="Udemy",
        )
        task = ts.create_task(
            goal_id=goal.id,
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        sls.add_study_log(task.id, date.today(), 60)

        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        page.refresh()

        # 自己ベストカードにデータが入っている
        assert page._personal_record_card._data is not None
        assert page._personal_record_card._data.best_day_minutes == 60
        assert page._personal_record_card._data.total_study_days == 1

        # 実施率カードにデータが入っている
        assert page._consistency_card._data is not None
        assert page._consistency_card._data.overall_study_days == 1

    def test_milestone_button_in_header(self, qtbot, stats_services):
        """実績ボタンがヘッダーに存在する."""
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        assert page._milestone_button is not None
        assert "\U0001f3c6" in page._milestone_button.text()

    def test_notification_button_in_header(self, qtbot, stats_services):
        """通知ボタンがヘッダーに存在する."""
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        assert page._notification_button is not None
        assert "\U0001f514" in page._notification_button.text()

    def test_goal_stats_section_exists(self, qtbot, stats_services):
        """GoalStatsSectionが存在する."""
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        assert page._goal_stats_section is not None
        assert page._goal_stats_section._combo.count() == 2

    def test_build_book_stats_data_without_book_service(self, qtbot, stats_services):
        """book_serviceなしの場合は空リストを返す."""
        gs, ts, sls, tm, ns = stats_services
        page = StatsPage(gs, ts, sls, tm, notification_service=ns)
        qtbot.addWidget(page)
        result = page._build_book_stats_data({})
        assert result == []
