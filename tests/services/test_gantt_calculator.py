"""GanttCalculatorのテスト."""

from datetime import date

from study_python.services.gantt_calculator import GanttCalculator, TimelineRange


class TestTimelineRange:
    """TimelineRangeのテスト."""

    def test_total_days(self):
        tr = TimelineRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        assert tr.total_days == 31

    def test_total_days_single_day(self):
        tr = TimelineRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 1))
        assert tr.total_days == 1


class TestGanttCalculatorTimeline:
    """calculate_timelineのテスト."""

    def test_empty_tasks_returns_default(self):
        calc = GanttCalculator()
        timeline = calc.calculate_timeline([])
        assert timeline.start_date < date.today()
        assert timeline.end_date > date.today()

    def test_single_task(self):
        calc = GanttCalculator()
        timeline = calc.calculate_timeline(
            [(date(2026, 3, 1), date(2026, 3, 31))], padding_days=7
        )
        assert timeline.start_date == date(2026, 2, 22)
        assert timeline.end_date == date(2026, 4, 7)

    def test_multiple_tasks_uses_extremes(self):
        calc = GanttCalculator()
        timeline = calc.calculate_timeline(
            [
                (date(2026, 3, 1), date(2026, 3, 15)),
                (date(2026, 4, 1), date(2026, 5, 31)),
            ],
            padding_days=0,
        )
        assert timeline.start_date == date(2026, 3, 1)
        assert timeline.end_date == date(2026, 5, 31)


class TestGanttCalculatorBarGeometry:
    """calculate_bar_geometryのテスト."""

    def test_bar_at_timeline_start(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        bar = calc.calculate_bar_geometry(
            date(2026, 3, 1), date(2026, 3, 10), 50, timeline
        )
        assert bar.x == 0.0
        assert bar.width == 100.0  # 10 days * 10px
        assert bar.progress_width == 50.0  # 50%

    def test_bar_offset_from_start(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        bar = calc.calculate_bar_geometry(
            date(2026, 3, 6), date(2026, 3, 10), 0, timeline
        )
        assert bar.x == 50.0  # 5 days * 10px
        assert bar.width == 50.0  # 5 days * 10px
        assert bar.progress_width == 0.0

    def test_bar_100_percent_progress(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        bar = calc.calculate_bar_geometry(
            date(2026, 3, 1), date(2026, 3, 10), 100, timeline
        )
        assert bar.progress_width == bar.width


class TestGanttCalculatorBarY:
    """calculate_bar_yのテスト."""

    def test_first_row(self):
        calc = GanttCalculator(header_height=50, row_height=40, bar_margin=8)
        assert calc.calculate_bar_y(0) == 58.0  # 50 + 0*40 + 8

    def test_second_row(self):
        calc = GanttCalculator(header_height=50, row_height=40, bar_margin=8)
        assert calc.calculate_bar_y(1) == 98.0  # 50 + 1*40 + 8


class TestGanttCalculatorDateToX:
    """date_to_xのテスト."""

    def test_date_at_start(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        assert calc.date_to_x(date(2026, 3, 1), timeline) == 0.0

    def test_date_offset(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        assert calc.date_to_x(date(2026, 3, 11), timeline) == 100.0


class TestGanttCalculatorMonthBoundaries:
    """get_month_boundariesのテスト."""

    def test_single_month(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        boundaries = calc.get_month_boundaries(timeline)
        assert len(boundaries) == 1
        assert boundaries[0][0] == date(2026, 3, 1)

    def test_multi_month(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 2, 15), end_date=date(2026, 5, 15)
        )
        boundaries = calc.get_month_boundaries(timeline)
        dates = [b[0] for b in boundaries]
        assert date(2026, 3, 1) in dates
        assert date(2026, 4, 1) in dates
        assert date(2026, 5, 1) in dates

    def test_year_boundary(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 11, 15), end_date=date(2027, 2, 15)
        )
        boundaries = calc.get_month_boundaries(timeline)
        dates = [b[0] for b in boundaries]
        assert date(2026, 12, 1) in dates
        assert date(2027, 1, 1) in dates
        assert date(2027, 2, 1) in dates


class TestGanttCalculatorSceneDimensions:
    """シーンサイズ計算のテスト."""

    def test_scene_width(self):
        calc = GanttCalculator(pixels_per_day=10.0)
        timeline = TimelineRange(
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        assert calc.calculate_scene_width(timeline) == 310.0  # 31 * 10

    def test_scene_height(self):
        calc = GanttCalculator(header_height=50, row_height=40)
        assert calc.calculate_scene_height(5) == 250.0  # 50 + 5*40

    def test_scene_height_minimum(self):
        calc = GanttCalculator(header_height=50, row_height=40)
        assert calc.calculate_scene_height(0) == 90.0  # 50 + 1*40
