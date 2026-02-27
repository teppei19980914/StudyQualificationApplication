"""書籍ガントチャートのビジネスロジック."""

from __future__ import annotations

import logging
from datetime import date, datetime

from study_python.models.book import Book, BookStatus
from study_python.models.task import BOOK_GANTT_GOAL_ID, Task, TaskStatus
from study_python.services.book_service import BookService
from study_python.services.task_service import TaskService


logger = logging.getLogger(__name__)

# re-export for backward compatibility
__all__ = ["BOOK_GANTT_COLOR", "BOOK_GANTT_GOAL_ID", "BookGanttService"]
BOOK_GANTT_COLOR = "#F9E2AF"

_STATUS_MAP: dict[BookStatus, TaskStatus] = {
    BookStatus.UNREAD: TaskStatus.NOT_STARTED,
    BookStatus.READING: TaskStatus.IN_PROGRESS,
    BookStatus.COMPLETED: TaskStatus.COMPLETED,
}

_REVERSE_STATUS_MAP: dict[TaskStatus, BookStatus] = {
    v: k for k, v in _STATUS_MAP.items()
}


class BookGanttService:
    """書籍をガントチャートで管理するためのサービス.

    Attributes:
        _book_service: BookService.
    """

    def __init__(
        self,
        book_service: BookService,
        task_service: TaskService | None = None,
    ) -> None:
        """BookGanttServiceを初期化する.

        Args:
            book_service: BookService.
            task_service: TaskService（書籍タスク連携用、省略可）.
        """
        self._book_service = book_service
        self._task_service = task_service

    def get_scheduled_books(self) -> list[Book]:
        """スケジュール設定済みの書籍を取得する.

        Returns:
            start_dateとend_dateが設定されたBookのリスト.
        """
        return [b for b in self._book_service.get_all_books() if b.has_schedule]

    def get_unscheduled_books(self) -> list[Book]:
        """スケジュール未設定の書籍を取得する.

        Returns:
            スケジュール未設定のBookのリスト.
        """
        return [b for b in self._book_service.get_all_books() if not b.has_schedule]

    def books_to_tasks(self, books: list[Book]) -> list[Task]:
        """BookリストをTaskリストに変換する（ガントチャート表示用）.

        Args:
            books: 変換するBookのリスト.

        Returns:
            Task化されたリスト.
        """
        tasks: list[Task] = []
        for book in books:
            if not book.has_schedule:
                continue
            assert book.start_date is not None
            assert book.end_date is not None
            task = Task(
                id=book.id,
                goal_id=BOOK_GANTT_GOAL_ID,
                title=f"\U0001f4d6 {book.title}",
                start_date=book.start_date,
                end_date=book.end_date,
                status=_STATUS_MAP.get(book.status, TaskStatus.NOT_STARTED),
                progress=book.progress,
            )
            tasks.append(task)
        return tasks

    def create_book_with_schedule(
        self,
        title: str,
        start_date: date,
        end_date: date,
    ) -> Book:
        """スケジュール付きで新規書籍を作成する.

        Args:
            title: 書籍名.
            start_date: 開始日.
            end_date: 終了日.

        Returns:
            作成されたBook.

        Raises:
            ValueError: バリデーションエラー.
        """
        if end_date < start_date:
            msg = "終了日は開始日以降に設定してください"
            raise ValueError(msg)
        book = self._book_service.create_book(title)
        book.start_date = start_date
        book.end_date = end_date
        self._book_service.book_repo.update(book)
        logger.info(f"Created book with schedule: {book.title}")
        return book

    def set_book_schedule(
        self,
        book_id: str,
        start_date: date,
        end_date: date,
    ) -> Book | None:
        """既存の書籍にスケジュールを設定する.

        Args:
            book_id: Book ID.
            start_date: 開始日.
            end_date: 終了日.

        Returns:
            更新されたBook。見つからない場合はNone.

        Raises:
            ValueError: 日付が不正な場合.
        """
        if end_date < start_date:
            msg = "終了日は開始日以降に設定してください"
            raise ValueError(msg)
        book = self._book_service.get_book(book_id)
        if book is None:
            return None
        book.start_date = start_date
        book.end_date = end_date
        book.updated_at = datetime.now()
        self._book_service.book_repo.update(book)
        logger.info(f"Set schedule for book: {book.title}")
        return book

    def update_book_schedule(
        self,
        book_id: str,
        title: str,
        start_date: date,
        end_date: date,
        progress: int,
    ) -> Book | None:
        """書籍のスケジュール情報を更新する.

        ステータスは進捗率から自動決定される:
        - 0%: 未読
        - 1-99%: 読書中
        - 100%: 読了

        Args:
            book_id: Book ID.
            title: 書籍名.
            start_date: 開始日.
            end_date: 終了日.
            progress: 進捗率（0-100）.

        Returns:
            更新されたBook。見つからない場合はNone.

        Raises:
            ValueError: バリデーションエラー.
        """
        if not title.strip():
            msg = "書籍名は必須です"
            raise ValueError(msg)
        if not 0 <= progress <= 100:
            msg = f"進捗率は0-100の範囲で指定してください: {progress}"
            raise ValueError(msg)
        if end_date < start_date:
            msg = "終了日は開始日以降に設定してください"
            raise ValueError(msg)

        book = self._book_service.get_book(book_id)
        if book is None:
            return None

        book.title = title
        book.start_date = start_date
        book.end_date = end_date
        book.progress = progress
        book.status = self._book_status_from_progress(progress)
        book.updated_at = datetime.now()

        self._book_service.book_repo.update(book)
        logger.info(f"Updated book schedule: {book.title}")
        return book

    def clear_book_schedule(self, book_id: str) -> Book | None:
        """書籍のスケジュールをクリアする（書籍自体は残す）.

        Args:
            book_id: Book ID.

        Returns:
            更新されたBook。見つからない場合はNone.
        """
        book = self._book_service.get_book(book_id)
        if book is None:
            return None

        book.start_date = None
        book.end_date = None
        book.progress = 0
        book.updated_at = datetime.now()
        self._book_service.book_repo.update(book)
        logger.info(f"Cleared schedule for book: {book.title}")
        return book

    @staticmethod
    def book_status_to_task_status(book_status: BookStatus) -> TaskStatus:
        """BookStatusをTaskStatusに変換する.

        Args:
            book_status: 書籍ステータス.

        Returns:
            対応するTaskStatus.
        """
        return _STATUS_MAP.get(book_status, TaskStatus.NOT_STARTED)

    @staticmethod
    def task_status_to_book_status(task_status: TaskStatus) -> BookStatus:
        """TaskStatusをBookStatusに変換する.

        Args:
            task_status: タスクステータス.

        Returns:
            対応するBookStatus.
        """
        return _REVERSE_STATUS_MAP.get(task_status, BookStatus.UNREAD)

    def sync_book_progress(self, book_id: str) -> None:
        """書籍タスクの進捗平均を書籍に同期する.

        タスクの進捗率平均 → book.progress
        進捗からstatus自動決定
        タスクのmin(start_date)/max(end_date) → book日付
        タスク0件: progress=0, start_date=None, end_date=None

        Args:
            book_id: 同期対象のBook ID.
        """
        if self._task_service is None:
            return
        book = self._book_service.get_book(book_id)
        if book is None:
            return
        tasks = self._task_service.get_tasks_for_book(book_id)
        if not tasks:
            book.progress = 0
            book.status = self._book_status_from_progress(0)
            book.start_date = None
            book.end_date = None
        else:
            avg_progress = round(sum(t.progress for t in tasks) / len(tasks))
            book.progress = avg_progress
            book.status = self._book_status_from_progress(avg_progress)
            book.start_date = min(t.start_date for t in tasks)
            book.end_date = max(t.end_date for t in tasks)
        book.updated_at = datetime.now()
        self._book_service.book_repo.update(book)
        logger.info(f"Synced book progress: {book.title} -> {book.progress}%")

    def get_all_book_tasks(self) -> list[Task]:
        """全書籍タスクを取得する.

        Returns:
            BOOK_GANTT_GOAL_IDに紐づくTaskのリスト.
        """
        if self._task_service is None:
            return []
        return self._task_service.get_tasks_for_goal(BOOK_GANTT_GOAL_ID)

    @staticmethod
    def _book_status_from_progress(progress: int) -> BookStatus:
        """進捗率からBookStatusを決定する.

        Args:
            progress: 進捗率（0-100）.

        Returns:
            対応するBookStatus.
        """
        if progress == 0:
            return BookStatus.UNREAD
        if progress == 100:
            return BookStatus.COMPLETED
        return BookStatus.READING
