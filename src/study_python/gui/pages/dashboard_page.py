"""カスタマイズ可能ダッシュボードページ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.pages.stats_page import SummaryCard
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.activity_chart_section import ActivityChartSection
from study_python.gui.widgets.bookshelf_widget import BookshelfWidget
from study_python.gui.widgets.consistency_card import ConsistencyCard
from study_python.gui.widgets.dashboard_widget_frame import (
    DRAG_MIME_TYPE,
    PALETTE_DRAG_MIME_TYPE,
    DashboardWidgetFrame,
)
from study_python.gui.widgets.milestone_button import MilestoneButton
from study_python.gui.widgets.notification_button import NotificationButton
from study_python.gui.widgets.personal_record_card import PersonalRecordCard
from study_python.gui.widgets.today_study_banner import TodayStudyBanner
from study_python.gui.widgets.widget_palette_panel import WidgetPalettePanel
from study_python.services.book_service import BookService
from study_python.services.dashboard_layout_service import (
    DashboardLayoutService,
    DashboardWidgetConfig,
)
from study_python.services.goal_service import GoalService
from study_python.services.motivation_calculator import MotivationCalculator
from study_python.services.notification_service import NotificationService
from study_python.services.study_log_service import StudyLogService
from study_python.services.study_stats_calculator import (
    ActivityPeriodType,
    StudyStatsCalculator,
)
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
        if event.mimeData().hasFormat(DRAG_MIME_TYPE) or event.mimeData().hasFormat(
            PALETTE_DRAG_MIME_TYPE
        ):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]  # pragma: no cover
        """ドラッグ移動イベント.

        Args:
            event: ドラッグイベント.
        """
        if event.mimeData().hasFormat(DRAG_MIME_TYPE) or event.mimeData().hasFormat(
            PALETTE_DRAG_MIME_TYPE
        ):
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
        elif event.mimeData().hasFormat(PALETTE_DRAG_MIME_TYPE):
            widget_type = bytes(event.mimeData().data(PALETTE_DRAG_MIME_TYPE)).decode(
                "utf-8"
            )
            to_index = self._dashboard_page._calculate_drop_index(
                event.position().toPoint()
            )
            self._dashboard_page._on_palette_drop(widget_type, to_index)
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
        notification_service: NotificationService | None = None,
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
            notification_service: 通知サービス.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal_service = goal_service
        self._task_service = task_service
        self._study_log_service = study_log_service
        self._theme_manager = theme_manager
        self._layout_service = layout_service
        self._book_service = book_service
        self._notification_service = notification_service
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

        self._milestone_button = MilestoneButton(self._theme_manager)
        header_layout.addWidget(self._milestone_button)

        self._notification_button = NotificationButton(
            self._theme_manager, self._notification_service
        )
        header_layout.addWidget(self._notification_button)

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
        self._grid_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        # 2カラムグリッドの幅を均等に
        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(1, 1)

        scroll.setWidget(self._grid_container)

        # ボディ（スクロールエリア + パレットパネル）
        body_layout = QHBoxLayout()
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(scroll, 1)

        self._palette_panel = WidgetPalettePanel(self._theme_manager)
        self._palette_panel.setVisible(False)
        body_layout.addWidget(self._palette_panel)

        layout.addLayout(body_layout, 1)

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
            "personal_record": lambda: PersonalRecordCard(self._theme_manager),
            "consistency": lambda: ConsistencyCard(self._theme_manager),
            "bookshelf": lambda: BookshelfWidget(self._theme_manager),
            "daily_chart": lambda: ActivityChartSection(self._theme_manager),
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

        personal_record = self._active_widgets.get("personal_record")
        if personal_record is not None:
            record_data = motivation.calculate_personal_records(all_logs)
            personal_record.set_data(record_data)  # type: ignore[union-attr]

        consistency_card = self._active_widgets.get("consistency")
        if consistency_card is not None:
            consistency_data = motivation.calculate_consistency(all_logs)
            consistency_card.set_data(consistency_data)  # type: ignore[union-attr]

        milestone_data = motivation.calculate_milestones(
            all_logs, streak_data.current_streak
        )
        self._milestone_button.set_data(milestone_data)

        if self._notification_service is not None:
            self._notification_service.check_and_create_achievement_notifications(
                milestone_data
            )
            unread = self._notification_service.get_unread_count()
            self._notification_button.update_badge(unread)

        bookshelf = self._active_widgets.get("bookshelf")
        if bookshelf is not None and self._book_service is not None:
            bookshelf_data = self._book_service.get_bookshelf_data()
            bookshelf.set_data(bookshelf_data)  # type: ignore[union-attr]

        chart_section = self._active_widgets.get("daily_chart")
        if chart_section is not None:
            calculator = StudyStatsCalculator()
            all_chart_data = {
                pt: calculator.calculate_activity(all_logs, pt)
                for pt in ActivityPeriodType
            }
            chart_section.set_all_data(all_chart_data)  # type: ignore[union-attr]

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

        self._palette_panel.setVisible(self._edit_mode)
        if self._edit_mode:
            self._refresh_palette()

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
        if self._edit_mode:
            self._refresh_palette()
            for frame in self._widget_frames:
                frame.set_edit_mode(True)

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

    def _refresh_palette(self) -> None:
        """パレットパネルのアイテムを更新する."""
        available = self._layout_service.get_available_widgets(self._current_layout)
        self._palette_panel.update_items(available)

    def _on_palette_drop(self, widget_type: str, to_index: int) -> None:
        """パレットからのドロップハンドラ.

        Args:
            widget_type: 追加するウィジェットタイプ.
            to_index: 挿入先インデックス.
        """
        self._current_layout = self._layout_service.add_widget(
            self._current_layout, widget_type
        )
        # add_widgetは末尾に追加するので、to_indexに移動
        from_index = len(self._current_layout) - 1
        if from_index != to_index and from_index > 0:
            self._current_layout = self._layout_service.reorder(
                self._current_layout, from_index, to_index
            )
        self._rebuild_grid()
        self.refresh()
        if self._edit_mode:
            self._refresh_palette()
            for frame in self._widget_frames:
                frame.set_edit_mode(True)

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
