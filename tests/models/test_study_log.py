"""StudyLogモデルのテスト."""

from datetime import date, datetime

import pytest

from study_python.models.study_log import StudyLog


class TestStudyLogCreation:
    """StudyLogの生成テスト."""

    def test_create_with_required_fields(self):
        log = StudyLog(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
        )
        assert log.task_id == "task-1"
        assert log.study_date == date(2026, 2, 26)
        assert log.duration_minutes == 30
        assert log.memo == ""
        assert log.id  # UUIDが生成される

    def test_create_with_all_fields(self):
        now = datetime(2026, 2, 26, 10, 0, 0)
        log = StudyLog(
            id="log-1",
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=90,
            memo="集中して学習できた",
            created_at=now,
        )
        assert log.id == "log-1"
        assert log.duration_minutes == 90
        assert log.memo == "集中して学習できた"
        assert log.created_at == now


class TestStudyLogValidation:
    """StudyLogのバリデーションテスト."""

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="学習時間は1分以上"):
            StudyLog(
                task_id="task-1",
                study_date=date(2026, 2, 26),
                duration_minutes=0,
            )

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError, match="学習時間は1分以上"):
            StudyLog(
                task_id="task-1",
                study_date=date(2026, 2, 26),
                duration_minutes=-10,
            )

    def test_minimum_duration(self):
        log = StudyLog(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=1,
        )
        assert log.duration_minutes == 1


class TestStudyLogDurationHours:
    """duration_hoursプロパティのテスト."""

    def test_60_minutes_is_1_hour(self):
        log = StudyLog(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=60,
        )
        assert log.duration_hours == 1.0

    def test_90_minutes_is_1_5_hours(self):
        log = StudyLog(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=90,
        )
        assert log.duration_hours == 1.5

    def test_30_minutes_is_0_5_hours(self):
        log = StudyLog(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
        )
        assert log.duration_hours == 0.5


class TestStudyLogSerialization:
    """StudyLogの直列化テスト."""

    def test_to_dict(self):
        now = datetime(2026, 2, 26, 10, 0, 0)
        log = StudyLog(
            id="log-1",
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=45,
            memo="テストメモ",
            created_at=now,
        )
        d = log.to_dict()
        assert d["id"] == "log-1"
        assert d["task_id"] == "task-1"
        assert d["study_date"] == "2026-02-26"
        assert d["duration_minutes"] == 45
        assert d["memo"] == "テストメモ"
        assert d["created_at"] == "2026-02-26T10:00:00"

    def test_from_dict(self):
        data = {
            "id": "log-1",
            "task_id": "task-1",
            "study_date": "2026-02-26",
            "duration_minutes": 45,
            "memo": "テストメモ",
            "created_at": "2026-02-26T10:00:00",
        }
        log = StudyLog.from_dict(data)
        assert log.id == "log-1"
        assert log.task_id == "task-1"
        assert log.study_date == date(2026, 2, 26)
        assert log.duration_minutes == 45
        assert log.memo == "テストメモ"

    def test_from_dict_without_memo(self):
        data = {
            "id": "log-1",
            "task_id": "task-1",
            "study_date": "2026-02-26",
            "duration_minutes": 30,
            "created_at": "2026-02-26T10:00:00",
        }
        log = StudyLog.from_dict(data)
        assert log.memo == ""

    def test_roundtrip_serialization(self):
        original = StudyLog(
            task_id="task-1",
            study_date=date(2026, 3, 15),
            duration_minutes=120,
            memo="往復テスト",
        )
        restored = StudyLog.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.study_date == original.study_date
        assert restored.duration_minutes == original.duration_minutes
        assert restored.memo == original.memo
