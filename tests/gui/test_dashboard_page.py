"""DashboardPageのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.pages.dashboard_page import DashboardPage
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.study_log_repository import StudyLogRepository
from study_python.repositories.task_repository import TaskRepository
from study_python.services.dashboard_layout_service import (
    DashboardLayoutService,
    DashboardWidgetConfig,
)
from study_python.services.goal_service import GoalService
from study_python.services.study_log_service import StudyLogService
from study_python.services.task_service import TaskService


@pytest.fixture
def settings_path(tmp_path: Path) -> Path:
    """設定ファイルパス."""
    return tmp_path / "settings.json"


@pytest.fixture
def theme_manager(settings_path: Path) -> ThemeManager:
    """テーママネージャ."""
    return ThemeManager(settings_path=settings_path)


@pytest.fixture
def layout_service(settings_path: Path) -> DashboardLayoutService:
    """レイアウトサービス."""
    return DashboardLayoutService(settings_path)


@pytest.fixture
def goal_service(tmp_path: Path) -> GoalService:
    """GoalService."""
    goal_storage = JsonStorage(tmp_path / "goals.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    goal_repo = GoalRepository(goal_storage)
    task_repo = TaskRepository(task_storage)
    return GoalService(goal_repo, task_repo)


@pytest.fixture
def task_service(tmp_path: Path) -> TaskService:
    """TaskService."""
    storage = JsonStorage(tmp_path / "tasks.json")
    repo = TaskRepository(storage)
    return TaskService(repo)


@pytest.fixture
def study_log_service(tmp_path: Path) -> StudyLogService:
    """StudyLogService."""
    storage = JsonStorage(tmp_path / "study_logs.json")
    repo = StudyLogRepository(storage)
    return StudyLogService(repo)


@pytest.fixture
def dashboard_page(
    qtbot,
    goal_service: GoalService,
    task_service: TaskService,
    study_log_service: StudyLogService,
    theme_manager: ThemeManager,
    layout_service: DashboardLayoutService,
) -> DashboardPage:
    """DashboardPageインスタンス."""
    page = DashboardPage(
        goal_service=goal_service,
        task_service=task_service,
        study_log_service=study_log_service,
        theme_manager=theme_manager,
        layout_service=layout_service,
    )
    qtbot.addWidget(page)
    return page


class TestDashboardPageCreation:
    """DashboardPage生成のテスト."""

    def test_create_page(self, dashboard_page: DashboardPage) -> None:
        assert dashboard_page is not None

    def test_default_layout_has_9_widgets(self, dashboard_page: DashboardPage) -> None:
        assert len(dashboard_page._widget_frames) == 9

    def test_edit_mode_off_by_default(self, dashboard_page: DashboardPage) -> None:
        assert dashboard_page._edit_mode is False

    def test_add_button_hidden_by_default(self, dashboard_page: DashboardPage) -> None:
        assert dashboard_page._add_widget_button.isHidden()


class TestDashboardPageEditMode:
    """編集モードのテスト."""

    def test_toggle_edit_mode_on(self, dashboard_page: DashboardPage) -> None:
        dashboard_page._toggle_edit_mode()
        assert dashboard_page._edit_mode is True
        assert not dashboard_page._add_widget_button.isHidden()

    def test_toggle_edit_mode_off(self, dashboard_page: DashboardPage) -> None:
        dashboard_page._toggle_edit_mode()
        dashboard_page._toggle_edit_mode()
        assert dashboard_page._edit_mode is False
        assert dashboard_page._add_widget_button.isHidden()

    def test_edit_mode_shows_headers(self, dashboard_page: DashboardPage) -> None:
        dashboard_page._toggle_edit_mode()
        for frame in dashboard_page._widget_frames:
            assert not frame._header.isHidden()

    def test_exit_edit_saves_layout(
        self, dashboard_page: DashboardPage, layout_service: DashboardLayoutService
    ) -> None:
        dashboard_page._toggle_edit_mode()
        dashboard_page._toggle_edit_mode()
        saved = layout_service.get_layout()
        assert len(saved) == 9

    def test_edit_button_text_changes(self, dashboard_page: DashboardPage) -> None:
        assert "\u7de8\u96c6" in dashboard_page._edit_button.text()
        dashboard_page._toggle_edit_mode()
        assert "\u5b8c\u4e86" in dashboard_page._edit_button.text()


class TestDashboardPageWidgetRemove:
    """ウィジェット削除のテスト."""

    def test_remove_widget(self, dashboard_page: DashboardPage) -> None:
        initial_count = len(dashboard_page._widget_frames)
        dashboard_page._on_widget_removed(0)
        assert len(dashboard_page._widget_frames) == initial_count - 1

    def test_remove_reduces_layout(self, dashboard_page: DashboardPage) -> None:
        dashboard_page._on_widget_removed(0)
        assert len(dashboard_page._current_layout) == 8


class TestDashboardPageWidgetResize:
    """ウィジェットリサイズのテスト."""

    def test_resize_resizable_widget(self, dashboard_page: DashboardPage) -> None:
        weekly_idx = None
        for i, config in enumerate(dashboard_page._current_layout):
            if config.widget_type == "weekly_comparison":
                weekly_idx = i
                break
        assert weekly_idx is not None
        original_span = dashboard_page._current_layout[weekly_idx].column_span
        dashboard_page._on_widget_resized(weekly_idx)
        new_span = dashboard_page._current_layout[weekly_idx].column_span
        assert new_span != original_span


class TestDashboardPageDrop:
    """ドロップ操作のテスト."""

    def test_drop_reorders_layout(self, dashboard_page: DashboardPage) -> None:
        first_type = dashboard_page._current_layout[0].widget_type
        second_type = dashboard_page._current_layout[1].widget_type
        dashboard_page._on_drop(0, 1)
        assert dashboard_page._current_layout[0].widget_type == second_type
        assert dashboard_page._current_layout[1].widget_type == first_type

    def test_drop_same_index_no_change(self, dashboard_page: DashboardPage) -> None:
        original = [c.widget_type for c in dashboard_page._current_layout]
        dashboard_page._on_drop(0, 0)
        current = [c.widget_type for c in dashboard_page._current_layout]
        assert original == current


class TestDashboardPageRefresh:
    """refresh()のテスト."""

    def test_refresh_with_no_data(self, dashboard_page: DashboardPage) -> None:
        dashboard_page.refresh()
        total_card = dashboard_page._active_widgets.get("total_time_card")
        assert total_card is not None

    def test_refresh_with_study_data(
        self,
        dashboard_page: DashboardPage,
        study_log_service: StudyLogService,
        goal_service: GoalService,
    ) -> None:
        from study_python.models.goal import WhenType

        goal_service.create_goal(
            what="Test Goal",
            why="Test Why",
            when_target="2026-03",
            when_type=WhenType.PERIOD,
            how="Test How",
        )

        study_log_service.add_study_log(
            task_id="test-task-1",
            study_date=date.today(),
            duration_minutes=45,
            memo="test",
        )
        dashboard_page.refresh()

        streak_card = dashboard_page._active_widgets.get("streak_card")
        assert streak_card is not None

    def test_refresh_populates_active_widgets(
        self, dashboard_page: DashboardPage
    ) -> None:
        dashboard_page.refresh()
        assert "today_banner" in dashboard_page._active_widgets
        assert "streak_card" in dashboard_page._active_widgets
        assert "daily_chart" in dashboard_page._active_widgets


class TestDashboardPageCustomLayout:
    """カスタムレイアウトのテスト."""

    def test_loads_saved_layout(
        self,
        qtbot,
        goal_service: GoalService,
        task_service: TaskService,
        study_log_service: StudyLogService,
        theme_manager: ThemeManager,
        layout_service: DashboardLayoutService,
    ) -> None:
        layout_service.save_layout(
            [
                DashboardWidgetConfig("streak_card", 1),
                DashboardWidgetConfig("today_banner", 2),
            ]
        )
        page = DashboardPage(
            goal_service=goal_service,
            task_service=task_service,
            study_log_service=study_log_service,
            theme_manager=theme_manager,
            layout_service=layout_service,
        )
        qtbot.addWidget(page)
        assert len(page._widget_frames) == 2
        assert page._current_layout[0].widget_type == "streak_card"

    def test_create_unknown_widget_returns_none(
        self, dashboard_page: DashboardPage
    ) -> None:
        result = dashboard_page._create_widget("nonexistent")
        assert result is None


class TestDashboardPageThemeChanged:
    """テーマ変更のテスト."""

    def test_on_theme_changed_rebuilds(self, dashboard_page: DashboardPage) -> None:
        initial_count = len(dashboard_page._widget_frames)
        dashboard_page.on_theme_changed()
        assert len(dashboard_page._widget_frames) == initial_count


class TestDashboardPageDropIndex:
    """ドロップインデックス計算のテスト."""

    def test_calculate_drop_index_at_top(self, dashboard_page: DashboardPage) -> None:
        from PySide6.QtCore import QPoint

        dashboard_page.show()
        index = dashboard_page._calculate_drop_index(QPoint(0, 0))
        assert index == 0

    def test_calculate_drop_index_at_bottom(
        self, dashboard_page: DashboardPage
    ) -> None:
        from PySide6.QtCore import QPoint

        dashboard_page.show()
        index = dashboard_page._calculate_drop_index(QPoint(0, 999999))
        assert index == len(dashboard_page._widget_frames) - 1
