"""BookRepositoryのテスト."""

from pathlib import Path

import pytest

from study_python.models.book import Book, BookStatus
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.json_storage import JsonStorage


@pytest.fixture
def repo(tmp_path: Path) -> BookRepository:
    """テスト用BookRepository."""
    storage = JsonStorage(tmp_path / "books.json")
    return BookRepository(storage)


def _make_book(**kwargs) -> Book:
    """テスト用Bookを作成するヘルパー."""
    defaults = {"title": "テスト本"}
    defaults.update(kwargs)
    return Book(**defaults)


class TestBookRepositoryGetAll:
    """get_allのテスト."""

    def test_empty_returns_empty_list(self, repo: BookRepository) -> None:
        assert repo.get_all() == []

    def test_returns_all_books(self, repo: BookRepository) -> None:
        repo.add(_make_book(title="本A"))
        repo.add(_make_book(title="本B"))
        books = repo.get_all()
        assert len(books) == 2

    def test_returns_book_objects(self, repo: BookRepository) -> None:
        repo.add(_make_book(title="テスト"))
        books = repo.get_all()
        assert isinstance(books[0], Book)
        assert books[0].title == "テスト"


class TestBookRepositoryGetById:
    """get_by_idのテスト."""

    def test_existing_book(self, repo: BookRepository) -> None:
        book = _make_book(id="book-1", title="テスト")
        repo.add(book)
        result = repo.get_by_id("book-1")
        assert result is not None
        assert result.title == "テスト"

    def test_nonexistent_returns_none(self, repo: BookRepository) -> None:
        assert repo.get_by_id("nonexistent") is None

    def test_empty_repo_returns_none(self, repo: BookRepository) -> None:
        assert repo.get_by_id("any-id") is None


class TestBookRepositoryAdd:
    """addのテスト."""

    def test_add_book(self, repo: BookRepository) -> None:
        book = _make_book(title="新しい本")
        repo.add(book)
        books = repo.get_all()
        assert len(books) == 1
        assert books[0].title == "新しい本"

    def test_add_multiple(self, repo: BookRepository) -> None:
        repo.add(_make_book(title="本A"))
        repo.add(_make_book(title="本B"))
        repo.add(_make_book(title="本C"))
        assert len(repo.get_all()) == 3

    def test_add_persists(self, tmp_path: Path) -> None:
        storage = JsonStorage(tmp_path / "books.json")
        repo1 = BookRepository(storage)
        repo1.add(_make_book(title="永続化テスト"))

        repo2 = BookRepository(storage)
        books = repo2.get_all()
        assert len(books) == 1
        assert books[0].title == "永続化テスト"


class TestBookRepositoryUpdate:
    """updateのテスト."""

    def test_update_existing(self, repo: BookRepository) -> None:
        book = _make_book(id="book-1", title="旧タイトル")
        repo.add(book)

        book.title = "新タイトル"  # title は mutable
        book.status = BookStatus.READING
        result = repo.update(book)
        assert result is True

        updated = repo.get_by_id("book-1")
        assert updated is not None
        assert updated.status == BookStatus.READING

    def test_update_nonexistent(self, repo: BookRepository) -> None:
        book = _make_book(id="nonexistent")
        result = repo.update(book)
        assert result is False

    def test_update_preserves_others(self, repo: BookRepository) -> None:
        repo.add(_make_book(id="book-1", title="本A"))
        repo.add(_make_book(id="book-2", title="本B"))

        book1 = repo.get_by_id("book-1")
        assert book1 is not None
        book1.status = BookStatus.COMPLETED
        repo.update(book1)

        book2 = repo.get_by_id("book-2")
        assert book2 is not None
        assert book2.status == BookStatus.UNREAD


class TestBookRepositoryDelete:
    """deleteのテスト."""

    def test_delete_existing(self, repo: BookRepository) -> None:
        repo.add(_make_book(id="book-1", title="削除対象"))
        result = repo.delete("book-1")
        assert result is True
        assert len(repo.get_all()) == 0

    def test_delete_nonexistent(self, repo: BookRepository) -> None:
        result = repo.delete("nonexistent")
        assert result is False

    def test_delete_preserves_others(self, repo: BookRepository) -> None:
        repo.add(_make_book(id="book-1", title="残す"))
        repo.add(_make_book(id="book-2", title="削除"))
        repo.delete("book-2")
        books = repo.get_all()
        assert len(books) == 1
        assert books[0].id == "book-1"
