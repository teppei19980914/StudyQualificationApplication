"""日別学習アクティビティチャートウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.services.study_stats_calculator import DailyActivityData


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
        self.setFixedHeight(self._CHART_HEIGHT)

    def set_data(self, data: DailyActivityData) -> None:
        """チャートデータを設定する.

        Args:
            data: 日別学習アクティビティデータ.
        """
        self._data = data
        self.update()

    def sizeHint(self) -> QSize:
        """推奨サイズを返す.

        Returns:
            推奨サイズ.
        """
        if self._data:
            width = (
                self._PADDING_LEFT
                + self._PADDING_RIGHT
                + len(self._data.days) * (self._BAR_WIDTH + self._BAR_SPACING)
            )
            return QSize(max(width, 400), self._CHART_HEIGHT)
        return QSize(400, self._CHART_HEIGHT)

    def minimumSizeHint(self) -> QSize:
        """最小サイズを返す.

        Returns:
            最小サイズ.
        """
        return QSize(200, self._CHART_HEIGHT)

    def paintEvent(self, _event: QPaintEvent) -> None:  # pragma: no cover
        """チャートを描画する.

        Args:
            _event: ペイントイベント.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = self._theme_manager.get_colors()
        self._draw_background(painter, colors)

        if self._data is None or not self._data.days:
            self._draw_empty_message(painter, colors)
            painter.end()
            return

        self._draw_y_axis(painter, colors)
        self._draw_bars(painter, colors)
        self._draw_x_axis(painter, colors)
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
        if self._data is None or self._data.max_minutes == 0:
            return

        chart_top = self._PADDING_TOP
        chart_bottom = self._CHART_HEIGHT - self._PADDING_BOTTOM
        chart_height = chart_bottom - chart_top

        painter.setPen(QPen(QColor(colors.get("text_muted", "#6C7086"))))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        max_min = self._data.max_minutes
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

    def _draw_bars(  # pragma: no cover
        self, painter: QPainter, colors: dict[str, str]
    ) -> None:
        """棒グラフを描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
        """
        if self._data is None:
            return

        chart_top = self._PADDING_TOP
        chart_bottom = self._CHART_HEIGHT - self._PADDING_BOTTOM
        chart_height = chart_bottom - chart_top
        max_min = self._data.max_minutes if self._data.max_minutes > 0 else 1

        accent_color = QColor(colors.get("accent", "#89B4FA"))
        border_color = QColor(colors.get("border", "#45475A"))

        for i, day in enumerate(self._data.days):
            x = self._PADDING_LEFT + i * (self._BAR_WIDTH + self._BAR_SPACING)

            if day.total_minutes > 0:
                bar_height = (day.total_minutes / max_min) * chart_height
                bar_y = chart_bottom - bar_height

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(accent_color))
                painter.drawRoundedRect(
                    QRectF(x, bar_y, self._BAR_WIDTH, bar_height),
                    self._BAR_RADIUS,
                    self._BAR_RADIUS,
                )
            else:
                # 0分の日は細い線
                painter.setPen(QPen(border_color, 1))
                painter.drawLine(
                    int(x + self._BAR_WIDTH // 2),
                    int(chart_bottom),
                    int(x + self._BAR_WIDTH // 2),
                    int(chart_bottom - 1),
                )

    def _draw_x_axis(  # pragma: no cover
        self, painter: QPainter, colors: dict[str, str]
    ) -> None:
        """X軸ラベルを描画する.

        Args:
            painter: QPainterインスタンス.
            colors: テーマカラーパレット.
        """
        if self._data is None:
            return

        painter.setPen(QPen(QColor(colors.get("text_muted", "#6C7086"))))
        font = QFont("Segoe UI", 7)
        painter.setFont(font)

        label_y = self._CHART_HEIGHT - self._PADDING_BOTTOM + 4

        for i, day in enumerate(self._data.days):
            # 7日ごと、または最初と最後にラベルを表示
            if i % 7 == 0 or i == len(self._data.days) - 1:
                x = self._PADDING_LEFT + i * (self._BAR_WIDTH + self._BAR_SPACING)
                label = f"{day.study_date.month}/{day.study_date.day}"
                painter.drawText(
                    QRectF(x - 10, label_y, 36, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    label,
                )
