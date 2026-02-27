"""ダッシュボードレイアウト管理サービス."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar


logger = logging.getLogger(__name__)


@dataclass
class DashboardWidgetConfig:
    """ダッシュボードウィジェットの配置設定.

    Attributes:
        widget_type: ウィジェット識別子.
        column_span: カラムスパン（1=半幅, 2=全幅）.
    """

    widget_type: str
    column_span: int


@dataclass
class WidgetMetadata:
    """ウィジェットのメタデータ.

    Attributes:
        widget_type: ウィジェット識別子.
        display_name: 表示名.
        icon: アイコン絵文字.
        default_span: デフォルトのカラムスパン.
        allowed_spans: 許可されるカラムスパンのリスト.
    """

    widget_type: str
    display_name: str
    icon: str
    default_span: int
    allowed_spans: list[int]


class DashboardLayoutService:
    """ダッシュボードのレイアウト設定を管理するサービス.

    settings.jsonにレイアウト設定を永続化する。

    Attributes:
        WIDGET_REGISTRY: 利用可能なウィジェットの登録簿.
    """

    WIDGET_REGISTRY: ClassVar[dict[str, WidgetMetadata]] = {
        "today_banner": WidgetMetadata(
            widget_type="today_banner",
            display_name="\u4eca\u65e5\u306e\u5b66\u7fd2\u72b6\u6cc1",
            icon="\u2705",
            default_span=2,
            allowed_spans=[1, 2],
        ),
        "total_time_card": WidgetMetadata(
            widget_type="total_time_card",
            display_name="\u5408\u8a08\u5b66\u7fd2\u6642\u9593",
            icon="\u23f1\ufe0f",
            default_span=1,
            allowed_spans=[1, 2],
        ),
        "study_days_card": WidgetMetadata(
            widget_type="study_days_card",
            display_name="\u5b66\u7fd2\u65e5\u6570",
            icon="\U0001f4c5",
            default_span=1,
            allowed_spans=[1, 2],
        ),
        "goal_count_card": WidgetMetadata(
            widget_type="goal_count_card",
            display_name="\u76ee\u6a19\u6570",
            icon="\U0001f3af",
            default_span=1,
            allowed_spans=[1, 2],
        ),
        "streak_card": WidgetMetadata(
            widget_type="streak_card",
            display_name="\u9023\u7d9a\u5b66\u7fd2",
            icon="\U0001f525",
            default_span=1,
            allowed_spans=[1, 2],
        ),
        "bookshelf": WidgetMetadata(
            widget_type="bookshelf",
            display_name="\u672c\u68da",
            icon="\U0001f4da",
            default_span=2,
            allowed_spans=[1, 2],
        ),
        "personal_record": WidgetMetadata(
            widget_type="personal_record",
            display_name="\u81ea\u5df1\u30d9\u30b9\u30c8",
            icon="\U0001f3c5",
            default_span=1,
            allowed_spans=[1, 2],
        ),
        "consistency": WidgetMetadata(
            widget_type="consistency",
            display_name="学習の実施率",
            icon="\U0001f4ca",
            default_span=1,
            allowed_spans=[1, 2],
        ),
        "daily_chart": WidgetMetadata(
            widget_type="daily_chart",
            display_name="\u5b66\u7fd2\u30a2\u30af\u30c6\u30a3\u30d3\u30c6\u30a3",
            icon="\U0001f4c8",
            default_span=2,
            allowed_spans=[1, 2],
        ),
    }

    def __init__(self, settings_path: Path) -> None:
        """DashboardLayoutServiceを初期化する.

        Args:
            settings_path: settings.jsonのパス.
        """
        self._settings_path = settings_path

    def get_layout(self) -> list[DashboardWidgetConfig]:
        """保存済みレイアウトを取得する.

        Returns:
            ウィジェット配置設定のリスト。未保存の場合はデフォルトレイアウト.
        """
        try:
            if self._settings_path.exists():
                data: dict[str, Any] = json.loads(
                    self._settings_path.read_text(encoding="utf-8")
                )
                raw_layout = data.get("dashboard_layout")
                if raw_layout is not None:
                    layout = self._parse_layout(raw_layout)
                    if layout:
                        return layout
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.warning("Failed to load dashboard layout, using default")
        return self.get_default_layout()

    def save_layout(self, layout: list[DashboardWidgetConfig]) -> None:
        """レイアウト設定を保存する.

        Args:
            layout: 保存するウィジェット配置設定.
        """
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            data: dict[str, Any] = {}
            if self._settings_path.exists():
                data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            data["dashboard_layout"] = [
                {"widget_type": w.widget_type, "column_span": w.column_span}
                for w in layout
            ]
            self._settings_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info(f"Dashboard layout saved: {len(layout)} widgets")
        except OSError as e:  # pragma: no cover
            logger.error(f"Failed to save dashboard layout: {e}")

    def get_default_layout(self) -> list[DashboardWidgetConfig]:
        """デフォルトレイアウトを取得する.

        Returns:
            デフォルトのウィジェット配置設定.
        """
        return [
            DashboardWidgetConfig("today_banner", 2),
            DashboardWidgetConfig("total_time_card", 1),
            DashboardWidgetConfig("study_days_card", 1),
            DashboardWidgetConfig("streak_card", 1),
            DashboardWidgetConfig("goal_count_card", 1),
            DashboardWidgetConfig("personal_record", 1),
            DashboardWidgetConfig("consistency", 1),
            DashboardWidgetConfig("bookshelf", 2),
            DashboardWidgetConfig("daily_chart", 2),
        ]

    def get_available_widgets(
        self, current: list[DashboardWidgetConfig]
    ) -> list[WidgetMetadata]:
        """現在のレイアウトに含まれていないウィジェットを取得する.

        Args:
            current: 現在のレイアウト.

        Returns:
            追加可能なウィジェットのメタデータリスト.
        """
        current_types = {w.widget_type for w in current}
        return [
            meta
            for meta in self.WIDGET_REGISTRY.values()
            if meta.widget_type not in current_types
        ]

    def reorder(
        self,
        layout: list[DashboardWidgetConfig],
        from_index: int,
        to_index: int,
    ) -> list[DashboardWidgetConfig]:
        """ウィジェットの順序を変更する.

        Args:
            layout: 現在のレイアウト.
            from_index: 移動元インデックス.
            to_index: 移動先インデックス.

        Returns:
            並べ替え後のレイアウト.
        """
        result = list(layout)
        if (
            from_index < 0
            or from_index >= len(result)
            or to_index < 0
            or to_index >= len(result)
        ):
            return result
        widget = result.pop(from_index)
        result.insert(to_index, widget)
        return result

    def add_widget(
        self,
        layout: list[DashboardWidgetConfig],
        widget_type: str,
    ) -> list[DashboardWidgetConfig]:
        """ウィジェットを追加する.

        Args:
            layout: 現在のレイアウト.
            widget_type: 追加するウィジェットタイプ.

        Returns:
            追加後のレイアウト.
        """
        if widget_type not in self.WIDGET_REGISTRY:
            return list(layout)
        if any(w.widget_type == widget_type for w in layout):
            return list(layout)
        meta = self.WIDGET_REGISTRY[widget_type]
        result = list(layout)
        result.append(DashboardWidgetConfig(widget_type, meta.default_span))
        return result

    def remove_widget(
        self,
        layout: list[DashboardWidgetConfig],
        index: int,
    ) -> list[DashboardWidgetConfig]:
        """ウィジェットを削除する.

        Args:
            layout: 現在のレイアウト.
            index: 削除するウィジェットのインデックス.

        Returns:
            削除後のレイアウト.
        """
        result = list(layout)
        if 0 <= index < len(result):
            result.pop(index)
        return result

    def resize_widget(
        self,
        layout: list[DashboardWidgetConfig],
        index: int,
    ) -> list[DashboardWidgetConfig]:
        """ウィジェットのサイズを切り替える.

        allowed_spans内で次のサイズに切り替える。

        Args:
            layout: 現在のレイアウト.
            index: リサイズするウィジェットのインデックス.

        Returns:
            リサイズ後のレイアウト.
        """
        result = list(layout)
        if index < 0 or index >= len(result):
            return result
        widget = result[index]
        meta = self.WIDGET_REGISTRY.get(widget.widget_type)
        if meta is None or len(meta.allowed_spans) <= 1:
            return result
        current_idx = (
            meta.allowed_spans.index(widget.column_span)
            if widget.column_span in meta.allowed_spans
            else 0
        )
        next_idx = (current_idx + 1) % len(meta.allowed_spans)
        result[index] = DashboardWidgetConfig(
            widget.widget_type, meta.allowed_spans[next_idx]
        )
        return result

    def _parse_layout(self, raw: list[dict[str, Any]]) -> list[DashboardWidgetConfig]:
        """生データからレイアウト設定をパースする.

        Args:
            raw: JSON由来の生データ.

        Returns:
            パース済みウィジェット配置設定。無効なエントリはスキップ.
        """
        result: list[DashboardWidgetConfig] = []
        for item in raw:
            widget_type = item.get("widget_type", "")
            column_span = item.get("column_span", 1)
            if widget_type in self.WIDGET_REGISTRY:
                meta = self.WIDGET_REGISTRY[widget_type]
                if column_span not in meta.allowed_spans:
                    column_span = meta.default_span
                result.append(DashboardWidgetConfig(widget_type, column_span))
        return result
