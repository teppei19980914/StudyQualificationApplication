"""TaskDialogのテスト."""

from datetime import date

from PySide6.QtCore import QDate

from study_python.gui.dialogs.task_dialog import TaskDialog
from study_python.models.book import Book
from study_python.models.task import Task, TaskStatus


class TestTaskDialogCreate:
    """新規作成モードのテスト."""

    def test_create_dialog(self, qtbot):
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        assert dialog.task is None
        assert "タスク" in dialog.windowTitle()

    def test_get_values(self, qtbot):
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        dialog._title_input.setText("テストタスク")
        dialog._start_date_input.setDate(QDate(2026, 3, 1))
        dialog._end_date_input.setDate(QDate(2026, 3, 15))
        dialog._status_combo.setCurrentIndex(1)  # 進行中
        dialog._progress_slider.setValue(50)
        dialog._memo_input.setPlainText("メモ")

        values = dialog.get_values()
        assert values["title"] == "テストタスク"
        assert values["start_date"] == "2026-03-01"
        assert values["end_date"] == "2026-03-15"
        assert values["status"] == "in_progress"
        assert values["progress"] == 50
        assert values["memo"] == "メモ"

    def test_slider_spinbox_sync(self, qtbot):
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        dialog._progress_slider.setValue(75)
        assert dialog._progress_spin.value() == 75

        dialog._progress_spin.setValue(30)
        assert dialog._progress_slider.value() == 30


class TestTaskDialogEdit:
    """編集モードのテスト."""

    def test_edit_populates_fields(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.IN_PROGRESS,
            progress=60,
            memo="テストメモ",
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert dialog._title_input.text() == "テスト"
        assert dialog._progress_spin.value() == 60
        assert dialog._memo_input.toPlainText() == "テストメモ"
        assert dialog._status_combo.currentIndex() == 1

    def test_edit_dialog_title(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert "編集" in dialog.windowTitle()

    def test_edit_populates_completed_status(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.COMPLETED,
            progress=100,
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert dialog._status_combo.currentIndex() == 2

    def test_edit_populates_not_started_status(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.NOT_STARTED,
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert dialog._status_combo.currentIndex() == 0


class TestTaskDialogValidation:
    """バリデーションのテスト."""

    def test_empty_title_warns(self, qtbot, monkeypatch):
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != TaskDialog.DialogCode.Accepted

    def test_end_before_start_warns(self, qtbot, monkeypatch):
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        dialog._start_date_input.setDate(QDate(2026, 3, 15))
        dialog._end_date_input.setDate(QDate(2026, 3, 1))
        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != TaskDialog.DialogCode.Accepted

    def test_valid_data_accepts(self, qtbot):
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        dialog._start_date_input.setDate(QDate(2026, 3, 1))
        dialog._end_date_input.setDate(QDate(2026, 3, 15))
        dialog._on_save()
        assert dialog.result() == TaskDialog.DialogCode.Accepted


class TestTaskDialogBookSelection:
    """書籍選択のテスト."""

    def test_no_books_shows_only_none(self, qtbot):
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        assert dialog._book_combo.count() == 1
        assert dialog._book_combo.currentData() == ""

    def test_books_list_populated(self, qtbot):
        books = [
            Book(title="Python入門", id="book-1"),
            Book(title="統計学基礎", id="book-2"),
        ]
        dialog = TaskDialog(books=books)
        qtbot.addWidget(dialog)
        assert dialog._book_combo.count() == 3  # なし + 2冊

    def test_get_values_includes_book_id(self, qtbot):
        books = [Book(title="Python入門", id="book-1")]
        dialog = TaskDialog(books=books)
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        dialog._book_combo.setCurrentIndex(1)  # Python入門

        values = dialog.get_values()
        assert values["book_id"] == "book-1"

    def test_default_book_is_none(self, qtbot):
        books = [Book(title="Python入門", id="book-1")]
        dialog = TaskDialog(books=books)
        qtbot.addWidget(dialog)

        values = dialog.get_values()
        assert values["book_id"] == ""

    def test_edit_restores_book_selection(self, qtbot):
        books = [
            Book(title="Python入門", id="book-1"),
            Book(title="統計学基礎", id="book-2"),
        ]
        task = Task(
            goal_id="goal-1",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id="book-2",
        )
        dialog = TaskDialog(task=task, books=books)
        qtbot.addWidget(dialog)
        assert dialog._book_combo.currentData() == "book-2"
