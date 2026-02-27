"""ActivityChartSectionのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.activity_chart_section import (
    _PERIOD_LABELS,
    ActivityChartSection,
)
from study_python.services.study_stats_calculator import (
    ActivityBucketData,
    ActivityChartData,
    ActivityPeriodType,
)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


def _make_chart_data(
    period_type: ActivityPeriodType,
    total_minutes: int = 60,
) -> ActivityChartData:
    """テスト用チャートデータを作成する."""
    return ActivityChartData(
        period_type=period_type,
        buckets=[
            ActivityBucketData(
                label="test",
                total_minutes=total_minutes,
                period_start=date(2026, 1, 1),
                period_end=date(2026, 12, 31),
            )
        ],
        max_minutes=total_minutes,
    )


class TestActivityChartSection:
    """ActivityChartSectionのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)
        assert section is not None

    def test_combo_has_4_items(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)
        assert section._combo.count() == 4

    def test_combo_order(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)
        assert section._combo.itemText(0) == "日別"
        assert section._combo.itemText(1) == "週別"
        assert section._combo.itemText(2) == "月別"
        assert section._combo.itemText(3) == "年別"

    def test_default_selection_is_daily(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)
        assert section._combo.currentIndex() == 0
        assert section._combo.currentText() == "日別"

    def test_set_all_data_stores_data(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)

        all_data = {
            ActivityPeriodType.DAILY: _make_chart_data(ActivityPeriodType.DAILY, 30),
            ActivityPeriodType.WEEKLY: _make_chart_data(ActivityPeriodType.WEEKLY, 60),
            ActivityPeriodType.MONTHLY: _make_chart_data(
                ActivityPeriodType.MONTHLY, 120
            ),
            ActivityPeriodType.YEARLY: _make_chart_data(ActivityPeriodType.YEARLY, 240),
        }
        section.set_all_data(all_data)
        assert len(section._all_data) == 4

    def test_set_all_data_updates_chart_with_default(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)

        daily_data = _make_chart_data(ActivityPeriodType.DAILY, 45)
        section.set_all_data({ActivityPeriodType.DAILY: daily_data})

        # Default is daily, so chart should have activity_data set
        assert section._chart._activity_data is not None
        assert section._chart._activity_data.max_minutes == 45

    def test_combo_change_updates_chart(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)

        all_data = {
            ActivityPeriodType.DAILY: _make_chart_data(ActivityPeriodType.DAILY, 30),
            ActivityPeriodType.MONTHLY: _make_chart_data(
                ActivityPeriodType.MONTHLY, 120
            ),
        }
        section.set_all_data(all_data)

        # Switch to monthly (index 2)
        section._combo.setCurrentIndex(2)
        assert section._chart._activity_data is not None
        assert section._chart._activity_data.max_minutes == 120

    def test_combo_change_to_missing_data(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)

        # Only daily data available
        section.set_all_data(
            {ActivityPeriodType.DAILY: _make_chart_data(ActivityPeriodType.DAILY, 30)}
        )

        # Switch to yearly (index 3) — no data available, chart stays as-is
        section._combo.setCurrentIndex(3)
        # chart still has daily data from previous set
        assert section._chart._activity_data is not None

    def test_period_labels_match_enum(self):
        types_in_labels = {pt for pt, _label in _PERIOD_LABELS}
        assert types_in_labels == set(ActivityPeriodType)

    def test_has_chart_child(self, qtbot, theme_manager):
        section = ActivityChartSection(theme_manager)
        qtbot.addWidget(section)
        assert section._chart is not None
