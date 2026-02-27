"""BookScheduleDialogのテスト."""

from datetime import date
from unittest.mock import patch

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QMessageBox

from study_python.gui.dialogs.book_schedule_dialog import BookScheduleDialog
from study_python.models.book import Book, BookStatus


class TestBookScheduleDialogCreate:
    """新規作成モードのテスト."""

    def test_create_dialog(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        assert dialog.book is None
        assert "追加" in dialog.windowTitle()

    def test_get_values(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        dialog._title_input.setText("Python入門")
        dialog._start_date_input.setDate(QDate(2026, 3, 1))
        dialog._end_date_input.setDate(QDate(2026, 3, 31))
        dialog._progress_slider.setValue(50)

        values = dialog.get_values()
        assert values["title"] == "Python入門"
        assert values["start_date"] == "2026-03-01"
        assert values["end_date"] == "2026-03-31"
        assert values["status"] == "in_progress"  # 進捗50%で自動設定
        assert values["progress"] == 50

    def test_slider_spinbox_sync(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        dialog._progress_slider.setValue(75)
        assert dialog._progress_spin.value() == 75

        dialog._progress_spin.setValue(30)
        assert dialog._progress_slider.value() == 30

    def test_new_book_source_default(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        assert dialog._book_source_combo is not None
        assert dialog._book_source_combo.currentData() == "__new__"

    def test_get_values_includes_book_source(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        values = dialog.get_values()
        assert values["book_source"] == "__new__"


class TestBookScheduleDialogWithUnscheduledBooks:
    """既存書籍選択のテスト."""

    def test_source_combo_populated(self, qtbot):
        books = [
            Book(title="Python入門", id="book-1"),
            Book(title="統計学基礎", id="book-2"),
        ]
        dialog = BookScheduleDialog(unscheduled_books=books)
        qtbot.addWidget(dialog)
        # 「新しい書籍を作成」 + 2冊 = 3
        assert dialog._book_source_combo.count() == 3

    def test_select_existing_book_fills_title(self, qtbot):
        books = [Book(title="Python入門", id="book-1")]
        dialog = BookScheduleDialog(unscheduled_books=books)
        qtbot.addWidget(dialog)
        dialog._book_source_combo.setCurrentIndex(1)  # Python入門
        assert dialog._title_input.text() == "Python入門"

    def test_select_existing_book_disables_title(self, qtbot):
        books = [Book(title="Python入門", id="book-1")]
        dialog = BookScheduleDialog(unscheduled_books=books)
        qtbot.addWidget(dialog)
        dialog._book_source_combo.setCurrentIndex(1)
        assert not dialog._title_input.isEnabled()

    def test_switch_back_to_new_enables_title(self, qtbot):
        books = [Book(title="Python入門", id="book-1")]
        dialog = BookScheduleDialog(unscheduled_books=books)
        qtbot.addWidget(dialog)
        dialog._book_source_combo.setCurrentIndex(1)
        dialog._book_source_combo.setCurrentIndex(0)
        assert dialog._title_input.isEnabled()

    def test_get_values_with_existing_book_source(self, qtbot):
        books = [Book(title="Python入門", id="book-1")]
        dialog = BookScheduleDialog(unscheduled_books=books)
        qtbot.addWidget(dialog)
        dialog._book_source_combo.setCurrentIndex(1)
        values = dialog.get_values()
        assert values["book_source"] == "book-1"


class TestBookScheduleDialogEdit:
    """編集モードのテスト."""

    def test_edit_populates_fields(self, qtbot):
        book = Book(
            title="Python入門",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            status=BookStatus.READING,
            progress=60,
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        assert dialog._title_input.text() == "Python入門"
        assert dialog._progress_spin.value() == 60
        assert dialog._status_combo.currentIndex() == 1  # 読書中

    def test_edit_dialog_title(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        assert "編集" in dialog.windowTitle()

    def test_no_source_combo_in_edit_mode(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        assert dialog._book_source_combo is None

    def test_edit_populates_completed_status(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=BookStatus.COMPLETED,
            progress=100,
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        assert dialog._status_combo.currentIndex() == 2

    def test_edit_no_book_source_in_values(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        values = dialog.get_values()
        assert "book_source" not in values


class TestBookScheduleDialogValidation:
    """バリデーションのテスト."""

    def test_empty_title_warns(self, qtbot, monkeypatch):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != BookScheduleDialog.DialogCode.Accepted

    def test_end_before_start_warns(self, qtbot, monkeypatch):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        dialog._start_date_input.setDate(QDate(2026, 3, 31))
        dialog._end_date_input.setDate(QDate(2026, 3, 1))
        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != BookScheduleDialog.DialogCode.Accepted

    def test_valid_data_accepts(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        dialog._start_date_input.setDate(QDate(2026, 3, 1))
        dialog._end_date_input.setDate(QDate(2026, 3, 31))
        dialog._on_save()
        assert dialog.result() == BookScheduleDialog.DialogCode.Accepted


class TestBookScheduleDialogDelete:
    """スケジュール削除のテスト."""

    def test_no_delete_button_in_create_mode(self, qtbot):
        dialog = BookScheduleDialog()
        qtbot.addWidget(dialog)
        assert dialog.delete_requested is False

    def test_delete_requested_default_false(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        assert dialog.delete_requested is False

    def test_delete_confirmed(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
        ):
            dialog._on_delete()
        assert dialog.delete_requested is True

    def test_delete_cancelled(self, qtbot):
        book = Book(
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = BookScheduleDialog(book=book)
        qtbot.addWidget(dialog)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.No
        ):
            dialog._on_delete()
        assert dialog.delete_requested is False
