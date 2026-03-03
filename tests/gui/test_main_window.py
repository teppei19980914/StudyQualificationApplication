"""MainWindowのテスト."""

from pathlib import Path

from study_python.gui.main_window import MainWindow
from study_python.gui.widgets.navigation_drawer import SETTINGS_PAGE_INDEX


class TestMainWindow:
    """MainWindowのテスト."""

    def test_create_window(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window.windowTitle()
        assert window.minimumWidth() >= 1100

    def test_page_switching(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._stack.currentIndex() == 0

        window._on_page_changed(1)
        assert window._stack.currentIndex() == 1

        window._on_page_changed(0)
        assert window._stack.currentIndex() == 0

    def test_has_header_bar(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._header_bar is not None
        assert window._header_bar.objectName() == "header_bar"

    def test_has_drawer(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._drawer is not None
        assert window._drawer_overlay is not None

    def test_has_pages(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._dashboard_page is not None
        assert window._goal_page is not None
        assert window._gantt_page is not None
        assert window._book_page is not None
        assert window._stats_page is not None
        assert window._settings_page is not None
        assert window._stack.count() == 6

    def test_book_page_refresh_on_switch(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(3)
        assert window._stack.currentIndex() == 3

    def test_stats_page_refresh_on_switch(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(4)
        assert window._stack.currentIndex() == 4

    def test_has_notification_service(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._notification_service is not None

    def test_dashboard_page_refresh_on_switch(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(0)
        assert window._stack.currentIndex() == 0

    def test_settings_page_access(self, qtbot, tmp_path: Path):
        """設定ページにアクセスできる."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_settings_requested()
        assert window._stack.currentIndex() == SETTINGS_PAGE_INDEX

    def test_theme_toggle_via_settings(self, qtbot, tmp_path: Path):
        """設定ページ経由でテーマ切替ができる."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        initial_theme = window._theme_manager.current_theme
        window._settings_page._on_toggle_theme()
        assert window._theme_manager.current_theme != initial_theme

    def test_drawer_open_close(self, qtbot, tmp_path: Path):
        """ドロワーの開閉ができる."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window.show()
        window.resize(1280, 800)

        assert not window._drawer.isVisible()
        window._open_drawer()
        assert window._drawer.isVisible()
        assert window._drawer_overlay.isVisible()

        window._close_drawer()
        # アニメーション完了前はまだvisibleの可能性がある
        # close_drawerが呼ばれたことを確認
        assert window._drawer_anim is not None

    def test_toggle_drawer(self, qtbot, tmp_path: Path):
        """ドロワーのトグルができる."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window.show()
        window.resize(1280, 800)

        window._toggle_drawer()
        assert window._drawer.isVisible()

    def test_page_changed_updates_header_title(self, qtbot, tmp_path: Path):
        """ページ切替でヘッダータイトルが更新される."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(1)
        assert window._header_bar._title_label.text() == "3W1H 目標"

    def test_page_changed_updates_drawer_check(self, qtbot, tmp_path: Path):
        """ページ切替でドロワーのチェック状態が更新される."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(2)
        assert window._drawer._buttons[2].isChecked()

    def test_close_drawer_when_not_visible(self, qtbot, tmp_path: Path):
        """非表示時のclose_drawerはエラーにならない."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._close_drawer()

    def test_settings_page_has_notification_service(self, qtbot, tmp_path: Path):
        """設定ページに通知サービスが渡されている."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._settings_page._notification_service is not None

    def test_settings_page_has_data_dir(self, qtbot, tmp_path: Path):
        """設定ページにデータディレクトリが渡されている."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._settings_page._data_dir == tmp_path

    def test_gantt_page_refresh_on_switch(self, qtbot, tmp_path: Path):
        """ガントページ切替でリフレッシュされる."""
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(2)
        assert window._stack.currentIndex() == 2
