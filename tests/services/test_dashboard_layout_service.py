"""DashboardLayoutServiceのテスト."""

import json
from pathlib import Path

import pytest

from study_python.services.dashboard_layout_service import (
    DashboardLayoutService,
    DashboardWidgetConfig,
)


@pytest.fixture
def settings_path(tmp_path: Path) -> Path:
    """テスト用設定ファイルパス."""
    return tmp_path / "settings.json"


@pytest.fixture
def service(settings_path: Path) -> DashboardLayoutService:
    """テスト用サービスインスタンス."""
    return DashboardLayoutService(settings_path)


class TestGetDefaultLayout:
    """get_default_layoutのテスト."""

    def test_returns_9_widgets(self, service: DashboardLayoutService) -> None:
        layout = service.get_default_layout()
        assert len(layout) == 9

    def test_first_widget_is_today_banner(
        self, service: DashboardLayoutService
    ) -> None:
        layout = service.get_default_layout()
        assert layout[0].widget_type == "today_banner"
        assert layout[0].column_span == 2

    def test_last_widget_is_daily_chart(self, service: DashboardLayoutService) -> None:
        layout = service.get_default_layout()
        assert layout[-1].widget_type == "daily_chart"
        assert layout[-1].column_span == 2

    def test_all_widget_types_are_valid(self, service: DashboardLayoutService) -> None:
        layout = service.get_default_layout()
        for widget in layout:
            assert widget.widget_type in DashboardLayoutService.WIDGET_REGISTRY


class TestGetLayout:
    """get_layoutのテスト."""

    def test_returns_default_when_no_file(
        self, service: DashboardLayoutService
    ) -> None:
        layout = service.get_layout()
        default = service.get_default_layout()
        assert len(layout) == len(default)

    def test_returns_saved_layout(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        saved = [
            {"widget_type": "streak_card", "column_span": 1},
            {"widget_type": "today_banner", "column_span": 2},
        ]
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"dashboard_layout": saved}), encoding="utf-8"
        )
        layout = service.get_layout()
        assert len(layout) == 2
        assert layout[0].widget_type == "streak_card"
        assert layout[1].widget_type == "today_banner"

    def test_returns_default_on_invalid_json(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text("not valid json", encoding="utf-8")
        layout = service.get_layout()
        default = service.get_default_layout()
        assert len(layout) == len(default)

    def test_returns_default_when_layout_key_missing(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
        layout = service.get_layout()
        default = service.get_default_layout()
        assert len(layout) == len(default)

    def test_returns_default_when_layout_is_empty(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps({"dashboard_layout": []}), encoding="utf-8")
        layout = service.get_layout()
        default = service.get_default_layout()
        assert len(layout) == len(default)

    def test_skips_unknown_widget_types(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        saved = [
            {"widget_type": "unknown_widget", "column_span": 1},
            {"widget_type": "streak_card", "column_span": 1},
        ]
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"dashboard_layout": saved}), encoding="utf-8"
        )
        layout = service.get_layout()
        assert len(layout) == 1
        assert layout[0].widget_type == "streak_card"

    def test_corrects_invalid_column_span(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        saved = [
            {"widget_type": "today_banner", "column_span": 1},
        ]
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"dashboard_layout": saved}), encoding="utf-8"
        )
        layout = service.get_layout()
        assert layout[0].column_span == 2


