"""StudyLogDialogのテスト."""

from datetime import date

from PySide6.QtCore import QDate

from study_python.gui.dialogs.study_log_dialog import StudyLogDialog
from study_python.models.task import Task


def _make_tasks() -> list[Task]:
    return [
        Task(
            id="task-1",
            goal_id="goal-1",
            title="Udemy学習",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        ),
        Task(
            id="task-2",
            goal_id="goal-1",
            title="問題集",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        ),
    ]


class TestStudyLogDialogCreate:
    """生成テスト."""

    def test_create_dialog(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "学習時間を記録"

    def test_task_combo_populated(self, qtbot):
        tasks = _make_tasks()
        dialog = StudyLogDialog(tasks=tasks)
        qtbot.addWidget(dialog)
        assert dialog._task_combo.count() == 2
        assert dialog._task_combo.itemText(0) == "Udemy学習"
        assert dialog._task_combo.itemText(1) == "問題集"

    def test_preselected_task(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks(), preselected_task_id="task-2")
        qtbot.addWidget(dialog)
        assert dialog._task_combo.currentData() == "task-2"

    def test_default_minutes(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        assert dialog._minutes_spin.value() == 30
        assert dialog._hours_spin.value() == 0


class TestStudyLogDialogGetValues:
    """get_valuesのテスト."""

    def test_get_values(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        dialog._task_combo.setCurrentIndex(0)
        dialog._date_input.setDate(QDate(2026, 3, 15))
        dialog._hours_spin.setValue(1)
        dialog._minutes_spin.setValue(30)
        dialog._memo_input.setText("テストメモ")

        values = dialog.get_values()
        assert values["task_id"] == "task-1"
        assert values["task_name"] == "Udemy学習"
        assert values["study_date"] == "2026-03-15"
        assert values["duration_minutes"] == 90
        assert values["memo"] == "テストメモ"

    def test_get_values_hours_only(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        dialog._hours_spin.setValue(2)
        dialog._minutes_spin.setValue(0)
        values = dialog.get_values()
        assert values["duration_minutes"] == 120

    def test_get_values_minutes_only(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        dialog._hours_spin.setValue(0)
        dialog._minutes_spin.setValue(45)
        values = dialog.get_values()
        assert values["duration_minutes"] == 45


class TestStudyLogDialogValidation:
    """バリデーションのテスト."""

    def test_zero_duration_warns(self, qtbot, monkeypatch):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        dialog._hours_spin.setValue(0)
        dialog._minutes_spin.setValue(0)
        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != StudyLogDialog.DialogCode.Accepted

    def test_valid_data_accepts(self, qtbot):
        dialog = StudyLogDialog(tasks=_make_tasks())
        qtbot.addWidget(dialog)
        dialog._hours_spin.setValue(0)
        dialog._minutes_spin.setValue(30)
        dialog._on_save()
        assert dialog.result() == StudyLogDialog.DialogCode.Accepted

    def test_no_tasks_warns(self, qtbot, monkeypatch):
        dialog = StudyLogDialog(tasks=[])
        qtbot.addWidget(dialog)
        dialog._hours_spin.setValue(0)
        dialog._minutes_spin.setValue(30)
        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != StudyLogDialog.DialogCode.Accepted
