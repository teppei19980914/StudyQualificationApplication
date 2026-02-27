"""TaskDialogのテスト."""

import time
from datetime import date
from unittest.mock import patch

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QMessageBox

from study_python.gui.dialogs.task_dialog import TaskDialog
from study_python.models.book import Book
from study_python.models.goal import Goal, WhenType
from study_python.models.task import Task
from study_python.services.study_log_service import StudyLogService


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
        dialog._progress_slider.setValue(50)
        dialog._memo_input.setPlainText("メモ")

        values = dialog.get_values()
        assert values["title"] == "テストタスク"
        assert values["start_date"] == "2026-03-01"
        assert values["end_date"] == "2026-03-15"
        assert values["status"] == "in_progress"  # 進捗50%で自動設定
        assert values["progress"] == 50
        assert values["memo"] == "メモ"

    def test_slider_spinbox_sync(self, qtbot):
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        dialog._progress_slider.setValue(75)
        assert dialog._progress_spin.value() == 75

        dialog._progress_spin.setValue(30)
        assert dialog._progress_slider.value() == 30

    def test_status_auto_sync_from_progress(self, qtbot):
        """進捗率変更でステータスが自動更新される."""
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        # 0% → 未着手
        dialog._progress_spin.setValue(0)
        assert dialog._status_combo.currentIndex() == 0
        # 50% → 進行中
        dialog._progress_spin.setValue(50)
        assert dialog._status_combo.currentIndex() == 1
        # 100% → 完了
        dialog._progress_spin.setValue(100)
        assert dialog._status_combo.currentIndex() == 2

    def test_status_combo_disabled(self, qtbot):
        """ステータスコンボは編集不可."""
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        assert not dialog._status_combo.isEnabled()


class TestTaskDialogEdit:
    """編集モードのテスト."""

    def test_edit_populates_fields(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            progress=60,
            memo="テストメモ",
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert dialog._title_input.text() == "テスト"
        assert dialog._progress_spin.value() == 60
        assert dialog._memo_input.toPlainText() == "テストメモ"
        assert dialog._status_combo.currentIndex() == 1  # 進行中

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
        """進捗100%でステータスが完了になる."""
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            progress=100,
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert dialog._status_combo.currentIndex() == 2

    def test_edit_populates_not_started_status(self, qtbot):
        """進捗0%でステータスが未着手になる."""
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            progress=0,
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


class TestTaskDialogDelete:
    """タスク削除のテスト."""

    def test_no_delete_button_in_create_mode(self, qtbot):
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        assert dialog.delete_requested is False

    def test_delete_requested_default_false(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        assert dialog.delete_requested is False

    def test_delete_confirmed(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
        ):
            dialog._on_delete()
        assert dialog.delete_requested is True

    def test_delete_cancelled(self, qtbot):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        dialog = TaskDialog(task=task)
        qtbot.addWidget(dialog)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.No
        ):
            dialog._on_delete()
        assert dialog.delete_requested is False


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


class TestTaskDialogGoalSelection:
    """目標選択のテスト."""

    def _make_goals(self) -> list[Goal]:
        return [
            Goal(
                id="goal-1",
                why="test",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="AWS資格",
                how="test",
            ),
            Goal(
                id="goal-2",
                why="test",
                when_target="2026-12-31",
                when_type=WhenType.DATE,
                what="TOEIC",
                how="test",
            ),
        ]

    def test_goal_combo_shown_when_goals_provided(self, qtbot):
        """goalsが渡された場合、目標選択コンボが表示される."""
        goals = self._make_goals()
        dialog = TaskDialog(goals=goals)
        qtbot.addWidget(dialog)
        assert dialog._goal_combo is not None
        assert dialog._goal_combo.count() == 2

    def test_goal_combo_hidden_when_goal_id_provided(self, qtbot):
        """goal_idが直接指定された場合、目標選択コンボは非表示."""
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        assert dialog._goal_combo is None

    def test_goal_combo_hidden_when_no_goals(self, qtbot):
        """goalsが渡されない場合、目標選択コンボは非表示."""
        dialog = TaskDialog()
        qtbot.addWidget(dialog)
        assert dialog._goal_combo is None

    def test_get_values_includes_goal_id(self, qtbot):
        """goalsモード時、get_valuesにgoal_idが含まれる."""
        goals = self._make_goals()
        dialog = TaskDialog(goals=goals)
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")
        dialog._goal_combo.setCurrentIndex(1)  # TOEIC

        values = dialog.get_values()
        assert values["goal_id"] == "goal-2"

    def test_get_values_no_goal_id_without_goals(self, qtbot):
        """通常モード時、get_valuesにgoal_idが含まれない."""
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        dialog._title_input.setText("test")

        values = dialog.get_values()
        assert "goal_id" not in values


def _make_task() -> Task:
    """テスト用タスクを作成する."""
    return Task(
        id="task-1",
        goal_id="goal-1",
        title="テストタスク",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 15),
    )


