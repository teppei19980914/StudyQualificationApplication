"""GoalPageとGanttPageのテスト."""

from datetime import date
from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from study_python.gui.pages.gantt_page import GanttPage
from study_python.gui.pages.goal_page import GoalCard, GoalPage
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.goal import Goal, WhenType
from study_python.repositories.book_repository import BookRepository
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.book_service import BookService
from study_python.services.goal_service import GoalService
from study_python.services.task_service import TaskService


@pytest.fixture
def services(tmp_path: Path):
    goal_storage = JsonStorage(tmp_path / "goals.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    goal_repo = GoalRepository(goal_storage)
    task_repo = TaskRepository(task_storage)
    goal_service = GoalService(goal_repo, task_repo)
    task_service = TaskService(task_repo)
    theme_manager = ThemeManager(tmp_path / "settings.json")
    return goal_service, task_service, theme_manager


class TestGoalCard:
    """GoalCardのテスト."""

    def test_create_card(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="テスト理由",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="Udemy",
            color="#4A9EFF",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        assert card.objectName() == "goal_card"

    def test_card_edit_signal(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        with qtbot.waitSignal(card.edit_requested, timeout=1000):
            card.edit_requested.emit(goal.id)

    def test_card_delete_signal(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        with qtbot.waitSignal(card.delete_requested, timeout=1000):
            card.delete_requested.emit(goal.id)

    def test_card_period_type_format(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="3ヶ月",
            when_type=WhenType.PERIOD,
            what="TOEIC",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        assert card._format_when() == "目標: 3ヶ月"

    def test_card_date_type_format(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        assert "2026/06/30" in card._format_when()


class TestGoalPage:
    """GoalPageのテスト."""

    def test_create_page(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        assert page is not None

    def test_empty_state(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        # 空の状態でも表示できる
        assert page._cards_layout.count() >= 1  # stretch item

    def test_theme_changed(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        page.on_theme_changed()  # エラーなく実行

    def test_goals_changed_signal_exists(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        # Signal exists
        assert hasattr(page, "goals_changed")


class TestGanttPage:
    """GanttPageのテスト."""

    def test_create_page(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        assert page is not None

    def test_refresh_empty(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()  # エラーなく実行

    def test_refresh_with_goals(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        # 「すべてのタスク」 + 個別目標1つ = 2
        assert page._selector_combo.count() == 2

    def test_theme_changed(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.on_theme_changed()

    def test_selector_with_multiple_goals(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        goal_service.create_goal(
            why="test1",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="目標1",
            how="test",
        )
        goal_service.create_goal(
            why="test2",
            when_target="2026-12-31",
            when_type=WhenType.DATE,
            what="目標2",
            how="test",
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        # 「すべてのタスク」 + 個別目標2つ = 3
        assert page._selector_combo.count() == 3

    def test_all_tasks_option_in_combo(self, qtbot, services):
        """「すべてのタスク」がコンボの先頭にあることを確認."""
        goal_service, task_service, theme_manager = services
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        assert page._selector_combo.itemData(0) == "__all_tasks__"
        assert "すべてのタスク" in page._selector_combo.itemText(0)

    def test_refresh_all_tasks_mode(self, qtbot, services):
        """「すべてのタスク」選択時に全タスクが表示される."""
        goal_service, task_service, theme_manager = services
        goal1 = goal_service.create_goal(
            why="test1",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="目標1",
            how="test",
        )
        goal2 = goal_service.create_goal(
            why="test2",
            when_target="2026-12-31",
            when_type=WhenType.DATE,
            what="目標2",
            how="test",
        )
        task_service.create_task(
            goal_id=goal1.id,
            title="タスクA",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        task_service.create_task(
            goal_id=goal2.id,
            title="タスクB",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 15),
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        # 先頭の「すべてのタスク」を選択
        page._selector_combo.setCurrentIndex(0)
        page._refresh_chart()
        # エラーなく表示される

    def test_combo_preserves_selection(self, qtbot, services):
        """コンボの選択が更新後も維持される."""
        goal_service, task_service, theme_manager = services
        goal = goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        # 個別目標を選択
        page._selector_combo.setCurrentIndex(1)
        assert page._selector_combo.currentData() == goal.id
        # リフレッシュ後も選択維持
        page.refresh()
        assert page._selector_combo.currentData() == goal.id

    def test_selector_label_is_display(self, qtbot, services):
        """セレクタラベルが「表示:」であることを確認."""
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        assert page._selector_label.text() == "表示:"

    def test_empty_state_message(self, qtbot, services):
        """目標も書籍もない場合のメッセージ表示."""
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        assert "登録してください" in page._selector_combo.itemText(0)
        assert not page._add_task_btn.isEnabled()


class TestGanttPageUnifiedSelector:
    """GanttPageの統合セレクタのテスト."""

    @pytest.fixture
    def book_services(self, tmp_path: Path):
        goal_storage = JsonStorage(tmp_path / "goals.json")
        task_storage = JsonStorage(tmp_path / "tasks.json")
        book_storage = JsonStorage(tmp_path / "books.json")
        goal_repo = GoalRepository(goal_storage)
        task_repo = TaskRepository(task_storage)
        book_repo = BookRepository(book_storage)
        goal_service = GoalService(goal_repo, task_repo)
        task_service = TaskService(task_repo)
        book_service = BookService(book_repo, task_repo)
        theme_manager = ThemeManager(tmp_path / "settings.json")
        return goal_service, task_service, theme_manager, book_service

    def test_unified_selector_shows_goals_and_books(self, qtbot, book_services):
        """セレクタが常に目標と書籍の両方を表示することを確認."""
        goal_service, task_service, theme_manager, book_service = book_services
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="test",
        )
        book_service.create_book("Python入門")
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        # すべてのタスク + AWS資格 + すべての書籍 + Python入門 = 4
        assert page._selector_combo.count() == 4

    def test_selector_order(self, qtbot, book_services):
        """セレクタの項目順序を確認: すべてのタスク→各目標→すべての書籍→各書籍."""
        goal_service, task_service, theme_manager, book_service = book_services
        goal = goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="test",
        )
        book = book_service.create_book("Python入門")
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        assert page._selector_combo.itemData(0) == "__all_tasks__"
        assert page._selector_combo.itemData(1) == goal.id
        assert page._selector_combo.itemData(2) == "__all_books__"
        assert page._selector_combo.itemData(3) == book.id

    def test_all_books_option(self, qtbot, book_services):
        """「すべての書籍」がセレクタに含まれることを確認."""
        goal_service, task_service, theme_manager, book_service = book_services
        book_service.create_book("Python入門")
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        found = False
        for i in range(page._selector_combo.count()):
            if page._selector_combo.itemData(i) == "__all_books__":
                found = True
                assert "すべての書籍" in page._selector_combo.itemText(i)
                break
        assert found

    def test_individual_books_in_selector(self, qtbot, book_services):
        """個別の書籍がセレクタに含まれることを確認."""
        goal_service, task_service, theme_manager, book_service = book_services
        book1 = book_service.create_book("Python入門")
        book2 = book_service.create_book("Django実践")
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        book_ids = [
            page._selector_combo.itemData(i)
            for i in range(page._selector_combo.count())
        ]
        assert book1.id in book_ids
        assert book2.id in book_ids

    def test_all_tasks_includes_book_tasks(self, qtbot, book_services):
        """「すべてのタスク」が目標タスクと書籍タスクの両方を含む."""
        from study_python.models.task import BOOK_GANTT_GOAL_ID

        goal_service, task_service, theme_manager, book_service = book_services
        goal = goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        book = book_service.create_book("Python入門")
        task_service.create_task(
            goal_id=goal.id,
            title="目標タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        task_service.create_task(
            goal_id=BOOK_GANTT_GOAL_ID,
            title="書籍タスク",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 15),
            book_id=book.id,
        )
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        # 先頭の「すべてのタスク」を選択
        page._selector_combo.setCurrentIndex(0)
        page._refresh_chart()
        # エラーなく表示される

    def test_empty_without_goals_and_books(self, qtbot, book_services):
        """目標も書籍もない場合にメッセージが表示される."""
        goal_service, task_service, theme_manager, book_service = book_services
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        assert "登録してください" in page._selector_combo.itemText(0)
        assert not page._add_task_btn.isEnabled()

    def test_goals_only_no_books_section(self, qtbot, book_services):
        """書籍が0件の場合、「すべての書籍」が表示されない."""
        goal_service, task_service, theme_manager, book_service = book_services
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        for i in range(page._selector_combo.count()):
            assert page._selector_combo.itemData(i) != "__all_books__"

    def test_add_button_text_unified(self, qtbot, book_services):
        """ボタンテキストが常に「タスク追加」であることを確認."""
        goal_service, task_service, theme_manager, book_service = book_services
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        assert "タスク" in page._add_task_btn.text()

    def test_selector_preserves_selection(self, qtbot, book_services):
        """セレクタの選択が更新後も維持される."""
        goal_service, task_service, theme_manager, book_service = book_services
        book = book_service.create_book("Python入門")
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        # 書籍を選択
        for i in range(page._selector_combo.count()):
            if page._selector_combo.itemData(i) == book.id:
                page._selector_combo.setCurrentIndex(i)
                break
        assert page._selector_combo.currentData() == book.id
        # リフレッシュ後も選択維持
        page.refresh()
        assert page._selector_combo.currentData() == book.id

    def test_refresh_individual_book(self, qtbot, book_services):
        """個別書籍選択時にチャートが表示される."""
        goal_service, task_service, theme_manager, book_service = book_services
        book = book_service.create_book("Python入門")
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()
        # 書籍を選択
        for i in range(page._selector_combo.count()):
            if page._selector_combo.itemData(i) == book.id:
                page._selector_combo.setCurrentIndex(i)
                break
        page._refresh_chart()
        # エラーなく表示される

    def test_selector_label_is_display(self, qtbot, book_services):
        """セレクタラベルが「表示:」であることを確認."""
        goal_service, task_service, theme_manager, book_service = book_services
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        assert page._selector_label.text() == "表示:"

    def test_no_tab_bar(self, qtbot, book_services):
        """タブバーが存在しないことを確認."""
        goal_service, task_service, theme_manager, book_service = book_services
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        assert not hasattr(page, "_tab_bar")

    def test_add_task_shows_selection_dialog(self, qtbot, book_services, monkeypatch):
        """book_serviceがある場合、タスク追加で選択ダイアログが表示される."""
        from unittest.mock import patch

        goal_service, task_service, theme_manager, book_service = book_services
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(
            goal_service, task_service, theme_manager, book_service=book_service
        )
        qtbot.addWidget(page)
        page.refresh()

        # QMessageBox.exec をモックしてキャンセルを返す
        with (
            patch.object(QMessageBox, "exec", return_value=None),
            patch.object(QMessageBox, "clickedButton", return_value=None),
        ):
            page._on_add_task()
            # キャンセルの場合は何も起きない（エラーなし）

    def test_add_task_without_book_service_goes_to_goal(
        self, qtbot, services, monkeypatch
    ):
        """book_serviceなしの場合、タスク追加で直接目標タスク追加になる."""
        from unittest.mock import MagicMock

        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        mock_add_goal = MagicMock()
        monkeypatch.setattr(page, "_on_add_goal_task", mock_add_goal)
        page._on_add_task()
        mock_add_goal.assert_called_once()
