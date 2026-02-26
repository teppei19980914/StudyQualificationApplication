"""ガントチャートページ."""

from __future__ import annotations

import logging
from datetime import date

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.dialogs.study_log_dialog import StudyLogDialog
from study_python.gui.dialogs.task_dialog import TaskDialog
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.gantt_chart import GanttChart
from study_python.gui.widgets.study_timer import StudyTimerWidget
from study_python.models.task import TaskStatus
from study_python.services.book_service import BookService
from study_python.services.goal_service import GoalService
from study_python.services.study_log_service import StudyLogService
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)


class GanttPage(QWidget):
    """ガントチャートページ."""

    def __init__(
        self,
        goal_service: GoalService,
        task_service: TaskService,
        theme_manager: ThemeManager,
        study_log_service: StudyLogService | None = None,
        book_service: BookService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """GanttPageを初期化する.

        Args:
            goal_service: GoalService.
            task_service: TaskService.
            theme_manager: テーママネージャ.
            study_log_service: 学習ログサービス.
            book_service: 書籍サービス.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal_service = goal_service
        self._task_service = task_service
        self._theme_manager = theme_manager
        self._study_log_service = study_log_service
        self._book_service = book_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ヘッダー
        header_layout = QHBoxLayout()
        title = QLabel("ガントチャート")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Goal選択コンボ
        goal_label = QLabel("目標:")
        goal_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        header_layout.addWidget(goal_label)

        self._goal_combo = QComboBox()
        self._goal_combo.setMinimumWidth(250)
        self._goal_combo.currentIndexChanged.connect(self._on_goal_changed)
        header_layout.addWidget(self._goal_combo)

        # タスク追加ボタン
        self._add_task_btn = QPushButton("+ タスク追加")
        self._add_task_btn.setFixedHeight(40)
        self._add_task_btn.clicked.connect(self._on_add_task)
        header_layout.addWidget(self._add_task_btn)

        # 学習記録ボタン
        self._record_btn = QPushButton("\U0001f4dd \u5b66\u7fd2\u8a18\u9332")
        self._record_btn.setFixedHeight(40)
        self._record_btn.clicked.connect(self._on_record_study)
        header_layout.addWidget(self._record_btn)

        layout.addLayout(header_layout)

        # タイマー
        self._timer_widget = StudyTimerWidget()
        self._timer_widget.timer_stopped.connect(self._on_timer_stopped)
        layout.addWidget(self._timer_widget)

        # 説明テキスト
        desc = QLabel(
            "学習計画をタスクに分解し、ガントチャートで進捗を管理しましょう。"
            "バーをクリックするとタスクを編集・タイマー計測できます。"
        )
        desc.setObjectName("muted_text")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ガントチャート
        self._gantt_chart = GanttChart(self._theme_manager)
        self._gantt_chart.bar_clicked.connect(self._on_bar_clicked)
        layout.addWidget(self._gantt_chart, 1)

    def refresh(self) -> None:
        """ページを更新する."""
        self._refresh_goal_combo()
        self._refresh_chart()

    def _refresh_goal_combo(self) -> None:
        """Goal選択コンボを更新する."""
        current_id = self._goal_combo.currentData()
        self._goal_combo.blockSignals(True)
        self._goal_combo.clear()

        goals = self._goal_service.get_all_goals()
        if not goals:
            self._goal_combo.addItem("目標が登録されていません", "")
            self._add_task_btn.setEnabled(False)
        else:
            self._add_task_btn.setEnabled(True)
            for goal in goals:
                self._goal_combo.addItem(f"{goal.what}", goal.id)

            # 以前の選択を復元
            if current_id:
                for i in range(self._goal_combo.count()):
                    if self._goal_combo.itemData(i) == current_id:
                        self._goal_combo.setCurrentIndex(i)
                        break

        self._goal_combo.blockSignals(False)

    def _refresh_chart(self) -> None:
        """ガントチャートを更新する."""
        goal_id = self._goal_combo.currentData()
        if not goal_id:
            self._gantt_chart.display_tasks([])
            return

        goal = self._goal_service.get_goal(goal_id)
        if goal is None:
            self._gantt_chart.display_tasks([])
            return

        tasks = self._task_service.get_tasks_for_goal(goal_id)
        self._gantt_chart.display_tasks(tasks, goal.color)

    def _on_goal_changed(self, _index: int) -> None:
        """Goal選択変更ハンドラ.

        Args:
            index: 選択インデックス.
        """
        self._refresh_chart()

    def _on_add_task(self) -> None:
        """タスク追加ハンドラ."""
        goal_id = self._goal_combo.currentData()
        if not goal_id:
            QMessageBox.information(self, "情報", "まず目標を登録してください。")
            return

        books = self._book_service.get_all_books() if self._book_service else []
        dialog = TaskDialog(self, goal_id=goal_id, books=books)
        if dialog.exec() == TaskDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._task_service.create_task(
                    goal_id=goal_id,
                    title=str(values["title"]),
                    start_date=date.fromisoformat(str(values["start_date"])),
                    end_date=date.fromisoformat(str(values["end_date"])),
                    memo=str(values.get("memo", "")),
                    book_id=str(values.get("book_id", "")),
                )
                self._refresh_chart()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_bar_clicked(self, task_id: str) -> None:
        """バークリックハンドラ.

        Args:
            task_id: クリックされたTask ID.
        """
        tasks = self._task_service.get_tasks_for_goal(
            self._goal_combo.currentData() or ""
        )
        task = None
        for t in tasks:
            if t.id == task_id:
                task = t
                break
        if task is None:
            return

        # タイマーの対象タスクを設定
        self._timer_widget.set_task(task.id, task.title)

        books = self._book_service.get_all_books() if self._book_service else []
        dialog = TaskDialog(self, task=task, books=books)
        if dialog.exec() == TaskDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._task_service.update_task(
                    task_id=task_id,
                    title=str(values["title"]),
                    start_date=date.fromisoformat(str(values["start_date"])),
                    end_date=date.fromisoformat(str(values["end_date"])),
                    status=TaskStatus(str(values["status"])),
                    progress=int(values["progress"]),
                    memo=str(values.get("memo", "")),
                    book_id=str(values.get("book_id", "")),
                )
                self._refresh_chart()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_record_study(self) -> None:
        """学習記録ボタンハンドラ."""
        goal_id = self._goal_combo.currentData()
        if not goal_id:
            QMessageBox.information(self, "情報", "まず目標を登録してください。")
            return

        tasks = self._task_service.get_tasks_for_goal(goal_id)
        if not tasks:
            QMessageBox.information(self, "情報", "まずタスクを追加してください。")
            return

        preselected = self._timer_widget.current_task_id or None
        dialog = StudyLogDialog(
            tasks=tasks, parent=self, preselected_task_id=preselected
        )
        if dialog.exec() == StudyLogDialog.DialogCode.Accepted:
            values = dialog.get_values()
            if self._study_log_service:
                try:
                    self._study_log_service.add_study_log(
                        task_id=str(values["task_id"]),
                        study_date=date.fromisoformat(str(values["study_date"])),
                        duration_minutes=int(values["duration_minutes"]),
                        memo=str(values.get("memo", "")),
                    )
                    logger.info("Study log recorded via dialog")
                except ValueError as e:
                    QMessageBox.warning(self, "エラー", str(e))

    def _on_timer_stopped(self, task_id: str, duration_minutes: int) -> None:
        """タイマー停止ハンドラ.

        Args:
            task_id: タスクID.
            duration_minutes: 経過分数.
        """
        if self._study_log_service:
            try:
                self._study_log_service.add_study_log(
                    task_id=task_id,
                    study_date=date.today(),
                    duration_minutes=duration_minutes,
                    memo="タイマー計測",
                )
                logger.info(
                    f"Study log recorded via timer: {duration_minutes}min for {task_id}"
                )
            except ValueError as e:
                logger.error(f"Failed to record timer study log: {e}")

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self._refresh_chart()
