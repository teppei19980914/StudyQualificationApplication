"""ガントチャートの座標計算ロジック."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class TimelineRange:
    """タイムラインの表示範囲.

    Attributes:
        start_date: 表示開始日.
        end_date: 表示終了日.
        total_days: 総日数.
    """

    start_date: date
    end_date: date

    @property
    def total_days(self) -> int:
        """総日数を返す.

        Returns:
            開始日から終了日までの日数.
        """
        return (self.end_date - self.start_date).days + 1


@dataclass
class BarGeometry:
    """ガントバーの描画座標.

    Attributes:
        x: 開始X座標.
        width: バーの幅.
        progress_width: 進捗部分の幅.
    """

    x: float
    width: float
    progress_width: float


class GanttCalculator:
    """ガントチャートの座標計算を行うクラス.

    Attributes:
        pixels_per_day: 1日あたりのピクセル数.
        row_height: 行の高さ（ピクセル）.
        header_height: ヘッダーの高さ（ピクセル）.
        bar_height: バーの高さ（ピクセル）.
        bar_margin: バーの上下マージン（ピクセル）.
    """

    def __init__(
        self,
        pixels_per_day: float = 30.0,
        row_height: int = 40,
        header_height: int = 50,
        bar_height: int = 24,
        bar_margin: int = 8,
    ) -> None:
        """GanttCalculatorを初期化する.

        Args:
            pixels_per_day: 1日あたりのピクセル数.
            row_height: 行の高さ.
            header_height: ヘッダーの高さ.
            bar_height: バーの高さ.
            bar_margin: バーの上下マージン.
        """
        self.pixels_per_day = pixels_per_day
        self.row_height = row_height
        self.header_height = header_height
        self.bar_height = bar_height
        self.bar_margin = bar_margin

    def calculate_timeline(
        self,
        task_dates: list[tuple[date, date]],
        padding_days: int = 7,
    ) -> TimelineRange:
        """タスク群からタイムライン範囲を計算する.

        Args:
            task_dates: (start_date, end_date)のリスト.
            padding_days: 前後に追加する余白日数.

        Returns:
            タイムラインの表示範囲.
        """
        if not task_dates:
            today = date.today()
            return TimelineRange(
                start_date=today - timedelta(days=padding_days),
                end_date=today + timedelta(days=30 + padding_days),
            )
        all_starts = [s for s, _ in task_dates]
        all_ends = [e for _, e in task_dates]
        earliest = min(all_starts) - timedelta(days=padding_days)
        latest = max(all_ends) + timedelta(days=padding_days)
        return TimelineRange(start_date=earliest, end_date=latest)

    def calculate_bar_geometry(
        self,
        task_start: date,
        task_end: date,
        progress: int,
        timeline: TimelineRange,
    ) -> BarGeometry:
        """タスクのバー描画座標を計算する.

        Args:
            task_start: タスク開始日.
            task_end: タスク終了日.
            progress: 進捗率（0-100）.
            timeline: タイムライン範囲.

        Returns:
            バーの描画座標.
        """
        days_from_start = (task_start - timeline.start_date).days
        duration = (task_end - task_start).days + 1
        x = days_from_start * self.pixels_per_day
        width = duration * self.pixels_per_day
        progress_width = width * (progress / 100.0)
        return BarGeometry(x=x, width=width, progress_width=progress_width)

    def calculate_bar_y(self, row_index: int) -> float:
        """行インデックスからバーのY座標を計算する.

        Args:
            row_index: 行インデックス（0始まり）.

        Returns:
            バーのY座標.
        """
        return self.header_height + row_index * self.row_height + self.bar_margin

    def calculate_today_x(self, timeline: TimelineRange) -> float:
        """今日の日付のX座標を計算する.

        Args:
            timeline: タイムライン範囲.

        Returns:
            今日線のX座標.
        """
        today = date.today()
        days_from_start = (today - timeline.start_date).days
        return days_from_start * self.pixels_per_day

    def date_to_x(self, target_date: date, timeline: TimelineRange) -> float:
        """日付をX座標に変換する.

        Args:
            target_date: 変換する日付.
            timeline: タイムライン範囲.

        Returns:
            X座標.
        """
        days_from_start = (target_date - timeline.start_date).days
        return days_from_start * self.pixels_per_day

    def get_month_boundaries(self, timeline: TimelineRange) -> list[tuple[date, float]]:
        """タイムライン内の月境界とX座標を取得する.

        Args:
            timeline: タイムライン範囲.

        Returns:
            (月初日, X座標)のリスト.
        """
        boundaries: list[tuple[date, float]] = []
        current = timeline.start_date.replace(day=1)
        if current < timeline.start_date:
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        while current <= timeline.end_date:
            x = self.date_to_x(current, timeline)
            boundaries.append((current, x))
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return boundaries

    def calculate_scene_width(self, timeline: TimelineRange) -> float:
        """シーン全体の幅を計算する.

        Args:
            timeline: タイムライン範囲.

        Returns:
            シーンの幅（ピクセル）.
        """
        return timeline.total_days * self.pixels_per_day

    def calculate_scene_height(self, task_count: int) -> float:
        """シーン全体の高さを計算する.

        Args:
            task_count: タスク数.

        Returns:
            シーンの高さ（ピクセル）.
        """
        return self.header_height + max(task_count, 1) * self.row_height
