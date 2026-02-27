"""書籍スケジュールの登録/編集ダイアログ."""

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
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.widgets.japanese_calendar_widget import create_japanese_date_edit
from study_python.models.book import Book
from study_python.models.task import TaskStatus


_NEW_BOOK_KEY = "__new__"


class BookScheduleDialog(QDialog):
    """書籍スケジュール登録/編集ダイアログ.

    Attributes:
        book: 編集対象のBook（新規作成時はNone）.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        book: Book | None = None,
        unscheduled_books: list[Book] | None = None,
    ) -> None:
        """BookScheduleDialogを初期化する.

        Args:
            parent: 親ウィジェット.
            book: 編集対象のBook（editモード）.
            unscheduled_books: スケジュール未設定の既存書籍（addモード）.
        """
        super().__init__(parent)
        self.book = book
        self._unscheduled_books = unscheduled_books or []
        self._delete_requested = False
        self._setup_ui()
        if book:
            self._populate_from_book(book)

    def _setup_ui(self) -> None:
        """UIを構築する."""
        title = (
            "\u8aad\u66f8\u30b9\u30b1\u30b8\u30e5\u30fc\u30eb\u3092\u7de8\u96c6"
            if self.book
            else "\u8aad\u66f8\u30b9\u30b1\u30b8\u30e5\u30fc\u30eb\u3092\u8ffd\u52a0"
        )
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel(title)
        header.setObjectName("section_title")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 書籍選択（addモードのみ）
        self._book_source_combo: QComboBox | None = None
        if not self.book:
            self._book_source_combo = QComboBox()
            self._book_source_combo.addItem(
                "\U0001f4dd \u65b0\u3057\u3044\u66f8\u7c4d\u3092\u4f5c\u6210",
                _NEW_BOOK_KEY,
            )
            for b in self._unscheduled_books:
                self._book_source_combo.addItem(f"\U0001f4d6 {b.title}", b.id)
            self._book_source_combo.currentIndexChanged.connect(self._on_source_changed)
            form.addRow(self._create_label("\u66f8\u7c4d"), self._book_source_combo)

        # 書籍名
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("\u4f8b: Python\u5165\u9580")
        form.addRow(self._create_label("\u66f8\u7c4d\u540d"), self._title_input)

        # 開始日
        self._start_date_input = create_japanese_date_edit()
        self._start_date_input.setDate(QDate.currentDate())
        self._start_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("\u958b\u59cb\u65e5"), self._start_date_input)

        # 終了日
        self._end_date_input = create_japanese_date_edit()
        self._end_date_input.setDate(QDate.currentDate().addDays(30))
        self._end_date_input.setDisplayFormat("yyyy/MM/dd")
        form.addRow(self._create_label("\u7d42\u4e86\u65e5"), self._end_date_input)

        # ステータス（進捗率から自動決定、編集不可）
        self._status_combo = QComboBox()
        self._status_combo.addItem("未読", TaskStatus.NOT_STARTED.value)
        self._status_combo.addItem("読書中", TaskStatus.IN_PROGRESS.value)
        self._status_combo.addItem("読了", TaskStatus.COMPLETED.value)
        self._status_combo.setEnabled(False)
        form.addRow(self._create_label("ステータス"), self._status_combo)

        # 進捗率
        progress_layout = QHBoxLayout()
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 100)
        self._progress_slider.setValue(0)
        self._progress_slider.setTickInterval(10)
        progress_layout.addWidget(self._progress_slider, 1)

        self._progress_spin = QSpinBox()
        self._progress_spin.setRange(0, 100)
        self._progress_spin.setSuffix("%")
        self._progress_spin.setValue(0)
        self._progress_spin.setFixedWidth(80)
        progress_layout.addWidget(self._progress_spin)

        # スライダーとスピンボックスの同期 + ステータス自動更新
        self._progress_slider.valueChanged.connect(self._progress_spin.setValue)
        self._progress_spin.valueChanged.connect(self._progress_slider.setValue)
        self._progress_spin.valueChanged.connect(self._update_status_from_progress)

        form.addRow(self._create_label("\u9032\u6357\u7387"), progress_layout)

        layout.addLayout(form)

        # ボタン
        button_layout = QHBoxLayout()

        if self.book:
            delete_btn = QPushButton(
                "\U0001f5d1 \u30b9\u30b1\u30b8\u30e5\u30fc\u30eb\u524a\u9664"
            )
            delete_btn.setObjectName("danger_button")
            delete_btn.clicked.connect(self._on_delete)
            button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("\u30ad\u30e3\u30f3\u30bb\u30eb")
        cancel_btn.setObjectName("secondary_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("\u4fdd\u5b58" if self.book else "\u8ffd\u52a0")
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

    def _on_source_changed(self, _index: int) -> None:
        """書籍選択コンボの変更ハンドラ.

        Args:
            _index: 選択インデックス.
        """
        if self._book_source_combo is None:
            return
        book_id = self._book_source_combo.currentData()
        if book_id == _NEW_BOOK_KEY:
            self._title_input.setEnabled(True)
            self._title_input.clear()
        else:
            for b in self._unscheduled_books:
                if b.id == book_id:
                    self._title_input.setText(b.title)
                    self._title_input.setEnabled(False)
                    break

    def _update_status_from_progress(self, progress: int) -> None:
        """進捗率からステータスを自動更新する.

        Args:
            progress: 進捗率（0-100）.
        """
        if progress == 0:
            self._status_combo.setCurrentIndex(0)  # 未読
        elif progress == 100:
            self._status_combo.setCurrentIndex(2)  # 読了
        else:
            self._status_combo.setCurrentIndex(1)  # 読書中

    def _populate_from_book(self, book: Book) -> None:
        """Bookの値をフォームに設定する.

        Args:
            book: 設定するBook.
        """
        self._title_input.setText(book.title)
        if book.start_date:
            self._start_date_input.setDate(
                QDate(
                    book.start_date.year,
                    book.start_date.month,
                    book.start_date.day,
                )
            )
        if book.end_date:
            self._end_date_input.setDate(
                QDate(
                    book.end_date.year,
                    book.end_date.month,
                    book.end_date.day,
                )
            )
        # 進捗率を設定（ステータスは自動更新される）
        self._progress_slider.setValue(book.progress)

    def _on_delete(self) -> None:
        """削除ボタンのハンドラ."""
        reply = QMessageBox.question(
            self,
            "\u78ba\u8a8d",
            "\u3053\u306e\u66f8\u7c4d\u306e\u30b9\u30b1\u30b8\u30e5\u30fc\u30eb\u3092\u524a\u9664\u3057\u307e\u3059\u304b\uff1f\n"
            "\uff08\u66f8\u7c4d\u81ea\u4f53\u306f\u524a\u9664\u3055\u308c\u307e\u305b\u3093\uff09",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_requested = True
            self.reject()

    @property
    def delete_requested(self) -> bool:
        """削除がリクエストされたかどうかを返す."""
        return self._delete_requested

    def _on_save(self) -> None:
        """保存ボタンのハンドラ."""
        if not self._title_input.text().strip():
            QMessageBox.warning(
                self,
                "\u5165\u529b\u30a8\u30e9\u30fc",
                "\u66f8\u7c4d\u540d\u306f\u5fc5\u9808\u3067\u3059\u3002",
            )
            return

        start_qdate = self._start_date_input.date()
        end_qdate = self._end_date_input.date()
        if end_qdate < start_qdate:
            QMessageBox.warning(
                self,
                "\u5165\u529b\u30a8\u30e9\u30fc",
                "\u7d42\u4e86\u65e5\u306f\u958b\u59cb\u65e5\u4ee5\u964d\u306b\u8a2d\u5b9a\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
            )
            return

        self.accept()

    def get_values(self) -> dict[str, str | int]:
        """フォームの入力値を取得する.

        Returns:
            入力値の辞書.
        """
        start_qdate = self._start_date_input.date()
        end_qdate = self._end_date_input.date()

        values: dict[str, str | int] = {
            "title": self._title_input.text().strip(),
            "start_date": (
                f"{start_qdate.year():04d}-{start_qdate.month():02d}"
                f"-{start_qdate.day():02d}"
            ),
            "end_date": (
                f"{end_qdate.year():04d}-{end_qdate.month():02d}-{end_qdate.day():02d}"
            ),
            "status": str(self._status_combo.currentData()),
            "progress": self._progress_spin.value(),
        }
        if self._book_source_combo is not None:
            values["book_source"] = str(self._book_source_combo.currentData())
        return values
