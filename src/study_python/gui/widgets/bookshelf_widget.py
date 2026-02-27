"""本棚ダッシュボードウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.book_service import BookshelfData


logger = logging.getLogger(__name__)


class BookshelfWidget(QFrame):
    """本棚ウィジェット.

    登録書籍数・読了数・最近の読了を表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _content_layout: コンテンツレイアウト.
        _data: 本棚データ.
        _stats_label: 統計ラベル.
        _book_labels: 書籍ラベルのリスト.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """BookshelfWidgetを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: BookshelfData | None = None
        self._book_labels: list[QWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("bookshelf_widget")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        border = colors.get("border", "#45475A")
        self.setStyleSheet(
            f"QFrame#bookshelf_widget {{"
            f"  background-color: {bg_card};"
            f"  border: 1px solid {border};"
            f"  border-radius: 12px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # タイトル
        title_layout = QHBoxLayout()
        title_icon = QLabel("\U0001f4da")
        title_icon.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(title_icon)
        title_label = QLabel("\u672c\u68da")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 統計ラベル
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self._stats_label)

        # 最近の読了セクション
        self._recent_header = QLabel("\u6700\u8fd1\u306e\u8aad\u4e86:")
        self._recent_header.setStyleSheet("font-size: 12px; font-weight: 600;")
        self._recent_header.hide()
        layout.addWidget(self._recent_header)

        # コンテンツエリア（動的に更新）
        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(4)
        layout.addLayout(self._content_layout)

        # 初期表示
        self._show_empty()

    def set_data(self, data: BookshelfData) -> None:
        """本棚データを設定する.

        Args:
            data: 本棚データ.
        """
        self._data = data
        self._clear_books()

        colors = self._theme_manager.get_colors()
        success_color = colors.get("success", "#A6E3A1")

        # 統計表示
        stats_parts = [f"\u767b\u9332: {data.total_count}\u518a"]
        if data.completed_count > 0:
            stats_parts.append(f"\u8aad\u4e86: {data.completed_count}\u518a")
        if data.reading_count > 0:
            stats_parts.append(f"\u8aad\u66f8\u4e2d: {data.reading_count}\u518a")
        self._stats_label.setText(" | ".join(stats_parts))

        # 最近の読了
        if data.recent_completed:
            self._recent_header.show()
            for book in data.recent_completed:
                book_widget = QWidget()
                book_layout = QVBoxLayout(book_widget)
                book_layout.setContentsMargins(4, 2, 4, 2)
                book_layout.setSpacing(2)

                # 書籍名 + 読了日
                date_str = ""
                if book.completed_date:
                    date_str = (
                        f" ({book.completed_date.month}/{book.completed_date.day})"
                    )
                title_label = QLabel(f"\U0001f4d6 {book.title}{date_str}")
                title_label.setStyleSheet(f"font-size: 12px; color: {success_color};")
                book_layout.addWidget(title_label)

                # 要約（あれば）
                if book.summary:
                    summary_text = book.summary
                    if len(summary_text) > 50:
                        summary_text = summary_text[:50] + "..."
                    summary_label = QLabel(f"  {summary_text}")
                    summary_label.setStyleSheet("font-size: 11px; color: #888;")
                    summary_label.setWordWrap(True)
                    book_layout.addWidget(summary_label)

                self._content_layout.addWidget(book_widget)
                self._book_labels.append(book_widget)
        else:
            self._recent_header.hide()
            if data.total_count == 0:
                self._show_empty()
            else:
                empty_label = QLabel(
                    "\u307e\u3060\u8aad\u4e86\u3057\u305f\u66f8\u7c4d\u306f\u3042\u308a\u307e\u305b\u3093"
                )
                empty_label.setObjectName("muted_text")
                self._content_layout.addWidget(empty_label)
                self._book_labels.append(empty_label)

        logger.debug(
            f"Bookshelf widget updated: "
            f"{data.total_count} total, "
            f"{data.completed_count} completed"
        )

    def _clear_books(self) -> None:
        """書籍ラベルをクリアする."""
        for widget in self._book_labels:
            self._content_layout.removeWidget(widget)
            widget.deleteLater()
        self._book_labels.clear()

    def _show_empty(self) -> None:
        """初期表示（空状態）."""
        empty_label = QLabel(
            "\u66f8\u7c4d\u304c\u767b\u9332\u3055\u308c\u3066\u3044\u307e\u305b\u3093"
        )
        empty_label.setObjectName("muted_text")
        self._content_layout.addWidget(empty_label)
        self._book_labels.append(empty_label)
