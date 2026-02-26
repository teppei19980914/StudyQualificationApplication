"""HolidayServiceのテスト."""

from __future__ import annotations

from datetime import date

from study_python.services.holiday_service import HolidayService


class TestIsHoliday:
    """is_holidayのテスト."""

    def test_new_years_day(self):
        """元日は祝日."""
        service = HolidayService()
        assert service.is_holiday(date(2026, 1, 1)) is True

    def test_coming_of_age_day(self):
        """成人の日は祝日."""
        service = HolidayService()
        # 2026年の成人の日は1月12日（1月の第2月曜日）
        assert service.is_holiday(date(2026, 1, 12)) is True

    def test_national_foundation_day(self):
        """建国記念の日は祝日."""
        service = HolidayService()
        assert service.is_holiday(date(2026, 2, 11)) is True

    def test_regular_weekday_is_not_holiday(self):
        """通常の平日は祝日でない."""
        service = HolidayService()
        assert service.is_holiday(date(2026, 2, 2)) is False

    def test_substitute_holiday(self):
        """振替休日の判定."""
        service = HolidayService()
        # 2026-05-06 は振替休日（こどもの日の振替）
        assert service.is_holiday(date(2026, 5, 6)) is True


class TestGetHolidayName:
    """get_holiday_nameのテスト."""

    def test_holiday_returns_name(self):
        """祝日は名前を返す."""
        service = HolidayService()
        name = service.get_holiday_name(date(2026, 1, 1))
        assert name == "元日"

    def test_non_holiday_returns_none(self):
        """非祝日はNoneを返す."""
        service = HolidayService()
        assert service.get_holiday_name(date(2026, 2, 2)) is None

    def test_culture_day_name(self):
        """文化の日の名前確認."""
        service = HolidayService()
        name = service.get_holiday_name(date(2026, 11, 3))
        assert name == "文化の日"


class TestGetHolidaysInMonth:
    """get_holidays_in_monthのテスト."""

    def test_january_has_new_years(self):
        """1月に元日が含まれる."""
        service = HolidayService()
        holidays = service.get_holidays_in_month(2026, 1)
        assert date(2026, 1, 1) in holidays
        assert holidays[date(2026, 1, 1)] == "元日"

    def test_january_has_multiple_holidays(self):
        """1月には複数の祝日がある."""
        service = HolidayService()
        holidays = service.get_holidays_in_month(2026, 1)
        assert len(holidays) >= 2

    def test_june_has_no_holidays(self):
        """6月は祝日がない."""
        service = HolidayService()
        holidays = service.get_holidays_in_month(2026, 6)
        assert holidays == {}


class TestIsSaturday:
    """is_saturdayのテスト."""

    def test_saturday_returns_true(self):
        """土曜日はTrueを返す."""
        service = HolidayService()
        # 2026-02-28 is Saturday
        assert service.is_saturday(date(2026, 2, 28)) is True

    def test_non_saturday_returns_false(self):
        """土曜日以外はFalseを返す."""
        service = HolidayService()
        # 2026-02-27 is Friday
        assert service.is_saturday(date(2026, 2, 27)) is False


class TestIsSunday:
    """is_sundayのテスト."""

    def test_sunday_returns_true(self):
        """日曜日はTrueを返す."""
        service = HolidayService()
        # 2026-03-01 is Sunday
        assert service.is_sunday(date(2026, 3, 1)) is True

    def test_non_sunday_returns_false(self):
        """日曜日以外はFalseを返す."""
        service = HolidayService()
        # 2026-03-02 is Monday
        assert service.is_sunday(date(2026, 3, 2)) is False


class TestCache:
    """キャッシュのテスト."""

    def test_cache_is_populated_on_first_call(self):
        """初回呼び出しでキャッシュが作成される."""
        service = HolidayService()
        assert 2026 not in service._cache
        service.is_holiday(date(2026, 1, 1))
        assert 2026 in service._cache

    def test_cache_reused_on_second_call(self):
        """2回目以降はキャッシュが再利用される."""
        service = HolidayService()
        service.is_holiday(date(2026, 1, 1))
        # キャッシュを空にすることで再利用確認
        service._cache[2026] = {}
        assert service.is_holiday(date(2026, 1, 1)) is False

    def test_clear_cache(self):
        """キャッシュクリアが正しく動作する."""
        service = HolidayService()
        service.is_holiday(date(2026, 1, 1))
        assert len(service._cache) > 0
        service.clear_cache()
        assert len(service._cache) == 0

    def test_different_years_cached_independently(self):
        """異なる年は独立にキャッシュされる."""
        service = HolidayService()
        service.is_holiday(date(2026, 1, 1))
        service.is_holiday(date(2027, 1, 1))
        assert 2026 in service._cache
        assert 2027 in service._cache
