"""BookshelfWidgetのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.bookshelf_widget import BookshelfWidget
from study_python.models.book import Book, BookStatus
from study_python.services.book_service import BookshelfData


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    """テスト用ThemeManager."""
    return ThemeManager(tmp_path / "settings.json")


@pytest.fixture
def widget(qtbot, theme_manager: ThemeManager) -> BookshelfWidget:
    """テスト用ウィジェット."""
    w = BookshelfWidget(theme_manager)
    qtbot.addWidget(w)
    return w


class TestBookshelfWidgetCreation:
    """ウィジェット生成のテスト."""

    def test_create_widget(self, widget: BookshelfWidget) -> None:
        assert widget is not None

    def test_initial_empty_state(self, widget: BookshelfWidget) -> None:
        assert len(widget._book_labels) == 1  # 空メッセージ

    def test_stats_label_empty_initially(self, widget: BookshelfWidget) -> None:
        assert widget._stats_label.text() == ""


class TestBookshelfWidgetSetData:
    """set_dataのテスト."""

    def test_empty_data(self, widget: BookshelfWidget) -> None:
        data = BookshelfData(
            total_count=0,
            completed_count=0,
            reading_count=0,
            recent_completed=[],
        )
        widget.set_data(data)
        assert "0冊" in widget._stats_label.text()

    def test_stats_display(self, widget: BookshelfWidget) -> None:
        data = BookshelfData(
            total_count=5,
            completed_count=3,
            reading_count=1,
            recent_completed=[],
        )
        widget.set_data(data)
        text = widget._stats_label.text()
        assert "5冊" in text
        assert "3冊" in text
        assert "1冊" in text

    def test_stats_hides_zero_counts(self, widget: BookshelfWidget) -> None:
        data = BookshelfData(
            total_count=2,
            completed_count=0,
            reading_count=0,
            recent_completed=[],
        )
        widget.set_data(data)
        text = widget._stats_label.text()
        assert "登録: 2冊" in text
        assert "読了" not in text
        assert "読書中" not in text

    def test_recent_completed_shown(self, widget: BookshelfWidget) -> None:
        book = Book(
            title="Python入門",
            id="book-1",
            status=BookStatus.COMPLETED,
            summary="Pythonの基礎を学んだ",
            completed_date=date(2026, 2, 20),
        )
        data = BookshelfData(
            total_count=1,
            completed_count=1,
            reading_count=0,
            recent_completed=[book],
        )
        widget.set_data(data)
        assert not widget._recent_header.isHidden()
        assert len(widget._book_labels) == 1

    def test_recent_header_hidden_when_no_completed(
        self, widget: BookshelfWidget
    ) -> None:
        data = BookshelfData(
            total_count=2,
            completed_count=0,
            reading_count=1,
            recent_completed=[],
        )
        widget.set_data(data)
        assert widget._recent_header.isHidden()

    def test_long_summary_truncated(self, widget: BookshelfWidget) -> None:
        book = Book(
            title="テスト本",
            id="book-1",
            status=BookStatus.COMPLETED,
            summary="あ" * 100,
            completed_date=date(2026, 2, 20),
        )
        data = BookshelfData(
            total_count=1,
            completed_count=1,
            reading_count=0,
            recent_completed=[book],
        )
        widget.set_data(data)
        # 切り捨てされること（50文字+...）
        assert len(widget._book_labels) == 1

    def test_set_data_clears_previous(self, widget: BookshelfWidget) -> None:
        book = Book(
            title="本A",
            id="book-1",
            status=BookStatus.COMPLETED,
            completed_date=date(2026, 2, 20),
        )
        data1 = BookshelfData(
            total_count=1,
            completed_count=1,
            reading_count=0,
            recent_completed=[book],
        )
        widget.set_data(data1)
        assert len(widget._book_labels) == 1

        data2 = BookshelfData(
            total_count=0,
            completed_count=0,
            reading_count=0,
            recent_completed=[],
        )
        widget.set_data(data2)
        assert len(widget._book_labels) == 1  # 空メッセージのみ

    def test_no_summary_book(self, widget: BookshelfWidget) -> None:
        book = Book(
            title="テスト本",
            id="book-1",
            status=BookStatus.COMPLETED,
            summary="",
            completed_date=date(2026, 2, 20),
        )
        data = BookshelfData(
            total_count=1,
            completed_count=1,
            reading_count=0,
            recent_completed=[book],
        )
        widget.set_data(data)
        assert len(widget._book_labels) == 1

    def test_has_books_but_no_completed(self, widget: BookshelfWidget) -> None:
        data = BookshelfData(
            total_count=3,
            completed_count=0,
            reading_count=2,
            recent_completed=[],
        )
        widget.set_data(data)
        assert widget._recent_header.isHidden()
        assert len(widget._book_labels) == 1  # "まだ読了した書籍はありません"
