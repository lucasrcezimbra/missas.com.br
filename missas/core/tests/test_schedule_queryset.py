from datetime import date

import pytest
from model_bakery import baker

from missas.core.models import Schedule


@pytest.mark.django_db
class TestFilterVerified:
    def test_returns_verified_schedules(self):
        verified_schedule = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        unverified_schedule = baker.make("core.Schedule", verified_at=None)

        result = Schedule.objects.filter_verified()

        assert verified_schedule in result
        assert unverified_schedule not in result
        assert result.count() == 1

    def test_with_multiple_verified_schedules(self):
        verified1 = baker.make("core.Schedule", verified_at=date(2024, 1, 1))
        verified2 = baker.make("core.Schedule", verified_at=date(2024, 2, 1))
        unverified = baker.make("core.Schedule", verified_at=None)

        result = Schedule.objects.filter_verified()

        assert verified1 in result
        assert verified2 in result
        assert unverified not in result
        assert result.count() == 2

    def test_with_no_schedules(self):
        result = Schedule.objects.filter_verified()

        assert result.count() == 0

    def test_chaining_with_other_filters(self):
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

        result = Schedule.objects.filter_verified().filter(type=Schedule.Type.MASS)

        assert verified_mass in result
        assert verified_confession not in result
        assert unverified_mass not in result
        assert result.count() == 1
