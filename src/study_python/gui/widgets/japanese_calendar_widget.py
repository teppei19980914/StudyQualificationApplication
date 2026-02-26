"""日本の祝日対応カレンダーウィジェット."""

from __future__ import annotations

import logging
from datetime import date

from PySide6.QtCore import QDate, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_python.services.holiday_service import HolidayService


logger = logging.getLogger(__name__)

# カレンダー表示色
SATURDAY_COLOR = QColor("#2563EB")
SUNDAY_COLOR = QColor("#DC2626")
HOLIDAY_COLOR = QColor("#DC2626")
WEEKDAY_COLOR = QColor("#1F2937")
OTHER_MONTH_COLOR = QColor("#9CA3AF")
SELECTED_BG_COLOR = QColor("#3B82F6")
SELECTED_TEXT_COLOR = QColor("#FFFFFF")
TODAY_BORDER_COLOR = QColor("#3B82F6")


class JapaneseCalendarWidget(QCalendarWidget):
    """日本の祝日を色分け表示するカレンダーウィジェット.

    土曜日は青、日曜日と祝日は赤で日付を表示する。

    Attributes:
        _holiday_service: 祝日判定サービス.
    """

    def __init__(
        self,
        holiday_service: HolidayService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """JapaneseCalendarWidgetを初期化する.

        Args:
            holiday_service: 祝日判定サービス（Noneの場合は新規作成）.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._holiday_service = holiday_service or HolidayService()
        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

    def paintCell(  # pragma: no cover
        self, painter: QPainter, rect: QRect, date: QDate
    ) -> None:
        """セルを描画する.

        土曜日は青、日曜日・祝日は赤でテキストを描画する。

        Args:
            painter: QPainterインスタンス.
            rect: セルの矩形領域.
            date: セルの日付.
        """
        py_date: date = date.toPython()
        is_current_month = date.month() == self.monthShown()

        painter.save()

        # 選択日の背景
        if date == self.selectedDate():
            painter.fillRect(rect, SELECTED_BG_COLOR)
            painter.setPen(QPen(SELECTED_TEXT_COLOR))
        elif is_current_month:
            text_color = self._determine_text_color(py_date)
            painter.setPen(QPen(text_color))
        else:
            painter.setPen(QPen(OTHER_MONTH_COLOR))

        # 今日の枠線
        if date == QDate.currentDate():
            old_pen = painter.pen()
            painter.setPen(QPen(TODAY_BORDER_COLOR, 1))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            painter.setPen(old_pen)

        painter.drawText(
            rect,
            int(Qt.AlignmentFlag.AlignCenter),
            str(date.day()),
        )
        painter.restore()

    def _determine_text_color(self, target_date: date) -> QColor:
        """日付に対応するテキスト色を決定する.

        Args:
            target_date: 対象日付.

        Returns:
            テキスト色.
        """
        if self._holiday_service.is_holiday(target_date):
            return HOLIDAY_COLOR
        if self._holiday_service.is_sunday(target_date):
            return SUNDAY_COLOR
        if self._holiday_service.is_saturday(target_date):
            return SATURDAY_COLOR
        return self.palette().color(QPalette.ColorRole.WindowText)


class CalendarDialog(QDialog):
    """カレンダー日付選択ダイアログ.

    JapaneseCalendarWidgetを表示し、日付クリックで選択・閉じる。
    """

    def __init__(
        self,
        current_date: QDate,
        holiday_service: HolidayService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """CalendarDialogを初期化する.

        Args:
            current_date: 初期選択日付.
            holiday_service: 祝日判定サービス.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setWindowTitle("日付を選択")
        self.setModal(True)

        self._selected_date = current_date

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._calendar = JapaneseCalendarWidget(
            holiday_service=holiday_service, parent=self
        )
        self._calendar.setSelectedDate(current_date)
        self._calendar.setGridVisible(True)
        self._calendar.setMinimumSize(350, 250)
        self._calendar.clicked.connect(self._on_date_clicked)
        layout.addWidget(self._calendar)

        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    def _on_date_clicked(self, date: QDate) -> None:
        """日付クリックハンドラ.

        Args:
            date: クリックされた日付.
        """
        self._selected_date = date
        self.accept()

    def selected_date(self) -> QDate:
        """選択された日付を返す.

        Returns:
            選択されたQDate.
        """
        return self._selected_date


class CalendarDatePicker(QWidget):
    """日付表示 + カレンダーボタンによる日付選択ウィジェット.

    読み取り専用の日付表示と、クリックでカレンダーダイアログを開くボタンで構成。
    日付フィールド全体がクリック可能。

    Signals:
        date_changed: 日付が変更された時に発行するシグナル.
    """

    date_changed = Signal(QDate)

    def __init__(
        self,
        holiday_service: HolidayService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """CalendarDatePickerを初期化する.

        Args:
            holiday_service: 祝日判定サービス.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._holiday_service = holiday_service or HolidayService()
        self._current_date = QDate.currentDate()
        self._display_format = "yyyy/MM/dd"
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._date_label = QLineEdit()
        self._date_label.setReadOnly(True)
        self._date_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._date_label.mousePressEvent = lambda _: self._open_calendar()  # type: ignore[assignment]  # pragma: no cover
        layout.addWidget(self._date_label, 1)

        self._calendar_btn = QPushButton("📅")
        self._calendar_btn.setFixedWidth(36)
        self._calendar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._calendar_btn.clicked.connect(self._open_calendar)
        layout.addWidget(self._calendar_btn)

        self._update_display()

    def date(self) -> QDate:
        """現在の日付を返す.

        Returns:
            現在のQDate.
        """
        return self._current_date

    def setDate(self, date: QDate) -> None:
        """日付を設定する.

        Args:
            date: 設定するQDate.
        """
        self._current_date = date
        self._update_display()

    def setDisplayFormat(self, fmt: str) -> None:
        """表示フォーマットを設定する.

        Args:
            fmt: Qtの日付フォーマット文字列.
        """
        self._display_format = fmt
        self._update_display()

    def _update_display(self) -> None:
        """日付表示を更新する."""
        self._date_label.setText(self._current_date.toString(self._display_format))

    def _open_calendar(self) -> None:
        """カレンダーダイアログを開く."""
        dialog = CalendarDialog(
            current_date=self._current_date,
            holiday_service=self._holiday_service,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_date = dialog.selected_date()
            if new_date != self._current_date:
                self._current_date = new_date
                self._update_display()
                self.date_changed.emit(new_date)


def create_japanese_date_edit(
    holiday_service: HolidayService | None = None,
    parent: QWidget | None = None,
) -> CalendarDatePicker:
    """日本の祝日対応カレンダー付き日付ピッカーを作成する.

    Args:
        holiday_service: 祝日判定サービス.
        parent: 親ウィジェット.

    Returns:
        CalendarDatePickerインスタンス.
    """
    return CalendarDatePicker(holiday_service=holiday_service, parent=parent)
