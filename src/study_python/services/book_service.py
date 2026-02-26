"""書籍管理のビジネスロジック."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from study_python.models.book import Book, BookStatus
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.task_repository import TaskRepository


logger = logging.getLogger(__name__)


@dataclass
class BookshelfData:
    """ダッシュボード用の本棚データ.

    Attributes:
        total_count: 登録書籍数.
        completed_count: 読了書籍数.
        reading_count: 読書中書籍数.
        recent_completed: 最近読了した書籍リスト（最大5件）.
    """

    total_count: int
    completed_count: int
    reading_count: int
    recent_completed: list[Book]


class BookService:
    """Bookのビジネスロジックを提供するサービス.

    Attributes:
        book_repo: Bookリポジトリ.
        task_repo: Taskリポジトリ（書籍削除時のbook_idクリア用）.
    """

    def __init__(self, book_repo: BookRepository, task_repo: TaskRepository) -> None:
        """BookServiceを初期化する.

        Args:
            book_repo: Bookリポジトリ.
            task_repo: Taskリポジトリ.
        """
        self.book_repo = book_repo
        self.task_repo = task_repo

    def get_all_books(self) -> list[Book]:
        """全Bookを取得する.

        Returns:
            Bookのリスト.
        """
        return self.book_repo.get_all()

    def get_book(self, book_id: str) -> Book | None:
        """IDでBookを取得する.

        Args:
            book_id: BookのID.

        Returns:
            該当するBook。見つからない場合はNone.
        """
        return self.book_repo.get_by_id(book_id)

    def create_book(self, title: str) -> Book:
        """新しいBookを作成する.

        Args:
            title: 書籍名.

        Returns:
            作成されたBook.

        Raises:
            ValueError: タイトルが空の場合.
        """
        if not title.strip():
            msg = "書籍名は必須です"
            raise ValueError(msg)
        book = Book(title=title.strip())
        self.book_repo.add(book)
        logger.info(f"Created book: {book.title}")
        return book

    def update_status(self, book_id: str, status: BookStatus) -> Book | None:
        """書籍のステータスを更新する.

        Args:
            book_id: Book ID.
            status: 新しいステータス.

        Returns:
            更新されたBook。見つからない場合はNone.
        """
        book = self.book_repo.get_by_id(book_id)
        if book is None:
            return None
        book.status = status
        book.updated_at = datetime.now()
        self.book_repo.update(book)
        logger.info(f"Updated book status: {book.title} -> {status.value}")
        return book

    def complete_book(
        self,
        book_id: str,
        summary: str,
        impressions: str,
        completed_date: date | None = None,
    ) -> Book | None:
        """書籍を読了として記録する.

        Args:
            book_id: Book ID.
            summary: 要約.
            impressions: 感想.
            completed_date: 読了日（デフォルト今日）.

        Returns:
            更新されたBook。見つからない場合はNone.
        """
        book = self.book_repo.get_by_id(book_id)
        if book is None:
            return None
        book.status = BookStatus.COMPLETED
        book.summary = summary
        book.impressions = impressions
        book.completed_date = completed_date or date.today()
        book.updated_at = datetime.now()
        self.book_repo.update(book)
        logger.info(f"Completed book: {book.title}")
        return book

    def delete_book(self, book_id: str) -> bool:
        """Bookを削除し、関連タスクのbook_idをクリアする.

        Args:
            book_id: 削除対象のBook ID.

        Returns:
            削除に成功した場合True.
        """
        result = self.book_repo.delete(book_id)
        if result:
            tasks = self.task_repo.get_all()
            cleared_count = 0
            for task in tasks:
                if task.book_id == book_id:
                    task.book_id = ""
                    task.updated_at = datetime.now()
                    self.task_repo.update(task)
                    cleared_count += 1
            if cleared_count > 0:
                logger.info(
                    f"Cleared book_id from {cleared_count} tasks "
                    f"for deleted book: {book_id}"
                )
        return result

    def get_bookshelf_data(self) -> BookshelfData:
        """ダッシュボード用の本棚データを取得する.

        Returns:
            本棚データ.
        """
        books = self.book_repo.get_all()
        completed = [b for b in books if b.status == BookStatus.COMPLETED]
        reading = [b for b in books if b.status == BookStatus.READING]

        recent = sorted(
            completed,
            key=lambda b: b.completed_date or date.min,
            reverse=True,
        )[:5]

        return BookshelfData(
            total_count=len(books),
            completed_count=len(completed),
            reading_count=len(reading),
            recent_completed=recent,
        )
