"""Bookモデルのテスト."""

from datetime import date, datetime

import pytest

from study_python.models.book import Book, BookStatus


class TestBookCreation:
    """Book生成のテスト."""

    def test_create_with_title(self) -> None:
        book = Book(title="Python入門")
        assert book.title == "Python入門"
        assert book.status == BookStatus.UNREAD
        assert book.summary == ""
        assert book.impressions == ""
        assert book.completed_date is None
        assert book.id != ""

    def test_create_with_all_fields(self) -> None:
        book = Book(
            title="統計学基礎",
            id="test-id",
            status=BookStatus.COMPLETED,
            summary="要約テスト",
            impressions="感想テスト",
            completed_date=date(2026, 2, 20),
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 2, 20),
        )
        assert book.title == "統計学基礎"
        assert book.id == "test-id"
        assert book.status == BookStatus.COMPLETED
        assert book.summary == "要約テスト"
        assert book.impressions == "感想テスト"
        assert book.completed_date == date(2026, 2, 20)

    def test_default_id_is_uuid(self) -> None:
        book = Book(title="テスト")
        assert len(book.id) == 36  # UUID format

    def test_default_timestamps(self) -> None:
        book = Book(title="テスト")
        assert isinstance(book.created_at, datetime)
        assert isinstance(book.updated_at, datetime)


class TestBookValidation:
    """Bookバリデーションのテスト."""

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValueError, match="書籍名は必須です"):
            Book(title="")

    def test_whitespace_title_raises(self) -> None:
        with pytest.raises(ValueError, match="書籍名は必須です"):
            Book(title="   ")

    def test_valid_title(self) -> None:
        book = Book(title="Python")
        assert book.title == "Python"


class TestBookStatus:
    """BookStatusのテスト."""

    def test_unread_value(self) -> None:
        assert BookStatus.UNREAD.value == "unread"

    def test_reading_value(self) -> None:
        assert BookStatus.READING.value == "reading"

    def test_completed_value(self) -> None:
        assert BookStatus.COMPLETED.value == "completed"

    def test_from_string(self) -> None:
        assert BookStatus("unread") == BookStatus.UNREAD
        assert BookStatus("reading") == BookStatus.READING
        assert BookStatus("completed") == BookStatus.COMPLETED

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            BookStatus("invalid")


class TestBookSerialization:
    """Bookシリアライズのテスト."""

    def test_to_dict(self) -> None:
        book = Book(
            title="テスト本",
            id="book-1",
            status=BookStatus.COMPLETED,
            summary="要約",
            impressions="感想",
            completed_date=date(2026, 2, 20),
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 2, 20, 12, 0, 0),
        )
        d = book.to_dict()
        assert d["id"] == "book-1"
        assert d["title"] == "テスト本"
        assert d["status"] == "completed"
        assert d["summary"] == "要約"
        assert d["impressions"] == "感想"
        assert d["completed_date"] == "2026-02-20"
        assert d["created_at"] == "2026-01-01T10:00:00"
        assert d["updated_at"] == "2026-02-20T12:00:00"

    def test_to_dict_none_completed_date(self) -> None:
        book = Book(title="テスト本", id="book-2")
        d = book.to_dict()
        assert d["completed_date"] is None

    def test_from_dict(self) -> None:
        data = {
            "id": "book-1",
            "title": "テスト本",
            "status": "completed",
            "summary": "要約",
            "impressions": "感想",
            "completed_date": "2026-02-20",
            "created_at": "2026-01-01T10:00:00",
            "updated_at": "2026-02-20T12:00:00",
        }
        book = Book.from_dict(data)
        assert book.id == "book-1"
        assert book.title == "テスト本"
        assert book.status == BookStatus.COMPLETED
        assert book.summary == "要約"
        assert book.impressions == "感想"
        assert book.completed_date == date(2026, 2, 20)

    def test_from_dict_none_completed_date(self) -> None:
        data = {
            "id": "book-2",
            "title": "テスト本",
            "status": "unread",
            "completed_date": None,
            "created_at": "2026-01-01T10:00:00",
            "updated_at": "2026-01-01T10:00:00",
        }
        book = Book.from_dict(data)
        assert book.completed_date is None

    def test_from_dict_missing_optional_fields(self) -> None:
        data = {
            "id": "book-3",
            "title": "テスト本",
            "status": "unread",
            "created_at": "2026-01-01T10:00:00",
            "updated_at": "2026-01-01T10:00:00",
        }
        book = Book.from_dict(data)
        assert book.summary == ""
        assert book.impressions == ""
        assert book.completed_date is None

    def test_roundtrip(self) -> None:
        original = Book(
            title="ラウンドトリップ",
            status=BookStatus.READING,
            summary="要約テスト",
            impressions="感想テスト",
            completed_date=date(2026, 3, 1),
        )
        restored = Book.from_dict(original.to_dict())
        assert restored.title == original.title
        assert restored.status == original.status
        assert restored.summary == original.summary
        assert restored.impressions == original.impressions
        assert restored.completed_date == original.completed_date

    def test_roundtrip_no_completed_date(self) -> None:
        original = Book(title="未読本")
        restored = Book.from_dict(original.to_dict())
        assert restored.title == original.title
        assert restored.completed_date is None


