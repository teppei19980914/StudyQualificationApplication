"""メインウィンドウ."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect
from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.pages.book_page import BookPage
from study_python.gui.pages.dashboard_page import DashboardPage
from study_python.gui.pages.gantt_page import GanttPage
from study_python.gui.pages.goal_page import GoalPage
from study_python.gui.pages.settings_page import SettingsPage
from study_python.gui.pages.stats_page import StatsPage
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.header_bar import HeaderBar
from study_python.gui.widgets.navigation_drawer import (
    SETTINGS_PAGE_INDEX,
    DrawerOverlay,
    NavigationDrawer,
)
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository
from study_python.repositories.study_log_repository import StudyLogRepository
from study_python.repositories.task_repository import TaskRepository
from study_python.services.book_service import BookService
from study_python.services.dashboard_layout_service import DashboardLayoutService
from study_python.services.goal_service import GoalService
from study_python.services.notification_service import NotificationService
from study_python.services.study_log_service import StudyLogService
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)

# ナビゲーションページのタイトル一覧
_PAGE_TITLES: list[str] = [
    "\u30c0\u30c3\u30b7\u30e5\u30dc\u30fc\u30c9",
    "3W1H \u76ee\u6a19",
    "\u30ac\u30f3\u30c8\u30c1\u30e3\u30fc\u30c8",
    "\u66f8\u7c4d",
    "\u7d71\u8a08",
]


class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """MainWindowを初期化する.

        Args:
            data_dir: データ保存先ディレクトリ.
        """
        super().__init__()
        self._data_dir = data_dir or Path("data")
        self._drawer_anim: QPropertyAnimation | None = None
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
        notification_storage = JsonStorage(self._data_dir / "notifications.json")
        notification_repo = NotificationRepository(notification_storage)
        self._notification_service = NotificationService(
            notification_repo,
            system_notifications_path=self._data_dir / "system_notifications.json",
            settings_path=self._data_dir / "settings.json",
        )
        self._notification_service.load_system_notifications()

    def _setup_theme(self) -> None:
        """テーママネージャを初期化する."""
        self._theme_manager = ThemeManager(self._data_dir / "settings.json")

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("Study Planner - \u5b66\u7fd2\u8a08\u753b\u7ba1\u7406")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # 中央ウィジェット（縦レイアウト）
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ヘッダーバー
        self._header_bar = HeaderBar()
        main_layout.addWidget(self._header_bar)

        # ページスタック
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # ページ追加（index 0-4）
        self._dashboard_page = DashboardPage(
            self._goal_service,
            self._task_service,
            self._study_log_service,
            self._theme_manager,
            self._layout_service,
            book_service=self._book_service,
            notification_service=self._notification_service,
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
            book_service=self._book_service,
            notification_service=self._notification_service,
        )
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._goal_page)
        self._stack.addWidget(self._gantt_page)
        self._stack.addWidget(self._book_page)
        self._stack.addWidget(self._stats_page)

        # 設定ページ（index 5）
        self._settings_page = SettingsPage(
            self._theme_manager,
            notification_service=self._notification_service,
            data_dir=self._data_dir,
        )
        self._stack.addWidget(self._settings_page)

        # ドロワーオーバーレイ（中央ウィジェット上にフロート）
        self._drawer_overlay = DrawerOverlay(central)
        self._drawer_overlay.hide()

        # ナビゲーションドロワー（中央ウィジェット上にフロート）
        self._drawer = NavigationDrawer(central)
        self._drawer.hide()

        # シグナル接続
        self._header_bar.hamburger_clicked.connect(self._toggle_drawer)
        self._drawer.nav_item_clicked.connect(self._on_page_changed)
        self._drawer.settings_clicked.connect(self._on_settings_requested)
        self._drawer_overlay.clicked.connect(self._close_drawer)
        self._settings_page.theme_changed.connect(self._apply_theme)

        # Goal変更時にダッシュボード、GanttPage、統計ページを更新
        self._goal_page.goals_changed.connect(self._dashboard_page.refresh)
        self._goal_page.goals_changed.connect(self._gantt_page.refresh)
        self._goal_page.goals_changed.connect(self._stats_page.refresh)

    def _toggle_drawer(self) -> None:
        """ドロワーの開閉を切り替える."""
        if self._drawer.isVisible():
            self._close_drawer()
        else:
            self._open_drawer()

    def _open_drawer(self) -> None:
        """ドロワーを開く."""
        header_h = self._header_bar.height()
        central_h = self.centralWidget().height()
        content_h = central_h - header_h

        # オーバーレイをスタック領域に配置
        self._drawer_overlay.setGeometry(
            0, header_h, self.centralWidget().width(), content_h
        )
        self._drawer_overlay.show()
        self._drawer_overlay.raise_()

        # ドロワーの目標位置
        drawer_rect = QRect(0, header_h, NavigationDrawer.DRAWER_WIDTH, content_h)

        self._drawer.setGeometry(drawer_rect)
        self._drawer.show()
        self._drawer.raise_()

        # スライドインアニメーション
        start_rect = QRect(drawer_rect)
        start_rect.moveLeft(-NavigationDrawer.DRAWER_WIDTH)
        self._drawer_anim = QPropertyAnimation(self._drawer, b"geometry")
        self._drawer_anim.setDuration(200)
        self._drawer_anim.setStartValue(start_rect)
        self._drawer_anim.setEndValue(drawer_rect)
        self._drawer_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._drawer_anim.start()

    def _close_drawer(self) -> None:
        """ドロワーを閉じる."""
        if not self._drawer.isVisible():
            return
        self._drawer_overlay.hide()

        # スライドアウトアニメーション
        current = self._drawer.geometry()
        end_rect = QRect(current)
        end_rect.moveLeft(-NavigationDrawer.DRAWER_WIDTH)
        self._drawer_anim = QPropertyAnimation(self._drawer, b"geometry")
        self._drawer_anim.setDuration(150)
        self._drawer_anim.setStartValue(current)
        self._drawer_anim.setEndValue(end_rect)
        self._drawer_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._drawer_anim.finished.connect(self._drawer.hide)
        self._drawer_anim.start()

    def _on_page_changed(self, index: int) -> None:
        """ページ切替ハンドラ.

        Args:
            index: ページインデックス.
        """
        self._close_drawer()
        self._stack.setCurrentIndex(index)
        if index < len(_PAGE_TITLES):
            self._header_bar.set_title(_PAGE_TITLES[index])
        self._drawer.set_checked_button(index)

        if index == 0:
            self._dashboard_page.refresh()
        elif index == 2:
            self._gantt_page.refresh()
        elif index == 3:
            self._book_page.refresh()
        elif index == 4:
            self._stats_page.refresh()

    def _on_settings_requested(self) -> None:
        """設定ページ表示ハンドラ."""
        self._close_drawer()
        self._stack.setCurrentIndex(SETTINGS_PAGE_INDEX)
        self._header_bar.set_title("\u8a2d\u5b9a")
        self._drawer.set_checked_button(SETTINGS_PAGE_INDEX)

    def _apply_theme(self) -> None:
        """現在のテーマをアプリケーションに適用する."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        self._dashboard_page.on_theme_changed()
        self._goal_page.on_theme_changed()
        self._gantt_page.on_theme_changed()
        self._book_page.on_theme_changed()
        self._stats_page.on_theme_changed()
        self._settings_page.on_theme_changed()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """リサイズ時にオーバーレイ・ドロワーのサイズを追従させる.

        Args:
            event: リサイズイベント.
        """
        super().resizeEvent(event)
        if self._drawer.isVisible():
            header_h = self._header_bar.height()
            central_h = self.centralWidget().height()
            content_h = central_h - header_h
            self._drawer_overlay.setGeometry(
                0, header_h, self.centralWidget().width(), content_h
            )
            self._drawer.setGeometry(
                0, header_h, NavigationDrawer.DRAWER_WIDTH, content_h
            )
