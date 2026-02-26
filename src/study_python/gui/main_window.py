"""メインウィンドウ."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from study_python.gui.pages.book_page import BookPage
from study_python.gui.pages.dashboard_page import DashboardPage
from study_python.gui.pages.gantt_page import GanttPage
from study_python.gui.pages.goal_page import GoalPage
from study_python.gui.pages.stats_page import StatsPage
from study_python.gui.theme.theme_manager import ThemeManager, ThemeType
from study_python.gui.widgets.sidebar import Sidebar
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.study_log_repository import StudyLogRepository
from study_python.repositories.task_repository import TaskRepository
from study_python.services.book_service import BookService
from study_python.services.dashboard_layout_service import DashboardLayoutService
from study_python.services.goal_service import GoalService
from study_python.services.study_log_service import StudyLogService
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """MainWindowを初期化する.

        Args:
            data_dir: データ保存先ディレクトリ.
        """
        super().__init__()
        self._data_dir = data_dir or Path("data")
        self._setup_services()
        self._setup_theme()
        self._setup_ui()
        self._apply_theme()

    def _setup_services(self) -> None:
        """サービス層を初期化する."""
        goal_storage = JsonStorage(self._data_dir / "goals.json")
        task_storage = JsonStorage(self._data_dir / "tasks.json")
        study_log_storage = JsonStorage(self._data_dir / "study_logs.json")
        goal_repo = GoalRepository(goal_storage)
        task_repo = TaskRepository(task_storage)
        study_log_repo = StudyLogRepository(study_log_storage)
        self._goal_service = GoalService(goal_repo, task_repo)
        self._task_service = TaskService(task_repo)
        self._study_log_service = StudyLogService(study_log_repo)
        self._layout_service = DashboardLayoutService(self._data_dir / "settings.json")
        book_storage = JsonStorage(self._data_dir / "books.json")
        book_repo = BookRepository(book_storage)
        self._book_service = BookService(book_repo, task_repo)

    def _setup_theme(self) -> None:
        """テーママネージャを初期化する."""
        self._theme_manager = ThemeManager(self._data_dir / "settings.json")

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("Study Planner - \u5b66\u7fd2\u8a08\u753b\u7ba1\u7406")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # 中央ウィジェット
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # サイドバー
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # ページスタック
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # ページ追加
        self._dashboard_page = DashboardPage(
            self._goal_service,
            self._task_service,
            self._study_log_service,
            self._theme_manager,
            self._layout_service,
            book_service=self._book_service,
        )
        self._goal_page = GoalPage(self._goal_service, self._theme_manager)
        self._gantt_page = GanttPage(
            self._goal_service,
            self._task_service,
            self._theme_manager,
            study_log_service=self._study_log_service,
            book_service=self._book_service,
        )
        self._book_page = BookPage(
            self._book_service,
            self._theme_manager,
        )
        self._stats_page = StatsPage(
            self._goal_service,
            self._task_service,
            self._study_log_service,
            self._theme_manager,
        )
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._goal_page)
        self._stack.addWidget(self._gantt_page)
        self._stack.addWidget(self._book_page)
        self._stack.addWidget(self._stats_page)

        # シグナル接続
        self._sidebar.page_changed.connect(self._on_page_changed)
        self._sidebar.theme_button.clicked.connect(self._on_toggle_theme)

        # Goal変更時にダッシュボード、GanttPage、統計ページを更新
        self._goal_page.goals_changed.connect(self._dashboard_page.refresh)
        self._goal_page.goals_changed.connect(self._gantt_page.refresh)
        self._goal_page.goals_changed.connect(self._stats_page.refresh)

    def _on_page_changed(self, index: int) -> None:
        """ページ切替ハンドラ.

        Args:
            index: ページインデックス.
        """
        self._stack.setCurrentIndex(index)
        if index == 0:
            self._dashboard_page.refresh()
        elif index == 2:
            self._gantt_page.refresh()
        elif index == 3:
            self._book_page.refresh()
        elif index == 4:
            self._stats_page.refresh()

    def _on_toggle_theme(self) -> None:
        """テーマ切替ハンドラ."""
        new_theme = self._theme_manager.toggle_theme()
        self._apply_theme()
        self._sidebar.set_theme_indicator(new_theme == ThemeType.DARK)

    def _apply_theme(self) -> None:
        """現在のテーマをアプリケーションに適用する."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        is_dark = self._theme_manager.current_theme == ThemeType.DARK
        self._sidebar.set_theme_indicator(is_dark)
        # ページにもテーマ変更を通知
        self._dashboard_page.on_theme_changed()
        self._goal_page.on_theme_changed()
        self._gantt_page.on_theme_changed()
        self._book_page.on_theme_changed()
        self._stats_page.on_theme_changed()
