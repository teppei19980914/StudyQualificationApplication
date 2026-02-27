"""ガントチャートタスクの登録/編集ダイアログ."""

from __future__ import annotations

from datetime import date as date_type
from functools import partial

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.dialogs.task_study_log_logic import TaskStudyLogLogic
from study_python.gui.widgets.japanese_calendar_widget import create_japanese_date_edit
from study_python.models.book import Book
from study_python.models.goal import Goal
from study_python.models.task import Task, TaskStatus
from study_python.services.study_log_service import StudyLogService


class TaskDialog(QDialog):
    """タスク登録/編集ダイアログ.

    Attributes:
        task: 編集対象のTask（新規作成時はNone）.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        task: Task | None = None,
        goal_id: str = "",
        books: list[Book] | None = None,
        goals: list[Goal] | None = None,
        study_log_service: StudyLogService | None = None,
        book_task_mode: bool = False,
    ) -> None:
        """TaskDialogを初期化する.

        Args:
            parent: 親ウィジェット.
            task: 編集対象のTask.
            goal_id: 新規作成時のGoal ID.
            books: 選択可能な書籍リスト.
            goals: 目標選択用のGoalリスト（複数目標モード時）.
            study_log_service: 学習ログサービス（編集モード時に学習記録セクション表示）.
            book_task_mode: 書籍タスクモード（必須書籍セレクタを表示）.
        """
        super().__init__(parent)
        self.task = task
        self._goal_id = goal_id
        self._books = books or []
        self._goals = goals or []
        self._delete_requested = False
        self._study_log_service = study_log_service
        self._study_log_logic: TaskStudyLogLogic | None = None
        self._study_logs_changed = False
        self._book_task_mode = book_task_mode
        self._setup_ui()
        if task:
            self._populate_from_task(task)

    def _setup_ui(self) -> None:
        """UIを構築する."""
        title = "タスクを編集" if self.task else "新しいタスク"
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header_layout = QHBoxLayout()
        header = QLabel(title)
        header.setObjectName("section_title")
        header_layout.addWidget(header)
        header_layout.addStretch()

        self._timer_label: QLabel | None = None
        self._start_btn: QPushButton | None = None
        self._stop_btn: QPushButton | None = None
        self._display_timer: QTimer | None = None
        if self.task and self._study_log_service:
            self._timer_label = QLabel("00:00:00")
            self._timer_label.setStyleSheet("font-size: 14px; font-family: monospace;")
            header_layout.addWidget(self._timer_label)
            self._start_btn = QPushButton("\u25b6 \u958b\u59cb")
            self._start_btn.clicked.connect(self._on_timer_start)
            header_layout.addWidget(self._start_btn)
            self._stop_btn = QPushButton("\u25a0 \u505c\u6b62")
            self._stop_btn.clicked.connect(self._on_timer_stop)
            self._stop_btn.setEnabled(False)
            header_layout.addWidget(self._stop_btn)
            self._display_timer = QTimer(self)
            self._display_timer.setInterval(1000)
            self._display_timer.timeout.connect(self._update_timer_display)

        layout.addLayout(header_layout)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 書籍セレクタ（book_task_mode時のみ表示）
        self._book_selector: QComboBox | None = None
        if self._book_task_mode:
            self._book_selector = QComboBox()
            for book in self._books:
                self._book_selector.addItem(book.title, book.id)
            form.addRow(self._create_label("書籍"), self._book_selector)

        # 目標選択（複数目標モード時のみ表示、book_task_mode時は非表示）
        self._goal_combo: QComboBox | None = None
        if self._goals and not self._book_task_mode:
            self._goal_combo = QComboBox()
            for goal in self._goals:
                self._goal_combo.addItem(goal.what, goal.id)
            form.addRow(self._create_label("目標"), self._goal_combo)

        # タスク名
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("例: Udemyセクション1-5を完了")
        form.addRow(self._create_label("タスク名"), self._title_input)

        # 開始日
        self._start_date_input = create_japanese_date_edit()
        self._start_date_input.setDate(QDate.currentDate())
        self._start_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("開始日"), self._start_date_input)

        # 終了日
        self._end_date_input = create_japanese_date_edit()
        self._end_date_input.setDate(QDate.currentDate().addDays(14))
        self._end_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("終了日"), self._end_date_input)

        # ステータス（進捗率から自動決定、編集不可）
        self._status_combo = QComboBox()
        self._status_combo.addItem("未着手", TaskStatus.NOT_STARTED.value)
        self._status_combo.addItem("進行中", TaskStatus.IN_PROGRESS.value)
        self._status_combo.addItem("完了", TaskStatus.COMPLETED.value)
        self._status_combo.setEnabled(False)
        form.addRow(self._create_label("ステータス"), self._status_combo)

        # 進捗率
        progress_layout = QHBoxLayout()
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 100)
        self._progress_slider.setValue(0)
        self._progress_slider.setTickInterval(10)
        progress_layout.addWidget(self._progress_slider, 1)

        self._progress_spin = QSpinBox()
        self._progress_spin.setRange(0, 100)
        self._progress_spin.setSuffix("%")
        self._progress_spin.setValue(0)
        self._progress_spin.setFixedWidth(80)
        progress_layout.addWidget(self._progress_spin)

        # スライダーとスピンボックスの同期 + ステータス自動更新
        self._progress_slider.valueChanged.connect(self._progress_spin.setValue)
        self._progress_spin.valueChanged.connect(self._progress_slider.setValue)
        self._progress_spin.valueChanged.connect(self._update_status_from_progress)

        form.addRow(self._create_label("進捗率"), progress_layout)

        # メモ
        self._memo_input = QTextEdit()
        self._memo_input.setPlaceholderText("メモ（任意）")
        self._memo_input.setMaximumHeight(80)
        form.addRow(self._create_label("メモ"), self._memo_input)

        # 関連書籍（book_task_mode時は非表示）
        self._book_combo: QComboBox | None = None
        if not self._book_task_mode:
            self._book_combo = QComboBox()
            self._book_combo.addItem("\u306a\u3057", "")
            for book in self._books:
                self._book_combo.addItem(book.title, book.id)
            form.addRow(
                self._create_label("\u95a2\u9023\u66f8\u7c4d"), self._book_combo
            )

        layout.addLayout(form)

        # 学習記録セクション（編集モード + study_log_service提供時のみ）
        self._study_log_group: QGroupBox | None = None
        self._study_log_table: QTableWidget | None = None
        if self.task and self._study_log_service:
            self._study_log_logic = TaskStudyLogLogic(
                study_log_service=self._study_log_service,
                task_id=self.task.id,
                task_name=self.task.title,
            )
            self._setup_study_log_section(layout)

        # ボタン
        button_layout = QHBoxLayout()

        if self.task:
            delete_btn = QPushButton("\U0001f5d1 削除")
            delete_btn.setObjectName("danger_button")
            delete_btn.clicked.connect(self._on_delete)
            button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setObjectName("secondary_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存" if self.task else "追加")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _create_label(self, text: str) -> QLabel:
        """フォームラベルを作成する.

        Args:
            text: ラベルテキスト.

        Returns:
            QLabelインスタンス.
        """
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; font-size: 13px;")
        return label

    def _update_status_from_progress(self, progress: int) -> None:
        """進捗率からステータスを自動更新する.

        Args:
            progress: 進捗率（0-100）.
        """
        if progress == 0:
            self._status_combo.setCurrentIndex(0)  # 未着手
        elif progress == 100:
            self._status_combo.setCurrentIndex(2)  # 完了
        else:
            self._status_combo.setCurrentIndex(1)  # 進行中

    def _populate_from_task(self, task: Task) -> None:
        """Taskの値をフォームに設定する.

        Args:
            task: 設定するTask.
        """
        self._title_input.setText(task.title)
        self._start_date_input.setDate(
            QDate(task.start_date.year, task.start_date.month, task.start_date.day)
        )
        self._end_date_input.setDate(
            QDate(task.end_date.year, task.end_date.month, task.end_date.day)
        )
        # 進捗率を設定（ステータスは自動更新される）
        self._progress_slider.setValue(task.progress)
        self._memo_input.setPlainText(task.memo)

        # 書籍選択の復元
        if task.book_id:
            if self._book_selector is not None:
                for i in range(self._book_selector.count()):
                    if self._book_selector.itemData(i) == task.book_id:
                        self._book_selector.setCurrentIndex(i)
                        break
            elif self._book_combo is not None:
                for i in range(self._book_combo.count()):
                    if self._book_combo.itemData(i) == task.book_id:
                        self._book_combo.setCurrentIndex(i)
                        break

    def _on_delete(self) -> None:
        """削除ボタンのハンドラ."""
        reply = QMessageBox.question(
            self,
            "確認",
            "このタスクを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_requested = True
            self.reject()

    @property
    def delete_requested(self) -> bool:
        """削除がリクエストされたかどうかを返す."""
        return self._delete_requested

    @property
    def study_logs_changed(self) -> bool:
        """学習ログが変更されたかどうかを返す."""
        return self._study_logs_changed

    def _on_save(self) -> None:
        """保存ボタンのハンドラ."""
        if not self._title_input.text().strip():
            QMessageBox.warning(self, "入力エラー", "タスク名は必須です。")
            return

        start_qdate = self._start_date_input.date()
        end_qdate = self._end_date_input.date()
        if end_qdate < start_qdate:
            QMessageBox.warning(
                self, "入力エラー", "終了日は開始日以降に設定してください。"
            )
            return

        self.accept()

    def get_values(self) -> dict[str, str | int]:
        """フォームの入力値を取得する.

        Returns:
            入力値の辞書.
        """
        start_qdate = self._start_date_input.date()
        end_qdate = self._end_date_input.date()

        # book_id の取得: book_task_modeでは_book_selectorから、通常は_book_comboから
        if self._book_selector is not None:
            book_id = str(self._book_selector.currentData())
        elif self._book_combo is not None:
            book_id = str(self._book_combo.currentData())
        else:
            book_id = ""

        values: dict[str, str | int] = {
            "title": self._title_input.text().strip(),
            "start_date": f"{start_qdate.year():04d}-{start_qdate.month():02d}-{start_qdate.day():02d}",
            "end_date": f"{end_qdate.year():04d}-{end_qdate.month():02d}-{end_qdate.day():02d}",
            "status": str(self._status_combo.currentData()),
            "progress": self._progress_spin.value(),
            "memo": self._memo_input.toPlainText().strip(),
            "book_id": book_id,
        }
        if self._goal_combo is not None:
            values["goal_id"] = str(self._goal_combo.currentData())
        return values

    def _setup_study_log_section(self, layout: QVBoxLayout) -> None:
        """学習記録セクションを構築する.

        Args:
            layout: 親レイアウト.
        """
        assert self._study_log_logic is not None

        self._study_log_group = QGroupBox("学習記録")
        group_layout = QVBoxLayout(self._study_log_group)
        group_layout.setSpacing(8)

        # ログテーブル
        self._study_log_table = QTableWidget()
        self._study_log_table.setColumnCount(4)
        self._study_log_table.setHorizontalHeaderLabels(
            ["日付", "学習時間", "メモ", "操作"]
        )
        self._study_log_table.setMaximumHeight(150)
        self._study_log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._study_log_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._study_log_table.verticalHeader().setVisible(False)
        self._study_log_table.setAlternatingRowColors(True)

        header = self._study_log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        group_layout.addWidget(self._study_log_table)

        add_row1 = QHBoxLayout()
        add_row1.addWidget(QLabel("学習日:"))
        self._log_date_input = create_japanese_date_edit()
        self._log_date_input.setDate(QDate.currentDate())
        self._log_date_input.setDisplayFormat("yyyy/MM/dd")
        add_row1.addWidget(self._log_date_input)

        add_row1.addWidget(QLabel("時間:"))
        self._log_hours_spin = QSpinBox()
        self._log_hours_spin.setRange(0, 23)
        self._log_hours_spin.setSuffix(" 時間")
        self._log_hours_spin.setFixedWidth(100)
        add_row1.addWidget(self._log_hours_spin)

        self._log_minutes_spin = QSpinBox()
        self._log_minutes_spin.setRange(0, 59)
        self._log_minutes_spin.setValue(30)
        self._log_minutes_spin.setSuffix(" 分")
        self._log_minutes_spin.setFixedWidth(100)
        add_row1.addWidget(self._log_minutes_spin)
        add_row1.addStretch()
        group_layout.addLayout(add_row1)

        add_row2 = QHBoxLayout()
        add_row2.addWidget(QLabel("メモ:"))
        self._log_memo_input = QLineEdit()
        self._log_memo_input.setPlaceholderText("メモ（任意）")
        add_row2.addWidget(self._log_memo_input, 1)

        add_btn = QPushButton("+ 記録追加")
        add_btn.clicked.connect(self._on_add_study_log)
        add_row2.addWidget(add_btn)
        group_layout.addLayout(add_row2)

        layout.addWidget(self._study_log_group)
        self._refresh_study_log_table()

    def _refresh_study_log_table(self) -> None:
        """学習ログテーブルを更新する."""
        if self._study_log_logic is None or self._study_log_table is None:
            return

        logs = self._study_log_logic.get_logs()
        self._study_log_table.setRowCount(len(logs))

        for row, entry in enumerate(logs):
            date_item = QTableWidgetItem(entry.study_date.strftime("%Y/%m/%d"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._study_log_table.setItem(row, 0, date_item)

            duration_item = QTableWidgetItem(
                TaskStudyLogLogic.format_duration(entry.duration_minutes)
            )
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._study_log_table.setItem(row, 1, duration_item)

            self._study_log_table.setItem(row, 2, QTableWidgetItem(entry.memo))

            delete_btn = QPushButton("削除")
            delete_btn.setFixedHeight(24)
            delete_btn.clicked.connect(partial(self._on_delete_study_log, entry.log_id))
            self._study_log_table.setCellWidget(row, 3, delete_btn)

        self._update_study_log_stats()

    def _update_study_log_stats(self) -> None:
        """学習記録セクションのタイトルに統計を反映する."""
        if self._study_log_logic is None or self._study_log_group is None:
            return

        stats = self._study_log_logic.get_stats()
        formatted = TaskStudyLogLogic.format_duration(stats.total_minutes)
        self._study_log_group.setTitle(
            f"学習記録 (合計: {formatted} / {stats.study_days}日 / {stats.log_count}件)"
        )

    def _on_add_study_log(self) -> None:
        """学習記録追加ハンドラ."""
        if self._study_log_logic is None:
            return  # pragma: no cover

        hours = self._log_hours_spin.value()
        minutes = self._log_minutes_spin.value()

        try:
            total_minutes = TaskStudyLogLogic.validate_duration(hours, minutes)
        except ValueError as e:
            QMessageBox.warning(self, "入力エラー", str(e))
            return

        qdate = self._log_date_input.date()
        study_date = date_type(qdate.year(), qdate.month(), qdate.day())
        memo = self._log_memo_input.text().strip()

        self._study_log_logic.add_log(
            study_date=study_date,
            duration_minutes=total_minutes,
            memo=memo,
        )
        self._log_memo_input.clear()
        self._log_hours_spin.setValue(0)
        self._log_minutes_spin.setValue(30)
        self._study_logs_changed = True
        self._refresh_study_log_table()

    def _on_delete_study_log(self, log_id: str) -> None:
        """学習記録削除ハンドラ.

        Args:
            log_id: 削除するログID.
        """
        if self._study_log_logic is None:
            return  # pragma: no cover

        reply = QMessageBox.question(
            self,
            "確認",
            "この学習記録を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._study_log_logic.delete_log(log_id)
            self._study_logs_changed = True
            self._refresh_study_log_table()

    def _on_timer_start(self) -> None:
        """タイマー開始ハンドラ."""
        if self._study_log_logic is None:
            return  # pragma: no cover
        self._study_log_logic.start_timer()
        if self._display_timer:
            self._display_timer.start()
        if self._start_btn:
            self._start_btn.setEnabled(False)
        if self._stop_btn:
            self._stop_btn.setEnabled(True)

    def _on_timer_stop(self) -> None:
        """タイマー停止ハンドラ."""
        if self._study_log_logic is None:
            return  # pragma: no cover
        if self._display_timer:
            self._display_timer.stop()
        minutes = self._study_log_logic.stop_timer()
        if minutes > 0:
            self._study_log_logic.add_log(
                study_date=date_type.today(),
                duration_minutes=minutes,
                memo="タイマー計測",
            )
            self._study_logs_changed = True
            self._refresh_study_log_table()
        if self._start_btn:
            self._start_btn.setEnabled(True)
        if self._stop_btn:
            self._stop_btn.setEnabled(False)
        if self._timer_label:
            self._timer_label.setText("00:00:00")

    def _update_timer_display(self) -> None:
        """タイマー表示を更新する."""
        if self._study_log_logic is None or self._timer_label is None:
            return  # pragma: no cover
        seconds = self._study_log_logic.elapsed_seconds
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self._timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def reject(self) -> None:
        """ダイアログを閉じる時にタイマーが実行中なら停止して記録する."""
        if self._study_log_logic and self._study_log_logic.is_timer_running:
            self._on_timer_stop()
        super().reject()
