"""カスタマイズ可能ダッシュボードページ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.pages.stats_page import SummaryCard
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.bookshelf_widget import BookshelfWidget
from study_python.gui.widgets.daily_activity_chart import DailyActivityChart
from study_python.gui.widgets.dashboard_widget_frame import (
    DRAG_MIME_TYPE,
    DashboardWidgetFrame,
)
from study_python.gui.widgets.milestone_section import MilestoneSection
from study_python.gui.widgets.today_study_banner import TodayStudyBanner
from study_python.gui.widgets.weekly_comparison_card import WeeklyComparisonCard
from study_python.services.book_service import BookService
from study_python.services.dashboard_layout_service import (
    DashboardLayoutService,
    DashboardWidgetConfig,
)
from study_python.services.goal_service import GoalService
from study_python.services.motivation_calculator import MotivationCalculator
from study_python.services.study_log_service import StudyLogService
from study_python.services.study_stats_calculator import StudyStatsCalculator
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)


class DashboardGridContainer(QWidget):
    """ダッシュボードのグリッドコンテナ.

    ドラッグ&ドロップを受け付ける。

    Attributes:
        _dashboard_page: 親ダッシュボードページ.
    """

    def __init__(
        self, dashboard_page: DashboardPage, parent: QWidget | None = None
    ) -> None:
        """DashboardGridContainerを初期化する.

        Args:
            dashboard_page: 親ダッシュボードページ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._dashboard_page = dashboard_page
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]  # pragma: no cover
        """ドラッグ入場イベント.

        Args:
            event: ドラッグイベント.
        """
        if event.mimeData().hasFormat(DRAG_MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]  # pragma: no cover
        """ドラッグ移動イベント.

        Args:
            event: ドラッグイベント.
        """
        if event.mimeData().hasFormat(DRAG_MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]  # pragma: no cover
        """ドロップイベント.

        Args:
            event: ドロップイベント.
        """
        if event.mimeData().hasFormat(DRAG_MIME_TYPE):
            from_index = int(
                bytes(event.mimeData().data(DRAG_MIME_TYPE)).decode("utf-8")
            )
            to_index = self._dashboard_page._calculate_drop_index(
                event.position().toPoint()
            )
            self._dashboard_page._on_drop(from_index, to_index)
            event.acceptProposedAction()


