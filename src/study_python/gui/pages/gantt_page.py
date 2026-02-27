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

from study_python.gui.dialogs.task_dialog import TaskDialog
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.gantt_chart import GanttChart
from study_python.models.task import BOOK_GANTT_GOAL_ID, Task
from study_python.services.book_gantt_service import (
    BOOK_GANTT_COLOR,
    BookGanttService,
)
from study_python.services.book_service import BookService
from study_python.services.goal_service import GoalService
from study_python.services.study_log_service import StudyLogService
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)

_ALL_TASKS_KEY = "__all_tasks__"
_ALL_BOOKS_KEY = "__all_books__"


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
        self._book_gantt_service: BookGanttService | None = None
        if book_service:
            self._book_gantt_service = BookGanttService(book_service, task_service)
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

        # セレクタラベル
        self._selector_label = QLabel("表示:")
        self._selector_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        header_layout.addWidget(self._selector_label)

        # セレクタコンボ（常時統合：目標+書籍すべて表示）
        self._selector_combo = QComboBox()
        self._selector_combo.setMinimumWidth(250)
        self._selector_combo.currentIndexChanged.connect(self._on_selector_changed)
        header_layout.addWidget(self._selector_combo)

        # タスク追加ボタン
        self._add_task_btn = QPushButton("+ タスク追加")
        self._add_task_btn.setFixedHeight(40)
        self._add_task_btn.clicked.connect(self._on_add_task)
        header_layout.addWidget(self._add_task_btn)

        layout.addLayout(header_layout)

        # 説明テキスト
        desc = QLabel(
            "学習計画をタスクに分解し、ガントチャートで進捗を管理しましょう。"
            "バーをクリックするとタスクを編集できます。"
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
        self._refresh_selector()
        self._refresh_chart()

    def _refresh_selector(self) -> None:
        """セレクタコンボを更新する."""
        current_data = self._selector_combo.currentData()
        self._selector_combo.blockSignals(True)
        self._selector_combo.clear()

        goals = self._goal_service.get_all_goals()
        books = self._book_service.get_all_books() if self._book_service else []

        if not goals and not books:
            self._selector_combo.addItem("目標または書籍を登録してください", "")
            self._add_task_btn.setEnabled(False)
        else:
            self._add_task_btn.setEnabled(True)
            # すべてのタスク（目標+書籍）
            self._selector_combo.addItem("\U0001f4cb すべてのタスク", _ALL_TASKS_KEY)
            # 各目標
            for goal in goals:
                self._selector_combo.addItem(f"{goal.what}", goal.id)
            # 書籍セクション
            if self._book_gantt_service and books:
                self._selector_combo.addItem("\U0001f4da すべての書籍", _ALL_BOOKS_KEY)
                for book in books:
                    self._selector_combo.addItem(f"{book.title}", book.id)

        # 以前の選択を復元
        if current_data:
            for i in range(self._selector_combo.count()):
                if self._selector_combo.itemData(i) == current_data:
                    self._selector_combo.setCurrentIndex(i)
                    break

        self._selector_combo.blockSignals(False)

    def _refresh_chart(self) -> None:
        """ガントチャートを更新する."""
        selected = self._selector_combo.currentData()
        if not selected:
            self._gantt_chart.display_tasks([])
            return

        if selected == _ALL_TASKS_KEY:
            self._refresh_all_tasks_chart()
            return

        if selected == _ALL_BOOKS_KEY:
            if self._book_gantt_service:
                tasks = self._book_gantt_service.get_all_book_tasks()
                self._gantt_chart.display_tasks(tasks, goal_color=BOOK_GANTT_COLOR)
            return

        # 個別の目標かチェック
        goal = self._goal_service.get_goal(selected)
        if goal is not None:
            tasks = self._task_service.get_tasks_for_goal(selected)
            self._gantt_chart.display_tasks(tasks, goal.color)
            return

        # 個別の書籍
        tasks = self._task_service.get_tasks_for_book(selected)
        self._gantt_chart.display_tasks(tasks, goal_color=BOOK_GANTT_COLOR)

    def _refresh_all_tasks_chart(self) -> None:
        """すべてのタスク（目標+書籍）を表示する."""
        goals = self._goal_service.get_all_goals()
        goal_colors: dict[str, str] = {g.id: g.color for g in goals}
        goal_colors[BOOK_GANTT_GOAL_ID] = BOOK_GANTT_COLOR
        tasks = self._task_service.get_all_tasks()
        self._gantt_chart.display_tasks(tasks, goal_colors=goal_colors)

    def _on_selector_changed(self, _index: int) -> None:
        """セレクタ変更ハンドラ.

        Args:
            _index: 選択インデックス.
        """
        self._refresh_chart()

    def _on_add_task(self) -> None:
        """タスク追加ハンドラ.

        書籍機能が有効な場合、目標/読書の選択ダイアログを表示する。
        """
        if not self._book_gantt_service:
            self._on_add_goal_task()
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("タスク追加")
        msg.setText("どちらのタスクを追加しますか？")
        goal_btn = msg.addButton("目標", QMessageBox.ButtonRole.AcceptRole)
        book_btn = msg.addButton("読書", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("キャンセル", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == goal_btn:
            self._on_add_goal_task()
        elif clicked == book_btn:
            self._on_add_book_task()

    def _on_add_goal_task(self) -> None:
        """目標タスク追加ハンドラ."""
        goals = self._goal_service.get_all_goals()
        if not goals:
            QMessageBox.information(self, "情報", "まず目標を登録してください。")
            return

        selected = self._selector_combo.currentData()
        books = self._book_service.get_all_books() if self._book_service else []

        # 個別目標が選択されている場合はその目標にバインド
        goal = self._goal_service.get_goal(selected) if selected else None
        if goal is not None:
            dialog = TaskDialog(self, goal_id=selected, books=books)
        else:
            dialog = TaskDialog(self, books=books, goals=goals)

        if dialog.exec() == TaskDialog.DialogCode.Accepted:
            values = dialog.get_values()
            selected_goal_id = str(values.get("goal_id", selected or ""))
            if not selected_goal_id or selected_goal_id in (
                _ALL_TASKS_KEY,
                _ALL_BOOKS_KEY,
            ):
                return
            try:
                self._task_service.create_task(
                    goal_id=selected_goal_id,
                    title=str(values["title"]),
                    start_date=date.fromisoformat(str(values["start_date"])),
                    end_date=date.fromisoformat(str(values["end_date"])),
                    memo=str(values.get("memo", "")),
                    book_id=str(values.get("book_id", "")),
                )
                self._refresh_chart()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_add_book_task(self) -> None:
        """書籍タスク追加ハンドラ."""
        if not self._book_gantt_service or not self._book_service:
            return
        books = self._book_service.get_all_books()
        if not books:
            QMessageBox.information(self, "情報", "まず書籍を登録してください。")
            return

        dialog = TaskDialog(self, book_task_mode=True, books=books)
        if dialog.exec() == TaskDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._task_service.create_task(
                    goal_id=BOOK_GANTT_GOAL_ID,
                    title=str(values["title"]),
                    start_date=date.fromisoformat(str(values["start_date"])),
                    end_date=date.fromisoformat(str(values["end_date"])),
                    memo=str(values.get("memo", "")),
                    book_id=str(values.get("book_id", "")),
                )
                book_id = str(values.get("book_id", ""))
                if book_id:
                    self._book_gantt_service.sync_book_progress(book_id)
                self._refresh_chart()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_bar_clicked(self, task_id: str) -> None:
        """バークリックハンドラ.

        タスクのgoal_idから目標タスクか書籍タスクかを自動判定する。

        Args:
            task_id: クリックされたTask ID.
        """
        task = self._find_task(task_id)
        if task is None:
            return

        if task.goal_id == BOOK_GANTT_GOAL_ID:
            self._on_book_bar_clicked(task)
        else:
            self._on_goal_bar_clicked(task)

    def _find_task(self, task_id: str) -> Task | None:
        """現在表示中のタスクからIDで検索する.

        Args:
            task_id: 検索するTask ID.

        Returns:
            該当するTask。見つからない場合はNone.
        """
        selected = self._selector_combo.currentData() or ""

        if selected == _ALL_TASKS_KEY:
            tasks = self._task_service.get_all_tasks()
        elif selected == _ALL_BOOKS_KEY:
            tasks = (
                self._book_gantt_service.get_all_book_tasks()
                if self._book_gantt_service
                else []
            )
        else:
            # 個別の目標かチェック
            goal = self._goal_service.get_goal(selected)
            if goal is not None:
                tasks = self._task_service.get_tasks_for_goal(selected)
            else:
                tasks = self._task_service.get_tasks_for_book(selected)

        for t in tasks:
            if t.id == task_id:
                return t
        return None

    def _on_goal_bar_clicked(self, task: Task) -> None:
        """目標タスクのバークリックハンドラ.

        Args:
            task: クリックされたTask.
        """
        books = self._book_service.get_all_books() if self._book_service else []
        dialog = TaskDialog(
            self,
            task=task,
            books=books,
            study_log_service=self._study_log_service,
        )
        result = dialog.exec()

        if dialog.delete_requested:
            self._task_service.delete_task(task.id)
            logger.info(f"Deleted task: {task.title}")
            self._refresh_chart()
        elif result == TaskDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._task_service.update_task(
                    task_id=task.id,
                    title=str(values["title"]),
                    start_date=date.fromisoformat(str(values["start_date"])),
                    end_date=date.fromisoformat(str(values["end_date"])),
                    progress=int(values["progress"]),
                    memo=str(values.get("memo", "")),
                    book_id=str(values.get("book_id", "")),
                )
                self._refresh_chart()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_book_bar_clicked(self, task: Task) -> None:
        """書籍タスクのバークリックハンドラ.

        Args:
            task: クリックされたTask.
        """
        if not self._book_gantt_service or not self._book_service:
            return

        old_book_id = task.book_id
        books = self._book_service.get_all_books()
        dialog = TaskDialog(
            self,
            task=task,
            book_task_mode=True,
            books=books,
            study_log_service=self._study_log_service,
        )
        result = dialog.exec()

        if dialog.delete_requested:
            self._task_service.delete_task(task.id)
            logger.info(f"Deleted book task: {task.title}")
            if old_book_id:
                self._book_gantt_service.sync_book_progress(old_book_id)
            self._refresh_chart()
        elif result == TaskDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._task_service.update_task(
                    task_id=task.id,
                    title=str(values["title"]),
                    start_date=date.fromisoformat(str(values["start_date"])),
                    end_date=date.fromisoformat(str(values["end_date"])),
                    progress=int(values["progress"]),
                    memo=str(values.get("memo", "")),
                    book_id=str(values.get("book_id", "")),
                )
                new_book_id = str(values.get("book_id", ""))
                # 書籍変更時は両方のbookをsync
                if old_book_id and old_book_id != new_book_id:
                    self._book_gantt_service.sync_book_progress(old_book_id)
                if new_book_id:
                    self._book_gantt_service.sync_book_progress(new_book_id)
                self._refresh_chart()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))
        elif dialog.study_logs_changed:
            self._refresh_chart()

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self._refresh_chart()
