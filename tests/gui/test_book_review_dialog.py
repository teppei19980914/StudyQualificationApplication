"""BookReviewDialogのテスト."""

from datetime import date

import pytest
from PySide6.QtCore import QDate

from study_python.gui.dialogs.book_review_dialog import BookReviewDialog
from study_python.models.book import Book


@pytest.fixture
def book() -> Book:
    """テスト用Book."""
    return Book(title="Python入門", id="book-1")


@pytest.fixture
def dialog(qtbot, book: Book) -> BookReviewDialog:
    """テスト用ダイアログ."""
    dlg = BookReviewDialog(book)
    qtbot.addWidget(dlg)
    return dlg


class TestBookReviewDialogCreation:
    """ダイアログ生成のテスト."""

    def test_create_dialog(self, dialog: BookReviewDialog) -> None:
        assert dialog is not None

    def test_window_title(self, dialog: BookReviewDialog) -> None:
        assert dialog.windowTitle() == "読了記録"

    def test_has_summary_input(self, dialog: BookReviewDialog) -> None:
        assert dialog._summary_input is not None

    def test_has_impressions_input(self, dialog: BookReviewDialog) -> None:
        assert dialog._impressions_input is not None

    def test_default_date_is_today(self, dialog: BookReviewDialog) -> None:
        values = dialog.get_values()
        assert values["completed_date"] == date.today().isoformat()


class TestBookReviewDialogGetValues:
    """get_valuesのテスト."""

    def test_default_values(self, dialog: BookReviewDialog) -> None:
        values = dialog.get_values()
        assert values["summary"] == ""
        assert values["impressions"] == ""
        assert "completed_date" in values

    def test_filled_values(self, dialog: BookReviewDialog) -> None:
        dialog._summary_input.setPlainText("テスト要約")
        dialog._impressions_input.setPlainText("テスト感想")
        dialog._completed_date_input.setDate(QDate(2026, 2, 20))

        values = dialog.get_values()
        assert values["summary"] == "テスト要約"
        assert values["impressions"] == "テスト感想"
        assert values["completed_date"] == "2026-02-20"

    def test_trims_whitespace(self, dialog: BookReviewDialog) -> None:
        dialog._summary_input.setPlainText("  要約  ")
        dialog._impressions_input.setPlainText("  感想  ")

        values = dialog.get_values()
        assert values["summary"] == "要約"
        assert values["impressions"] == "感想"
