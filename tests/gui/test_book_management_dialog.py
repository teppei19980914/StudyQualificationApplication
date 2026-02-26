"""BookManagementDialogのテスト."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from study_python.gui.dialogs.book_management_dialog import BookManagementDialog
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
def dialog(qtbot, book_service: BookService) -> BookManagementDialog:
    """テスト用ダイアログ."""
    dlg = BookManagementDialog(book_service)
    qtbot.addWidget(dlg)
    return dlg


class TestBookManagementDialogCreation:
    """ダイアログ生成のテスト."""

    def test_create_dialog(self, dialog: BookManagementDialog) -> None:
        assert dialog is not None

    def test_window_title(self, dialog: BookManagementDialog) -> None:
        assert dialog.windowTitle() == "書籍管理"

    def test_initially_not_changed(self, dialog: BookManagementDialog) -> None:
        assert dialog.books_changed is False

    def test_empty_book_list(self, dialog: BookManagementDialog) -> None:
        assert len(dialog._book_rows) == 0


class TestBookManagementDialogAddBook:
    """書籍追加のテスト."""

    def test_add_book(
        self, dialog: BookManagementDialog, book_service: BookService
    ) -> None:
        dialog._title_input.setText("テスト本")
        dialog._on_add_book()
        assert len(book_service.get_all_books()) == 1
        assert dialog.books_changed is True

    def test_add_book_clears_input(self, dialog: BookManagementDialog) -> None:
        dialog._title_input.setText("テスト本")
        dialog._on_add_book()
        assert dialog._title_input.text() == ""

    def test_add_book_refreshes_list(self, dialog: BookManagementDialog) -> None:
        dialog._title_input.setText("テスト本")
        dialog._on_add_book()
        assert len(dialog._book_rows) == 1

    def test_add_empty_title_does_nothing(
        self, dialog: BookManagementDialog, book_service: BookService
    ) -> None:
        dialog._title_input.setText("")
        dialog._on_add_book()
        assert len(book_service.get_all_books()) == 0
        assert dialog.books_changed is False


class TestBookManagementDialogChangeStatus:
    """ステータス変更のテスト."""

    def test_change_to_reading(
        self, dialog: BookManagementDialog, book_service: BookService
    ) -> None:
        book = book_service.create_book("テスト")
        dialog._refresh_book_list()
        dialog._on_change_status(book.id, BookStatus.READING)

        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.status == BookStatus.READING
        assert dialog.books_changed is True


class TestBookManagementDialogCompleteBook:
    """読了のテスト."""

    def test_complete_book_updates_service(
        self,
        dialog: BookManagementDialog,
        book_service: BookService,
        monkeypatch,
    ) -> None:
        book = book_service.create_book("テスト")
        dialog._refresh_book_list()

        # BookReviewDialog.exec をモック
        monkeypatch.setattr(
            "study_python.gui.dialogs.book_management_dialog.BookReviewDialog.exec",
            lambda self: BookManagementDialog.DialogCode.Accepted,
        )
        monkeypatch.setattr(
            "study_python.gui.dialogs.book_management_dialog.BookReviewDialog.get_values",
            lambda self: {
                "summary": "テスト要約",
                "impressions": "テスト感想",
                "completed_date": "2026-02-20",
            },
        )

        dialog._on_complete_book(book.id)

        updated = book_service.get_book(book.id)
        assert updated is not None
        assert updated.status == BookStatus.COMPLETED
        assert updated.summary == "テスト要約"
        assert dialog.books_changed is True

    def test_complete_nonexistent_book(self, dialog: BookManagementDialog) -> None:
        dialog._on_complete_book("nonexistent")
        # エラーが発生しないこと


class TestBookManagementDialogDeleteBook:
    """書籍削除のテスト."""

    def test_delete_book(
        self,
        dialog: BookManagementDialog,
        book_service: BookService,
        monkeypatch,
    ) -> None:
        book = book_service.create_book("テスト")
        dialog._refresh_book_list()

        # QMessageBox.question をモック
        monkeypatch.setattr(
            "study_python.gui.dialogs.book_management_dialog.QMessageBox.question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        dialog._on_delete_book(book.id)

        assert len(book_service.get_all_books()) == 0
        assert dialog.books_changed is True


class TestBookManagementDialogBookRows:
    """書籍行表示のテスト."""

    def test_shows_books_after_refresh(
        self, dialog: BookManagementDialog, book_service: BookService
    ) -> None:
        book_service.create_book("本A")
        book_service.create_book("本B")
        dialog._refresh_book_list()
        assert len(dialog._book_rows) == 2

    def test_refresh_clears_old_rows(
        self, dialog: BookManagementDialog, book_service: BookService
    ) -> None:
        book_service.create_book("本A")
        dialog._refresh_book_list()
        assert len(dialog._book_rows) == 1

        book_service.create_book("本B")
        dialog._refresh_book_list()
        assert len(dialog._book_rows) == 2
