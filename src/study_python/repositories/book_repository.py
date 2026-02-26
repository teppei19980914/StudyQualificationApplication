"""Book（書籍）のリポジトリ."""

from __future__ import annotations

import logging

from study_python.models.book import Book
from study_python.repositories.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class BookRepository:
    """BookのCRUD操作を提供するリポジトリ.

    Attributes:
        storage: JSON永続化ストレージ.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """BookRepositoryを初期化する.

        Args:
            storage: JSON永続化ストレージ.
        """
        self.storage = storage

    def get_all(self) -> list[Book]:
        """全Bookを取得する.

        Returns:
            Bookのリスト.
        """
        data = self.storage.load()
        return [Book.from_dict(d) for d in data]

    def get_by_id(self, book_id: str) -> Book | None:
        """IDでBookを取得する.

        Args:
            book_id: 取得するBookのID.

        Returns:
            該当するBook。見つからない場合はNone.
        """
        books = self.get_all()
        for book in books:
            if book.id == book_id:
                return book
        return None

    def add(self, book: Book) -> None:
        """Bookを追加する.

        Args:
            book: 追加するBook.
        """
        data = self.storage.load()
        data.append(book.to_dict())
        self.storage.save(data)
        logger.info(f"Added book: {book.id} - {book.title}")

    def update(self, book: Book) -> bool:
        """Bookを更新する.

        Args:
            book: 更新するBook.

        Returns:
            更新に成功した場合True.
        """
        data = self.storage.load()
        for i, d in enumerate(data):
            if d["id"] == book.id:
                data[i] = book.to_dict()
                self.storage.save(data)
                logger.info(f"Updated book: {book.id}")
                return True
        logger.warning(f"Book not found for update: {book.id}")
        return False

    def delete(self, book_id: str) -> bool:
        """Bookを削除する.

        Args:
            book_id: 削除するBookのID.

        Returns:
            削除に成功した場合True.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d["id"] != book_id]
        if len(data) < original_len:
            self.storage.save(data)
            logger.info(f"Deleted book: {book_id}")
            return True
        logger.warning(f"Book not found for delete: {book_id}")
        return False
