"""NotificationServiceのテスト."""

import json
from pathlib import Path

import pytest

from study_python.models.notification import Notification, NotificationType
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository
from study_python.services.motivation_calculator import MilestoneData
from study_python.services.notification_service import NotificationService


@pytest.fixture
def repo(tmp_path: Path) -> NotificationRepository:
    """テスト用リポジトリ."""
    storage = JsonStorage(tmp_path / "notifications.json")
    return NotificationRepository(storage)


@pytest.fixture
def service(repo: NotificationRepository) -> NotificationService:
    """テスト用サービス."""
    return NotificationService(repo)


class TestNotificationServiceBasic:
    """基本操作のテスト."""

    def test_get_all_notifications(
        self, service: NotificationService, repo: NotificationRepository
    ):
        n = Notification(
            notification_type=NotificationType.SYSTEM,
            title="テスト",
            message="メッセージ",
        )
        repo.add(n)
        result = service.get_all_notifications()
        assert len(result) == 1

    def test_get_unread_count(
        self, service: NotificationService, repo: NotificationRepository
    ):
        n1 = Notification(
            notification_type=NotificationType.SYSTEM,
            title="未読",
            message="msg",
            is_read=False,
        )
        n2 = Notification(
            notification_type=NotificationType.SYSTEM,
            title="既読",
            message="msg",
            is_read=True,
        )
        repo.add(n1)
        repo.add(n2)
        assert service.get_unread_count() == 1

    def test_mark_as_read(
        self, service: NotificationService, repo: NotificationRepository
    ):
        n = Notification(
            notification_type=NotificationType.SYSTEM,
            title="テスト",
            message="msg",
        )
        repo.add(n)
        assert service.mark_as_read(n.id) is True
        assert service.get_unread_count() == 0

    def test_mark_all_as_read(
        self, service: NotificationService, repo: NotificationRepository
    ):
        for i in range(3):
            repo.add(
                Notification(
                    notification_type=NotificationType.SYSTEM,
                    title=f"通知{i}",
                    message="msg",
                )
            )
        count = service.mark_all_as_read()
        assert count == 3
        assert service.get_unread_count() == 0


