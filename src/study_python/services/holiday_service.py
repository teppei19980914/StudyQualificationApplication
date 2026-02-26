"""日本の祝日判定サービス."""

from __future__ import annotations

import logging
from datetime import date

import jpholiday


logger = logging.getLogger(__name__)


class HolidayService:
    """日本の祝日を判定するサービス.

    祝日データのキャッシュにより、同一年の複数回呼び出しを高速化する.

    Attributes:
        _cache: 年ごとの祝日キャッシュ {year: {date: name}}.
    """

    def __init__(self) -> None:
        """HolidayServiceを初期化する."""
        self._cache: dict[int, dict[date, str]] = {}

    def is_holiday(self, target_date: date) -> bool:
        """指定日が祝日かどうかを判定する.

        Args:
            target_date: 判定対象の日付.

        Returns:
            祝日の場合True.
        """
        holidays = self._get_year_holidays(target_date.year)
        return target_date in holidays

    def get_holiday_name(self, target_date: date) -> str | None:
        """指定日の祝日名を取得する.

        Args:
            target_date: 対象の日付.

        Returns:
            祝日名。祝日でない場合はNone.
        """
        holidays = self._get_year_holidays(target_date.year)
        return holidays.get(target_date)

    def get_holidays_in_month(self, year: int, month: int) -> dict[date, str]:
        """指定年月の祝日を取得する.

        Args:
            year: 年.
            month: 月.

        Returns:
            {日付: 祝日名} の辞書.
        """
        year_holidays = self._get_year_holidays(year)
        return {d: name for d, name in year_holidays.items() if d.month == month}

    def is_saturday(self, target_date: date) -> bool:
        """指定日が土曜日かどうかを判定する.

        Args:
            target_date: 判定対象の日付.

        Returns:
            土曜日の場合True.
        """
        return target_date.weekday() == 5

    def is_sunday(self, target_date: date) -> bool:
        """指定日が日曜日かどうかを判定する.

        Args:
            target_date: 判定対象の日付.

        Returns:
            日曜日の場合True.
        """
        return target_date.weekday() == 6

    def clear_cache(self) -> None:
        """キャッシュをクリアする."""
        self._cache.clear()
        logger.debug("Holiday cache cleared")

    def _get_year_holidays(self, year: int) -> dict[date, str]:
        """指定年の祝日を取得する（キャッシュ付き）.

        Args:
            year: 年.

        Returns:
            {日付: 祝日名} の辞書.
        """
        if year not in self._cache:
            holidays: list[tuple[date, str]] = jpholiday.year_holidays(year)
            self._cache[year] = dict(holidays)
            logger.debug(f"Cached {len(self._cache[year])} holidays for year {year}")
        return self._cache[year]