class TestBookScheduleFields:
    """スケジュールフィールドのテスト."""

    def test_default_schedule_is_none(self) -> None:
        book = Book(title="テスト")
        assert book.start_date is None
        assert book.end_date is None
        assert book.progress == 0

    def test_create_with_schedule(self) -> None:
        book = Book(
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=50,
        )
        assert book.start_date == date(2026, 3, 1)
        assert book.end_date == date(2026, 3, 31)
        assert book.progress == 50

    def test_has_schedule_true(self) -> None:
        book = Book(
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )
        assert book.has_schedule is True

    def test_has_schedule_false_no_dates(self) -> None:
        book = Book(title="テスト")
        assert book.has_schedule is False

    def test_has_schedule_false_partial(self) -> None:
        book = Book(title="テスト", start_date=date(2026, 3, 1))
        assert book.has_schedule is False

    def test_progress_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="進捗率は0-100"):
            Book(title="テスト", progress=-1)

    def test_progress_above_100_raises(self) -> None:
        with pytest.raises(ValueError, match="進捗率は0-100"):
            Book(title="テスト", progress=101)

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            Book(
                title="テスト",
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 1),
            )

    def test_to_dict_with_schedule(self) -> None:
        book = Book(
            title="テスト",
            id="book-1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=50,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        d = book.to_dict()
        assert d["start_date"] == "2026-03-01"
        assert d["end_date"] == "2026-03-31"
        assert d["progress"] == 50

    def test_to_dict_without_schedule(self) -> None:
        book = Book(title="テスト", id="book-2")
        d = book.to_dict()
        assert d["start_date"] is None
        assert d["end_date"] is None
        assert d["progress"] == 0

    def test_from_dict_with_schedule(self) -> None:
        data = {
            "id": "book-1",
            "title": "テスト",
            "status": "reading",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "progress": 50,
            "created_at": "2026-01-01T10:00:00",
            "updated_at": "2026-01-01T10:00:00",
        }
        book = Book.from_dict(data)
        assert book.start_date == date(2026, 3, 1)
        assert book.end_date == date(2026, 3, 31)
        assert book.progress == 50

    def test_from_dict_backward_compatible(self) -> None:
        """旧データ（スケジュールフィールドなし）からの読み込み."""
        data = {
            "id": "book-old",
            "title": "旧データ",
            "status": "unread",
            "created_at": "2026-01-01T10:00:00",
            "updated_at": "2026-01-01T10:00:00",
        }
        book = Book.from_dict(data)
        assert book.start_date is None
        assert book.end_date is None
        assert book.progress == 0

    def test_roundtrip_with_schedule(self) -> None:
        original = Book(
            title="往復テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            progress=75,
        )
        restored = Book.from_dict(original.to_dict())
        assert restored.start_date == original.start_date
        assert restored.end_date == original.end_date
        assert restored.progress == original.progress
