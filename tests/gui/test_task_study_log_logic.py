"""TaskStudyLogLogicのテスト."""

import time
from datetime import date

import pytest

from study_python.gui.dialogs.task_study_log_logic import (
    StudyLogDisplayEntry,
    TaskStudyLogLogic,
)
from study_python.services.study_log_service import StudyLogService


class TestTaskStudyLogLogicGetLogs:
    """ログ取得のテスト."""

    def test_get_logs_returns_entries(self, study_log_service: StudyLogService):
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
            memo="テスト",
            task_name="タスク1",
        )
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        logs = logic.get_logs()
        assert len(logs) == 1
        assert isinstance(logs[0], StudyLogDisplayEntry)
        assert logs[0].study_date == date(2026, 2, 25)
        assert logs[0].duration_minutes == 60
        assert logs[0].memo == "テスト"

    def test_get_logs_empty(self, study_log_service: StudyLogService):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        assert logic.get_logs() == []

    def test_get_logs_sorted_descending(self, study_log_service: StudyLogService):
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 20),
            duration_minutes=30,
        )
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 22),
            duration_minutes=45,
        )
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        logs = logic.get_logs()
        assert len(logs) == 3
        assert logs[0].study_date == date(2026, 2, 25)
        assert logs[1].study_date == date(2026, 2, 22)
        assert logs[2].study_date == date(2026, 2, 20)

    def test_get_logs_filters_by_task(self, study_log_service: StudyLogService):
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        study_log_service.add_study_log(
            task_id="task-2",
            study_date=date(2026, 2, 25),
            duration_minutes=30,
        )
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        logs = logic.get_logs()
        assert len(logs) == 1


class TestTaskStudyLogLogicGetStats:
    """統計取得のテスト."""

    def test_get_stats(self, study_log_service: StudyLogService):
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
        )
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        stats = logic.get_stats()
        assert stats.total_minutes == 90
        assert stats.study_days == 2
        assert stats.log_count == 2


class TestTaskStudyLogLogicAddLog:
    """ログ追加のテスト."""

    def test_add_log(self, study_log_service: StudyLogService):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        log = logic.add_log(
            study_date=date(2026, 2, 27),
            duration_minutes=45,
            memo="テストメモ",
        )
        assert log.task_id == "task-1"
        assert log.duration_minutes == 45
        assert log.task_name == "タスク1"
        # 永続化確認
        logs = logic.get_logs()
        assert len(logs) == 1

    def test_add_log_zero_duration_raises(self, study_log_service: StudyLogService):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        with pytest.raises(ValueError):
            logic.add_log(
                study_date=date(2026, 2, 27),
                duration_minutes=0,
            )


class TestTaskStudyLogLogicDeleteLog:
    """ログ削除のテスト."""

    def test_delete_log(self, study_log_service: StudyLogService):
        log = study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        assert logic.delete_log(log.id) is True
        assert logic.get_logs() == []

    def test_delete_log_nonexistent(self, study_log_service: StudyLogService):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        assert logic.delete_log("nonexistent-id") is False


class TestTaskStudyLogLogicValidateDuration:
    """時間検証のテスト."""

    def test_validate_duration_valid(self):
        assert TaskStudyLogLogic.validate_duration(1, 30) == 90
        assert TaskStudyLogLogic.validate_duration(0, 15) == 15
        assert TaskStudyLogLogic.validate_duration(2, 0) == 120

    def test_validate_duration_zero_raises(self):
        with pytest.raises(ValueError, match="1分以上"):
            TaskStudyLogLogic.validate_duration(0, 0)

    def test_validate_duration_negative_raises(self):
        with pytest.raises(ValueError, match="1分以上"):
            TaskStudyLogLogic.validate_duration(0, -5)


class TestTaskStudyLogLogicFormatDuration:
    """時間フォーマットのテスト."""

    def test_format_duration_hours_and_minutes(self):
        assert TaskStudyLogLogic.format_duration(90) == "1h 30min"
        assert TaskStudyLogLogic.format_duration(150) == "2h 30min"

    def test_format_duration_hours_only(self):
        assert TaskStudyLogLogic.format_duration(60) == "1h 00min"
        assert TaskStudyLogLogic.format_duration(120) == "2h 00min"

    def test_format_duration_minutes_only(self):
        assert TaskStudyLogLogic.format_duration(45) == "45min"
        assert TaskStudyLogLogic.format_duration(1) == "1min"

    def test_format_duration_zero(self):
        assert TaskStudyLogLogic.format_duration(0) == "0min"


class TestTaskStudyLogLogicTimer:
    """タイマーのテスト."""

    def test_start_timer(self, study_log_service: StudyLogService):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        assert logic.is_timer_running is False
        logic.start_timer()
        assert logic.is_timer_running is True

    def test_stop_timer(
        self, study_log_service: StudyLogService, monkeypatch: pytest.MonkeyPatch
    ):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        logic.start_timer()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 150)
        minutes = logic.stop_timer()
        assert minutes == 3
        assert logic.is_timer_running is False

    def test_stop_timer_min_1_minute(
        self, study_log_service: StudyLogService, monkeypatch: pytest.MonkeyPatch
    ):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        logic.start_timer()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 5)
        minutes = logic.stop_timer()
        assert minutes == 1

    def test_stop_timer_not_started_returns_zero(
        self, study_log_service: StudyLogService
    ):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        assert logic.stop_timer() == 0

    def test_elapsed_seconds(
        self, study_log_service: StudyLogService, monkeypatch: pytest.MonkeyPatch
    ):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        assert logic.elapsed_seconds == 0

        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        logic.start_timer()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 65)
        assert logic.elapsed_seconds == 65

    def test_stop_timer_ceil_up(
        self, study_log_service: StudyLogService, monkeypatch: pytest.MonkeyPatch
    ):
        logic = TaskStudyLogLogic(study_log_service, "task-1", "タスク1")
        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        logic.start_timer()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 61)
        minutes = logic.stop_timer()
        assert minutes == 2
