from datetime import date

import pytest
from model_bakery import baker

from missas.core.models import Schedule


@pytest.mark.django_db
class TestScheduleQuerySet:
    def test_filter_verified_default_returns_verified_schedules(self):
        # Create schedules - some verified, some not
        verified_schedule = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        unverified_schedule = baker.make("core.Schedule", verified_at=None)

        # Test default behavior (should return verified)
        result = Schedule.objects.filter_verified()

        assert verified_schedule in result
        assert unverified_schedule not in result
        assert result.count() == 1

    def test_filter_verified_true_returns_verified_schedules(self):
        # Create schedules - some verified, some not
        verified_schedule = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        unverified_schedule = baker.make("core.Schedule", verified_at=None)

        # Test explicit True
        result = Schedule.objects.filter_verified(True)

        assert verified_schedule in result
        assert unverified_schedule not in result
        assert result.count() == 1

    def test_filter_verified_false_returns_unverified_schedules(self):
        # Create schedules - some verified, some not
        verified_schedule = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        unverified_schedule = baker.make("core.Schedule", verified_at=None)

        # Test False
        result = Schedule.objects.filter_verified(False)

        assert unverified_schedule in result
        assert verified_schedule not in result
        assert result.count() == 1

    def test_filter_verified_with_multiple_verified_schedules(self):
        # Create multiple verified schedules
        verified1 = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        verified2 = baker.make("core.Schedule", verified_at=date(2024, 2, 1))
        unverified = baker.make("core.Schedule", verified_at=None)

        result = Schedule.objects.filter_verified(True)

        assert verified1 in result
        assert verified2 in result
        assert unverified not in result
        assert result.count() == 2

    def test_filter_verified_with_multiple_unverified_schedules(self):
        # Create multiple unverified schedules
        verified = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        unverified1 = baker.make("core.Schedule", verified_at=None)
        unverified2 = baker.make("core.Schedule", verified_at=None)

        result = Schedule.objects.filter_verified(False)

        assert unverified1 in result
        assert unverified2 in result
        assert verified not in result
        assert result.count() == 2

    def test_filter_verified_with_no_schedules(self):
        # Test with empty database
        result_verified = Schedule.objects.filter_verified(True)
        result_unverified = Schedule.objects.filter_verified(False)

        assert result_verified.count() == 0
        assert result_unverified.count() == 0

    def test_filter_verified_chaining_with_other_filters(self):
        # Test that filter_verified can be chained with other filters
        parish = baker.make("core.Parish")
        verified_mass = baker.make(
            "core.Schedule",
            verified_at=date(2024, 1, 1),
            type=Schedule.Type.MASS,
            parish=parish,
        )
        verified_confession = baker.make(
            "core.Schedule",
            verified_at=date(2024, 1, 1),
            type=Schedule.Type.CONFESSION,
            parish=parish,
        )
        unverified_mass = baker.make(
            "core.Schedule", verified_at=None, type=Schedule.Type.MASS, parish=parish
        )

        # Filter for verified masses only
        result = Schedule.objects.filter_verified(True).filter(type=Schedule.Type.MASS)

        assert verified_mass in result
        assert verified_confession not in result
        assert unverified_mass not in result
        assert result.count() == 1