class TestTaskDialogStudyLog:
    """学習記録セクションのテスト."""

    def test_study_log_section_hidden_in_create_mode(self, qtbot):
        """新規作成モードでは学習記録セクションが非表示."""
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        assert dialog._study_log_logic is None
        assert dialog._study_log_group is None

    def test_study_log_section_hidden_without_service(self, qtbot):
        """study_log_serviceなしでは学習記録セクションが非表示."""
        dialog = TaskDialog(task=_make_task())
        qtbot.addWidget(dialog)
        assert dialog._study_log_logic is None
        assert dialog._study_log_group is None

    def test_study_log_section_visible_in_edit_mode(
        self, qtbot, study_log_service: StudyLogService
    ):
        """編集モード + service提供時は学習記録セクションが表示."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_logic is not None
        assert dialog._study_log_group is not None
        assert dialog._study_log_table is not None

    def test_study_logs_changed_default_false(
        self, qtbot, study_log_service: StudyLogService
    ):
        """初期状態ではstudy_logs_changedはFalse."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog.study_logs_changed is False

    def test_existing_logs_displayed(self, qtbot, study_log_service: StudyLogService):
        """既存の学習ログがテーブルに表示される."""
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
            memo="テスト1",
        )
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 26),
            duration_minutes=30,
            memo="テスト2",
        )
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 2

    def test_add_study_log_updates_table(
        self, qtbot, study_log_service: StudyLogService
    ):
        """学習記録追加でテーブルが更新される."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 0

        dialog._log_hours_spin.setValue(1)
        dialog._log_minutes_spin.setValue(30)
        dialog._log_memo_input.setText("新しい記録")
        dialog._on_add_study_log()

        assert dialog._study_log_table.rowCount() == 1
        assert dialog.study_logs_changed is True

    def test_add_study_log_clears_form(self, qtbot, study_log_service: StudyLogService):
        """学習記録追加後にフォームがクリアされる."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        dialog._log_hours_spin.setValue(1)
        dialog._log_minutes_spin.setValue(15)
        dialog._log_memo_input.setText("テストメモ")
        dialog._on_add_study_log()

        assert dialog._log_memo_input.text() == ""
        assert dialog._log_hours_spin.value() == 0
        assert dialog._log_minutes_spin.value() == 30

    def test_add_study_log_zero_duration_warns(
        self, qtbot, study_log_service: StudyLogService, monkeypatch
    ):
        """0分で追加するとエラー表示."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        dialog._log_hours_spin.setValue(0)
        dialog._log_minutes_spin.setValue(0)
        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_add_study_log()

        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 0
        assert dialog.study_logs_changed is False

    def test_delete_study_log_updates_table(
        self, qtbot, study_log_service: StudyLogService
    ):
        """学習記録削除でテーブルが更新される."""
        log = study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 1

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
        ):
            dialog._on_delete_study_log(log.id)

        assert dialog._study_log_table.rowCount() == 0
        assert dialog.study_logs_changed is True

    def test_delete_study_log_cancelled(
        self, qtbot, study_log_service: StudyLogService
    ):
        """学習記録削除キャンセルでテーブルは変わらない."""
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_table is not None

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.No
        ):
            dialog._on_delete_study_log("some-id")

        assert dialog._study_log_table.rowCount() == 1
        assert dialog.study_logs_changed is False

    def test_stats_displayed_in_group_title(
        self, qtbot, study_log_service: StudyLogService
    ):
        """統計がグループボックスタイトルに表示される."""
        study_log_service.add_study_log(
            task_id="task-1",
            study_date=date(2026, 2, 25),
            duration_minutes=90,
        )
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_group is not None
        title = dialog._study_log_group.title()
        assert "1h 30min" in title
        assert "1日" in title
        assert "1件" in title

    def test_other_task_logs_not_shown(self, qtbot, study_log_service: StudyLogService):
        """他タスクのログは表示されない."""
        study_log_service.add_study_log(
            task_id="task-other",
            study_date=date(2026, 2, 25),
            duration_minutes=60,
        )
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 0


class TestTaskDialogTimer:
    """タイマーUIのテスト."""

    def test_timer_buttons_visible_in_edit_mode(
        self, qtbot, study_log_service: StudyLogService
    ):
        """編集モード + service提供時はタイマーUIが表示される."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._start_btn is not None
        assert dialog._stop_btn is not None
        assert dialog._timer_label is not None

    def test_timer_buttons_hidden_in_create_mode(self, qtbot):
        """新規作成モードではタイマーUIが非表示."""
        dialog = TaskDialog(goal_id="goal-1")
        qtbot.addWidget(dialog)
        assert dialog._start_btn is None
        assert dialog._stop_btn is None
        assert dialog._timer_label is None

    def test_timer_buttons_hidden_without_service(self, qtbot):
        """study_log_serviceなしではタイマーUIが非表示."""
        dialog = TaskDialog(task=_make_task())
        qtbot.addWidget(dialog)
        assert dialog._start_btn is None
        assert dialog._stop_btn is None
        assert dialog._timer_label is None

    def test_stop_button_disabled_initially(
        self, qtbot, study_log_service: StudyLogService
    ):
        """初期状態で停止ボタンは無効."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        assert dialog._stop_btn is not None
        assert dialog._start_btn is not None
        assert not dialog._stop_btn.isEnabled()
        assert dialog._start_btn.isEnabled()

    def test_timer_start_enables_stop(self, qtbot, study_log_service: StudyLogService):
        """開始ボタンで停止ボタンが有効になる."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)
        dialog._on_timer_start()
        assert dialog._start_btn is not None
        assert dialog._stop_btn is not None
        assert not dialog._start_btn.isEnabled()
        assert dialog._stop_btn.isEnabled()

    def test_timer_start_stop_records_log(
        self, qtbot, study_log_service: StudyLogService, monkeypatch
    ):
        """タイマー停止で学習ログが自動追加される."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)

        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        dialog._on_timer_start()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 150)
        dialog._on_timer_stop()

        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 1
        assert dialog.study_logs_changed is True

    def test_timer_display_updates(
        self, qtbot, study_log_service: StudyLogService, monkeypatch
    ):
        """タイマー表示が更新される."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)

        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        dialog._on_timer_start()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 3661)
        dialog._update_timer_display()
        assert dialog._timer_label is not None
        assert dialog._timer_label.text() == "01:01:01"

    def test_timer_stop_resets_display(
        self, qtbot, study_log_service: StudyLogService, monkeypatch
    ):
        """タイマー停止で表示がリセットされる."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)

        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        dialog._on_timer_start()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 90)
        dialog._on_timer_stop()
        assert dialog._timer_label is not None
        assert dialog._timer_label.text() == "00:00:00"

    def test_reject_stops_timer_and_records(
        self, qtbot, study_log_service: StudyLogService, monkeypatch
    ):
        """ダイアログを閉じるとタイマーが停止して記録される."""
        dialog = TaskDialog(task=_make_task(), study_log_service=study_log_service)
        qtbot.addWidget(dialog)

        start_time = 1000.0
        monkeypatch.setattr(time, "monotonic", lambda: start_time)
        dialog._on_timer_start()

        monkeypatch.setattr(time, "monotonic", lambda: start_time + 120)
        dialog.reject()

        assert dialog._study_log_table is not None
        assert dialog._study_log_table.rowCount() == 1
        assert dialog.study_logs_changed is True


class TestTaskDialogBookTaskMode:
    """書籍タスクモードのテスト."""

    def _make_books(self) -> list[Book]:
        return [
            Book(title="Python入門", id="book-1"),
            Book(title="統計学基礎", id="book-2"),
        ]

    def test_book_selector_visible(self, qtbot):
        """book_task_mode時は書籍セレクタが表示される."""
        books = self._make_books()
        dialog = TaskDialog(book_task_mode=True, books=books)
        qtbot.addWidget(dialog)
        assert dialog._book_selector is not None
        assert dialog._book_selector.count() == 2

    def test_book_combo_hidden(self, qtbot):
        """book_task_mode時は関連書籍コンボが非表示."""
        books = self._make_books()
        dialog = TaskDialog(book_task_mode=True, books=books)
        qtbot.addWidget(dialog)
        assert dialog._book_combo is None

    def test_goal_combo_hidden(self, qtbot):
        """book_task_mode時はgoalsを渡しても目標コンボが非表示."""
        books = self._make_books()
        goals = [
            Goal(
                id="goal-1",
                why="test",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="test",
                how="test",
            ),
        ]
        dialog = TaskDialog(book_task_mode=True, books=books, goals=goals)
        qtbot.addWidget(dialog)
        assert dialog._goal_combo is None

    def test_get_values_includes_book_id(self, qtbot):
        """book_task_modeでget_valuesにbook_idが含まれる."""
        books = self._make_books()
        dialog = TaskDialog(book_task_mode=True, books=books)
        qtbot.addWidget(dialog)
        dialog._title_input.setText("テスト")
        dialog._book_selector.setCurrentIndex(1)  # 統計学基礎

        values = dialog.get_values()
        assert values["book_id"] == "book-2"

    def test_edit_restores_book_selector(self, qtbot):
        """編集モードで書籍セレクタが復元される."""
        books = self._make_books()
        task = Task(
            goal_id="__books__",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id="book-2",
        )
        dialog = TaskDialog(task=task, book_task_mode=True, books=books)
        qtbot.addWidget(dialog)
        assert dialog._book_selector is not None
        assert dialog._book_selector.currentData() == "book-2"

    def test_normal_mode_no_book_selector(self, qtbot):
        """通常モードでは書籍セレクタは非表示."""
        books = self._make_books()
        dialog = TaskDialog(books=books)
        qtbot.addWidget(dialog)
        assert dialog._book_selector is None
        assert dialog._book_combo is not None
