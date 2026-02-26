"""書籍管理ダイアログ."""

from __future__ import annotations

import logging
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
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
from study_python.models.book import Book, BookStatus
from study_python.services.book_service import BookService


logger = logging.getLogger(__name__)

_STATUS_LABELS: dict[BookStatus, str] = {
    BookStatus.UNREAD: "\u672a\u8aad",
    BookStatus.READING: "\u8aad\u66f8\u4e2d",
    BookStatus.COMPLETED: "\u8aad\u4e86",
}


class BookManagementDialog(QDialog):
    """書籍管理ダイアログ.

    書籍の登録・ステータス変更・読了記録・削除を行う。

    Attributes:
        _book_service: BookService.
        _books_changed: 書籍が変更されたかどうか.
    """

    def __init__(
        self,
        book_service: BookService,
        parent: QWidget | None = None,
    ) -> None:
        """BookManagementDialogを初期化する.

        Args:
            book_service: BookService.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._book_service = book_service
        self._books_changed = False
        self._book_rows: list[QWidget] = []
        self._setup_ui()
        self._refresh_book_list()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("\u66f8\u7c4d\u7ba1\u7406")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("\U0001f4da \u66f8\u7c4d\u7ba1\u7406")
        header.setObjectName("section_title")
        layout.addWidget(header)

        # 新規登録エリア
        add_layout = QHBoxLayout()
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("\u66f8\u7c4d\u540d\u3092\u5165\u529b...")
        self._title_input.returnPressed.connect(self._on_add_book)
        add_layout.addWidget(self._title_input, 1)

        add_btn = QPushButton("\u8ffd\u52a0")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._on_add_book)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

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

        # 閉じるボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("\u9589\u3058\u308b")
        close_btn.setObjectName("secondary_button")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def _refresh_book_list(self) -> None:
        """書籍リストを更新する."""
        # 既存行を削除
        for row in self._book_rows:
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._book_rows.clear()

        books = self._book_service.get_all_books()
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
        row_layout.addWidget(title_label, 1)

        # ステータスバッジ
        status_text = _STATUS_LABELS.get(book.status, book.status.value)
        status_label = QLabel(status_text)
        status_label.setStyleSheet(self._get_status_style(book.status))
        status_label.setFixedWidth(60)
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
            reading_btn = QPushButton("\u8aad\u66f8\u4e2d")
            reading_btn.setObjectName("secondary_button")
            reading_btn.setFixedSize(64, 28)
            reading_btn.clicked.connect(
                lambda _checked=False, bid=book.id: self._on_change_status(
                    bid, BookStatus.READING
                )
            )
            row_layout.addWidget(reading_btn)

        if book.status != BookStatus.COMPLETED:
            complete_btn = QPushButton("\u8aad\u4e86")
            complete_btn.setFixedSize(48, 28)
            complete_btn.clicked.connect(
                lambda _checked=False, bid=book.id: self._on_complete_book(bid)
            )
            row_layout.addWidget(complete_btn)

        delete_btn = QPushButton("\U0001f5d1")
        delete_btn.setObjectName("danger_button")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setToolTip("\u524a\u9664")
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
        colors = {
            BookStatus.UNREAD: "#888888",
            BookStatus.READING: "#89B4FA",
            BookStatus.COMPLETED: "#A6E3A1",
        }
        color = colors.get(status, "#888888")
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
            self._books_changed = True
            self._refresh_book_list()
            logger.info(f"Book added via dialog: {title}")
        except ValueError as e:
            QMessageBox.warning(self, "\u30a8\u30e9\u30fc", str(e))

    def _on_change_status(self, book_id: str, status: BookStatus) -> None:
        """ステータス変更ハンドラ.

        Args:
            book_id: Book ID.
            status: 新しいステータス.
        """
        self._book_service.update_status(book_id, status)
        self._books_changed = True
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
            self._books_changed = True
            self._refresh_book_list()
            logger.info(f"Book completed via dialog: {book.title}")

    def _on_delete_book(self, book_id: str) -> None:
        """削除ハンドラ.

        Args:
            book_id: Book ID.
        """
        reply = QMessageBox.question(
            self,
            "\u78ba\u8a8d",
            "\u3053\u306e\u66f8\u7c4d\u3092\u524a\u9664\u3057\u307e\u3059\u304b\uff1f",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._book_service.delete_book(book_id)
            self._books_changed = True
            self._refresh_book_list()

    @property
    def books_changed(self) -> bool:
        """書籍が変更されたかどうかを返す."""
        return self._books_changed
