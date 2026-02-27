"""BookGanttServiceのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.models.book import Book, BookStatus
from study_python.models.task import TaskStatus
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.book_gantt_service import (
    BOOK_GANTT_GOAL_ID,
    BookGanttService,
)
from study_python.services.book_service import BookService
from study_python.services.task_service import TaskService


@pytest.fixture
def task_repo(tmp_path: Path) -> TaskRepository:
    """共有TaskRepositoryフィクスチャ."""
    task_storage = JsonStorage(tmp_path / "tasks.json")
    return TaskRepository(task_storage)


@pytest.fixture
def book_service(tmp_path: Path, task_repo: TaskRepository) -> BookService:
    """BookServiceフィクスチャ."""
    book_storage = JsonStorage(tmp_path / "books.json")
    book_repo = BookRepository(book_storage)
    return BookService(book_repo, task_repo)


@pytest.fixture
def task_service(task_repo: TaskRepository) -> TaskService:
    """TaskServiceフィクスチャ."""
    return TaskService(task_repo)


@pytest.fixture
def service(book_service: BookService, task_service: TaskService) -> BookGanttService:
    """BookGanttServiceフィクスチャ."""
    return BookGanttService(book_service, task_service)


class TestGetScheduledBooks:
    """get_scheduled_booksのテスト."""

    def test_empty(self, service: BookGanttService) -> None:
        assert service.get_scheduled_books() == []

    def test_only_scheduled(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        book.start_date = date(2026, 3, 1)
        book.end_date = date(2026, 3, 31)
        book_service.book_repo.update(book)

        book_service.create_book("未スケジュール本")

        result = service.get_scheduled_books()
        assert len(result) == 1
        assert result[0].title == "テスト本"

    def test_excludes_unscheduled(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book_service.create_book("未スケジュール")
        assert service.get_scheduled_books() == []


class TestGetUnscheduledBooks:
    """get_unscheduled_booksのテスト."""

    def test_empty(self, service: BookGanttService) -> None:
        assert service.get_unscheduled_books() == []

    def test_only_unscheduled(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book_service.create_book("未スケジュール本")
        book = book_service.create_book("スケジュール済み")
        book.start_date = date(2026, 3, 1)
        book.end_date = date(2026, 3, 31)
        book_service.book_repo.update(book)

        result = service.get_unscheduled_books()
        assert len(result) == 1
        assert result[0].title == "未スケジュール本"


class TestBooksToTasks:
    """books_to_tasksのテスト."""

    def test_converts_book_to_task(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("Python入門")
        book.start_date = date(2026, 3, 1)
        book.end_date = date(2026, 3, 31)
        book.progress = 50
        book.status = BookStatus.READING
        book_service.book_repo.update(book)

        tasks = service.books_to_tasks([book])
        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == book.id
        assert task.start_date == date(2026, 3, 1)
        assert task.end_date == date(2026, 3, 31)
        assert task.progress == 50
        assert task.status == TaskStatus.IN_PROGRESS

    def test_skips_unscheduled(self, service: BookGanttService) -> None:
        book = Book(title="未スケジュール")
        tasks = service.books_to_tasks([book])
        assert tasks == []

    def test_status_mapping_unread(self, service: BookGanttService) -> None:
        book = Book(
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            status=BookStatus.UNREAD,
        )
        tasks = service.books_to_tasks([book])
        assert tasks[0].status == TaskStatus.NOT_STARTED

    def test_status_mapping_reading(self, service: BookGanttService) -> None:
        book = Book(
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            status=BookStatus.READING,
        )
        tasks = service.books_to_tasks([book])
        assert tasks[0].status == TaskStatus.IN_PROGRESS

    def test_status_mapping_completed(self, service: BookGanttService) -> None:
        book = Book(
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            status=BookStatus.COMPLETED,
            progress=100,
        )
        tasks = service.books_to_tasks([book])
        assert tasks[0].status == TaskStatus.COMPLETED

    def test_task_goal_id_is_sentinel(self, service: BookGanttService) -> None:
        book = Book(
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        tasks = service.books_to_tasks([book])
        assert tasks[0].goal_id == BOOK_GANTT_GOAL_ID

    def test_title_prefix(self, service: BookGanttService) -> None:
        book = Book(
            title="Python入門",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        tasks = service.books_to_tasks([book])
        assert "Python入門" in tasks[0].title
        assert "\U0001f4d6" in tasks[0].title

    def test_progress_preserved(self, service: BookGanttService) -> None:
        book = Book(
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=75,
        )
        tasks = service.books_to_tasks([book])
        assert tasks[0].progress == 75


class TestCreateBookWithSchedule:
    """create_book_with_scheduleのテスト."""

    def test_create_success(self, service: BookGanttService) -> None:
        book = service.create_book_with_schedule(
            title="テスト本",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert book.title == "テスト本"
        assert book.start_date == date(2026, 3, 1)
        assert book.end_date == date(2026, 3, 31)
        assert book.has_schedule is True

    def test_create_empty_title_raises(self, service: BookGanttService) -> None:
        with pytest.raises(ValueError, match="書籍名は必須です"):
            service.create_book_with_schedule(
                title="",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
            )

    def test_create_invalid_dates_raises(self, service: BookGanttService) -> None:
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            service.create_book_with_schedule(
                title="テスト",
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 1),
            )


class TestSetBookSchedule:
    """set_book_scheduleのテスト."""

    def test_set_schedule_success(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        result = service.set_book_schedule(
            book_id=book.id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result is not None
        assert result.start_date == date(2026, 3, 1)
        assert result.end_date == date(2026, 3, 31)

    def test_set_schedule_nonexistent(self, service: BookGanttService) -> None:
        result = service.set_book_schedule(
            book_id="nonexistent",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert result is None

    def test_set_schedule_invalid_dates_raises(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            service.set_book_schedule(
                book_id=book.id,
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 1),
            )


class TestUpdateBookSchedule:
    """update_book_scheduleのテスト."""

    def test_update_success(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        result = service.update_book_schedule(
            book_id=book.id,
            title="更新後タイトル",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=50,
        )
        assert result is not None
        assert result.title == "更新後タイトル"
        assert result.progress == 50
        assert result.status == BookStatus.READING

    def test_update_nonexistent(self, service: BookGanttService) -> None:
        result = service.update_book_schedule(
            book_id="nonexistent",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=0,
        )
        assert result is None

    def test_update_empty_title_raises(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        with pytest.raises(ValueError, match="書籍名は必須です"):
            service.update_book_schedule(
                book_id=book.id,
                title="",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
                progress=0,
            )

    def test_update_invalid_progress_raises(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        with pytest.raises(ValueError, match="進捗率は0-100"):
            service.update_book_schedule(
                book_id=book.id,
                title="テスト",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
                progress=150,
            )

    def test_update_invalid_dates_raises(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            service.update_book_schedule(
                book_id=book.id,
                title="テスト",
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 1),
                progress=0,
            )

    def test_auto_status_from_progress(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        """進捗率からステータスが自動決定される."""
        book = book_service.create_book("テスト本")
        # 0% → 未読
        result = service.update_book_schedule(
            book_id=book.id,
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=0,
        )
        assert result is not None
        assert result.status == BookStatus.UNREAD

        # 50% → 読書中
        result = service.update_book_schedule(
            book_id=book.id,
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=50,
        )
        assert result is not None
        assert result.status == BookStatus.READING

        # 100% → 読了
        result = service.update_book_schedule(
            book_id=book.id,
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=100,
        )
        assert result is not None
        assert result.status == BookStatus.COMPLETED


class TestClearBookSchedule:
    """clear_book_scheduleのテスト."""

    def test_clear_success(
        self, service: BookGanttService, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト本")
        book.start_date = date(2026, 3, 1)
        book.end_date = date(2026, 3, 31)
        book.progress = 50
        book_service.book_repo.update(book)

        result = service.clear_book_schedule(book.id)
        assert result is not None
        assert result.start_date is None
        assert result.end_date is None
        assert result.progress == 0
        assert result.has_schedule is False

    def test_clear_nonexistent(self, service: BookGanttService) -> None:
        result = service.clear_book_schedule("nonexistent")
        assert result is None


class TestStatusMapping:
    """ステータスマッピングのテスト."""

    def test_book_to_task_unread(self) -> None:
        assert (
            BookGanttService.book_status_to_task_status(BookStatus.UNREAD)
            == TaskStatus.NOT_STARTED
        )

    def test_book_to_task_reading(self) -> None:
        assert (
            BookGanttService.book_status_to_task_status(BookStatus.READING)
            == TaskStatus.IN_PROGRESS
        )

    def test_book_to_task_completed(self) -> None:
        assert (
            BookGanttService.book_status_to_task_status(BookStatus.COMPLETED)
            == TaskStatus.COMPLETED
        )

    def test_task_to_book_not_started(self) -> None:
        assert (
            BookGanttService.task_status_to_book_status(TaskStatus.NOT_STARTED)
            == BookStatus.UNREAD
        )

    def test_task_to_book_in_progress(self) -> None:
        assert (
            BookGanttService.task_status_to_book_status(TaskStatus.IN_PROGRESS)
            == BookStatus.READING
        )

    def test_task_to_book_completed(self) -> None:
        assert (
            BookGanttService.task_status_to_book_status(TaskStatus.COMPLETED)
            == BookStatus.COMPLETED
        )


class TestSyncBookProgress:
    """sync_book_progressのテスト."""

    def test_sync_average_progress(
        self,
        service: BookGanttService,
        book_service: BookService,
        task_service: TaskService,
    ) -> None:
        """タスクの進捗平均が書籍に反映される."""
        book = book_service.create_book("テスト本")
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
            book_id=book.id,
        )
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章2",
            start_date=date(2026, 3, 11),
            end_date=date(2026, 3, 20),
            book_id=book.id,
        )
        # 進捗を更新
        tasks = task_service.get_tasks_for_book(book.id)
        task_service.update_progress(tasks[0].id, 60)
        task_service.update_progress(tasks[1].id, 40)

        service.sync_book_progress(book.id)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.progress == 50
        assert updated.status == BookStatus.READING

    def test_sync_no_tasks(
        self,
        service: BookGanttService,
        book_service: BookService,
    ) -> None:
        """タスク0件の場合、progress=0でstart/end=None."""
        book = book_service.create_book("テスト本")
        book.start_date = date(2026, 3, 1)
        book.end_date = date(2026, 3, 31)
        book.progress = 50
        book_service.book_repo.update(book)

        service.sync_book_progress(book.id)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.progress == 0
        assert updated.status == BookStatus.UNREAD
        assert updated.start_date is None
        assert updated.end_date is None

    def test_sync_100_percent(
        self,
        service: BookGanttService,
        book_service: BookService,
        task_service: TaskService,
    ) -> None:
        """全タスク100%で書籍も完了."""
        book = book_service.create_book("テスト本")
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id=book.id,
        )
        tasks = task_service.get_tasks_for_book(book.id)
        task_service.update_progress(tasks[0].id, 100)

        service.sync_book_progress(book.id)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.progress == 100
        assert updated.status == BookStatus.COMPLETED

    def test_sync_progress_rounds(
        self,
        service: BookGanttService,
        book_service: BookService,
        task_service: TaskService,
    ) -> None:
        """進捗平均がroundされる（例: 33+67=50ではなく33.3→33）."""
        book = book_service.create_book("テスト本")
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
            book_id=book.id,
        )
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章2",
            start_date=date(2026, 3, 11),
            end_date=date(2026, 3, 20),
            book_id=book.id,
        )
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章3",
            start_date=date(2026, 3, 21),
            end_date=date(2026, 3, 31),
            book_id=book.id,
        )
        tasks = task_service.get_tasks_for_book(book.id)
        task_service.update_progress(tasks[0].id, 100)
        # 他は0% → avg = 33.33... → round → 33

        service.sync_book_progress(book.id)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.progress == 33

    def test_sync_nonexistent_book(
        self,
        service: BookGanttService,
    ) -> None:
        """存在しないbookではエラーにならない."""
        service.sync_book_progress("nonexistent-id")

    def test_sync_without_task_service(
        self,
        book_service: BookService,
    ) -> None:
        """task_serviceなしでは何もしない."""
        service = BookGanttService(book_service)
        book = book_service.create_book("テスト本")
        service.sync_book_progress(book.id)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.progress == 0

    def test_sync_updates_dates(
        self,
        service: BookGanttService,
        book_service: BookService,
        task_service: TaskService,
    ) -> None:
        """タスクのmin(start)/max(end)が書籍日付に反映."""
        book = book_service.create_book("テスト本")
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章1",
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 20),
            book_id=book.id,
        )
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="章2",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            book_id=book.id,
        )
        service.sync_book_progress(book.id)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.start_date == date(2026, 3, 1)
        assert updated.end_date == date(2026, 3, 31)


class TestGetAllBookTasks:
    """get_all_book_tasksのテスト."""

    def test_empty(
        self,
        service: BookGanttService,
    ) -> None:
        assert service.get_all_book_tasks() == []

    def test_returns_only_book_tasks(
        self,
        service: BookGanttService,
        task_service: TaskService,
    ) -> None:
        """BOOK_GANTT_GOAL_IDのタスクのみ返す."""
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="書籍タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id="book-1",
        )
        task_service.create_task(
            goal_id="goal-1",
            title="通常タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        tasks = service.get_all_book_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "書籍タスク"

    def test_without_task_service(
        self,
        book_service: BookService,
    ) -> None:
        """task_serviceなしでは空リスト."""
        service = BookGanttService(book_service)
        assert service.get_all_book_tasks() == []
