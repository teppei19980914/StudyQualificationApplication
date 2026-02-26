"""StatsPageのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.pages.stats_page import (
    GoalStatsCard,
    StatsPage,
    SummaryCard,
)
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.goal import WhenType
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.study_log_repository import StudyLogRepository
from study_python.repositories.task_repository import TaskRepository
from study_python.services.goal_service import GoalService
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
    return goal_service, task_service, study_log_service, theme_manager


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
        card = GoalStatsCard(
            goal_name="AWS資格",
            goal_color="#4A9EFF",
            stats=stats,
            task_names={"task-1": "Udemy学習", "task-2": "問題集"},
        )
        qtbot.addWidget(card)
        assert card.objectName() == "goal_stats_card"

    def test_card_with_no_tasks(self, qtbot):
        stats = GoalStudyStats(
            goal_id="goal-1",
            task_stats=[],
            total_minutes=0,
            total_study_days=0,
        )
        card = GoalStatsCard(
            goal_name="テスト",
            goal_color="#FF0000",
            stats=stats,
            task_names={},
        )
        qtbot.addWidget(card)
        assert card is not None


class TestStatsPage:
    """StatsPageのテスト."""

    def test_create_page(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        assert page is not None

    def test_refresh_empty(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "0min"
        assert page._total_days_card._value_label.text() == "0日"
        assert page._goal_count_card._value_label.text() == "0個"

    def test_refresh_with_data(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "2h 30min"
        assert page._total_days_card._value_label.text() == "2日"
        assert page._goal_count_card._value_label.text() == "1個"
        assert len(page._goal_cards) == 1

    def test_refresh_clears_old_cards(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
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
        assert len(page._goal_cards) == 1

        # 2回目のリフレッシュ（カードが重複しないこと）
        page.refresh()
        assert len(page._goal_cards) == 1

    def test_theme_changed(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.on_theme_changed()  # エラーなく実行

    def test_hours_format_over_1_hour(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "1h 15min"

    def test_minutes_only_format(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._total_time_card._value_label.text() == "45min"

    def test_refresh_populates_activity_chart(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._activity_chart._data is not None
        assert page._activity_chart._data.max_minutes == 60

    def test_refresh_populates_log_table(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._log_table._table.rowCount() == 2
        # 日付降順 → 最初の行は3/2
        assert page._log_table._table.item(0, 0).text() == "2026-03-02"
        assert page._log_table._table.item(0, 1).text() == "タスク1"

    def test_refresh_empty_chart_and_table(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._activity_chart._data is not None
        assert page._activity_chart._data.max_minutes == 0
        assert page._log_table._table.rowCount() == 0

    def test_refresh_populates_today_banner(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._today_banner._data is not None
        assert page._today_banner._data.studied is True
        assert page._today_banner._data.total_minutes == 45

    def test_refresh_populates_streak_card(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._streak_card._value_label.text() == "0日"

    def test_refresh_populates_milestone_section(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._milestone_section._data is not None

    def test_refresh_populates_weekly_card(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._weekly_card._data is not None
        assert page._weekly_card._data.this_week_minutes == 0

    def test_refresh_with_study_today_shows_streak(self, qtbot, stats_services):
        gs, ts, sls, tm = stats_services
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

        page = StatsPage(gs, ts, sls, tm)
        qtbot.addWidget(page)
        page.refresh()
        assert page._streak_card._value_label.text() == "2日"
