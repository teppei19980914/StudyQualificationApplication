"""実績ポップアップダイアログ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.motivation_calculator import MilestoneData


logger = logging.getLogger(__name__)


class MilestonePopup(QDialog):
    """実績を表示するポップアップダイアログ.

    累計値の表示と閾値達成通知を行う。

    Attributes:
        _theme_manager: テーママネージャ.
        _data: 実績データ.
        _stat_labels: 統計値ラベルのリスト.
        _milestone_labels: 達成通知ラベルのリスト.
        _next_label: 次の目標ラベル.
    """

    def __init__(
        self,
        data: MilestoneData,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """MilestonePopupを初期化する.

        Args:
            data: 実績データ.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data = data
        self._stat_labels: list[QLabel] = []
        self._milestone_labels: list[QLabel] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("実績")
        self.setMinimumWidth(320)

        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        text_color = colors.get("text", "#CDD6F4")
        border = colors.get("border", "#45475A")
        success_color = colors.get("success", "#A6E3A1")

        self.setStyleSheet(
            f"QDialog {{ background-color: {bg_card}; color: {text_color}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # タイトル
        title_layout = QHBoxLayout()
        title_icon = QLabel("\U0001f3c6")
        title_icon.setStyleSheet("font-size: 20px;")
        title_layout.addWidget(title_icon)

        title_label = QLabel("実績")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 区切り線
        separator1 = QLabel()
        separator1.setFixedHeight(1)
        separator1.setStyleSheet(f"background-color: {border};")
        layout.addWidget(separator1)

        # 累計値の表示
        stats = [
            ("\u23f0", "累計学習時間", f"{self._data.total_hours}時間"),
            ("\U0001f4c5", "累計学習日数", f"{self._data.study_days}日"),
            ("\U0001f525", "連続学習日数", f"{self._data.current_streak}日"),
        ]

        for icon, label_text, value_text in stats:
            row_layout = QHBoxLayout()

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px;")
            icon_label.setFixedWidth(24)
            row_layout.addWidget(icon_label)

            name_label = QLabel(label_text)
            name_label.setStyleSheet("font-size: 13px;")
            row_layout.addWidget(name_label)

            row_layout.addStretch()

            value_label = QLabel(value_text)
            value_label.setStyleSheet(
                f"font-size: 14px; color: {success_color}; font-weight: bold;"
            )
            row_layout.addWidget(value_label)
            self._stat_labels.append(value_label)

            layout.addLayout(row_layout)

        # 区切り線
        separator2 = QLabel()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet(f"background-color: {border};")
        layout.addWidget(separator2)

        # 達成通知
        if self._data.achieved:
            for milestone in self._data.achieved:
                label = QLabel(f"\u2728 {milestone.label}")
                label.setStyleSheet(
                    f"font-size: 13px; color: {success_color}; font-weight: 600;"
                )
                label.setWordWrap(True)
                layout.addWidget(label)
                self._milestone_labels.append(label)
        else:
            empty_label = QLabel("まだ実績はありません")
            empty_label.setObjectName("muted_text")
            empty_label.setStyleSheet("font-size: 13px;")
            layout.addWidget(empty_label)
            self._milestone_labels.append(empty_label)

        # 次の目標
        self._next_label = QLabel()
        self._next_label.setObjectName("muted_text")
        self._next_label.setStyleSheet("font-size: 12px;")
        if self._data.next_milestone:
            self._next_label.setText(f"次の目標: {self._data.next_milestone.label}")
            self._next_label.setVisible(True)
        else:
            self._next_label.setVisible(False)
        layout.addWidget(self._next_label)

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.setFixedHeight(32)
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {border};"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  padding: 4px 16px;"
            f"}}"
        )
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        logger.debug(
            f"MilestonePopup created: "
            f"total_hours={self._data.total_hours}, "
            f"study_days={self._data.study_days}, "
            f"current_streak={self._data.current_streak}, "
            f"{len(self._data.achieved)} achieved, "
            f"next={'yes' if self._data.next_milestone else 'none'}"
        )
