"""3W1H学習目標の登録/編集ダイアログ."""

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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from study_python.models.goal import Goal, WhenType


class GoalDialog(QDialog):
    """3W1H学習目標の登録/編集ダイアログ.

    Attributes:
        goal: 編集対象のGoal（新規作成時はNone）.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        goal: Goal | None = None,
    ) -> None:
        """GoalDialogを初期化する.

        Args:
            parent: 親ウィジェット.
            goal: 編集対象のGoal（新規作成時はNone）.
        """
        super().__init__(parent)
        self.goal = goal
        self._setup_ui()
        if goal:
            self._populate_from_goal(goal)

    def _setup_ui(self) -> None:
        """UIを構築する."""
        title = "目標を編集" if self.goal else "新しい目標を登録"
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # ヘッダー
        header = QLabel(title)
        header.setObjectName("section_title")
        layout.addWidget(header)

        # フォーム
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # What（何を）
        self._what_input = QLineEdit()
        self._what_input.setPlaceholderText("例: AWS Solutions Architect Associate")
        form.addRow(self._create_label("What (何を)"), self._what_input)

        # Why（なぜ）
        self._why_input = QTextEdit()
        self._why_input.setPlaceholderText(
            "例: キャリアアップのため、クラウド技術を証明したい"
        )
        self._why_input.setMaximumHeight(80)
        form.addRow(self._create_label("Why (なぜ)"), self._why_input)

        # When Type
        self._when_type_combo = QComboBox()
        self._when_type_combo.addItem("目標日を指定", WhenType.DATE.value)
        self._when_type_combo.addItem("期間を指定", WhenType.PERIOD.value)
        self._when_type_combo.currentIndexChanged.connect(self._on_when_type_changed)
        form.addRow(self._create_label("When (タイプ)"), self._when_type_combo)

        # When Date
        self._when_date_input = QDateEdit()
        self._when_date_input.setCalendarPopup(True)
        self._when_date_input.setDate(QDate.currentDate().addMonths(3))
        self._when_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("When (いつまでに)"), self._when_date_input)

        # When Period (hidden by default)
        self._when_period_input = QLineEdit()
        self._when_period_input.setPlaceholderText("例: 3ヶ月以内")
        self._when_period_input.setVisible(False)
        self._when_period_label = self._create_label("When (期間)")
        self._when_period_label.setVisible(False)
        form.addRow(self._when_period_label, self._when_period_input)

        # How（どうやって）
        self._how_input = QTextEdit()
        self._how_input.setPlaceholderText(
            "例: Udemyの講座を受講し、模擬試験を繰り返す"
        )
        self._how_input.setMaximumHeight(80)
        form.addRow(self._create_label("How (どうやって)"), self._how_input)

        layout.addLayout(form)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setObjectName("secondary_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存" if self.goal else "登録")
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

    def _on_when_type_changed(self, index: int) -> None:
        """Whenタイプ変更ハンドラ.

        Args:
            index: コンボボックスのインデックス.
        """
        is_date = index == 0
        self._when_date_input.setVisible(is_date)
        self._when_period_input.setVisible(not is_date)
        self._when_period_label.setVisible(not is_date)

    def _populate_from_goal(self, goal: Goal) -> None:
        """Goalの値をフォームに設定する.

        Args:
            goal: 設定するGoal.
        """
        self._what_input.setText(goal.what)
        self._why_input.setPlainText(goal.why)
        self._how_input.setPlainText(goal.how)

        if goal.when_type == WhenType.DATE:
            self._when_type_combo.setCurrentIndex(0)
            target_date = goal.get_target_date()
            if target_date:
                self._when_date_input.setDate(
                    QDate(target_date.year, target_date.month, target_date.day)
                )
        else:
            self._when_type_combo.setCurrentIndex(1)
            self._when_period_input.setText(goal.when_target)

    def _on_save(self) -> None:
        """保存ボタンのハンドラ."""
        if not self._what_input.text().strip():
            QMessageBox.warning(self, "入力エラー", "「What (何を)」は必須です。")
            return
        if not self._why_input.toPlainText().strip():
            QMessageBox.warning(self, "入力エラー", "「Why (なぜ)」は必須です。")
            return
        if not self._how_input.toPlainText().strip():
            QMessageBox.warning(self, "入力エラー", "「How (どうやって)」は必須です。")
            return

        when_type_value = self._when_type_combo.currentData()
        if (
            when_type_value == WhenType.PERIOD.value
            and not self._when_period_input.text().strip()
        ):
            QMessageBox.warning(self, "入力エラー", "「When (期間)」は必須です。")
            return

        self.accept()

    def get_values(self) -> dict[str, str]:
        """フォームの入力値を取得する.

        Returns:
            入力値の辞書.
        """
        when_type_value = self._when_type_combo.currentData()
        when_type = WhenType(when_type_value)

        if when_type == WhenType.DATE:
            qdate = self._when_date_input.date()
            when_target = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        else:
            when_target = self._when_period_input.text().strip()

        return {
            "what": self._what_input.text().strip(),
            "why": self._why_input.toPlainText().strip(),
            "when_target": when_target,
            "when_type": when_type.value,
            "how": self._how_input.toPlainText().strip(),
        }
