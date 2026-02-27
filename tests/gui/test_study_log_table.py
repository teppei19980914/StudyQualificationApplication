"""StudyLogTableのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.study_log_table import StudyLogEntry, StudyLogTable


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestStudyLogEntry:
    """StudyLogEntryのテスト."""

    def test_create(self):
        entry = StudyLogEntry(
            study_date=date(2026, 2, 26),
            task_name="Udemy学習",
            duration_minutes=60,
            memo="Section 5完了",
        )
        assert entry.study_date == date(2026, 2, 26)
        assert entry.task_name == "Udemy学習"
        assert entry.duration_minutes == 60
        assert entry.memo == "Section 5完了"
        assert entry.task_status == ""

    def test_create_with_status(self):
        entry = StudyLogEntry(
            study_date=date(2026, 2, 26),
            task_name="Udemy学習",
            duration_minutes=60,
            memo="",
            task_status="実施中",
        )
        assert entry.task_status == "実施中"


class TestStudyLogTable:
    """StudyLogTableのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        table = StudyLogTable(theme_manager)
        qtbot.addWidget(table)
        assert table is not None

    def test_set_entries_populates_table(self, qtbot, theme_manager):
        table = StudyLogTable(theme_manager)
        qtbot.addWidget(table)

        entries = [
            StudyLogEntry(date(2026, 2, 26), "タスク1", 60, "メモ1"),
            StudyLogEntry(date(2026, 2, 25), "タスク2", 30, "メモ2"),
        ]
        table.set_entries(entries)
        assert table._table.rowCount() == 2

    def test_set_entries_empty(self, qtbot, theme_manager):
        table = StudyLogTable(theme_manager)
        qtbot.addWidget(table)

        table.set_entries([])
        assert table._table.rowCount() == 0
        assert not table._empty_label.isHidden()
        assert table._table.isHidden()

    def test_set_entries_displays_correct_values(self, qtbot, theme_manager):
        table = StudyLogTable(theme_manager)
        qtbot.addWidget(table)

        entries = [
            StudyLogEntry(
                date(2026, 2, 26), "Udemy", 90, "テストメモ", task_status="実施中"
            ),
        ]
        table.set_entries(entries)

        assert table._table.item(0, 0).text() == "2026-02-26"
        assert table._table.item(0, 1).text() == "Udemy"
        assert table._table.item(0, 2).text() == "実施中"
        assert table._table.item(0, 3).text() == "1h 30min"
        assert table._table.item(0, 4).text() == "テストメモ"

    def test_set_entries_replaces_previous(self, qtbot, theme_manager):
        table = StudyLogTable(theme_manager)
        qtbot.addWidget(table)

        entries1 = [
            StudyLogEntry(date(2026, 2, 26), "タスク1", 60, ""),
            StudyLogEntry(date(2026, 2, 25), "タスク2", 30, ""),
        ]
        table.set_entries(entries1)
        assert table._table.rowCount() == 2

        entries2 = [
            StudyLogEntry(date(2026, 2, 26), "タスク3", 45, ""),
        ]
        table.set_entries(entries2)
        assert table._table.rowCount() == 1

    def test_format_duration_hours_and_minutes(self, qtbot, theme_manager):
        assert StudyLogTable._format_duration(90) == "1h 30min"
        assert StudyLogTable._format_duration(120) == "2h 00min"

    def test_format_duration_minutes_only(self, qtbot, theme_manager):
        assert StudyLogTable._format_duration(45) == "45min"
        assert StudyLogTable._format_duration(1) == "1min"

    def test_empty_then_populated(self, qtbot, theme_manager):
        table = StudyLogTable(theme_manager)
        qtbot.addWidget(table)

        table.set_entries([])
        assert not table._empty_label.isHidden()

        entries = [StudyLogEntry(date(2026, 2, 26), "タスク", 60, "")]
        table.set_entries(entries)
        assert not table._table.isHidden()
        assert table._empty_label.isHidden()
