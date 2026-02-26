"""書籍読了レビューダイアログ."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.widgets.japanese_calendar_widget import create_japanese_date_edit
from study_python.models.book import Book


class BookReviewDialog(QDialog):
    """書籍読了レビューダイアログ.

    読了時に要約・感想を記録するためのダイアログ。

    Attributes:
        _book: 対象の書籍.
    """

    def __init__(
        self,
        book: Book,
        parent: QWidget | None = None,
    ) -> None:
        """BookReviewDialogを初期化する.

        Args:
            book: レビュー対象の書籍.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._book = book
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("読了記録")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel(f"\u300c{self._book.title}\u300d\u306e\u8aad\u4e86\u8a18\u9332")
        header.setObjectName("section_title")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 読了日
        self._completed_date_input = create_japanese_date_edit()
        self._completed_date_input.setDate(QDate.currentDate())
        self._completed_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(
            self._create_label("\u8aad\u4e86\u65e5"), self._completed_date_input
        )

        # 要約
        self._summary_input = QTextEdit()
        self._summary_input.setPlaceholderText(
            "\u66f8\u7c4d\u306e\u8981\u7d04\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044..."
        )
        self._summary_input.setMaximumHeight(120)
        form.addRow(self._create_label("\u8981\u7d04"), self._summary_input)

        # 感想
        self._impressions_input = QTextEdit()
        self._impressions_input.setPlaceholderText(
            "\u611f\u60f3\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044..."
        )
        self._impressions_input.setMaximumHeight(120)
        form.addRow(self._create_label("\u611f\u60f3"), self._impressions_input)

        layout.addLayout(form)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("\u30ad\u30e3\u30f3\u30bb\u30eb")
        cancel_btn.setObjectName("secondary_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("\u8a18\u9332")
        save_btn.clicked.connect(self.accept)
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

    def get_values(self) -> dict[str, str]:
        """フォームの入力値を取得する.

        Returns:
            入力値の辞書.
        """
        qdate = self._completed_date_input.date()
        return {
            "summary": self._summary_input.toPlainText().strip(),
            "impressions": self._impressions_input.toPlainText().strip(),
            "completed_date": (
                f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
            ),
        }
