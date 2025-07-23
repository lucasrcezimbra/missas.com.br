import pytest
from model_bakery import baker

from missas.core.models import City


@pytest.mark.django_db
class TestFilterWithSchedule:
    def test_returns_cities_with_schedules(self):
        city_with_schedule = baker.make("core.City")
        parish_with_schedule = baker.make("core.Parish", city=city_with_schedule)
        baker.make("core.Schedule", parish=parish_with_schedule)

        city_without_schedule = baker.make("core.City")
        baker.make("core.Parish", city=city_without_schedule)  # Parish but no schedule

        result = City.objects.filter_with_schedule()

        assert city_with_schedule in result
        assert city_without_schedule not in result
        assert result.count() == 1

    def test_with_multiple_cities_with_schedules(self):
        # City 1 with schedule
        city1 = baker.make("core.City")
        parish1 = baker.make("core.Parish", city=city1)
        baker.make("core.Schedule", parish=parish1)

        # City 2 with schedule
        city2 = baker.make("core.City")
        parish2 = baker.make("core.Parish", city=city2)
        baker.make("core.Schedule", parish=parish2)

        # City 3 without schedule
        city3 = baker.make("core.City")
        baker.make("core.Parish", city=city3)

        result = City.objects.filter_with_schedule()

        assert city1 in result
        assert city2 in result
        assert city3 not in result
        assert result.count() == 2

    def test_with_no_cities(self):
        result = City.objects.filter_with_schedule()

        assert result.count() == 0

    def test_with_no_cities_with_schedules(self):
        city1 = baker.make("core.City")
        baker.make("core.Parish", city=city1)  # Parish but no schedule

        city2 = baker.make("core.City")  # No parish at all

        result = City.objects.filter_with_schedule()

        assert city1 not in result
        assert city2 not in result
        assert result.count() == 0

    def test_chaining_with_other_filters(self):
        state1 = baker.make("core.State", short_name="RN")
        state2 = baker.make("core.State", short_name="SP")

        # City in RN with schedule
        city_rn_with_schedule = baker.make("core.City", state=state1)
        parish_rn = baker.make("core.Parish", city=city_rn_with_schedule)
        baker.make("core.Schedule", parish=parish_rn)

        # City in SP with schedule
        city_sp_with_schedule = baker.make("core.City", state=state2)
        parish_sp = baker.make("core.Parish", city=city_sp_with_schedule)
        baker.make("core.Schedule", parish=parish_sp)

        # City in RN without schedule
        city_rn_without_schedule = baker.make("core.City", state=state1)
        baker.make("core.Parish", city=city_rn_without_schedule)

        result = City.objects.filter_with_schedule().filter(state=state1)

        assert city_rn_with_schedule in result
        assert city_sp_with_schedule not in result
        assert city_rn_without_schedule not in result
        assert result.count() == 1

    def test_city_with_multiple_parishes_and_schedules(self):
        city = baker.make("core.City")
        parish1 = baker.make("core.Parish", city=city)
        parish2 = baker.make("core.Parish", city=city)
        baker.make("core.Schedule", parish=parish1)
        baker.make("core.Schedule", parish=parish2)

        result = City.objects.filter_with_schedule()

        assert city in result
        assert result.count() == 1

    def test_uses_existing_annotation_correctly(self):
        # This test ensures the method returns annotated objects with has_schedules field
        city_with_schedule = baker.make("core.City")
        parish = baker.make("core.Parish", city=city_with_schedule)
        baker.make("core.Schedule", parish=parish)

        result = City.objects.filter_with_schedule().first()

        assert hasattr(result, "has_schedules")
        assert result.has_schedules is True
        assert hasattr(result, "number_of_schedules")
        assert result.number_of_schedules > 0
