"""MainWindowのテスト."""

from pathlib import Path

from study_python.gui.main_window import MainWindow


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

    def test_theme_toggle(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        initial_theme = window._theme_manager.current_theme

        window._on_toggle_theme()
        assert window._theme_manager.current_theme != initial_theme

        window._on_toggle_theme()
        assert window._theme_manager.current_theme == initial_theme

    def test_has_sidebar(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._sidebar is not None

    def test_has_pages(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        assert window._dashboard_page is not None
        assert window._goal_page is not None
        assert window._gantt_page is not None
        assert window._book_page is not None
        assert window._stats_page is not None
        assert window._stack.count() == 5

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

    def test_dashboard_page_refresh_on_switch(self, qtbot, tmp_path: Path):
        window = MainWindow(data_dir=tmp_path)
        qtbot.addWidget(window)
        window._on_page_changed(0)
        assert window._stack.currentIndex() == 0
