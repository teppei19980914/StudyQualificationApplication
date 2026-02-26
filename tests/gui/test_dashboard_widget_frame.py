"""DashboardWidgetFrameのテスト."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.dashboard_widget_frame import (
    DashboardWidgetFrame,
)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    """テスト用テーママネージャ."""
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestDashboardWidgetFrame:
    """DashboardWidgetFrameのテスト."""

    def test_create_widget(self, qtbot, theme_manager: ThemeManager) -> None:
        content = QLabel("Test Content")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test Widget",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        assert frame is not None
        assert frame.widget_index == 0

    def test_content_widget_accessible(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Hello")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        assert frame.content_widget is content

    def test_header_hidden_by_default(self, qtbot, theme_manager: ThemeManager) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        assert frame._header.isHidden()

    def test_set_edit_mode_shows_header(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        frame.set_edit_mode(True)
        assert not frame._header.isHidden()

    def test_set_edit_mode_false_hides_header(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        frame.set_edit_mode(True)
        frame.set_edit_mode(False)
        assert frame._header.isHidden()

    def test_remove_button_emits_signal(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=3,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        frame.set_edit_mode(True)

        with qtbot.waitSignal(frame.remove_requested) as blocker:
            frame._remove_button.click()
        assert blocker.args == [3]

    def test_resize_button_emits_signal(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=2,
            display_name="Test",
            theme_manager=theme_manager,
            resizable=True,
        )
        qtbot.addWidget(frame)
        frame.set_edit_mode(True)

        with qtbot.waitSignal(frame.resize_requested) as blocker:
            frame._resize_button.click()
        assert blocker.args == [2]

    def test_resize_button_hidden_when_not_resizable(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
            resizable=False,
        )
        qtbot.addWidget(frame)
        assert frame._resize_button.isHidden()

    def test_resize_button_visible_when_resizable(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
            resizable=True,
        )
        qtbot.addWidget(frame)
        assert not frame._resize_button.isHidden()

    def test_widget_index_setter(self, qtbot, theme_manager: ThemeManager) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        frame.widget_index = 5
        assert frame.widget_index == 5

    def test_display_name_shown_in_header(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="\u30c6\u30b9\u30c8\u30a6\u30a3\u30b8\u30a7\u30c3\u30c8",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        assert (
            "\u30c6\u30b9\u30c8\u30a6\u30a3\u30b8\u30a7\u30c3\u30c8"
            in frame._name_label.text()
        )

    def test_mouse_press_in_edit_mode_sets_drag_start(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        frame.set_edit_mode(True)
        frame.show()

        qtbot.mousePress(frame, Qt.MouseButton.LeftButton)
        assert frame._drag_start_pos is not None

    def test_mouse_press_not_in_edit_mode_no_drag_start(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        frame.show()

        qtbot.mousePress(frame, Qt.MouseButton.LeftButton)
        assert frame._drag_start_pos is None

    def test_drag_handle_has_open_hand_cursor(
        self, qtbot, theme_manager: ThemeManager
    ) -> None:
        content = QLabel("Test")
        frame = DashboardWidgetFrame(
            content_widget=content,
            widget_index=0,
            display_name="Test",
            theme_manager=theme_manager,
        )
        qtbot.addWidget(frame)
        assert frame._drag_handle.cursor().shape() == Qt.CursorShape.OpenHandCursor