class TestSaveLayout:
    """save_layoutのテスト."""

    def test_saves_layout(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        layout = [
            DashboardWidgetConfig("streak_card", 1),
            DashboardWidgetConfig("today_banner", 2),
        ]
        service.save_layout(layout)
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert len(data["dashboard_layout"]) == 2
        assert data["dashboard_layout"][0]["widget_type"] == "streak_card"

    def test_preserves_other_settings(
        self, service: DashboardLayoutService, settings_path: Path
    ) -> None:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
        layout = [DashboardWidgetConfig("streak_card", 1)]
        service.save_layout(layout)
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["theme"] == "light"
        assert "dashboard_layout" in data

    def test_creates_parent_directory(
        self,
        tmp_path: Path,
    ) -> None:
        deep_path = tmp_path / "a" / "b" / "settings.json"
        svc = DashboardLayoutService(deep_path)
        svc.save_layout([DashboardWidgetConfig("streak_card", 1)])
        assert deep_path.exists()

    def test_roundtrip(
        self,
        service: DashboardLayoutService,
    ) -> None:
        layout = [
            DashboardWidgetConfig("today_banner", 2),
            DashboardWidgetConfig("streak_card", 1),
            DashboardWidgetConfig("weekly_comparison", 2),
        ]
        service.save_layout(layout)
        loaded = service.get_layout()
        assert len(loaded) == 3
        assert loaded[0].widget_type == "today_banner"
        assert loaded[1].widget_type == "streak_card"
        assert loaded[2].widget_type == "weekly_comparison"
        assert loaded[2].column_span == 2


class TestGetAvailableWidgets:
    """get_available_widgetsのテスト."""

    def test_returns_empty_when_all_placed(
        self, service: DashboardLayoutService
    ) -> None:
        layout = service.get_default_layout()
        available = service.get_available_widgets(layout)
        assert len(available) == 0

    def test_returns_all_when_empty_layout(
        self, service: DashboardLayoutService
    ) -> None:
        available = service.get_available_widgets([])
        assert len(available) == len(DashboardLayoutService.WIDGET_REGISTRY)

    def test_returns_unplaced_widgets(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("today_banner", 2)]
        available = service.get_available_widgets(layout)
        types = {w.widget_type for w in available}
        assert "today_banner" not in types
        assert "streak_card" in types


class TestReorder:
    """reorderのテスト."""

    def test_move_forward(self, service: DashboardLayoutService) -> None:
        layout = [
            DashboardWidgetConfig("a", 1),
            DashboardWidgetConfig("b", 1),
            DashboardWidgetConfig("c", 1),
        ]
        result = service.reorder(layout, 0, 2)
        assert [w.widget_type for w in result] == ["b", "c", "a"]

    def test_move_backward(self, service: DashboardLayoutService) -> None:
        layout = [
            DashboardWidgetConfig("a", 1),
            DashboardWidgetConfig("b", 1),
            DashboardWidgetConfig("c", 1),
        ]
        result = service.reorder(layout, 2, 0)
        assert [w.widget_type for w in result] == ["c", "a", "b"]

    def test_same_index(self, service: DashboardLayoutService) -> None:
        layout = [
            DashboardWidgetConfig("a", 1),
            DashboardWidgetConfig("b", 1),
        ]
        result = service.reorder(layout, 0, 0)
        assert [w.widget_type for w in result] == ["a", "b"]

    def test_invalid_from_index(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("a", 1)]
        result = service.reorder(layout, -1, 0)
        assert len(result) == 1

    def test_invalid_to_index(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("a", 1)]
        result = service.reorder(layout, 0, 5)
        assert len(result) == 1

    def test_does_not_mutate_original(self, service: DashboardLayoutService) -> None:
        layout = [
            DashboardWidgetConfig("a", 1),
            DashboardWidgetConfig("b", 1),
        ]
        service.reorder(layout, 0, 1)
        assert layout[0].widget_type == "a"


class TestAddWidget:
    """add_widgetのテスト."""

    def test_add_valid_widget(self, service: DashboardLayoutService) -> None:
        layout: list[DashboardWidgetConfig] = []
        result = service.add_widget(layout, "streak_card")
        assert len(result) == 1
        assert result[0].widget_type == "streak_card"
        assert result[0].column_span == 1

    def test_add_unknown_widget(self, service: DashboardLayoutService) -> None:
        layout: list[DashboardWidgetConfig] = []
        result = service.add_widget(layout, "nonexistent")
        assert len(result) == 0

    def test_add_duplicate_widget(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("streak_card", 1)]
        result = service.add_widget(layout, "streak_card")
        assert len(result) == 1

    def test_uses_default_span(self, service: DashboardLayoutService) -> None:
        result = service.add_widget([], "today_banner")
        assert result[0].column_span == 2

    def test_does_not_mutate_original(self, service: DashboardLayoutService) -> None:
        layout: list[DashboardWidgetConfig] = []
        service.add_widget(layout, "streak_card")
        assert len(layout) == 0


class TestRemoveWidget:
    """remove_widgetのテスト."""

    def test_remove_valid_index(self, service: DashboardLayoutService) -> None:
        layout = [
            DashboardWidgetConfig("a", 1),
            DashboardWidgetConfig("b", 1),
        ]
        result = service.remove_widget(layout, 0)
        assert len(result) == 1
        assert result[0].widget_type == "b"

    def test_remove_invalid_index(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("a", 1)]
        result = service.remove_widget(layout, 5)
        assert len(result) == 1

    def test_remove_negative_index(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("a", 1)]
        result = service.remove_widget(layout, -1)
        assert len(result) == 1

    def test_does_not_mutate_original(self, service: DashboardLayoutService) -> None:
        layout = [
            DashboardWidgetConfig("a", 1),
            DashboardWidgetConfig("b", 1),
        ]
        service.remove_widget(layout, 0)
        assert len(layout) == 2


class TestResizeWidget:
    """resize_widgetのテスト."""

    def test_resize_toggles_span(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("weekly_comparison", 1)]
        result = service.resize_widget(layout, 0)
        assert result[0].column_span == 2

    def test_resize_cycles_back(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("weekly_comparison", 2)]
        result = service.resize_widget(layout, 0)
        assert result[0].column_span == 1

    def test_resize_single_span_widget_unchanged(
        self, service: DashboardLayoutService
    ) -> None:
        layout = [DashboardWidgetConfig("streak_card", 1)]
        result = service.resize_widget(layout, 0)
        assert result[0].column_span == 1

    def test_resize_invalid_index(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("weekly_comparison", 1)]
        result = service.resize_widget(layout, 5)
        assert result[0].column_span == 1

    def test_resize_negative_index(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("weekly_comparison", 1)]
        result = service.resize_widget(layout, -1)
        assert result[0].column_span == 1

    def test_does_not_mutate_original(self, service: DashboardLayoutService) -> None:
        layout = [DashboardWidgetConfig("weekly_comparison", 1)]
        service.resize_widget(layout, 0)
        assert layout[0].column_span == 1


class TestWidgetRegistry:
    """ウィジェット登録簿のテスト."""

    def test_all_entries_have_valid_metadata(self) -> None:
        for key, meta in DashboardLayoutService.WIDGET_REGISTRY.items():
            assert meta.widget_type == key
            assert len(meta.display_name) > 0
            assert len(meta.icon) > 0
            assert meta.default_span in meta.allowed_spans
            assert all(s in (1, 2) for s in meta.allowed_spans)

    def test_registry_has_9_widgets(self) -> None:
        assert len(DashboardLayoutService.WIDGET_REGISTRY) == 9
