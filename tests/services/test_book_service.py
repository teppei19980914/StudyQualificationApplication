"""BookServiceのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.models.book import BookStatus
from study_python.models.task import Task
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.book_service import BookService, BookshelfData


@pytest.fixture
def book_repo(tmp_path: Path) -> BookRepository:
    """テスト用BookRepository."""
    storage = JsonStorage(tmp_path / "books.json")
    return BookRepository(storage)


@pytest.fixture
def task_repo(tmp_path: Path) -> TaskRepository:
    """テスト用TaskRepository."""
    storage = JsonStorage(tmp_path / "tasks.json")
    return TaskRepository(storage)


@pytest.fixture
def service(book_repo: BookRepository, task_repo: TaskRepository) -> BookService:
    """テスト用BookService."""
    return BookService(book_repo, task_repo)


class TestBookServiceCreate:
    """create_bookのテスト."""

    def test_create_book(self, service: BookService) -> None:
        book = service.create_book("Python入門")
        assert book.title == "Python入門"
        assert book.status == BookStatus.UNREAD
        assert book.id != ""

    def test_create_trims_whitespace(self, service: BookService) -> None:
        book = service.create_book("  Python入門  ")
        assert book.title == "Python入門"

    def test_create_persists(self, service: BookService) -> None:
        service.create_book("テスト")
        books = service.get_all_books()
        assert len(books) == 1

    def test_create_empty_title_raises(self, service: BookService) -> None:
        with pytest.raises(ValueError, match="書籍名は必須です"):
            service.create_book("")

    def test_create_whitespace_title_raises(self, service: BookService) -> None:
        with pytest.raises(ValueError, match="書籍名は必須です"):
            service.create_book("   ")


class TestBookServiceGetAllBooks:
    """get_all_booksのテスト."""

    def test_empty(self, service: BookService) -> None:
        assert service.get_all_books() == []

    def test_multiple(self, service: BookService) -> None:
        service.create_book("本A")
        service.create_book("本B")
        assert len(service.get_all_books()) == 2


class TestBookServiceGetBook:
    """get_bookのテスト."""

    def test_existing(self, service: BookService) -> None:
        book = service.create_book("テスト")
        result = service.get_book(book.id)
        assert result is not None
        assert result.title == "テスト"

    def test_nonexistent(self, service: BookService) -> None:
        assert service.get_book("nonexistent") is None


class TestBookServiceUpdateStatus:
    """update_statusのテスト."""

    def test_update_to_reading(self, service: BookService) -> None:
        book = service.create_book("テスト")
        result = service.update_status(book.id, BookStatus.READING)
        assert result is not None
        assert result.status == BookStatus.READING

    def test_update_nonexistent(self, service: BookService) -> None:
        result = service.update_status("nonexistent", BookStatus.READING)
        assert result is None

    def test_update_persists(self, service: BookService) -> None:
        book = service.create_book("テスト")
        service.update_status(book.id, BookStatus.READING)
        loaded = service.get_book(book.id)
        assert loaded is not None
        assert loaded.status == BookStatus.READING


class TestBookServiceCompleteBook:
    """complete_bookのテスト."""

    def test_complete_with_review(self, service: BookService) -> None:
        book = service.create_book("テスト")
        result = service.complete_book(
            book.id, "要約テスト", "感想テスト", date(2026, 2, 20)
        )
        assert result is not None
        assert result.status == BookStatus.COMPLETED
        assert result.summary == "要約テスト"
        assert result.impressions == "感想テスト"
        assert result.completed_date == date(2026, 2, 20)

    def test_complete_default_date(self, service: BookService) -> None:
        book = service.create_book("テスト")
        result = service.complete_book(book.id, "要約", "感想")
        assert result is not None
        assert result.completed_date == date.today()

    def test_complete_nonexistent(self, service: BookService) -> None:
        result = service.complete_book("nonexistent", "要約", "感想")
        assert result is None

    def test_complete_persists(self, service: BookService) -> None:
        book = service.create_book("テスト")
        service.complete_book(book.id, "要約", "感想", date(2026, 2, 20))
        loaded = service.get_book(book.id)
        assert loaded is not None
        assert loaded.status == BookStatus.COMPLETED
        assert loaded.summary == "要約"

    def test_complete_empty_review(self, service: BookService) -> None:
        book = service.create_book("テスト")
        result = service.complete_book(book.id, "", "")
        assert result is not None
        assert result.summary == ""
        assert result.impressions == ""


class TestBookServiceDeleteBook:
    """delete_bookのテスト."""

    def test_delete_existing(self, service: BookService) -> None:
        book = service.create_book("テスト")
        result = service.delete_book(book.id)
        assert result is True
        assert len(service.get_all_books()) == 0

    def test_delete_nonexistent(self, service: BookService) -> None:
        result = service.delete_book("nonexistent")
        assert result is False

    def test_delete_clears_task_book_id(
        self, service: BookService, task_repo: TaskRepository
    ) -> None:
        book = service.create_book("テスト")
        task = Task(
            goal_id="goal-1",
            title="タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id=book.id,
        )
        task_repo.add(task)

        service.delete_book(book.id)

        updated_task = task_repo.get_by_id(task.id)
        assert updated_task is not None
        assert updated_task.book_id == ""

    def test_delete_preserves_unrelated_tasks(
        self, service: BookService, task_repo: TaskRepository
    ) -> None:
        book = service.create_book("テスト")
        task = Task(
            goal_id="goal-1",
            title="無関係タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id="other-book",
        )
        task_repo.add(task)

        service.delete_book(book.id)

        updated_task = task_repo.get_by_id(task.id)
        assert updated_task is not None
        assert updated_task.book_id == "other-book"


class TestBookServiceGetBookshelfData:
    """get_bookshelf_dataのテスト."""

    def test_empty(self, service: BookService) -> None:
        data = service.get_bookshelf_data()
        assert data.total_count == 0
        assert data.completed_count == 0
        assert data.reading_count == 0
        assert data.recent_completed == []

    def test_counts(self, service: BookService) -> None:
        service.create_book("未読")
        b2 = service.create_book("読書中")
        service.update_status(b2.id, BookStatus.READING)
        b3 = service.create_book("読了")
        service.complete_book(b3.id, "要約", "感想")

        data = service.get_bookshelf_data()
        assert data.total_count == 3
        assert data.completed_count == 1
        assert data.reading_count == 1

    def test_recent_completed_order(self, service: BookService) -> None:
        b1 = service.create_book("古い本")
        service.complete_book(b1.id, "要約1", "感想1", date(2026, 1, 1))
        b2 = service.create_book("新しい本")
        service.complete_book(b2.id, "要約2", "感想2", date(2026, 2, 15))
        b3 = service.create_book("最新本")
        service.complete_book(b3.id, "要約3", "感想3", date(2026, 2, 20))

        data = service.get_bookshelf_data()
        assert len(data.recent_completed) == 3
        assert data.recent_completed[0].title == "最新本"
        assert data.recent_completed[1].title == "新しい本"
        assert data.recent_completed[2].title == "古い本"

    def test_recent_completed_max_5(self, service: BookService) -> None:
        for i in range(7):
            book = service.create_book(f"本{i}")
            service.complete_book(book.id, f"要約{i}", f"感想{i}", date(2026, 1, i + 1))

        data = service.get_bookshelf_data()
        assert len(data.recent_completed) == 5

    def test_returns_bookshelf_data_type(self, service: BookService) -> None:
        data = service.get_bookshelf_data()
        assert isinstance(data, BookshelfData)
