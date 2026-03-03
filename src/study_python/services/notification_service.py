"""通知のビジネスロジック."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from study_python.models.notification import Notification, NotificationType
from study_python.repositories.notification_repository import NotificationRepository
from study_python.services.motivation_calculator import (
    MilestoneData,
    MilestoneType,
)


logger = logging.getLogger(__name__)

# 実績通知の閾値（motivation_calculator.py と同じ値）
_TOTAL_HOURS_THRESHOLDS = [1, 5, 10, 25, 50, 100, 250, 500, 1000]
_STUDY_DAYS_THRESHOLDS = [3, 7, 14, 30, 60, 100, 200, 365]
_STREAK_THRESHOLDS = [3, 7, 14, 30, 60, 100]

# 実績通知のメッセージテンプレート
_ACHIEVEMENT_TITLES: dict[MilestoneType, str] = {
    MilestoneType.TOTAL_HOURS: "累計{value}時間達成！",
    MilestoneType.STUDY_DAYS: "学習{value}日達成！",
    MilestoneType.STREAK: "連続{value}日達成！",
}

_ACHIEVEMENT_MESSAGES: dict[MilestoneType, str] = {
    MilestoneType.TOTAL_HOURS: "累計学習時間が{value}時間に到達しました！",
    MilestoneType.STUDY_DAYS: "学習日数が{value}日に到達しました！",
    MilestoneType.STREAK: "連続学習日数が{value}日に到達しました！",
}

# 閾値マッピング（MilestoneType → 閾値リスト）
_THRESHOLD_MAP: dict[MilestoneType, list[int]] = {
    MilestoneType.TOTAL_HOURS: _TOTAL_HOURS_THRESHOLDS,
    MilestoneType.STUDY_DAYS: _STUDY_DAYS_THRESHOLDS,
    MilestoneType.STREAK: _STREAK_THRESHOLDS,
}


class NotificationService:
    """通知のビジネスロジックを提供するサービス.

    Attributes:
        _repo: NotificationRepository.
        _system_notifications_path: システム通知JSONファイルのパス.
    """

    def __init__(
        self,
        repo: NotificationRepository,
        system_notifications_path: Path | None = None,
        settings_path: Path | None = None,
    ) -> None:
        """NotificationServiceを初期化する.

        Args:
            repo: NotificationRepository.
            system_notifications_path: システム通知JSONファイルのパス.
            settings_path: 設定ファイルのパス.
        """
        self._repo = repo
        self._system_notifications_path = system_notifications_path
        self._settings_path = settings_path

    @property
    def notifications_enabled(self) -> bool:
        """実績通知が有効かどうかを返す.

        Returns:
            通知が有効な場合True.
        """
        if self._settings_path is None:
            return True
        try:
            if self._settings_path.exists():
                data: dict[str, Any] = json.loads(
                    self._settings_path.read_text(encoding="utf-8")
                )
                return bool(data.get("notifications_enabled", True))
        except (json.JSONDecodeError, ValueError, OSError):
            pass
        return True

    def set_notifications_enabled(self, enabled: bool) -> None:
        """実績通知の有効/無効を設定する.

        Args:
            enabled: 通知を有効にする場合True.
        """
        if self._settings_path is None:
            return
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            data: dict[str, Any] = {}
            if self._settings_path.exists():
                data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            data["notifications_enabled"] = enabled
            self._settings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info(f"Notifications enabled: {enabled}")
        except OSError as e:  # pragma: no cover
            logger.error(f"Failed to save notification setting: {e}")

    def get_all_notifications(self) -> list[Notification]:
        """全通知を取得する（作成日時降順）.

        Returns:
            通知のリスト.
        """
        return self._repo.get_all()

    def get_unread_count(self) -> int:
        """未読通知数を返す.

        Returns:
            未読通知の件数.
        """
        return self._repo.get_unread_count()

    def mark_as_read(self, notification_id: str) -> bool:
        """通知を既読にする.

        Args:
            notification_id: 通知ID.

        Returns:
            成功した場合True.
        """
        return self._repo.mark_as_read(notification_id)

    def mark_all_as_read(self) -> int:
        """全通知を既読にする.

        Returns:
            更新した件数.
        """
        return self._repo.mark_all_as_read()

    def check_and_create_achievement_notifications(
        self, milestone_data: MilestoneData
    ) -> list[Notification]:
        """実績達成に基づいて新しい通知を作成する.

        MilestoneDataの累計値と閾値リストを直接比較し、
        未通知の実績に対して通知を生成する。
        dedup_keyで重複チェックを行い、既に通知済みの実績はスキップする。

        Args:
            milestone_data: 現在の実績データ.

        Returns:
            新しく作成された通知のリスト.
        """
        if not self.notifications_enabled:
            return []

        # MilestoneType → 現在の累計値
        current_values: dict[MilestoneType, float] = {
            MilestoneType.TOTAL_HOURS: milestone_data.total_hours,
            MilestoneType.STUDY_DAYS: float(milestone_data.study_days),
            MilestoneType.STREAK: float(milestone_data.current_streak),
        }

        created: list[Notification] = []
        for milestone_type, thresholds in _THRESHOLD_MAP.items():
            current_value = current_values[milestone_type]
            for threshold in thresholds:
                if current_value < threshold:
                    break
                dedup_key = f"{milestone_type.value}:{threshold}"
                if self._repo.exists_by_dedup_key(dedup_key):
                    continue
                title = _ACHIEVEMENT_TITLES[milestone_type].format(value=threshold)
                message = _ACHIEVEMENT_MESSAGES[milestone_type].format(value=threshold)
                notification = Notification(
                    notification_type=NotificationType.ACHIEVEMENT,
                    title=title,
                    message=message,
                    dedup_key=dedup_key,
                )
                self._repo.add(notification)
                created.append(notification)
                logger.info(f"Created achievement notification: {title}")

        return created

    def load_system_notifications(self) -> list[Notification]:
        """システム通知JSONファイルから通知を読み込み、未登録のものを追加する.

        Returns:
            新しく追加された通知のリスト.
        """
        if self._system_notifications_path is None:
            return []
        if not self._system_notifications_path.exists():
            return []

        try:
            text = self._system_notifications_path.read_text(encoding="utf-8")
            items: list[dict[str, Any]] = json.loads(text)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load system notifications: {e}")
            return []

        created: list[Notification] = []
        for item in items:
            dedup_key = str(item.get("dedup_key", ""))
            if not dedup_key:
                continue
            if self._repo.exists_by_dedup_key(dedup_key):
                continue

            notification = Notification(
                notification_type=NotificationType.SYSTEM,
                title=str(item.get("title", "")),
                message=str(item.get("message", "")),
                dedup_key=dedup_key,
            )
            self._repo.add(notification)
            created.append(notification)

        if created:
            logger.info(f"Loaded {len(created)} new system notifications")
        return created
