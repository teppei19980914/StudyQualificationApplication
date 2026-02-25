"""GoalDialogのテスト."""

from PySide6.QtCore import QDate

from study_python.gui.dialogs.goal_dialog import GoalDialog
from study_python.models.goal import Goal, WhenType


class TestGoalDialogCreate:
    """新規作成モードのテスト."""

    def test_create_dialog(self, qtbot):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        assert dialog.goal is None
        assert "登録" in dialog.windowTitle()

    def test_get_values_date_type(self, qtbot):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._what_input.setText("AWS資格")
        dialog._why_input.setPlainText("キャリアアップ")
        dialog._how_input.setPlainText("Udemy")
        dialog._when_type_combo.setCurrentIndex(0)
        dialog._when_date_input.setDate(QDate(2026, 6, 30))

        values = dialog.get_values()
        assert values["what"] == "AWS資格"
        assert values["why"] == "キャリアアップ"
        assert values["how"] == "Udemy"
        assert values["when_type"] == "date"
        assert values["when_target"] == "2026-06-30"

    def test_get_values_period_type(self, qtbot):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._what_input.setText("TOEIC")
        dialog._why_input.setPlainText("転職")
        dialog._how_input.setPlainText("毎日30分")
        dialog._when_type_combo.setCurrentIndex(1)
        dialog._when_period_input.setText("3ヶ月以内")

        values = dialog.get_values()
        assert values["when_type"] == "period"
        assert values["when_target"] == "3ヶ月以内"

    def test_when_type_toggle_visibility(self, qtbot):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog.show()

        # デフォルトはdate
        assert not dialog._when_date_input.isHidden()
        assert dialog._when_period_input.isHidden()

        # period に切り替え
        dialog._when_type_combo.setCurrentIndex(1)
        assert dialog._when_date_input.isHidden()
        assert not dialog._when_period_input.isHidden()

        # date に戻す
        dialog._when_type_combo.setCurrentIndex(0)
        assert not dialog._when_date_input.isHidden()
        assert dialog._when_period_input.isHidden()


class TestGoalDialogEdit:
    """編集モードのテスト."""

    def test_edit_dialog_populates_date_type(self, qtbot):
        goal = Goal(
            why="理由",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="目標",
            how="方法",
        )
        dialog = GoalDialog(goal=goal)
        qtbot.addWidget(dialog)
        assert dialog._what_input.text() == "目標"
        assert dialog._why_input.toPlainText() == "理由"
        assert dialog._how_input.toPlainText() == "方法"
        assert dialog._when_type_combo.currentIndex() == 0

    def test_edit_dialog_populates_period_type(self, qtbot):
        goal = Goal(
            why="理由",
            when_target="3ヶ月",
            when_type=WhenType.PERIOD,
            what="目標",
            how="方法",
        )
        dialog = GoalDialog(goal=goal)
        qtbot.addWidget(dialog)
        assert dialog._when_type_combo.currentIndex() == 1
        assert dialog._when_period_input.text() == "3ヶ月"

    def test_edit_dialog_title(self, qtbot):
        goal = Goal(
            why="a",
            when_target="b",
            when_type=WhenType.DATE,
            what="c",
            how="d",
        )
        dialog = GoalDialog(goal=goal)
        qtbot.addWidget(dialog)
        assert "編集" in dialog.windowTitle()


class TestGoalDialogValidation:
    """バリデーションのテスト."""

    def test_save_without_what_shows_warning(self, qtbot, monkeypatch):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._why_input.setPlainText("test")
        dialog._how_input.setPlainText("test")

        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        # Dialog should not be accepted
        assert dialog.result() != GoalDialog.DialogCode.Accepted

    def test_save_without_why_shows_warning(self, qtbot, monkeypatch):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._what_input.setText("test")
        dialog._how_input.setPlainText("test")

        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != GoalDialog.DialogCode.Accepted

    def test_save_without_how_shows_warning(self, qtbot, monkeypatch):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._what_input.setText("test")
        dialog._why_input.setPlainText("test")

        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != GoalDialog.DialogCode.Accepted

    def test_save_period_without_value_shows_warning(self, qtbot, monkeypatch):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._what_input.setText("test")
        dialog._why_input.setPlainText("test")
        dialog._how_input.setPlainText("test")
        dialog._when_type_combo.setCurrentIndex(1)  # period

        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
        dialog._on_save()
        assert dialog.result() != GoalDialog.DialogCode.Accepted

    def test_save_valid_data_accepts(self, qtbot):
        dialog = GoalDialog()
        qtbot.addWidget(dialog)
        dialog._what_input.setText("test")
        dialog._why_input.setPlainText("test")
        dialog._how_input.setPlainText("test")
        dialog._when_type_combo.setCurrentIndex(0)

        dialog._on_save()
        assert dialog.result() == GoalDialog.DialogCode.Accepted
