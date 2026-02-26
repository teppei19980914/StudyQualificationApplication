"""BookPageのテスト."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QMessageBox

from study_python.gui.pages.book_page import BookPage
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.book import BookStatus
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.book_service import BookService


@pytest.fixture
def book_service(tmp_path: Path) -> BookService:
    """テスト用BookService."""
    book_storage = JsonStorage(tmp_path / "books.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    book_repo = BookRepository(book_storage)
    task_repo = TaskRepository(task_storage)
    return BookService(book_repo, task_repo)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    """テスト用ThemeManager."""
    return ThemeManager(tmp_path / "settings.json")


@pytest.fixture
def page(qtbot, book_service: BookService, theme_manager: ThemeManager) -> BookPage:
    """テスト用ページ."""
    p = BookPage(book_service, theme_manager)
    qtbot.addWidget(p)
    return p


class TestBookPageCreation:
    """ページ生成のテスト."""

    def test_create_page(self, page: BookPage) -> None:
        assert page is not None

    def test_has_title_input(self, page: BookPage) -> None:
        assert page._title_input is not None
        assert page._title_input.placeholderText() == "書籍名を入力..."

    def test_has_stats_label(self, page: BookPage) -> None:
        assert page._stats_label is not None

    def test_initial_empty_book_rows(self, page: BookPage) -> None:
        assert len(page._book_rows) == 0


class TestBookPageRefresh:
    """refreshのテスト."""

    def test_refresh_empty(self, page: BookPage) -> None:
        page.refresh()
        assert "0冊" in page._stats_label.text()
        assert len(page._book_rows) == 0

    def test_refresh_with_books(
        self, page: BookPage, book_service: BookService
    ) -> None:
        book_service.create_book("テスト本A")
        book_service.create_book("テスト本B")
        page.refresh()
        assert "2冊" in page._stats_label.text()
        assert len(page._book_rows) == 2

    def test_refresh_stats_completed(
        self, page: BookPage, book_service: BookService
    ) -> None:
        book = book_service.create_book("読了本")
        book_service.complete_book(book.id, "要約", "感想", date(2026, 2, 20))
        page.refresh()
        text = page._stats_label.text()
        assert "読了: 1冊" in text

    def test_refresh_stats_reading(
        self, page: BookPage, book_service: BookService
    ) -> None:
        book = book_service.create_book("読書中の本")
        book_service.update_status(book.id, BookStatus.READING)
        page.refresh()
        text = page._stats_label.text()
        assert "読書中: 1冊" in text

    def test_refresh_clears_previous(
        self, page: BookPage, book_service: BookService
    ) -> None:
        book_service.create_book("本A")
        page.refresh()
        assert len(page._book_rows) == 1

        book_service.create_book("本B")
        page.refresh()
        assert len(page._book_rows) == 2


class TestBookPageAddBook:
    """書籍追加のテスト."""

    def test_add_book(self, page: BookPage, book_service: BookService) -> None:
        page._title_input.setText("新しい本")
        page._on_add_book()
        assert len(page._book_rows) == 1
        assert page._title_input.text() == ""
        books = book_service.get_all_books()
        assert len(books) == 1
        assert books[0].title == "新しい本"

    def test_add_empty_title_ignored(self, page: BookPage) -> None:
        page._title_input.setText("  ")
        page._on_add_book()
        assert len(page._book_rows) == 0

    def test_add_book_error(self, page: BookPage) -> None:
        page._book_service.create_book = MagicMock(side_effect=ValueError("エラー"))
        page._title_input.setText("テスト")
        with patch.object(QMessageBox, "warning"):
            page._on_add_book()


class TestBookPageChangeStatus:
    """ステータス変更のテスト."""

    def test_change_to_reading(self, page: BookPage, book_service: BookService) -> None:
        book = book_service.create_book("テスト本")
        page.refresh()
        page._on_change_status(book.id, BookStatus.READING)
        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.status == BookStatus.READING


class TestBookPageCompleteBook:
    """読了のテスト."""

    def test_complete_book(self, page: BookPage, book_service: BookService) -> None:
        book = book_service.create_book("テスト本")
        with patch(
            "study_python.gui.pages.book_page.BookReviewDialog"
        ) as mock_dialog_cls:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = mock_dialog_cls.DialogCode.Accepted
            mock_dialog.get_values.return_value = {
                "summary": "要約",
                "impressions": "感想",
                "completed_date": "2026-02-20",
            }
            mock_dialog_cls.return_value = mock_dialog

            page._on_complete_book(book.id)

        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.status == BookStatus.COMPLETED
        assert updated.summary == "要約"

    def test_complete_nonexistent_book(self, page: BookPage) -> None:
        page._on_complete_book("nonexistent-id")
        # エラーなく終了


class TestBookPageDeleteBook:
    """削除のテスト."""

    def test_delete_book(self, page: BookPage, book_service: BookService) -> None:
        book = book_service.create_book("削除対象")
        page.refresh()
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
        ):
            page._on_delete_book(book.id)
        assert book_service.get_book(book.id) is None
        assert len(page._book_rows) == 0

    def test_delete_cancelled(self, page: BookPage, book_service: BookService) -> None:
        book = book_service.create_book("残す本")
        page.refresh()
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.No
        ):
            page._on_delete_book(book.id)
        assert book_service.get_book(book.id) is not None


class TestBookPageTheme:
    """テーマ変更のテスト."""

    def test_on_theme_changed(self, page: BookPage, book_service: BookService) -> None:
        book_service.create_book("テスト")
        page.on_theme_changed()
        assert len(page._book_rows) == 1
