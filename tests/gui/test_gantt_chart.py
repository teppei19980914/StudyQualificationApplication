"""GanttChartのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.gantt_chart import GanttBarItem, GanttChart
from study_python.models.task import Task, TaskStatus


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestGanttChart:
    """GanttChartのテスト."""

    def test_create_chart(self, qtbot, theme_manager):
        chart = GanttChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart.scene() is not None

    def test_display_empty_tasks(self, qtbot, theme_manager):
        chart = GanttChart(theme_manager)
        qtbot.addWidget(chart)
        chart.display_tasks([])
        assert chart.scene().items()  # empty message text item

    def test_display_tasks(self, qtbot, theme_manager):
        chart = GanttChart(theme_manager)
        qtbot.addWidget(chart)
        tasks = [
            Task(
                goal_id="g1",
                title="タスク1",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
                progress=50,
                status=TaskStatus.IN_PROGRESS,
            ),
            Task(
                goal_id="g1",
                title="タスク2",
                start_date=date(2026, 3, 16),
                end_date=date(2026, 3, 31),
                progress=0,
            ),
        ]
        chart.display_tasks(tasks, "#4A9EFF")
        items = chart.scene().items()
        assert len(items) > 0

    def test_display_tasks_with_completed(self, qtbot, theme_manager):
        chart = GanttChart(theme_manager)
        qtbot.addWidget(chart)
        tasks = [
            Task(
                goal_id="g1",
                title="完了タスク",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
                progress=100,
                status=TaskStatus.COMPLETED,
            ),
        ]
        chart.display_tasks(tasks, "#51CF66")
        items = chart.scene().items()
        bar_items = [i for i in items if isinstance(i, GanttBarItem)]
        assert len(bar_items) == 1


class TestGanttBarItem:
    """GanttBarItemのテスト."""

    def test_create_bar_item(self, qtbot):
        task = Task(
            goal_id="g1",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            progress=50,
            status=TaskStatus.IN_PROGRESS,
        )
        bar = GanttBarItem(
            task=task,
            goal_color="#4A9EFF",
            x=0,
            y=0,
            width=300,
            height=24,
            progress_width=150,
            colors={"text_primary": "#CDD6F4", "success": "#A6E3A1"},
        )
        assert bar.task.id == task.id
        assert bar.goal_color == "#4A9EFF"
        assert "テスト" in bar.toolTip()
        assert "50%" in bar.toolTip()

    def test_status_text_not_started(self, qtbot):
        task = Task(
            goal_id="g1",
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.NOT_STARTED,
        )
        bar = GanttBarItem(
            task=task,
            goal_color="#4A9EFF",
            x=0,
            y=0,
            width=100,
            height=24,
            progress_width=0,
            colors={},
        )
        assert "未着手" in bar.toolTip()

    def test_status_text_completed(self, qtbot):
        task = Task(
            goal_id="g1",
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.COMPLETED,
            progress=100,
        )
        bar = GanttBarItem(
            task=task,
            goal_color="#4A9EFF",
            x=0,
            y=0,
            width=100,
            height=24,
            progress_width=100,
            colors={},
        )
        assert "完了" in bar.toolTip()

    def test_status_text_in_progress(self, qtbot):
        task = Task(
            goal_id="g1",
            title="t",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.IN_PROGRESS,
            progress=50,
        )
        bar = GanttBarItem(
            task=task,
            goal_color="#4A9EFF",
            x=0,
            y=0,
            width=100,
            height=24,
            progress_width=50,
            colors={},
        )
        assert "進行中" in bar.toolTip()
