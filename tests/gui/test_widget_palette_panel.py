"""WidgetPalettePanelのテスト."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.widget_palette_panel import (
    PaletteItem,
    WidgetPalettePanel,
)
from study_python.services.dashboard_layout_service import WidgetMetadata


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    """テーママネージャ."""
    return ThemeManager(settings_path=tmp_path / "settings.json")


@pytest.fixture
def sample_metadata() -> list[WidgetMetadata]:
    """サンプルウィジェットメタデータ."""
    return [
        WidgetMetadata(
            widget_type="total_time_card",
            display_name="合計学習時間",
            icon="\u23f1\ufe0f",
            default_span=1,
            allowed_spans=[1],
        ),
        WidgetMetadata(
            widget_type="streak_card",
            display_name="連続学習",
            icon="\U0001f525",
            default_span=1,
            allowed_spans=[1],
        ),
    ]


class TestWidgetPalettePanel:
    """WidgetPalettePanelのテスト."""

    def test_create_panel(self, qtbot, theme_manager: ThemeManager) -> None:
        """パネルを生成できることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        assert panel is not None

    def test_fixed_width(self, qtbot, theme_manager: ThemeManager) -> None:
        """固定幅が220であることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        assert panel.minimumWidth() == 220
        assert panel.maximumWidth() == 220

    def test_initial_no_items(self, qtbot, theme_manager: ThemeManager) -> None:
        """初期状態でアイテムが0件であることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        assert len(panel.palette_items) == 0

    def test_update_items(
        self,
        qtbot,
        theme_manager: ThemeManager,
        sample_metadata: list[WidgetMetadata],
    ) -> None:
        """update_items後にPaletteItemが生成されることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        panel.update_items(sample_metadata)
        assert len(panel.palette_items) == 2

    def test_update_items_clears_old(
        self,
        qtbot,
        theme_manager: ThemeManager,
        sample_metadata: list[WidgetMetadata],
    ) -> None:
        """再呼び出しで古いアイテムがクリアされることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        panel.update_items(sample_metadata)
        assert len(panel.palette_items) == 2

        panel.update_items([sample_metadata[0]])
        assert len(panel.palette_items) == 1

    def test_update_items_empty(self, qtbot, theme_manager: ThemeManager) -> None:
        """空リストでアイテムが0件になることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        panel.update_items([])
        assert len(panel.palette_items) == 0

    def test_header_label(self, qtbot, theme_manager: ThemeManager) -> None:
        """ヘッダーラベルに'パーツ'が含まれることを確認する."""
        panel = WidgetPalettePanel(theme_manager)
        qtbot.addWidget(panel)
        # ヘッダーラベルを確認
        from PySide6.QtWidgets import QLabel

        labels = panel.findChildren(QLabel)
        header_texts = [label.text() for label in labels]
        assert any("パーツ" in text for text in header_texts)


class TestPaletteItem:
    """PaletteItemのテスト."""

    @pytest.fixture
    def metadata(self) -> WidgetMetadata:
        """テスト用メタデータ."""
        return WidgetMetadata(
            widget_type="total_time_card",
            display_name="合計学習時間",
            icon="\u23f1\ufe0f",
            default_span=1,
            allowed_spans=[1],
        )

    def test_create_item(
        self,
        qtbot,
        theme_manager: ThemeManager,
        metadata: WidgetMetadata,
    ) -> None:
        """アイテムを生成できることを確認する."""
        item = PaletteItem(metadata, theme_manager)
        qtbot.addWidget(item)
        assert item is not None

    def test_shows_icon_and_name(
        self,
        qtbot,
        theme_manager: ThemeManager,
        metadata: WidgetMetadata,
    ) -> None:
        """アイコンと表示名が表示されることを確認する."""
        item = PaletteItem(metadata, theme_manager)
        qtbot.addWidget(item)
        from PySide6.QtWidgets import QLabel

        labels = item.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("\u23f1\ufe0f" in text for text in texts)
        assert any("合計学習時間" in text for text in texts)

    def test_stores_widget_type(
        self,
        qtbot,
        theme_manager: ThemeManager,
        metadata: WidgetMetadata,
    ) -> None:
        """widget_typeプロパティが正しいことを確認する."""
        item = PaletteItem(metadata, theme_manager)
        qtbot.addWidget(item)
        assert item.widget_type == "total_time_card"

    def test_mouse_press_stores_pos(
        self,
        qtbot,
        theme_manager: ThemeManager,
        metadata: WidgetMetadata,
    ) -> None:
        """マウスプレスでドラッグ開始位置が記録されることを確認する."""
        item = PaletteItem(metadata, theme_manager)
        qtbot.addWidget(item)
        assert item._drag_start_pos is None
        qtbot.mousePress(item, Qt.MouseButton.LeftButton)
        assert item._drag_start_pos is not None

    def test_fixed_height(
        self,
        qtbot,
        theme_manager: ThemeManager,
        metadata: WidgetMetadata,
    ) -> None:
        """固定高さが48であることを確認する."""
        item = PaletteItem(metadata, theme_manager)
        qtbot.addWidget(item)
        assert item.minimumHeight() == 48
        assert item.maximumHeight() == 48
