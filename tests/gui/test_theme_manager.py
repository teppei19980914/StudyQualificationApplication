"""ThemeManagerのテスト."""

import json
from pathlib import Path

from study_python.gui.theme.theme_manager import (
    DARK_COLORS,
    LIGHT_COLORS,
    ThemeManager,
    ThemeType,
    _build_stylesheet,
)


class TestThemeType:
    """ThemeType列挙型のテスト."""

    def test_dark_value(self):
        assert ThemeType.DARK.value == "dark"

    def test_light_value(self):
        assert ThemeType.LIGHT.value == "light"

    def test_from_string(self):
        assert ThemeType("dark") == ThemeType.DARK
        assert ThemeType("light") == ThemeType.LIGHT


class TestBuildStylesheet:
    """_build_stylesheetのテスト."""

    def test_returns_string(self):
        result = _build_stylesheet(DARK_COLORS)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_colors(self):
        result = _build_stylesheet(DARK_COLORS)
        assert DARK_COLORS["bg_primary"] in result
        assert DARK_COLORS["text_primary"] in result

    def test_light_colors(self):
        result = _build_stylesheet(LIGHT_COLORS)
        assert LIGHT_COLORS["bg_primary"] in result


class TestThemeManagerInit:
    """ThemeManager初期化のテスト."""

    def test_default_theme_is_dark(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        assert manager.current_theme == ThemeType.DARK

    def test_loads_saved_preference(self, tmp_path: Path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
        manager = ThemeManager(settings_path)
        assert manager.current_theme == ThemeType.LIGHT

    def test_handles_invalid_settings_file(self, tmp_path: Path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("invalid json", encoding="utf-8")
        manager = ThemeManager(settings_path)
        assert manager.current_theme == ThemeType.DARK

    def test_handles_invalid_theme_value(self, tmp_path: Path):
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"theme": "invalid"}), encoding="utf-8")
        manager = ThemeManager(settings_path)
        assert manager.current_theme == ThemeType.DARK


class TestThemeManagerGetStylesheet:
    """get_stylesheetのテスト."""

    def test_returns_dark_stylesheet(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        stylesheet = manager.get_stylesheet()
        assert DARK_COLORS["bg_primary"] in stylesheet

    def test_returns_light_stylesheet(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        stylesheet = manager.get_stylesheet(ThemeType.LIGHT)
        assert LIGHT_COLORS["bg_primary"] in stylesheet

    def test_uses_current_theme_when_none(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        manager.current_theme = ThemeType.LIGHT
        stylesheet = manager.get_stylesheet()
        assert LIGHT_COLORS["bg_primary"] in stylesheet


class TestThemeManagerGetColors:
    """get_colorsのテスト."""

    def test_get_dark_colors(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        colors = manager.get_colors()
        assert colors["bg_primary"] == DARK_COLORS["bg_primary"]

    def test_get_light_colors(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        colors = manager.get_colors(ThemeType.LIGHT)
        assert colors["bg_primary"] == LIGHT_COLORS["bg_primary"]

    def test_returns_copy(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        colors1 = manager.get_colors()
        colors2 = manager.get_colors()
        assert colors1 is not colors2


class TestThemeManagerToggle:
    """toggle_themeのテスト."""

    def test_toggle_dark_to_light(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        result = manager.toggle_theme()
        assert result == ThemeType.LIGHT
        assert manager.current_theme == ThemeType.LIGHT

    def test_toggle_light_to_dark(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        manager.current_theme = ThemeType.LIGHT
        result = manager.toggle_theme()
        assert result == ThemeType.DARK

    def test_toggle_persists(self, tmp_path: Path):
        settings_path = tmp_path / "settings.json"
        manager = ThemeManager(settings_path)
        manager.toggle_theme()
        # 新しいインスタンスで読み込み確認
        manager2 = ThemeManager(settings_path)
        assert manager2.current_theme == ThemeType.LIGHT


class TestThemeManagerSetTheme:
    """set_themeのテスト."""

    def test_set_theme(self, tmp_path: Path):
        manager = ThemeManager(tmp_path / "settings.json")
        manager.set_theme(ThemeType.LIGHT)
        assert manager.current_theme == ThemeType.LIGHT

    def test_set_theme_persists(self, tmp_path: Path):
        settings_path = tmp_path / "settings.json"
        manager = ThemeManager(settings_path)
        manager.set_theme(ThemeType.LIGHT)
        manager2 = ThemeManager(settings_path)
        assert manager2.current_theme == ThemeType.LIGHT

    def test_set_theme_preserves_other_settings(self, tmp_path: Path):
        settings_path = tmp_path / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps({"other_key": "value", "theme": "dark"}),
            encoding="utf-8",
        )
        manager = ThemeManager(settings_path)
        manager.set_theme(ThemeType.LIGHT)
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["other_key"] == "value"
        assert data["theme"] == "light"