class DashboardPage(QWidget):
    """カスタマイズ可能なダッシュボードページ.

    ユーザーが自由にウィジェットを配置・並べ替えできる。

    Attributes:
        _goal_service: GoalService.
        _task_service: TaskService.
        _study_log_service: StudyLogService.
        _theme_manager: テーママネージャ.
        _layout_service: レイアウトサービス.
        _edit_mode: 編集モードかどうか.
        _current_layout: 現在のレイアウト設定.
        _widget_frames: 現在のウィジェットフレームのリスト.
        _active_widgets: ウィジェットタイプ→ウィジェットインスタンスのマップ.
    """

    def __init__(
        self,
        goal_service: GoalService,
        task_service: TaskService,
        study_log_service: StudyLogService,
        theme_manager: ThemeManager,
        layout_service: DashboardLayoutService,
        book_service: BookService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """DashboardPageを初期化する.

        Args:
            goal_service: GoalService.
            task_service: TaskService.
            study_log_service: StudyLogService.
            theme_manager: テーママネージャ.
            layout_service: レイアウトサービス.
            book_service: 書籍サービス.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal_service = goal_service
        self._task_service = task_service
        self._study_log_service = study_log_service
        self._theme_manager = theme_manager
        self._layout_service = layout_service
        self._book_service = book_service
        self._edit_mode = False
        self._current_layout: list[DashboardWidgetConfig] = []
        self._widget_frames: list[DashboardWidgetFrame] = []
        self._active_widgets: dict[str, QWidget] = {}
        self._setup_ui()
        self._load_layout()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ヘッダー
        header_layout = QHBoxLayout()

        title = QLabel("\u30c0\u30c3\u30b7\u30e5\u30dc\u30fc\u30c9")
        title.setObjectName("section_title")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._edit_button = QPushButton("\u270f\ufe0f \u7de8\u96c6")
        self._edit_button.setObjectName("secondary_button")
        self._edit_button.setFixedHeight(36)
        self._edit_button.clicked.connect(self._toggle_edit_mode)
        header_layout.addWidget(self._edit_button)

        layout.addLayout(header_layout)

        desc = QLabel(
            "\u81ea\u5206\u306b\u5408\u308f\u305b\u305f\u5b66\u7fd2\u72b6\u6cc1\u3092"
            "\u4e00\u76ee\u3067\u78ba\u8a8d\u3067\u304d\u307e\u3059\u3002"
        )
        desc.setObjectName("muted_text")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._grid_container = DashboardGridContainer(self)
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        # 2カラムグリッドの幅を均等に
        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(1, 1)

        scroll.setWidget(self._grid_container)
        layout.addWidget(scroll, 1)

        # ウィジェット追加ボタン（編集モード時のみ表示）
        self._add_widget_button = QPushButton(
            "\uff0b \u30a6\u30a3\u30b8\u30a7\u30c3\u30c8\u3092\u8ffd\u52a0"
        )
        self._add_widget_button.setObjectName("secondary_button")
        self._add_widget_button.setFixedHeight(40)
        self._add_widget_button.clicked.connect(self._on_add_widget)
        self._add_widget_button.setVisible(False)
        layout.addWidget(self._add_widget_button)

    def _load_layout(self) -> None:
        """レイアウト設定を読み込んでグリッドを構築する."""
        self._current_layout = self._layout_service.get_layout()
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        """グリッドレイアウトを再構築する."""
        # 既存ウィジェットをグリッドから除去
        for frame in self._widget_frames:
            self._grid_layout.removeWidget(frame)
            frame.deleteLater()
        self._widget_frames.clear()
        self._active_widgets.clear()

        # レイアウトに従ってウィジェットを配置
        row = 0
        col = 0

        for i, config in enumerate(self._current_layout):
            widget = self._create_widget(config.widget_type)
            if widget is None:
                continue

            meta = DashboardLayoutService.WIDGET_REGISTRY.get(config.widget_type)
            display_name = meta.display_name if meta else config.widget_type
            resizable = meta is not None and len(meta.allowed_spans) > 1

            frame = DashboardWidgetFrame(
                content_widget=widget,
                widget_index=i,
                display_name=display_name,
                theme_manager=self._theme_manager,
                resizable=resizable,
            )
            frame.set_edit_mode(self._edit_mode)
            frame.remove_requested.connect(self._on_widget_removed)
            frame.resize_requested.connect(self._on_widget_resized)

            self._widget_frames.append(frame)
            self._active_widgets[config.widget_type] = widget

            # グリッド配置
            span = config.column_span
            if span == 2:
                if col != 0:
                    row += 1
                    col = 0
                self._grid_layout.addWidget(frame, row, 0, 1, 2)
                row += 1
                col = 0
            else:
                self._grid_layout.addWidget(frame, row, col, 1, 1)
                col += 1
                if col >= 2:
                    row += 1
                    col = 0

        logger.debug(f"Dashboard grid rebuilt: {len(self._widget_frames)} widgets")

    def _create_widget(self, widget_type: str) -> QWidget | None:
        """ウィジェットタイプに応じたインスタンスを生成する.

        Args:
            widget_type: ウィジェットタイプ.

        Returns:
            生成されたウィジェット。不明なタイプの場合はNone.
        """
        factories: dict[str, callable] = {
            "today_banner": lambda: TodayStudyBanner(self._theme_manager),
            "total_time_card": lambda: SummaryCard(
                "\u23f1\ufe0f", "0h", "\u5408\u8a08\u5b66\u7fd2\u6642\u9593"
            ),
            "study_days_card": lambda: SummaryCard(
                "\U0001f4c5", "0\u65e5", "\u5b66\u7fd2\u65e5\u6570"
            ),
            "goal_count_card": lambda: SummaryCard(
                "\U0001f3af", "0\u500b", "\u76ee\u6a19\u6570"
            ),
            "streak_card": lambda: SummaryCard(
                "\U0001f525", "0\u65e5", "\u9023\u7d9a\u5b66\u7fd2"
            ),
            "weekly_comparison": lambda: WeeklyComparisonCard(self._theme_manager),
            "milestone": lambda: MilestoneSection(self._theme_manager),
            "bookshelf": lambda: BookshelfWidget(self._theme_manager),
            "daily_chart": lambda: DailyActivityChart(self._theme_manager),
        }
        factory = factories.get(widget_type)
        if factory is None:
            logger.warning(f"Unknown widget type: {widget_type}")
            return None
        return factory()

    def refresh(self) -> None:
        """ページのデータを更新する."""
        all_logs = self._study_log_service.get_all_logs()
        goals = self._goal_service.get_all_goals()
        motivation = MotivationCalculator()

        # 各ウィジェットにデータ設定
        today_banner = self._active_widgets.get("today_banner")
        if today_banner is not None:
            today_data = motivation.calculate_today_study(all_logs)
            today_banner.set_data(today_data)  # type: ignore[union-attr]

        streak_card = self._active_widgets.get("streak_card")
        streak_data = motivation.calculate_streak(all_logs)
        if streak_card is not None:
            streak_card.set_value(  # type: ignore[union-attr]
                f"{streak_data.current_streak}\u65e5"
            )

        total_time_card = self._active_widgets.get("total_time_card")
        if total_time_card is not None:
            total_minutes = sum(log.duration_minutes for log in all_logs)
            hours = total_minutes // 60
            mins = total_minutes % 60
            time_text = f"{hours}h {mins:02d}min" if hours > 0 else f"{mins}min"
            total_time_card.set_value(time_text)  # type: ignore[union-attr]

        study_days_card = self._active_widgets.get("study_days_card")
        if study_days_card is not None:
            unique_days = len({log.study_date for log in all_logs})
            study_days_card.set_value(  # type: ignore[union-attr]
                f"{unique_days}\u65e5"
            )

        goal_count_card = self._active_widgets.get("goal_count_card")
        if goal_count_card is not None:
            goal_count_card.set_value(  # type: ignore[union-attr]
                f"{len(goals)}\u500b"
            )

        weekly_card = self._active_widgets.get("weekly_comparison")
        if weekly_card is not None:
            weekly_data = motivation.calculate_weekly_comparison(all_logs)
            weekly_card.set_data(weekly_data)  # type: ignore[union-attr]

        milestone_section = self._active_widgets.get("milestone")
        if milestone_section is not None:
            milestone_data = motivation.calculate_milestones(
                all_logs, streak_data.current_streak
            )
            milestone_section.set_data(milestone_data)  # type: ignore[union-attr]

        bookshelf = self._active_widgets.get("bookshelf")
        if bookshelf is not None and self._book_service is not None:
            bookshelf_data = self._book_service.get_bookshelf_data()
            bookshelf.set_data(bookshelf_data)  # type: ignore[union-attr]

        daily_chart = self._active_widgets.get("daily_chart")
        if daily_chart is not None:
            calculator = StudyStatsCalculator()
            activity_data = calculator.calculate_daily_activity(all_logs)
            daily_chart.set_data(activity_data)  # type: ignore[union-attr]

        logger.debug("Dashboard refreshed")

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self._rebuild_grid()
        self.refresh()

    def _toggle_edit_mode(self) -> None:
        """編集モードを切り替える."""
        self._edit_mode = not self._edit_mode

        if self._edit_mode:
            self._edit_button.setText("\u2713 \u5b8c\u4e86")
        else:
            self._edit_button.setText("\u270f\ufe0f \u7de8\u96c6")
            self._layout_service.save_layout(self._current_layout)

        self._add_widget_button.setVisible(self._edit_mode)

        for frame in self._widget_frames:
            frame.set_edit_mode(self._edit_mode)

        logger.debug(f"Dashboard edit mode: {self._edit_mode}")

    def _on_widget_removed(self, index: int) -> None:
        """ウィジェット削除ハンドラ.

        Args:
            index: 削除するウィジェットのインデックス.
        """
        self._current_layout = self._layout_service.remove_widget(
            self._current_layout, index
        )
        self._rebuild_grid()
        self.refresh()

    def _on_widget_resized(self, index: int) -> None:
        """ウィジェットリサイズハンドラ.

        Args:
            index: リサイズするウィジェットのインデックス.
        """
        self._current_layout = self._layout_service.resize_widget(
            self._current_layout, index
        )
        self._rebuild_grid()
        self.refresh()

    def _on_add_widget(self) -> None:  # pragma: no cover
        """ウィジェット追加ボタンハンドラ."""
        available = self._layout_service.get_available_widgets(self._current_layout)
        if not available:
            return

        menu = QMenu(self)
        for meta in available:
            action = menu.addAction(f"{meta.icon} {meta.display_name}")
            action.setData(meta.widget_type)

        chosen = menu.exec(
            self._add_widget_button.mapToGlobal(
                self._add_widget_button.rect().topLeft()
            )
        )
        if chosen is not None:
            widget_type = chosen.data()
            self._current_layout = self._layout_service.add_widget(
                self._current_layout, widget_type
            )
            self._rebuild_grid()
            self.refresh()

    def _on_drop(self, from_index: int, to_index: int) -> None:
        """ドロップハンドラ.

        Args:
            from_index: 移動元インデックス.
            to_index: 移動先インデックス.
        """
        if from_index == to_index:
            return
        self._current_layout = self._layout_service.reorder(
            self._current_layout, from_index, to_index
        )
        self._rebuild_grid()
        self.refresh()

    def _calculate_drop_index(self, pos) -> int:
        """ドロップ位置からウィジェットインデックスを計算する.

        Args:
            pos: ドロップ位置（コンテナ座標）.

        Returns:
            ドロップ先インデックス.
        """
        for i, frame in enumerate(self._widget_frames):
            frame_rect = frame.geometry()
            if pos.y() < frame_rect.center().y():
                return i
        return len(self._widget_frames) - 1
