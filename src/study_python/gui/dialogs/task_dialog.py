"""ガントチャートタスクの登録/編集ダイアログ."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from study_python.models.task import Task, TaskStatus


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
    ) -> None:
        """TaskDialogを初期化する.

        Args:
            parent: 親ウィジェット.
            task: 編集対象のTask.
            goal_id: 新規作成時のGoal ID.
        """
        super().__init__(parent)
        self.task = task
        self._goal_id = goal_id
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

        header = QLabel(title)
        header.setObjectName("section_title")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # タスク名
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("例: Udemyセクション1-5を完了")
        form.addRow(self._create_label("タスク名"), self._title_input)

        # 開始日
        self._start_date_input = QDateEdit()
        self._start_date_input.setCalendarPopup(True)
        self._start_date_input.setDate(QDate.currentDate())
        self._start_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("開始日"), self._start_date_input)

        # 終了日
        self._end_date_input = QDateEdit()
        self._end_date_input.setCalendarPopup(True)
        self._end_date_input.setDate(QDate.currentDate().addDays(14))
        self._end_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("終了日"), self._end_date_input)

        # ステータス
        self._status_combo = QComboBox()
        self._status_combo.addItem("未着手", TaskStatus.NOT_STARTED.value)
        self._status_combo.addItem("進行中", TaskStatus.IN_PROGRESS.value)
        self._status_combo.addItem("完了", TaskStatus.COMPLETED.value)
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

        # スライダーとスピンボックスの同期
        self._progress_slider.valueChanged.connect(self._progress_spin.setValue)
        self._progress_spin.valueChanged.connect(self._progress_slider.setValue)

        form.addRow(self._create_label("進捗率"), progress_layout)

        # メモ
        self._memo_input = QTextEdit()
        self._memo_input.setPlaceholderText("メモ（任意）")
        self._memo_input.setMaximumHeight(80)
        form.addRow(self._create_label("メモ"), self._memo_input)

        layout.addLayout(form)

        # ボタン
        button_layout = QHBoxLayout()
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
        status_index = {
            TaskStatus.NOT_STARTED: 0,
            TaskStatus.IN_PROGRESS: 1,
            TaskStatus.COMPLETED: 2,
        }
        self._status_combo.setCurrentIndex(status_index.get(task.status, 0))
        self._progress_slider.setValue(task.progress)
        self._memo_input.setPlainText(task.memo)

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

        return {
            "title": self._title_input.text().strip(),
            "start_date": f"{start_qdate.year():04d}-{start_qdate.month():02d}-{start_qdate.day():02d}",
            "end_date": f"{end_qdate.year():04d}-{end_qdate.month():02d}-{end_qdate.day():02d}",
            "status": str(self._status_combo.currentData()),
            "progress": self._progress_spin.value(),
            "memo": self._memo_input.toPlainText().strip(),
        }
