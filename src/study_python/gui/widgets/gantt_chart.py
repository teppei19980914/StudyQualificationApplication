"""ガントチャートウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.task import Task, TaskStatus
from study_python.services.gantt_calculator import GanttCalculator, TimelineRange


logger = logging.getLogger(__name__)


class GanttBarItem(QGraphicsRectItem):
    """ガントチャートのバーアイテム.

    Attributes:
        task: 紐づくTask.
        goal_color: Goalの色.
    """

    def __init__(
        self,
        task: Task,
        goal_color: str,
        x: float,
        y: float,
        width: float,
        height: float,
        progress_width: float,
        colors: dict[str, str],
    ) -> None:
        """GanttBarItemを初期化する.

        Args:
            task: 紐づくTask.
            goal_color: Goalの表示色.
            x: X座標.
            y: Y座標.
            width: バーの幅.
            height: バーの高さ.
            progress_width: 進捗部分の幅.
            colors: テーマカラーパレット.
        """
        super().__init__(x, y, width, height)
        self.task = task
        self.goal_color = goal_color
        self._progress_width = progress_width
        self._colors = colors
        self._height = height

        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        tooltip_text = (
            f"{task.title}\n"
            f"期間: {task.start_date} ~ {task.end_date}\n"
            f"進捗: {task.progress}%\n"
            f"ステータス: {self._status_text()}"
        )
        self.setToolTip(tooltip_text)

    def _status_text(self) -> str:
        """ステータスのテキスト表現を返す.

        Returns:
            ステータス文字列.
        """
        status_map = {
            TaskStatus.NOT_STARTED: "未着手",
            TaskStatus.IN_PROGRESS: "進行中",
            TaskStatus.COMPLETED: "完了",
        }
        return status_map.get(self.task.status, "不明")

    def paint(  # pragma: no cover
        self,
        painter: QPainter,
        _option: object,
        _widget: QWidget | None = None,
    ) -> None:
        """バーを描画する.

        Args:
            painter: QPainterインスタンス.
            option: スタイルオプション.
            widget: ウィジェット.
        """
        rect = self.rect()
        radius = 6.0

        # 背景バー（計画）
        bg_color = QColor(self.goal_color)
        bg_color.setAlpha(60)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, radius, radius)

        # 進捗バー
        if self._progress_width > 0:
            progress_color = QColor(self.goal_color)
            if self.task.status == TaskStatus.COMPLETED:
                progress_color = QColor(self._colors.get("success", "#A6E3A1"))

            painter.setBrush(QBrush(progress_color))
            progress_rect = QRectF(
                rect.x(), rect.y(), self._progress_width, rect.height()
            )
            painter.drawRoundedRect(progress_rect, radius, radius)

        # テキスト
        painter.setPen(QPen(QColor(self._colors.get("text_primary", "#CDD6F4"))))
        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)

        text = f"{self.task.title} ({self.task.progress}%)"
        text_rect = rect.adjusted(8, 0, -8, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )

        # 枠線
        border_color = QColor(self.goal_color)
        border_color.setAlpha(120)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)


class GanttChart(QGraphicsView):
    """ガントチャートビュー.

    Signals:
        bar_clicked: バークリック時に発行するシグナル（task_id）.
    """

    bar_clicked = Signal(str)

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """GanttChartを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._calculator = GanttCalculator()
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def display_tasks(self, tasks: list[Task], goal_color: str = "#89B4FA") -> None:
        """タスクをガントチャートに表示する.

        Args:
            tasks: 表示するTaskのリスト.
            goal_color: Goalの表示色.
        """
        self._scene.clear()
        colors = self._theme_manager.get_colors()

        if not tasks:
            self._draw_empty_message(colors)
            return

        task_dates = [(t.start_date, t.end_date) for t in tasks]
        timeline = self._calculator.calculate_timeline(task_dates)

        scene_width = self._calculator.calculate_scene_width(timeline)
        scene_height = self._calculator.calculate_scene_height(len(tasks))
        self._scene.setSceneRect(0, 0, scene_width, scene_height)

        self._draw_grid(timeline, len(tasks), colors)
        self._draw_header(timeline, colors)
        self._draw_today_line(timeline, scene_height, colors)
        self._draw_bars(tasks, timeline, goal_color, colors)

    def _draw_empty_message(self, colors: dict[str, str]) -> None:
        """タスクが無い場合のメッセージを表示する.

        Args:
            colors: テーマカラーパレット.
        """
        self._scene.setSceneRect(0, 0, 600, 200)
        text = self._scene.addText(
            "タスクがありません。「+ タスク追加」ボタンから追加してください。"
        )
        text.setDefaultTextColor(QColor(colors.get("text_muted", "#6C7086")))
        font = QFont("Segoe UI", 12)
        text.setFont(font)
        text.setPos(50, 80)

    def _draw_grid(
        self,
        timeline: TimelineRange,
        task_count: int,
        colors: dict[str, str],
    ) -> None:
        """グリッド線を描画する.

        Args:
            timeline: タイムライン範囲.
            task_count: タスク数.
            colors: テーマカラーパレット.
        """
        calc = self._calculator
        grid_pen = QPen(QColor(colors.get("border", "#45475A")))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        grid_pen.setWidthF(0.5)

        scene_height = calc.calculate_scene_height(task_count)

        # 行グリッド
        for i in range(task_count + 1):
            y = calc.header_height + i * calc.row_height
            self._scene.addLine(0, y, calc.calculate_scene_width(timeline), y, grid_pen)

        # 月境界の縦線
        boundaries = calc.get_month_boundaries(timeline)
        for _, x in boundaries:
            self._scene.addLine(x, 0, x, scene_height, grid_pen)

    def _draw_header(self, timeline: TimelineRange, colors: dict[str, str]) -> None:
        """タイムラインヘッダーを描画する.

        Args:
            timeline: タイムライン範囲.
            colors: テーマカラーパレット.
        """
        calc = self._calculator
        scene_width = calc.calculate_scene_width(timeline)

        # ヘッダー背景
        header_bg = QColor(colors.get("bg_secondary", "#181825"))
        self._scene.addRect(
            0,
            0,
            scene_width,
            calc.header_height,
            QPen(Qt.PenStyle.NoPen),
            QBrush(header_bg),
        )

        # 月ラベル
        boundaries = calc.get_month_boundaries(timeline)
        text_color = QColor(colors.get("text_primary", "#CDD6F4"))
        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.DemiBold)

        for month_date, x in boundaries:
            label = month_date.strftime("%Y/%m")
            text_item = self._scene.addText(label)
            text_item.setDefaultTextColor(text_color)
            text_item.setFont(font)
            text_item.setPos(x + 4, 15)

    def _draw_today_line(
        self,
        timeline: TimelineRange,
        scene_height: float,
        colors: dict[str, str],
    ) -> None:
        """今日の線を描画する.

        Args:
            timeline: タイムライン範囲.
            scene_height: シーンの高さ.
            colors: テーマカラーパレット.
        """
        calc = self._calculator
        today_x = calc.calculate_today_x(timeline)
        today_pen = QPen(QColor(colors.get("error", "#F38BA8")))
        today_pen.setWidth(2)
        today_pen.setStyle(Qt.PenStyle.DashLine)
        self._scene.addLine(today_x, 0, today_x, scene_height, today_pen)

        # 今日ラベル
        label = self._scene.addText("Today")
        label.setDefaultTextColor(QColor(colors.get("error", "#F38BA8")))
        font = QFont("Segoe UI", 8)
        font.setWeight(QFont.Weight.Bold)
        label.setFont(font)
        label.setPos(today_x + 3, 2)

    def _draw_bars(
        self,
        tasks: list[Task],
        timeline: TimelineRange,
        goal_color: str,
        colors: dict[str, str],
    ) -> None:
        """タスクバーを描画する.

        Args:
            tasks: タスクのリスト.
            timeline: タイムライン範囲.
            goal_color: Goalの表示色.
            colors: テーマカラーパレット.
        """
        calc = self._calculator
        for i, task in enumerate(tasks):
            bar_geo = calc.calculate_bar_geometry(
                task.start_date, task.end_date, task.progress, timeline
            )
            y = calc.calculate_bar_y(i)

            bar = GanttBarItem(
                task=task,
                goal_color=goal_color,
                x=bar_geo.x,
                y=y,
                width=bar_geo.width,
                height=calc.bar_height,
                progress_width=bar_geo.progress_width,
                colors=colors,
            )
            bar.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            self._scene.addItem(bar)

    def mousePressEvent(self, event: object) -> None:  # pragma: no cover
        """マウスクリックイベントハンドラ.

        Args:
            event: マウスイベント.
        """
        super().mousePressEvent(event)  # type: ignore[arg-type]
        items = self.items(event.pos())  # type: ignore[union-attr]
        for item in items:
            if isinstance(item, GanttBarItem):
                self.bar_clicked.emit(item.task.id)
                break