class TestAchievementNotifications:
    """実績達成通知のテスト."""

    def test_creates_new_total_hours(self, service: NotificationService):
        """累計時間の閾値達成で通知が生成される."""
        data = MilestoneData(total_hours=12.0, study_days=0, current_streak=0)
        created = service.check_and_create_achievement_notifications(data)
        # 1, 5, 10 時間の3つ
        titles = [n.title for n in created]
        assert "累計1時間達成！" in titles
        assert "累計5時間達成！" in titles
        assert "累計10時間達成！" in titles
        assert len([n for n in created if "時間" in n.title]) == 3

    def test_creates_new_study_days(self, service: NotificationService):
        """学習日数の閾値達成で通知が生成される."""
        data = MilestoneData(total_hours=0.0, study_days=8, current_streak=0)
        created = service.check_and_create_achievement_notifications(data)
        titles = [n.title for n in created]
        assert "学習3日達成！" in titles
        assert "学習7日達成！" in titles

    def test_creates_new_streak(self, service: NotificationService):
        """連続学習の閾値達成で通知が生成される."""
        data = MilestoneData(total_hours=0.0, study_days=0, current_streak=5)
        created = service.check_and_create_achievement_notifications(data)
        titles = [n.title for n in created]
        assert "連続3日達成！" in titles

    def test_skips_existing(self, service: NotificationService):
        """既に通知済みの実績はスキップする."""
        data = MilestoneData(total_hours=12.0, study_days=0, current_streak=0)
        first = service.check_and_create_achievement_notifications(data)
        assert len(first) == 3

        # 2回目は同じデータで新規通知は生成されない
        second = service.check_and_create_achievement_notifications(data)
        assert len(second) == 0

    def test_all_types(self, service: NotificationService):
        """3タイプとも通知される."""
        data = MilestoneData(total_hours=2.0, study_days=4, current_streak=4)
        created = service.check_and_create_achievement_notifications(data)
        types = {n.dedup_key.split(":")[0] for n in created}
        assert "total_hours" in types
        assert "study_days" in types
        assert "streak" in types

    def test_dedup_key_format(self, service: NotificationService):
        """dedup_keyが正しい形式である."""
        data = MilestoneData(total_hours=6.0, study_days=0, current_streak=0)
        created = service.check_and_create_achievement_notifications(data)
        keys = [n.dedup_key for n in created]
        assert "total_hours:1" in keys
        assert "total_hours:5" in keys

    def test_no_milestones(self, service: NotificationService):
        """閾値未達で通知なし."""
        data = MilestoneData(total_hours=0.0, study_days=0, current_streak=0)
        created = service.check_and_create_achievement_notifications(data)
        assert len(created) == 0

    def test_notification_type_is_achievement(self, service: NotificationService):
        """生成される通知のタイプがACHIEVEMENTである."""
        data = MilestoneData(total_hours=2.0, study_days=0, current_streak=0)
        created = service.check_and_create_achievement_notifications(data)
        for n in created:
            assert n.notification_type == NotificationType.ACHIEVEMENT

    def test_incremental_achievement(self, service: NotificationService):
        """値が増加した時に新しい閾値の通知のみ生成される."""
        # まず5時間まで
        data1 = MilestoneData(total_hours=6.0, study_days=0, current_streak=0)
        first = service.check_and_create_achievement_notifications(data1)
        assert len(first) == 2  # 1h, 5h

        # 次に25時間まで
        data2 = MilestoneData(total_hours=26.0, study_days=0, current_streak=0)
        second = service.check_and_create_achievement_notifications(data2)
        assert len(second) == 2  # 10h, 25h
        titles = [n.title for n in second]
        assert "累計10時間達成！" in titles
        assert "累計25時間達成！" in titles


class TestSystemNotifications:
    """システム通知のテスト."""

    def test_creates_new(self, tmp_path: Path, repo: NotificationRepository):
        """新規システム通知が読み込まれる."""
        sys_path = tmp_path / "system_notifications.json"
        sys_path.write_text(
            json.dumps(
                [
                    {
                        "dedup_key": "system:v1.0",
                        "title": "v1.0リリース",
                        "message": "ご利用ありがとうございます",
                    }
                ]
            ),
            encoding="utf-8",
        )
        service = NotificationService(repo, system_notifications_path=sys_path)
        created = service.load_system_notifications()
        assert len(created) == 1
        assert created[0].title == "v1.0リリース"
        assert created[0].notification_type == NotificationType.SYSTEM

    def test_skips_existing(self, tmp_path: Path, repo: NotificationRepository):
        """既に読み込み済みのシステム通知はスキップする."""
        sys_path = tmp_path / "system_notifications.json"
        sys_path.write_text(
            json.dumps(
                [{"dedup_key": "system:v1.0", "title": "v1.0", "message": "msg"}]
            ),
            encoding="utf-8",
        )
        service = NotificationService(repo, system_notifications_path=sys_path)
        first = service.load_system_notifications()
        assert len(first) == 1
        second = service.load_system_notifications()
        assert len(second) == 0

    def test_no_file(self, tmp_path: Path, repo: NotificationRepository):
        """ファイルが存在しない場合は空リスト."""
        service = NotificationService(
            repo,
            system_notifications_path=tmp_path / "nonexistent.json",
        )
        assert service.load_system_notifications() == []

    def test_invalid_json(self, tmp_path: Path, repo: NotificationRepository):
        """不正なJSONの場合は空リスト."""
        sys_path = tmp_path / "system_notifications.json"
        sys_path.write_text("invalid json", encoding="utf-8")
        service = NotificationService(repo, system_notifications_path=sys_path)
        assert service.load_system_notifications() == []

    def test_no_path(self, repo: NotificationRepository):
        """パスがNoneの場合は空リスト."""
        service = NotificationService(repo, system_notifications_path=None)
        assert service.load_system_notifications() == []

    def test_skips_empty_dedup_key(self, tmp_path: Path, repo: NotificationRepository):
        """dedup_keyが空のエントリはスキップする."""
        sys_path = tmp_path / "system_notifications.json"
        sys_path.write_text(
            json.dumps([{"dedup_key": "", "title": "空キー", "message": "msg"}]),
            encoding="utf-8",
        )
        service = NotificationService(repo, system_notifications_path=sys_path)
        assert service.load_system_notifications() == []


