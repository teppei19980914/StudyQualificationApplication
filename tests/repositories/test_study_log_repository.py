"""StudyLogRepositoryのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.models.study_log import StudyLog
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.study_log_repository import StudyLogRepository


@pytest.fixture
def repo(tmp_path: Path) -> StudyLogRepository:
    storage = JsonStorage(tmp_path / "study_logs.json")
    return StudyLogRepository(storage)


def _make_log(**kwargs) -> StudyLog:
    defaults = {
        "task_id": "task-1",
        "study_date": date(2026, 2, 26),
        "duration_minutes": 30,
    }
    defaults.update(kwargs)
    return StudyLog(**defaults)


class TestStudyLogRepositoryGetAll:
    """get_allメソッドのテスト."""

    def test_get_all_empty(self, repo):
        assert repo.get_all() == []

    def test_get_all_returns_logs(self, repo):
        log = _make_log()
        repo.add(log)
        logs = repo.get_all()
        assert len(logs) == 1
        assert logs[0].id == log.id


class TestStudyLogRepositoryGetByTaskId:
    """get_by_task_idメソッドのテスト."""

    def test_get_by_task_id(self, repo):
        repo.add(_make_log(task_id="task-1"))
        repo.add(_make_log(task_id="task-2"))
        repo.add(_make_log(task_id="task-1"))
        logs = repo.get_by_task_id("task-1")
        assert len(logs) == 2

    def test_get_by_task_id_empty(self, repo):
        assert repo.get_by_task_id("nonexistent") == []

    def test_get_by_task_id_sorted_by_date(self, repo):
        repo.add(_make_log(task_id="task-1", study_date=date(2026, 3, 15)))
        repo.add(_make_log(task_id="task-1", study_date=date(2026, 3, 1)))
        repo.add(_make_log(task_id="task-1", study_date=date(2026, 3, 10)))
        logs = repo.get_by_task_id("task-1")
        assert logs[0].study_date == date(2026, 3, 1)
        assert logs[1].study_date == date(2026, 3, 10)
        assert logs[2].study_date == date(2026, 3, 15)


class TestStudyLogRepositoryGetByTaskIds:
    """get_by_task_idsメソッドのテスト."""

    def test_get_by_task_ids(self, repo):
        repo.add(_make_log(task_id="task-1"))
        repo.add(_make_log(task_id="task-2"))
        repo.add(_make_log(task_id="task-3"))
        logs = repo.get_by_task_ids(["task-1", "task-3"])
        assert len(logs) == 2
        task_ids = {log.task_id for log in logs}
        assert task_ids == {"task-1", "task-3"}

    def test_get_by_task_ids_empty_list(self, repo):
        repo.add(_make_log(task_id="task-1"))
        assert repo.get_by_task_ids([]) == []

    def test_get_by_task_ids_sorted_by_date(self, repo):
        repo.add(_make_log(task_id="task-1", study_date=date(2026, 3, 15)))
        repo.add(_make_log(task_id="task-2", study_date=date(2026, 3, 1)))
        logs = repo.get_by_task_ids(["task-1", "task-2"])
        assert logs[0].study_date == date(2026, 3, 1)
        assert logs[1].study_date == date(2026, 3, 15)


class TestStudyLogRepositoryAdd:
    """addメソッドのテスト."""

    def test_add_log(self, repo):
        log = _make_log()
        repo.add(log)
        assert len(repo.get_all()) == 1

    def test_add_preserves_data(self, repo):
        log = _make_log(duration_minutes=90, memo="テストメモ")
        repo.add(log)
        loaded = repo.get_all()[0]
        assert loaded.duration_minutes == 90
        assert loaded.memo == "テストメモ"


class TestStudyLogRepositoryDelete:
    """deleteメソッドのテスト."""

    def test_delete_existing(self, repo):
        log = _make_log()
        repo.add(log)
        assert repo.delete(log.id) is True
        assert len(repo.get_all()) == 0

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete("nonexistent") is False

    def test_delete_preserves_others(self, repo):
        log1 = _make_log(duration_minutes=30)
        log2 = _make_log(duration_minutes=60)
        repo.add(log1)
        repo.add(log2)
        repo.delete(log1.id)
        remaining = repo.get_all()
        assert len(remaining) == 1
        assert remaining[0].id == log2.id


class TestStudyLogRepositoryUpdate:
    """updateメソッドのテスト."""

    def test_update_existing(self, repo):
        log = _make_log(memo="before")
        repo.add(log)
        log.memo = "after"
        assert repo.update(log) is True
        loaded = repo.get_all()[0]
        assert loaded.memo == "after"

    def test_update_nonexistent_returns_false(self, repo):
        log = _make_log()
        assert repo.update(log) is False

    def test_update_preserves_others(self, repo):
        log1 = _make_log(duration_minutes=30)
        log2 = _make_log(duration_minutes=60)
        repo.add(log1)
        repo.add(log2)
        log1.memo = "updated"
        repo.update(log1)
        logs = repo.get_all()
        assert len(logs) == 2
        updated = next(log for log in logs if log.id == log1.id)
        other = next(log for log in logs if log.id == log2.id)
        assert updated.memo == "updated"
        assert other.duration_minutes == 60

    def test_update_task_name(self, repo):
        log = _make_log(task_name="")
        repo.add(log)
        log.task_name = "Udemy学習"
        repo.update(log)
        loaded = repo.get_all()[0]
        assert loaded.task_name == "Udemy学習"


class TestStudyLogRepositoryDeleteByTaskId:
    """delete_by_task_idメソッドのテスト."""

    def test_delete_by_task_id(self, repo):
        repo.add(_make_log(task_id="task-1"))
        repo.add(_make_log(task_id="task-1"))
        repo.add(_make_log(task_id="task-2"))
        deleted = repo.delete_by_task_id("task-1")
        assert deleted == 2
        assert len(repo.get_all()) == 1

    def test_delete_by_task_id_none_found(self, repo):
        repo.add(_make_log(task_id="task-1"))
        deleted = repo.delete_by_task_id("task-99")
        assert deleted == 0
        assert len(repo.get_all()) == 1
