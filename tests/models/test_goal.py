"""Goalモデルのテスト."""

from datetime import date, datetime

import pytest

from study_python.models.goal import GOAL_COLORS, Goal, WhenType


class TestGoalCreation:
    """Goalの生成テスト."""

    def test_create_goal_with_required_fields(self):
        goal = Goal(
            why="キャリアアップ",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="Udemyで学習",
        )
        assert goal.why == "キャリアアップ"
        assert goal.when_target == "2026-06-30"
        assert goal.when_type == WhenType.DATE
        assert goal.what == "AWS資格"
        assert goal.how == "Udemyで学習"
        assert goal.color == GOAL_COLORS[0]
        assert goal.id  # UUIDが生成される

    def test_create_goal_with_period_type(self):
        goal = Goal(
            why="スキルアップ",
            when_target="3ヶ月以内",
            when_type=WhenType.PERIOD,
            what="TOEIC 800点",
            how="毎日30分の英語学習",
        )
        assert goal.when_type == WhenType.PERIOD
        assert goal.when_target == "3ヶ月以内"

    def test_create_goal_with_custom_color(self):
        goal = Goal(
            why="テスト",
            when_target="2026-12-31",
            when_type=WhenType.DATE,
            what="テスト",
            how="テスト",
            color="#FF0000",
        )
        assert goal.color == "#FF0000"

    def test_create_goal_generates_unique_ids(self):
        goal1 = Goal(
            why="a", when_target="b", when_type=WhenType.DATE, what="c", how="d"
        )
        goal2 = Goal(
            why="a", when_target="b", when_type=WhenType.DATE, what="c", how="d"
        )
        assert goal1.id != goal2.id


class TestGoalGetTargetDate:
    """get_target_dateのテスト."""

    def test_get_target_date_with_date_type(self):
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        assert goal.get_target_date() == date(2026, 6, 30)

    def test_get_target_date_with_period_type_returns_none(self):
        goal = Goal(
            why="test",
            when_target="3ヶ月",
            when_type=WhenType.PERIOD,
            what="test",
            how="test",
        )
        assert goal.get_target_date() is None

    def test_get_target_date_with_invalid_date_returns_none(self):
        goal = Goal(
            why="test",
            when_target="invalid-date",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        assert goal.get_target_date() is None


class TestGoalSerialization:
    """Goalの直列化テスト."""

    def test_to_dict(self):
        now = datetime(2026, 2, 25, 10, 0, 0)
        goal = Goal(
            id="test-id",
            why="キャリアアップ",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="Udemyで学習",
            created_at=now,
            updated_at=now,
            color="#4A9EFF",
        )
        d = goal.to_dict()
        assert d["id"] == "test-id"
        assert d["why"] == "キャリアアップ"
        assert d["when_target"] == "2026-06-30"
        assert d["when_type"] == "date"
        assert d["what"] == "AWS資格"
        assert d["how"] == "Udemyで学習"
        assert d["created_at"] == "2026-02-25T10:00:00"
        assert d["updated_at"] == "2026-02-25T10:00:00"
        assert d["color"] == "#4A9EFF"

    def test_from_dict(self):
        data = {
            "id": "test-id",
            "why": "テスト理由",
            "when_target": "2026-12-31",
            "when_type": "period",
            "what": "テスト対象",
            "how": "テスト方法",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-02T00:00:00",
            "color": "#FF6B6B",
        }
        goal = Goal.from_dict(data)
        assert goal.id == "test-id"
        assert goal.why == "テスト理由"
        assert goal.when_type == WhenType.PERIOD
        assert goal.color == "#FF6B6B"
        assert goal.created_at == datetime(2026, 1, 1, 0, 0, 0)

    def test_from_dict_without_color_uses_default(self):
        data = {
            "id": "test-id",
            "why": "test",
            "when_target": "2026-12-31",
            "when_type": "date",
            "what": "test",
            "how": "test",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }
        goal = Goal.from_dict(data)
        assert goal.color == GOAL_COLORS[0]

    def test_roundtrip_serialization(self):
        original = Goal(
            why="往復テスト",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="テスト",
        )
        restored = Goal.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.why == original.why
        assert restored.when_type == original.when_type
        assert restored.what == original.what


class TestWhenType:
    """WhenType列挙型のテスト."""

    def test_date_value(self):
        assert WhenType.DATE.value == "date"

    def test_period_value(self):
        assert WhenType.PERIOD.value == "period"

    def test_from_string(self):
        assert WhenType("date") == WhenType.DATE
        assert WhenType("period") == WhenType.PERIOD

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            WhenType("invalid")