class TestNotificationsEnabled:
    """通知有効/無効設定のテスト."""

    def test_default_enabled(self, repo: NotificationRepository):
        """デフォルトで通知は有効."""
        service = NotificationService(repo)
        assert service.notifications_enabled is True

    def test_enabled_without_settings_path(self, repo: NotificationRepository):
        """settings_path=Noneの場合は常にTrue."""
        service = NotificationService(repo, settings_path=None)
        assert service.notifications_enabled is True

    def test_enabled_no_settings_file(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """設定ファイルが存在しない場合はTrue."""
        service = NotificationService(repo, settings_path=tmp_path / "settings.json")
        assert service.notifications_enabled is True

    def test_read_enabled_from_settings(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """設定ファイルからTrue読み込み."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"notifications_enabled": True}), encoding="utf-8"
        )
        service = NotificationService(repo, settings_path=settings_path)
        assert service.notifications_enabled is True

    def test_read_disabled_from_settings(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """設定ファイルからFalse読み込み."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            json.dumps({"notifications_enabled": False}), encoding="utf-8"
        )
        service = NotificationService(repo, settings_path=settings_path)
        assert service.notifications_enabled is False

    def test_set_notifications_enabled_true(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """通知を有効に設定できる."""
        settings_path = tmp_path / "settings.json"
        service = NotificationService(repo, settings_path=settings_path)
        service.set_notifications_enabled(True)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["notifications_enabled"] is True

    def test_set_notifications_enabled_false(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """通知を無効に設定できる."""
        settings_path = tmp_path / "settings.json"
        service = NotificationService(repo, settings_path=settings_path)
        service.set_notifications_enabled(False)
        assert service.notifications_enabled is False

    def test_set_enabled_no_settings_path(self, repo: NotificationRepository):
        """settings_path=Noneの場合はset_notifications_enabledがエラーにならない."""
        service = NotificationService(repo, settings_path=None)
        service.set_notifications_enabled(False)
        # エラーなし、値は変わらない
        assert service.notifications_enabled is True

    def test_preserves_other_settings(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """他の設定値を保持する."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
        service = NotificationService(repo, settings_path=settings_path)
        service.set_notifications_enabled(False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["theme"] == "dark"
        assert data["notifications_enabled"] is False

    def test_invalid_json_defaults_to_true(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """不正JSONの場合はTrueを返す."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("invalid json", encoding="utf-8")
        service = NotificationService(repo, settings_path=settings_path)
        assert service.notifications_enabled is True

    def test_achievement_skipped_when_disabled(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """通知無効時にachievement通知がスキップされる."""
        settings_path = tmp_path / "settings.json"
        service = NotificationService(repo, settings_path=settings_path)
        service.set_notifications_enabled(False)

        data = MilestoneData(total_hours=100.0, study_days=50, current_streak=30)
        created = service.check_and_create_achievement_notifications(data)
        assert len(created) == 0

    def test_achievement_works_when_enabled(
        self, tmp_path: Path, repo: NotificationRepository
    ):
        """通知有効時にachievement通知が正常に生成される."""
        settings_path = tmp_path / "settings.json"
        service = NotificationService(repo, settings_path=settings_path)
        service.set_notifications_enabled(True)

        data = MilestoneData(total_hours=2.0, study_days=0, current_streak=0)
        created = service.check_and_create_achievement_notifications(data)
        assert len(created) == 1
        assert "累計1時間達成！" in created[0].title
