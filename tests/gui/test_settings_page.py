"""SettingsPageのテスト."""

from pathlib import Path

from PySide6.QtWidgets import QLabel

from study_python.gui.pages.settings_page import SettingsPage
from study_python.gui.theme.theme_manager import ThemeManager, ThemeType
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository
from study_python.services.notification_service import NotificationService


def _make_notification_service(tmp_path: Path) -> NotificationService:
    """テスト用通知サービスを作成する."""
    storage = JsonStorage(tmp_path / "notifications.json")
    repo = NotificationRepository(storage)
    return NotificationService(repo, settings_path=tmp_path / "settings.json")


class TestSettingsPage:
    """SettingsPageのテスト."""

    def test_create(self, qtbot, theme_manager: ThemeManager):
        """生成テスト."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        assert page is not None

    def test_has_theme_toggle_button(self, qtbot, theme_manager: ThemeManager):
        """テーマ切替ボタンが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        assert page._theme_toggle_button is not None

    def test_theme_changed_signal(self, qtbot, theme_manager: ThemeManager):
        """テーマ切替でtheme_changedシグナルが発火する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        with qtbot.waitSignal(page.theme_changed, timeout=1000):
            page._on_toggle_theme()

    def test_toggle_theme_changes_theme(self, qtbot, theme_manager: ThemeManager):
        """テーマ切替でテーマが変更される."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        initial = theme_manager.current_theme
        page._on_toggle_theme()
        assert theme_manager.current_theme != initial

    def test_toggle_theme_twice_restores(self, qtbot, theme_manager: ThemeManager):
        """2回切替で元のテーマに戻る."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        initial = theme_manager.current_theme
        page._on_toggle_theme()
        page._on_toggle_theme()
        assert theme_manager.current_theme == initial

    def test_dark_mode_label(self, qtbot, tmp_path: Path):
        """ダークモード時のラベル表示."""
        tm = ThemeManager(settings_path=tmp_path / "settings.json")
        tm.current_theme = ThemeType.DARK
        page = SettingsPage(tm)
        qtbot.addWidget(page)
        label = page.findChild(QLabel, "settings_theme_label")
        assert "ダークモード" in label.text()

    def test_light_mode_label(self, qtbot, tmp_path: Path):
        """ライトモード時のラベル表示."""
        tm = ThemeManager(settings_path=tmp_path / "settings.json")
        tm.current_theme = ThemeType.LIGHT
        page = SettingsPage(tm)
        qtbot.addWidget(page)
        label = page.findChild(QLabel, "settings_theme_label")
        assert "ライトモード" in label.text()

    def test_dark_mode_button_text(self, qtbot, tmp_path: Path):
        """ダークモード時のボタンテキスト."""
        tm = ThemeManager(settings_path=tmp_path / "settings.json")
        tm.current_theme = ThemeType.DARK
        page = SettingsPage(tm)
        qtbot.addWidget(page)
        assert "ライトモード" in page._theme_toggle_button.text()

    def test_light_mode_button_text(self, qtbot, tmp_path: Path):
        """ライトモード時のボタンテキスト."""
        tm = ThemeManager(settings_path=tmp_path / "settings.json")
        tm.current_theme = ThemeType.LIGHT
        page = SettingsPage(tm)
        qtbot.addWidget(page)
        assert "ダークモード" in page._theme_toggle_button.text()

    def test_on_theme_changed_updates_display(self, qtbot, tmp_path: Path):
        """on_theme_changedで表示が更新される."""
        tm = ThemeManager(settings_path=tmp_path / "settings.json")
        tm.current_theme = ThemeType.DARK
        page = SettingsPage(tm)
        qtbot.addWidget(page)

        tm.current_theme = ThemeType.LIGHT
        page.on_theme_changed()

        label = page.findChild(QLabel, "settings_theme_label")
        assert "ライトモード" in label.text()

    def test_has_section_title(self, qtbot, theme_manager: ThemeManager):
        """セクションタイトルが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "section_title")
        assert len(labels) >= 1
        assert any("設定" in lbl.text() for lbl in labels)

    def test_has_theme_header(self, qtbot, theme_manager: ThemeManager):
        """テーマヘッダーが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "card_title")
        assert any("テーマ" in lbl.text() for lbl in labels)


class TestSettingsPageNotification:
    """SettingsPage通知セクションのテスト."""

    def test_has_notification_header(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """通知ヘッダーが存在する."""
        ns = _make_notification_service(tmp_path)
        page = SettingsPage(theme_manager, notification_service=ns)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "card_title")
        assert any("通知" in lbl.text() for lbl in labels)

    def test_notification_label_shows_enabled(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """通知有効時のラベル表示."""
        ns = _make_notification_service(tmp_path)
        page = SettingsPage(theme_manager, notification_service=ns)
        qtbot.addWidget(page)
        label = page.findChild(QLabel, "settings_notification_label")
        assert "有効" in label.text()

    def test_notification_label_shows_disabled(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """通知無効時のラベル表示."""
        ns = _make_notification_service(tmp_path)
        ns.set_notifications_enabled(False)
        page = SettingsPage(theme_manager, notification_service=ns)
        qtbot.addWidget(page)
        label = page.findChild(QLabel, "settings_notification_label")
        assert "無効" in label.text()

    def test_notification_toggle_changes_state(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """通知切替で状態が変更される."""
        ns = _make_notification_service(tmp_path)
        page = SettingsPage(theme_manager, notification_service=ns)
        qtbot.addWidget(page)
        assert ns.notifications_enabled is True
        page._on_toggle_notifications()
        assert ns.notifications_enabled is False

    def test_notification_toggle_updates_label(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """通知切替でラベルが更新される."""
        ns = _make_notification_service(tmp_path)
        page = SettingsPage(theme_manager, notification_service=ns)
        qtbot.addWidget(page)
        page._on_toggle_notifications()
        label = page.findChild(QLabel, "settings_notification_label")
        assert "無効" in label.text()

    def test_notification_without_service(self, qtbot, theme_manager: ThemeManager):
        """通知サービスなしでもエラーにならない."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        label = page.findChild(QLabel, "settings_notification_label")
        assert "未設定" in label.text()
        # ボタンが無効化されている
        assert not page._notification_toggle_button.isEnabled()

    def test_notification_toggle_without_service_noop(
        self, qtbot, theme_manager: ThemeManager
    ):
        """通知サービスなしで切替してもエラーにならない."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        page._on_toggle_notifications()


class TestSettingsPageDataManagement:
    """SettingsPageデータ管理セクションのテスト."""

    def test_has_data_management_header(self, qtbot, theme_manager: ThemeManager):
        """データ管理ヘッダーが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "card_title")
        assert any("データ管理" in lbl.text() for lbl in labels)

    def test_has_export_button(self, qtbot, theme_manager: ThemeManager):
        """エクスポートボタンが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        assert page._export_button is not None
        assert "エクスポート" in page._export_button.text()

    def test_has_import_button(self, qtbot, theme_manager: ThemeManager):
        """インポートボタンが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        assert page._import_button is not None
        assert "インポート" in page._import_button.text()

    def test_has_data_path_label(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """データ保存先ラベルが存在する."""
        page = SettingsPage(theme_manager, data_dir=tmp_path)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "muted_text")
        assert any("データ保存先" in lbl.text() for lbl in labels)

    def test_data_path_shows_correct_dir(
        self, qtbot, theme_manager: ThemeManager, tmp_path: Path
    ):
        """データ保存先にディレクトリパスが表示される."""
        page = SettingsPage(theme_manager, data_dir=tmp_path)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "muted_text")
        assert any(str(tmp_path) in lbl.text() for lbl in labels)

    def test_has_clear_data_button(self, qtbot, theme_manager: ThemeManager):
        """全データ削除ボタンが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        assert page._clear_data_button is not None
        assert "全データ削除" in page._clear_data_button.text()

    def test_clear_data_button_is_danger(self, qtbot, theme_manager: ThemeManager):
        """全データ削除ボタンがdanger_buttonスタイル."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        assert page._clear_data_button.objectName() == "danger_button"


class TestSettingsPageAbout:
    """SettingsPageアプリ情報セクションのテスト."""

    def test_has_about_header(self, qtbot, theme_manager: ThemeManager):
        """アプリ情報ヘッダーが存在する."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "card_title")
        assert any("アプリ情報" in lbl.text() for lbl in labels)

    def test_has_version_label(self, qtbot, theme_manager: ThemeManager):
        """バージョンラベルが存在する."""
        from study_python import __version__

        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "muted_text")
        assert any(__version__ in lbl.text() for lbl in labels)

    def test_version_label_contains_app_name(self, qtbot, theme_manager: ThemeManager):
        """バージョンラベルにアプリ名が含まれる."""
        page = SettingsPage(theme_manager)
        qtbot.addWidget(page)
        labels = page.findChildren(QLabel, "muted_text")
        assert any("Study Planner" in lbl.text() for lbl in labels)
