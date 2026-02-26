"""JapaneseCalendarWidgetのテスト."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from PySide6.QtCore import QDate
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QCalendarWidget, QDialog

from study_python.gui.widgets.japanese_calendar_widget import (
    HOLIDAY_COLOR,
    SATURDAY_COLOR,
    SUNDAY_COLOR,
    CalendarDatePicker,
    CalendarDialog,
    JapaneseCalendarWidget,
    create_japanese_date_edit,
)
from study_python.services.holiday_service import HolidayService


class TestJapaneseCalendarWidget:
    """JapaneseCalendarWidgetのテスト."""

    def test_create_widget(self, qtbot):
        """ウィジェットが正常に作成される."""
        widget = JapaneseCalendarWidget()
        qtbot.addWidget(widget)
        assert widget._holiday_service is not None

    def test_week_numbers_hidden(self, qtbot):
        """週番号が非表示."""
        widget = JapaneseCalendarWidget()
        qtbot.addWidget(widget)
        assert (
            widget.verticalHeaderFormat()
            == QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

    def test_create_with_injected_service(self, qtbot):
        """注入したサービスが使用される."""
        service = HolidayService()
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)
        assert widget._holiday_service is service


class TestDetermineTextColor:
    """_determine_text_colorのテスト."""

    def test_holiday_returns_holiday_color(self, qtbot):
        """祝日は赤色を返す."""
        service = MagicMock(spec=HolidayService)
        service.is_holiday.return_value = True
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)

        color = widget._determine_text_color(date(2026, 1, 1))
        assert color == HOLIDAY_COLOR

    def test_sunday_returns_sunday_color(self, qtbot):
        """日曜は赤色を返す."""
        service = MagicMock(spec=HolidayService)
        service.is_holiday.return_value = False
        service.is_sunday.return_value = True
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)

        color = widget._determine_text_color(date(2026, 3, 1))
        assert color == SUNDAY_COLOR

    def test_saturday_returns_saturday_color(self, qtbot):
        """土曜は青色を返す."""
        service = MagicMock(spec=HolidayService)
        service.is_holiday.return_value = False
        service.is_sunday.return_value = False
        service.is_saturday.return_value = True
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)

        color = widget._determine_text_color(date(2026, 2, 28))
        assert color == SATURDAY_COLOR

    def test_weekday_returns_palette_text_color(self, qtbot):
        """平日はパレットのテキスト色を返す."""
        service = MagicMock(spec=HolidayService)
        service.is_holiday.return_value = False
        service.is_sunday.return_value = False
        service.is_saturday.return_value = False
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)

        color = widget._determine_text_color(date(2026, 3, 2))
        expected = widget.palette().color(QPalette.ColorRole.WindowText)
        assert color == expected

    def test_holiday_takes_priority_over_saturday(self, qtbot):
        """祝日が土曜に重なった場合、祝日（赤）が優先."""
        service = MagicMock(spec=HolidayService)
        service.is_holiday.return_value = True
        service.is_saturday.return_value = True
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)

        color = widget._determine_text_color(date(2026, 1, 1))
        assert color == HOLIDAY_COLOR

    def test_holiday_takes_priority_over_sunday(self, qtbot):
        """祝日が日曜に重なった場合、祝日（赤）が優先."""
        service = MagicMock(spec=HolidayService)
        service.is_holiday.return_value = True
        service.is_sunday.return_value = True
        widget = JapaneseCalendarWidget(holiday_service=service)
        qtbot.addWidget(widget)

        color = widget._determine_text_color(date(2026, 1, 1))
        assert color == HOLIDAY_COLOR


class TestCalendarDialog:
    """CalendarDialogのテスト."""

    def test_create_dialog(self, qtbot):
        """ダイアログが正常に作成される."""
        dialog = CalendarDialog(current_date=QDate(2026, 6, 15))
        qtbot.addWidget(dialog)
        assert dialog.selected_date() == QDate(2026, 6, 15)
        assert dialog.windowTitle() == "日付を選択"

    def test_calendar_shows_selected_date(self, qtbot):
        """カレンダーが指定日付を選択状態で表示する."""
        dialog = CalendarDialog(current_date=QDate(2026, 3, 20))
        qtbot.addWidget(dialog)
        assert dialog._calendar.selectedDate() == QDate(2026, 3, 20)

    def test_date_click_accepts_dialog(self, qtbot):
        """日付クリックでダイアログが承認される."""
        dialog = CalendarDialog(current_date=QDate(2026, 6, 15))
        qtbot.addWidget(dialog)
        dialog._on_date_clicked(QDate(2026, 7, 1))
        assert dialog.selected_date() == QDate(2026, 7, 1)
        assert dialog.result() == CalendarDialog.DialogCode.Accepted

    def test_calendar_has_grid(self, qtbot):
        """カレンダーのグリッドが有効."""
        dialog = CalendarDialog(current_date=QDate(2026, 1, 1))
        qtbot.addWidget(dialog)
        assert dialog._calendar.isGridVisible() is True

    def test_accepts_custom_service(self, qtbot):
        """カスタムサービスを受け取れる."""
        service = HolidayService()
        dialog = CalendarDialog(current_date=QDate(2026, 1, 1), holiday_service=service)
        qtbot.addWidget(dialog)
        assert dialog._calendar._holiday_service is service


class TestCalendarDatePicker:
    """CalendarDatePickerのテスト."""

    def test_create_picker(self, qtbot):
        """ピッカーが正常に作成される."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        assert picker.date() == QDate.currentDate()

    def test_set_date(self, qtbot):
        """日付の設定と取得."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 12, 25))
        assert picker.date() == QDate(2026, 12, 25)

    def test_display_format_default(self, qtbot):
        """デフォルトの表示フォーマット."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 3, 15))
        assert picker._date_label.text() == "2026/03/15"

    def test_set_display_format(self, qtbot):
        """表示フォーマットの変更."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 3, 15))
        picker.setDisplayFormat("yyyy-MM-dd")
        assert picker._date_label.text() == "2026-03-15"

    def test_date_label_is_readonly(self, qtbot):
        """日付ラベルが読み取り専用."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        assert picker._date_label.isReadOnly() is True

    def test_has_calendar_button(self, qtbot):
        """カレンダーボタンが存在する."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        assert picker._calendar_btn is not None

    def test_open_calendar_updates_date(self, qtbot, monkeypatch):
        """カレンダーで日付選択すると値が更新される."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 1, 1))

        # CalendarDialogをモックして即座に日付を返す
        def mock_exec(dialog_self):
            dialog_self._selected_date = QDate(2026, 6, 15)
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(CalendarDialog, "exec", mock_exec)
        picker._open_calendar()
        assert picker.date() == QDate(2026, 6, 15)
        assert picker._date_label.text() == "2026/06/15"

    def test_open_calendar_cancel_keeps_date(self, qtbot, monkeypatch):
        """カレンダーでキャンセルすると日付が変わらない."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 1, 1))

        def mock_exec(_self):
            return QDialog.DialogCode.Rejected

        monkeypatch.setattr(CalendarDialog, "exec", mock_exec)
        picker._open_calendar()
        assert picker.date() == QDate(2026, 1, 1)

    def test_date_changed_signal_emitted(self, qtbot, monkeypatch):
        """日付変更時にシグナルが発行される."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 1, 1))

        def mock_exec(dialog_self):
            dialog_self._selected_date = QDate(2026, 6, 15)
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(CalendarDialog, "exec", mock_exec)

        with qtbot.waitSignal(picker.date_changed):
            picker._open_calendar()

    def test_date_changed_signal_not_emitted_on_same_date(self, qtbot, monkeypatch):
        """同じ日付を選択した場合シグナルが発行されない."""
        picker = CalendarDatePicker()
        qtbot.addWidget(picker)
        picker.setDate(QDate(2026, 1, 1))

        def mock_exec(dialog_self):
            dialog_self._selected_date = QDate(2026, 1, 1)
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(CalendarDialog, "exec", mock_exec)

        emitted = []
        picker.date_changed.connect(emitted.append)
        picker._open_calendar()
        assert len(emitted) == 0

    def test_accepts_custom_service(self, qtbot):
        """カスタムサービスを受け取れる."""
        service = HolidayService()
        picker = CalendarDatePicker(holiday_service=service)
        qtbot.addWidget(picker)
        assert picker._holiday_service is service


class TestCreateJapaneseDateEdit:
    """create_japanese_date_editのテスト."""

    def test_returns_calendar_date_picker(self, qtbot):
        """CalendarDatePickerインスタンスを返す."""
        picker = create_japanese_date_edit()
        qtbot.addWidget(picker)
        assert isinstance(picker, CalendarDatePicker)

    def test_accepts_custom_service(self, qtbot):
        """カスタムサービスを受け取れる."""
        service = HolidayService()
        picker = create_japanese_date_edit(holiday_service=service)
        qtbot.addWidget(picker)
        assert picker._holiday_service is service
