"""StudyLogServiceのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.study_log_repository import StudyLogRepository
from study_python.services.study_log_service import (
    GoalStudyStats,
    StudyLogService,
    TaskStudyStats,
)


@pytest.fixture
def service(tmp_path: Path) -> StudyLogService:
    storage = JsonStorage(tmp_path / "study_logs.json")
    repo = StudyLogRepository(storage)
    return StudyLogService(repo)


class TestTaskStudyStats:
    """TaskStudyStatsのテスト."""

    def test_total_hours(self):
        stats = TaskStudyStats(
            task_id="task-1",
            total_minutes=90,
            study_days=3,
            log_count=5,
        )
        assert stats.total_hours == 1.5

    def test_total_hours_zero(self):
        stats = TaskStudyStats(
            task_id="task-1",
            total_minutes=0,
            study_days=0,
            log_count=0,
        )
        assert stats.total_hours == 0.0


class TestGoalStudyStats:
    """GoalStudyStatsのテスト."""

    def test_total_hours(self):
        stats = GoalStudyStats(
            goal_id="goal-1",
            task_stats=[],
            total_minutes=150,
            total_study_days=5,
        )
        assert stats.total_hours == 2.5


class TestStudyLogServiceAddLog:
    """add_study_logメソッドのテスト."""

    def test_add_study_log(self, service):
        log = service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
        )
        assert log.task_id == "task-1"
        assert log.duration_minutes == 30
        assert log.id

    def test_add_study_log_with_memo(self, service):
        log = service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=60,
            memo="集中できた",
        )
        assert log.memo == "集中できた"

    def test_add_study_log_zero_duration_raises(self, service):
        with pytest.raises(ValueError, match="学習時間は1分以上"):
            service.add_study_log(
                task_id="task-1",
                study_date=date(2026, 2, 26),
                duration_minutes=0,
            )

    def test_add_study_log_with_task_name(self, service):
        log = service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
            task_name="Udemy学習",
        )
        assert log.task_name == "Udemy学習"

    def test_add_study_log_task_name_persisted(self, service):
        service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
            task_name="テスト",
        )
        logs = service.get_all_logs()
        assert logs[0].task_name == "テスト"

    def test_add_study_log_persisted(self, service):
        service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
        )
        logs = service.get_all_logs()
        assert len(logs) == 1


class TestStudyLogServiceGetLogs:
    """ログ取得メソッドのテスト."""

    def test_get_logs_for_task(self, service):
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-2", date(2026, 2, 26), 60)
        service.add_study_log("task-1", date(2026, 2, 27), 45)
        logs = service.get_logs_for_task("task-1")
        assert len(logs) == 2

    def test_get_logs_for_task_empty(self, service):
        assert service.get_logs_for_task("nonexistent") == []

    def test_get_all_logs(self, service):
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-2", date(2026, 2, 26), 60)
        logs = service.get_all_logs()
        assert len(logs) == 2


class TestStudyLogServiceDeleteLog:
    """delete_logメソッドのテスト."""

    def test_delete_log(self, service):
        log = service.add_study_log("task-1", date(2026, 2, 26), 30)
        assert service.delete_log(log.id) is True
        assert len(service.get_all_logs()) == 0

    def test_delete_nonexistent_log(self, service):
        assert service.delete_log("nonexistent") is False


class TestStudyLogServiceTaskStats:
    """get_task_statsメソッドのテスト."""

    def test_task_stats_basic(self, service):
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-1", date(2026, 2, 27), 60)
        stats = service.get_task_stats("task-1")
        assert stats.task_id == "task-1"
        assert stats.total_minutes == 90
        assert stats.study_days == 2
        assert stats.log_count == 2

    def test_task_stats_same_day_multiple_logs(self, service):
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-1", date(2026, 2, 26), 45)
        stats = service.get_task_stats("task-1")
        assert stats.total_minutes == 75
        assert stats.study_days == 1  # ユニーク日数
        assert stats.log_count == 2

    def test_task_stats_no_logs(self, service):
        stats = service.get_task_stats("task-1")
        assert stats.total_minutes == 0
        assert stats.study_days == 0
        assert stats.log_count == 0


class TestStudyLogServiceGoalStats:
    """get_goal_statsメソッドのテスト."""

    def test_goal_stats_basic(self, service):
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-1", date(2026, 2, 27), 60)
        service.add_study_log("task-2", date(2026, 2, 26), 45)
        stats = service.get_goal_stats("goal-1", ["task-1", "task-2"])
        assert stats.goal_id == "goal-1"
        assert stats.total_minutes == 135
        assert stats.total_study_days == 2  # 2/26と2/27
        assert len(stats.task_stats) == 2

    def test_goal_stats_task_breakdown(self, service):
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-2", date(2026, 2, 26), 60)
        stats = service.get_goal_stats("goal-1", ["task-1", "task-2"])
        task1_stats = stats.task_stats[0]
        task2_stats = stats.task_stats[1]
        assert task1_stats.task_id == "task-1"
        assert task1_stats.total_minutes == 30
        assert task2_stats.task_id == "task-2"
        assert task2_stats.total_minutes == 60

    def test_goal_stats_no_tasks(self, service):
        stats = service.get_goal_stats("goal-1", [])
        assert stats.total_minutes == 0
        assert stats.total_study_days == 0
        assert stats.task_stats == []

    def test_goal_stats_cross_task_unique_days(self, service):
        """異なるタスクで同じ日に学習→ユニーク日数は1."""
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-2", date(2026, 2, 26), 45)
        stats = service.get_goal_stats("goal-1", ["task-1", "task-2"])
        assert stats.total_study_days == 1

    def test_goal_stats_task_with_no_logs(self, service):
        """ログのないタスクも統計に含まれる."""
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        stats = service.get_goal_stats("goal-1", ["task-1", "task-2"])
        assert len(stats.task_stats) == 2
        task2_stats = stats.task_stats[1]
        assert task2_stats.total_minutes == 0
        assert task2_stats.study_days == 0


class TestStudyLogServiceBackfillTaskNames:
    """backfill_task_namesメソッドのテスト."""

    def test_backfill_updates_empty_task_name(self, service):
        """task_nameが空のログにタスク名がバックフィルされる."""
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        updated = service.backfill_task_names({"task-1": "Udemy学習"})
        assert updated == 1
        logs = service.get_all_logs()
        assert logs[0].task_name == "Udemy学習"

    def test_backfill_skips_already_set(self, service):
        """task_nameが既に設定済みのログはスキップされる."""
        service.add_study_log("task-1", date(2026, 2, 26), 30, task_name="既存名")
        updated = service.backfill_task_names({"task-1": "新しい名前"})
        assert updated == 0
        logs = service.get_all_logs()
        assert logs[0].task_name == "既存名"

    def test_backfill_skips_unknown_task(self, service):
        """task_name_mapに存在しないタスクはスキップされる."""
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        updated = service.backfill_task_names({"task-99": "存在しないタスク"})
        assert updated == 0

    def test_backfill_returns_zero_when_no_logs(self, service):
        """ログがない場合は0を返す."""
        updated = service.backfill_task_names({"task-1": "テスト"})
        assert updated == 0

    def test_backfill_multiple_logs(self, service):
        """複数のログが同時にバックフィルされる."""
        service.add_study_log("task-1", date(2026, 2, 26), 30)
        service.add_study_log("task-2", date(2026, 2, 27), 60)
        service.add_study_log("task-1", date(2026, 2, 28), 45)
        updated = service.backfill_task_names(
            {"task-1": "タスク1", "task-2": "タスク2"}
        )
        assert updated == 3
        logs = service.get_all_logs()
        for log in logs:
            if log.task_id == "task-1":
                assert log.task_name == "タスク1"
            else:
                assert log.task_name == "タスク2"
