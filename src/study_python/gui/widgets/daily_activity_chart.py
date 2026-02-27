"""日別学習アクティビティチャートウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QToolTip, QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.study_stats_calculator import (
    ActivityChartData,
    DailyActivityData,
)


logger = logging.getLogger(__name__)


class DailyActivityChart(QWidget):
    """日別学習アクティビティ棒グラフウィジェット.

    直近N日の日別学習時間を棒グラフで表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _data: チャートデータ.
    """

    _CHART_HEIGHT = 180
    _PADDING_LEFT = 48
    _PADDING_RIGHT = 16
    _PADDING_TOP = 12
    _PADDING_BOTTOM = 28
    _BAR_WIDTH = 12
    _BAR_SPACING = 4
    _BAR_RADIUS = 3.0

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """DailyActivityChartを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._data: DailyActivityData | None = None
        self._activity_data: ActivityChartData | None = None
        self.setMinimumHeight(self._CHART_HEIGHT)
        self.setMouseTracking(True)

    def set_data(self, data: DailyActivityData) -> None:
        """チャートデータを設定する（後方互換）.

        Args:
            data: 日別学習アクティビティデータ.
        """
        self._data = data
        self._activity_data = None
        self.update()

    def set_activity_data(self, data: ActivityChartData) -> None:
        """期間別アクティビティチャートデータを設定する.

        Args:
            data: 期間別アクティビティチャートデータ.
        """
        self._activity_data = data
        self._data = None
        self.update()

    def sizeHint(self) -> QSize:
        """推奨サイズを返す.

        Returns:
            推奨サイズ.
        """
        return QSize(400, self._CHART_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        """最小サイズを返す.

        Returns:
            最小サイズ.
        """
        return QSize(200, self._CHART_HEIGHT)

    def _get_num_bars(self) -> int:  # pragma: no cover
        """描画するバーの数を返す.

        Returns:
            バーの数.
        """
        if self._activity_data is not None:
            return len(self._activity_data.buckets)
        if self._data is not None:
            return len(self._data.days)
        return 0

    def _get_max_minutes(self) -> int:  # pragma: no cover
        """最大学習時間を返す.

        Returns:
            最大学習時間（分）.
        """
        if self._activity_data is not None:
            return self._activity_data.max_minutes
        if self._data is not None:
            return self._data.max_minutes
        return 0

    def _has_data(self) -> bool:  # pragma: no cover
        """描画データがあるか判定する.

        Returns:
            データがある場合True.
        """
        if self._activity_data is not None:
            return len(self._activity_data.buckets) > 0
        if self._data is not None:
            return len(self._data.days) > 0
        return False

    def _calculate_bar_geometry(self) -> tuple[float, float]:  # pragma: no cover
        """ウィジェット幅に基づいてバー幅と間隔を動的計算する.

        Returns:
            (bar_width, bar_spacing) のタプル.
        """
        num_bars = self._get_num_bars()
        if num_bars == 0:
            return (float(self._BAR_WIDTH), float(self._BAR_SPACING))

        available_width = self.width() - self._PADDING_LEFT - self._PADDING_RIGHT
        total_per_bar = available_width / max(num_bars, 1)
        bar_spacing = max(total_per_bar * 0.25, 2.0)
        bar_width = max(total_per_bar - bar_spacing, 2.0)
        return (bar_width, bar_spacing)

    def paintEvent(self, _event: QPaintEvent) -> None:  # pragma: no cover
        """チャートを描画する.

        Args:
            _event: ペイントイベント.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = self._theme_manager.get_colors()
        self._draw_background(painter, colors)

        if not self._has_data():
            self._draw_empty_message(painter, colors)
            painter.end()
            return

        bar_width, bar_spacing = self._calculate_bar_geometry()
        self._draw_y_axis(painter, colors)
        self._draw_bars(painter, colors, bar_width, bar_spacing)
        self._draw_x_axis(painter, colors, bar_width, bar_spacing)
        painter.end()

    def _draw_background(  # pragma: no cover
        self, painter: QPainter, colors: dict[str, str]
    ) -> None:
        """背景を描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
        """
        bg_color = QColor(colors.get("bg_surface", "#313244"))
        painter.fillRect(self.rect(), QBrush(bg_color))

    def _draw_empty_message(  # pragma: no cover
        self, painter: QPainter, colors: dict[str, str]
    ) -> None:
        """データなしメッセージを描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
        """
        painter.setPen(QPen(QColor(colors.get("text_muted", "#6C7086"))))
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "学習ログがありません",
        )

    def _draw_y_axis(  # pragma: no cover
        self, painter: QPainter, colors: dict[str, str]
    ) -> None:
        """Y軸ラベルを描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
        """
        max_min = self._get_max_minutes()
        if max_min == 0:
            return

        chart_top = self._PADDING_TOP
        chart_bottom = self.height() - self._PADDING_BOTTOM
        chart_height = chart_bottom - chart_top

        painter.setPen(QPen(QColor(colors.get("text_muted", "#6C7086"))))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        labels = [0, max_min // 2, max_min]
        for val in labels:
            y = chart_bottom - (val / max_min) * chart_height
            text = f"{val}m"
            painter.drawText(
                QRectF(0, y - 8, self._PADDING_LEFT - 4, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

        # 基準線
        line_pen = QPen(QColor(colors.get("border", "#45475A")))
        line_pen.setWidthF(0.5)
        line_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(line_pen)
        for val in labels:
            y = chart_bottom - (val / max_min) * chart_height
            painter.drawLine(
                int(self._PADDING_LEFT),
                int(y),
                int(self.width() - self._PADDING_RIGHT),
                int(y),
            )

    def _get_bar_values(self) -> list[int]:  # pragma: no cover
        """各バーの学習時間リストを返す.

        Returns:
            各バーの学習時間（分）のリスト.
        """
        if self._activity_data is not None:
            return [b.total_minutes for b in self._activity_data.buckets]
        if self._data is not None:
            return [d.total_minutes for d in self._data.days]
        return []

    def _draw_bars(  # pragma: no cover
        self,
        painter: QPainter,
        colors: dict[str, str],
        bar_width: float,
        bar_spacing: float,
    ) -> None:
        """棒グラフを描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
            bar_width: バーの幅.
            bar_spacing: バー間の間隔.
        """
        chart_top = self._PADDING_TOP
        chart_bottom = self.height() - self._PADDING_BOTTOM
        chart_height = chart_bottom - chart_top
        raw_max = self._get_max_minutes()
        max_min = raw_max if raw_max > 0 else 1

        accent_color = QColor(colors.get("accent", "#89B4FA"))
        border_color = QColor(colors.get("border", "#45475A"))

        for i, minutes in enumerate(self._get_bar_values()):
            x = self._PADDING_LEFT + i * (bar_width + bar_spacing)

            if minutes > 0:
                bh = (minutes / max_min) * chart_height
                bar_y = chart_bottom - bh

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(accent_color))
                painter.drawRoundedRect(
                    QRectF(x, bar_y, bar_width, bh),
                    self._BAR_RADIUS,
                    self._BAR_RADIUS,
                )
            else:
                painter.setPen(QPen(border_color, 1))
                painter.drawLine(
                    int(x + bar_width / 2),
                    int(chart_bottom),
                    int(x + bar_width / 2),
                    int(chart_bottom - 1),
                )

    def _get_x_labels(self) -> list[str]:  # pragma: no cover
        """X軸ラベルのリストを返す.

        Returns:
            各バーに対応するラベルのリスト.
        """
        if self._activity_data is not None:
            return [b.label for b in self._activity_data.buckets]
        if self._data is not None:
            return [f"{d.study_date.month}/{d.study_date.day}" for d in self._data.days]
        return []

    def _format_tooltip(self, label: str, minutes: int) -> str:
        """ツールチップ表示用テキストを生成する.

        Args:
            label: バーのラベル（X軸ラベル）.
            minutes: 学習時間（分）.

        Returns:
            フォーマット済みツールチップ文字列.
        """
        if minutes >= 60:
            h = minutes // 60
            m = minutes % 60
            return f"{label}: {h}h {m:02}min"
        return f"{label}: {minutes}min"

    def _find_bar_index(
        self, mouse_x: float, bar_width: float, bar_spacing: float
    ) -> int | None:
        """マウスX座標がどのバーに該当するかを返す.

        Args:
            mouse_x: マウスのX座標.
            bar_width: バーの幅.
            bar_spacing: バー間の間隔.

        Returns:
            バーのインデックス。該当なしの場合None.
        """
        offset = mouse_x - self._PADDING_LEFT
        if offset < 0:
            return None

        step = bar_width + bar_spacing
        if step <= 0:
            return None

        index = int(offset / step)
        num_bars = self._get_num_bars()
        if index < 0 or index >= num_bars:
            return None

        bar_start = index * step
        if offset > bar_start + bar_width:
            return None

        return index

    def _calculate_label_interval(self, num_labels: int) -> int:  # pragma: no cover
        """X軸ラベルの表示間隔を計算する.

        バケット数に応じて適切な間隔を返す。

        Args:
            num_labels: ラベル数.

        Returns:
            表示間隔（1=全ラベル表示）.
        """
        if num_labels <= 15:
            return 1
        return 7

    def _draw_x_axis(  # pragma: no cover
        self,
        painter: QPainter,
        colors: dict[str, str],
        bar_width: float,
        bar_spacing: float,
    ) -> None:
        """X軸ラベルを描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
            bar_width: バーの幅.
            bar_spacing: バー間の間隔.
        """
        labels = self._get_x_labels()
        if not labels:
            return

        painter.setPen(QPen(QColor(colors.get("text_muted", "#6C7086"))))
        font = QFont("Segoe UI", 7)
        painter.setFont(font)

        label_y = self.height() - self._PADDING_BOTTOM + 4
        interval = self._calculate_label_interval(len(labels))

        for i, label in enumerate(labels):
            if i % interval == 0 or i == len(labels) - 1:
                x = self._PADDING_LEFT + i * (bar_width + bar_spacing)
                painter.drawText(
                    QRectF(x - 10, label_y, 36, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    label,
                )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # pragma: no cover
        """マウス移動時にバーのツールチップを表示する.

        Args:
            event: マウスイベント.
        """
        if not self._has_data():
            QToolTip.hideText()
            super().mouseMoveEvent(event)
            return

        mouse_x = event.position().x()
        mouse_y = event.position().y()

        chart_top = self._PADDING_TOP
        chart_bottom = self.height() - self._PADDING_BOTTOM
        if mouse_y < chart_top or mouse_y > chart_bottom:
            QToolTip.hideText()
            super().mouseMoveEvent(event)
            return

        bar_width, bar_spacing = self._calculate_bar_geometry()
        index = self._find_bar_index(mouse_x, bar_width, bar_spacing)

        if index is not None:
            labels = self._get_x_labels()
            values = self._get_bar_values()
            text = self._format_tooltip(labels[index], values[index])
            global_pos = event.globalPosition().toPoint()
            QToolTip.showText(global_pos, text, self)
        else:
            QToolTip.hideText()

        super().mouseMoveEvent(event)
