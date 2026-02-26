"""学習時間記録ダイアログ."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.widgets.japanese_calendar_widget import create_japanese_date_edit
from study_python.models.task import Task


class StudyLogDialog(QDialog):
    """学習時間記録ダイアログ.

    タスクを選択し、学習日・学習時間・メモを入力して記録する。

    Attributes:
        _tasks: 選択可能なタスクのリスト.
    """

    def __init__(
        self,
        tasks: list[Task],
        parent: QWidget | None = None,
        preselected_task_id: str | None = None,
    ) -> None:
        """StudyLogDialogを初期化する.

        Args:
            tasks: 選択可能なタスクのリスト.
            parent: 親ウィジェット.
            preselected_task_id: 初期選択するタスクID.
        """
        super().__init__(parent)
        self._tasks = tasks
        self._preselected_task_id = preselected_task_id
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("学習時間を記録")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("学習時間を記録")
        header.setObjectName("section_title")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # タスク選択
        self._task_combo = QComboBox()
        for task in self._tasks:
            self._task_combo.addItem(task.title, task.id)
        if self._preselected_task_id:
            for i in range(self._task_combo.count()):
                if self._task_combo.itemData(i) == self._preselected_task_id:
                    self._task_combo.setCurrentIndex(i)
                    break
        form.addRow(self._create_label("タスク"), self._task_combo)

        # 学習日
        self._date_input = create_japanese_date_edit()
        self._date_input.setDate(QDate.currentDate())
        self._date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("学習日"), self._date_input)

        # 学習時間
        time_layout = QHBoxLayout()
        self._hours_spin = QSpinBox()
        self._hours_spin.setRange(0, 23)
        self._hours_spin.setSuffix(" 時間")
        self._hours_spin.setFixedWidth(100)
        time_layout.addWidget(self._hours_spin)

        self._minutes_spin = QSpinBox()
        self._minutes_spin.setRange(0, 59)
        self._minutes_spin.setValue(30)
        self._minutes_spin.setSuffix(" 分")
        self._minutes_spin.setFixedWidth(100)
        time_layout.addWidget(self._minutes_spin)
        time_layout.addStretch()
        form.addRow(self._create_label("学習時間"), time_layout)

        # メモ
        self._memo_input = QLineEdit()
        self._memo_input.setPlaceholderText("メモ（任意）")
        form.addRow(self._create_label("メモ"), self._memo_input)

        layout.addLayout(form)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setObjectName("secondary_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("記録")
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

    def _on_save(self) -> None:
        """記録ボタンのハンドラ."""
        total = self._hours_spin.value() * 60 + self._minutes_spin.value()
        if total <= 0:
            QMessageBox.warning(
                self, "入力エラー", "学習時間は1分以上で入力してください。"
            )
            return
        if self._task_combo.count() == 0:
            QMessageBox.warning(self, "入力エラー", "タスクが選択されていません。")
            return
        self.accept()

    def get_values(self) -> dict[str, str | int]:
        """フォームの入力値を取得する.

        Returns:
            入力値の辞書.
        """
        study_qdate = self._date_input.date()
        total_minutes = self._hours_spin.value() * 60 + self._minutes_spin.value()
        return {
            "task_id": str(self._task_combo.currentData()),
            "study_date": f"{study_qdate.year():04d}-{study_qdate.month():02d}-{study_qdate.day():02d}",
            "duration_minutes": total_minutes,
            "memo": self._memo_input.text().strip(),
        }
