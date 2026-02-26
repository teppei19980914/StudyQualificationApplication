"""マイルストーンセクションウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.motivation_calculator import MilestoneData


logger = logging.getLogger(__name__)


class MilestoneSection(QFrame):
    """達成済みマイルストーンと次の目標を表示するウィジェット.

    Attributes:
        _theme_manager: テーママネージャ.
        _content_layout: コンテンツレイアウト.
        _data: マイルストーンデータ.
        _milestone_labels: マイルストーンラベルのリスト.
        _next_label: 次のマイルストーンラベル.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """MilestoneSectionを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: MilestoneData | None = None
        self._milestone_labels: list[QLabel] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("milestone_section")
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#milestone_section {{"
            f"  background-color: {bg_card};"
            f"  border: 1px solid {border};"
            f"  border-radius: 12px;"
            f"  padding: 12px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # タイトル
        title_layout = QHBoxLayout()
        title_icon = QLabel("\U0001f3c6")
        title_icon.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(title_icon)
        title_label = QLabel("\u30de\u30a4\u30eb\u30b9\u30c8\u30fc\u30f3")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # コンテンツエリア（動的に更新）
        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(4)
        layout.addLayout(self._content_layout)

        # 次の目標ラベル
        self._next_label = QLabel()
        self._next_label.setObjectName("muted_text")
        layout.addWidget(self._next_label)

        # 初期表示
        self._show_empty()

    def set_data(self, data: MilestoneData) -> None:
        """マイルストーンデータを設定する.

        Args:
            data: マイルストーンデータ.
        """
        self._data = data
        self._clear_milestones()

        colors = self._theme_manager.get_colors()
        success_color = colors.get("success", "#A6E3A1")

        if data.achieved:
            for milestone in data.achieved:
                label = QLabel(f"\u2728 {milestone.label}")
                label.setStyleSheet(
                    f"font-size: 13px; color: {success_color}; font-weight: 600;"
                )
                self._content_layout.addWidget(label)
                self._milestone_labels.append(label)
        else:
            empty_label = QLabel(
                "\u307e\u3060\u30de\u30a4\u30eb\u30b9\u30c8\u30fc\u30f3\u306f\u3042\u308a\u307e\u305b\u3093"
            )
            empty_label.setObjectName("muted_text")
            self._content_layout.addWidget(empty_label)
            self._milestone_labels.append(empty_label)

        if data.next_milestone:
            self._next_label.setText(
                f"\u6b21\u306e\u76ee\u6a19: {data.next_milestone.label}"
            )
            self._next_label.setVisible(True)
        else:
            self._next_label.setVisible(False)

        logger.debug(
            f"Milestone section updated: "
            f"{len(data.achieved)} achieved, "
            f"next={'yes' if data.next_milestone else 'none'}"
        )

    def _clear_milestones(self) -> None:
        """マイルストーンラベルをクリアする."""
        for label in self._milestone_labels:
            self._content_layout.removeWidget(label)
            label.deleteLater()
        self._milestone_labels.clear()

    def _show_empty(self) -> None:
        """初期表示（空状態）."""
        empty_label = QLabel(
            "\u307e\u3060\u30de\u30a4\u30eb\u30b9\u30c8\u30fc\u30f3\u306f\u3042\u308a\u307e\u305b\u3093"
        )
        empty_label.setObjectName("muted_text")
        self._content_layout.addWidget(empty_label)
        self._milestone_labels.append(empty_label)
        self._next_label.setText("")
