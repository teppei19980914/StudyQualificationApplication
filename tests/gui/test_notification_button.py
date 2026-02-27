"""NotificationButtonのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.notification_button import NotificationButton
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository
from study_python.services.notification_service import NotificationService


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


@pytest.fixture
def notification_service(tmp_path: Path) -> NotificationService:
    storage = JsonStorage(tmp_path / "notifications.json")
    repo = NotificationRepository(storage)
    return NotificationService(repo)


class TestNotificationButton:
    """NotificationButtonのテスト."""

    def test_create_button(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        assert btn is not None

    def test_fixed_height(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        assert btn.minimumHeight() == 36
        assert btn.maximumHeight() == 36

    def test_tooltip(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        assert btn.toolTip() == "通知"

    def test_initial_badge_hidden(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        assert btn._badge_label.isHidden()

    def test_update_badge_positive(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        btn.update_badge(5)
        assert not btn._badge_label.isHidden()
        assert btn._badge_label.text() == "5"

    def test_update_badge_zero(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        btn.update_badge(5)
        assert not btn._badge_label.isHidden()
        btn.update_badge(0)
        assert btn._badge_label.isHidden()

    def test_update_badge_over_99(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        btn.update_badge(100)
        assert btn._badge_label.text() == "99+"
        assert not btn._badge_label.isHidden()

    def test_update_badge_exactly_99(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        btn.update_badge(99)
        assert btn._badge_label.text() == "99"

    def test_bell_emoji(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        btn = NotificationButton(theme_manager, notification_service)
        qtbot.addWidget(btn)
        assert "\U0001f514" in btn.text()
