"""学習ログ履歴テーブルウィジェット."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager


logger = logging.getLogger(__name__)


@dataclass
class StudyLogEntry:
    """表示用学習ログエントリ.

    Attributes:
        study_date: 学習実施日.
        task_name: タスク名（表示用）.
        duration_minutes: 学習時間（分）.
        memo: メモ.
    """

    study_date: date
    task_name: str
    duration_minutes: int
    memo: str


class StudyLogTable(QWidget):
    """学習ログ履歴テーブルウィジェット.

    個別の学習ログをテーブル形式で表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _table: テーブルウィジェット.
    """

    _HEADERS: ClassVar[list[str]] = ["日付", "タスク", "学習時間", "メモ"]

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """StudyLogTableを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self._HEADERS))
        self._table.setHorizontalHeaderLabels(self._HEADERS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setMaximumHeight(300)

        # ヘッダーの伸縮設定
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self._empty_label = QLabel("学習ログがありません")
        self._empty_label.setObjectName("muted_text")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setVisible(False)

        layout.addWidget(self._table)
        layout.addWidget(self._empty_label)

    def set_entries(self, entries: list[StudyLogEntry]) -> None:
        """テーブルにログエントリを設定する.

        Args:
            entries: 表示するログエントリのリスト（日付降順を推奨）.
        """
        self._table.setRowCount(0)

        if not entries:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            return

        self._table.setVisible(True)
        self._empty_label.setVisible(False)
        self._table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # 日付
            date_item = QTableWidgetItem(entry.study_date.isoformat())
            date_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 0, date_item)

            # タスク名
            task_item = QTableWidgetItem(entry.task_name)
            self._table.setItem(row, 1, task_item)

            # 学習時間
            time_text = self._format_duration(entry.duration_minutes)
            time_item = QTableWidgetItem(time_text)
            time_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 2, time_item)

            # メモ
            memo_item = QTableWidgetItem(entry.memo)
            self._table.setItem(row, 3, memo_item)

        logger.debug(f"Study log table updated: {len(entries)} entries")

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """学習時間をフォーマットする.

        Args:
            minutes: 学習時間（分）.

        Returns:
            フォーマット済み文字列.
        """
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins:02d}min"
        return f"{mins}min"
