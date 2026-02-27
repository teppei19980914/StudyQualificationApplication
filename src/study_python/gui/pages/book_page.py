"""書籍管理ページ."""

from __future__ import annotations

import logging
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.dialogs.book_review_dialog import BookReviewDialog
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.book import Book, BookStatus
from study_python.services.book_service import BookService


logger = logging.getLogger(__name__)

_STATUS_LABELS: dict[BookStatus, str] = {
    BookStatus.UNREAD: "未読",
    BookStatus.READING: "読書中",
    BookStatus.COMPLETED: "読了",
}


class BookPage(QWidget):
    """書籍管理ページ.

    書籍の登録・ステータス変更・読了記録・削除を行う。

    Attributes:
        _book_service: BookService.
        _theme_manager: テーママネージャ.
        _book_rows: 書籍行ウィジェットのリスト.
    """

    def __init__(
        self,
        book_service: BookService,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """BookPageを初期化する.

        Args:
            book_service: BookService.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._book_service = book_service
        self._theme_manager = theme_manager
        self._book_rows: list[QWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ヘッダー
        header_layout = QHBoxLayout()
        title = QLabel("\U0001f4da 書籍管理")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 説明テキスト
        desc = QLabel(
            "読書の記録を管理しましょう。"
            "書籍を登録し、読了時に要約・感想を記録して学びを蓄積できます。"
        )
        desc.setObjectName("muted_text")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 新規登録エリア
        add_layout = QHBoxLayout()
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("書籍名を入力...")
        self._title_input.returnPressed.connect(self._on_add_book)
        add_layout.addWidget(self._title_input, 1)

        add_btn = QPushButton("+ 追加")
        add_btn.setFixedHeight(40)
        add_btn.clicked.connect(self._on_add_book)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # 統計ラベル
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(self._stats_label)

        # 書籍リスト（スクロール）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

    def refresh(self) -> None:
        """ページを更新する."""
        self._refresh_book_list()

    def _refresh_book_list(self) -> None:
        """書籍リストを更新する."""
        # 既存行を削除
        for row in self._book_rows:
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._book_rows.clear()

        books = self._book_service.get_all_books()

        # 統計更新
        total = len(books)
        completed = sum(1 for b in books if b.status == BookStatus.COMPLETED)
        reading = sum(1 for b in books if b.status == BookStatus.READING)
        stats_parts = [f"登録: {total}冊"]
        if completed > 0:
            stats_parts.append(f"読了: {completed}冊")
        if reading > 0:
            stats_parts.append(f"読書中: {reading}冊")
        self._stats_label.setText(" | ".join(stats_parts))

        for book in books:
            row = self._create_book_row(book)
            # stretchの前に挿入
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)
            self._book_rows.append(row)

    def _create_book_row(self, book: Book) -> QWidget:
        """書籍行ウィジェットを作成する.

        Args:
            book: 表示する書籍.

        Returns:
            行ウィジェット.
        """
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 4, 8, 4)
        row_layout.setSpacing(8)

        # 書籍名
        title_label = QLabel(f"\U0001f4d6 {book.title}")
        title_label.setStyleSheet("font-size: 13px;")
        title_label.setMinimumWidth(0)
        row_layout.addWidget(title_label, 1)

        # ステータスバッジ
        status_text = _STATUS_LABELS.get(book.status, book.status.value)
        status_label = QLabel(status_text)
        status_label.setStyleSheet(self._get_status_style(book.status))
        status_label.setMinimumWidth(50)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(status_label)

        # 読了日表示（COMPLETEDの場合）
        if book.status == BookStatus.COMPLETED and book.completed_date:
            date_label = QLabel(
                f"({book.completed_date.month}/{book.completed_date.day})"
            )
            date_label.setStyleSheet("font-size: 11px; color: #888;")
            row_layout.addWidget(date_label)

        # アクションボタン
        if book.status == BookStatus.UNREAD:
            reading_btn = QPushButton("読書中")
            reading_btn.setObjectName("secondary_button")
            reading_btn.setFixedHeight(28)
            reading_btn.clicked.connect(
                lambda _checked=False, bid=book.id: self._on_change_status(
                    bid, BookStatus.READING
                )
            )
            row_layout.addWidget(reading_btn)

        if book.status != BookStatus.COMPLETED:
            complete_btn = QPushButton("読了")
            complete_btn.setFixedHeight(28)
            complete_btn.clicked.connect(
                lambda _checked=False, bid=book.id: self._on_complete_book(bid)
            )
            row_layout.addWidget(complete_btn)

        delete_btn = QPushButton("\U0001f5d1")
        delete_btn.setObjectName("danger_button")
        delete_btn.setFixedHeight(28)
        delete_btn.setToolTip("削除")
        delete_btn.clicked.connect(
            lambda _checked=False, bid=book.id: self._on_delete_book(bid)
        )
        row_layout.addWidget(delete_btn)

        return row

    def _get_status_style(self, status: BookStatus) -> str:
        """ステータスに応じたスタイルを返す.

        Args:
            status: 書籍ステータス.

        Returns:
            CSSスタイル文字列.
        """
        colors = self._theme_manager.get_colors()
        style_colors = {
            BookStatus.UNREAD: "#888888",
            BookStatus.READING: colors.get("accent", "#89B4FA"),
            BookStatus.COMPLETED: colors.get("success", "#A6E3A1"),
        }
        color = style_colors.get(status, "#888888")
        return (
            f"font-size: 11px; font-weight: 600; color: {color}; "
            f"border: 1px solid {color}; border-radius: 4px; padding: 2px 4px;"
        )

    def _on_add_book(self) -> None:
        """書籍追加ハンドラ."""
        title = self._title_input.text().strip()
        if not title:
            return
        try:
            self._book_service.create_book(title)
            self._title_input.clear()
            self._refresh_book_list()
            logger.info(f"Book added: {title}")
        except ValueError as e:
            QMessageBox.warning(self, "エラー", str(e))

    def _on_change_status(self, book_id: str, status: BookStatus) -> None:
        """ステータス変更ハンドラ.

        Args:
            book_id: Book ID.
            status: 新しいステータス.
        """
        self._book_service.update_status(book_id, status)
        self._refresh_book_list()

    def _on_complete_book(self, book_id: str) -> None:
        """読了ハンドラ.

        Args:
            book_id: Book ID.
        """
        book = self._book_service.get_book(book_id)
        if book is None:
            return

        dialog = BookReviewDialog(book, self)
        if dialog.exec() == BookReviewDialog.DialogCode.Accepted:
            values = dialog.get_values()
            self._book_service.complete_book(
                book_id=book_id,
                summary=str(values["summary"]),
                impressions=str(values["impressions"]),
                completed_date=date.fromisoformat(str(values["completed_date"])),
            )
            self._refresh_book_list()
            logger.info(f"Book completed: {book.title}")

    def _on_delete_book(self, book_id: str) -> None:
        """削除ハンドラ.

        Args:
            book_id: Book ID.
        """
        reply = QMessageBox.question(
            self,
            "確認",
            "この書籍を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._book_service.delete_book(book_id)
            self._refresh_book_list()

    def on_theme_changed(self) -> None:
        """テーマ変更通知ハンドラ."""
        self._refresh_book_list()
