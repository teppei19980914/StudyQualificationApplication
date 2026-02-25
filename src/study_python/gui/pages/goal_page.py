"""3W1H学習目標の一覧ページ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.dialogs.goal_dialog import GoalDialog
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.goal import Goal, WhenType
from study_python.services.goal_service import GoalService


logger = logging.getLogger(__name__)


class GoalCard(QFrame):
    """3W1H目標のカードウィジェット.

    Signals:
        edit_requested: 編集リクエスト時に発行.
        delete_requested: 削除リクエスト時に発行.
    """

    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(
        self, goal: Goal, theme_manager: ThemeManager, parent: QWidget | None = None
    ) -> None:
        """GoalCardを初期化する.

        Args:
            goal: 表示するGoal.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal = goal
        self._theme_manager = theme_manager
        self.setObjectName("goal_card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # ヘッダー（カラーバー + タイトル + ボタン）
        header_layout = QHBoxLayout()

        color_bar = QFrame()
        color_bar.setFixedSize(4, 40)
        color_bar.setStyleSheet(
            f"background-color: {self._goal.color}; border-radius: 2px;"
        )
        header_layout.addWidget(color_bar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        what_label = QLabel(self._goal.what)
        what_label.setObjectName("card_title")
        title_layout.addWidget(what_label)

        when_text = self._format_when()
        when_label = QLabel(when_text)
        when_label.setObjectName("card_subtitle")
        title_layout.addWidget(when_label)

        header_layout.addLayout(title_layout, 1)

        # 編集・削除ボタン
        edit_btn = QPushButton("編集")
        edit_btn.setObjectName("secondary_button")
        edit_btn.setFixedSize(64, 32)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._goal.id))
        header_layout.addWidget(edit_btn)

        delete_btn = QPushButton("削除")
        delete_btn.setObjectName("danger_button")
        delete_btn.setFixedSize(64, 32)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._goal.id))
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # 3W1H詳細
        details_layout = QVBoxLayout()
        details_layout.setSpacing(6)

        self._add_detail_row(details_layout, "Why", self._goal.why)
        self._add_detail_row(details_layout, "How", self._goal.how)

        layout.addLayout(details_layout)

    def _add_detail_row(self, layout: QVBoxLayout, label: str, value: str) -> None:
        """詳細行を追加する.

        Args:
            layout: 追加先のレイアウト.
            label: ラベル.
            value: 値.
        """
        row = QHBoxLayout()
        row.setSpacing(8)

        label_widget = QLabel(f"{label}:")
        label_widget.setObjectName("muted_text")
        label_widget.setFixedWidth(40)
        row.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet("font-size: 13px;")
        row.addWidget(value_widget, 1)

        layout.addLayout(row)

    def _format_when(self) -> str:
        """When情報をフォーマットする.

        Returns:
            フォーマットされた文字列.
        """
        if self._goal.when_type == WhenType.DATE:
            target_date = self._goal.get_target_date()
            if target_date:
                return f"目標: {target_date.strftime('%Y/%m/%d')}"
        return f"目標: {self._goal.when_target}"


class GoalPage(QWidget):
    """3W1H学習目標の一覧ページ.

    Signals:
        goals_changed: Goal変更時に発行するシグナル.
    """

    goals_changed = Signal()

    def __init__(
        self,
        goal_service: GoalService,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """GoalPageを初期化する.

        Args:
            goal_service: GoalService.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._goal_service = goal_service
        self._theme_manager = theme_manager
        self._setup_ui()
        self._refresh_goals()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ヘッダー
        header_layout = QHBoxLayout()
        title = QLabel("3W1H 学習目標")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_btn = QPushButton("+ 新しい目標")
        add_btn.setFixedHeight(40)
        add_btn.clicked.connect(self._on_add_goal)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # 説明テキスト
        desc = QLabel(
            "学習の動機（Why）、期限（When）、対象（What）、方法（How）を設定して、"
            "モチベーションを維持しましょう。"
        )
        desc.setObjectName("muted_text")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setSpacing(12)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll)

    def _refresh_goals(self) -> None:
        """目標カードを再描画する."""
        # 既存カードを削除
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        goals = self._goal_service.get_all_goals()

        if not goals:
            empty_label = QLabel(
                "まだ目標が登録されていません。\n「+ 新しい目標」ボタンから目標を登録しましょう。"
            )
            empty_label.setObjectName("muted_text")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("padding: 60px; font-size: 14px;")
            self._cards_layout.insertWidget(0, empty_label)
            return

        for goal in goals:
            card = GoalCard(goal, self._theme_manager)
            card.edit_requested.connect(self._on_edit_goal)
            card.delete_requested.connect(self._on_delete_goal)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _on_add_goal(self) -> None:
        """目標追加ハンドラ."""
        dialog = GoalDialog(self)
        if dialog.exec() == GoalDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._goal_service.create_goal(
                    why=values["why"],
                    when_target=values["when_target"],
                    when_type=WhenType(values["when_type"]),
                    what=values["what"],
                    how=values["how"],
                )
                self._refresh_goals()
                self.goals_changed.emit()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_edit_goal(self, goal_id: str) -> None:
        """目標編集ハンドラ.

        Args:
            goal_id: 編集対象のGoal ID.
        """
        goal = self._goal_service.get_goal(goal_id)
        if goal is None:
            return
        dialog = GoalDialog(self, goal=goal)
        if dialog.exec() == GoalDialog.DialogCode.Accepted:
            values = dialog.get_values()
            try:
                self._goal_service.update_goal(
                    goal_id=goal_id,
                    why=values["why"],
                    when_target=values["when_target"],
                    when_type=WhenType(values["when_type"]),
                    what=values["what"],
                    how=values["how"],
                )
                self._refresh_goals()
                self.goals_changed.emit()
            except ValueError as e:
                QMessageBox.warning(self, "エラー", str(e))

    def _on_delete_goal(self, goal_id: str) -> None:
        """目標削除ハンドラ.

        Args:
            goal_id: 削除対象のGoal ID.
        """
        reply = QMessageBox.question(
            self,
            "確認",
            "この目標と関連するすべてのタスクを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._goal_service.delete_goal(goal_id)
            self._refresh_goals()
            self.goals_changed.emit()

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self._refresh_goals()
