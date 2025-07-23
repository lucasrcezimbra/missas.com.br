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
        city_with_schedule_1 = baker.make("core.City")
        parish1 = baker.make("core.Parish", city=city_with_schedule_1)
        baker.make("core.Schedule", parish=parish1)

        city_with_schedule_2 = baker.make("core.City")
        parish2 = baker.make("core.Parish", city=city_with_schedule_2)
        baker.make("core.Schedule", parish=parish2)

        city_without_schedule = baker.make("core.City")
        baker.make("core.Parish", city=city_without_schedule)

        result = City.objects.filter_with_schedule()

        assert city_with_schedule_1 in result
        assert city_with_schedule_2 in result
        assert city_without_schedule not in result
        assert result.count() == 2

    def test_with_no_cities(self):
        result = City.objects.filter_with_schedule()

        assert result.count() == 0

    def test_with_no_cities_with_schedules(self):
        city_with_parish_no_schedule = baker.make("core.City")
        baker.make(
            "core.Parish", city=city_with_parish_no_schedule
        )  # Parish but no schedule

        city_without_parish = baker.make("core.City")  # No parish at all

        result = City.objects.filter_with_schedule()

        assert city_with_parish_no_schedule not in result
        assert city_without_parish not in result
        assert result.count() == 0

    def test_chaining_with_other_filters(self):
        state_rn = baker.make("core.State", short_name="RN")
        state_sp = baker.make("core.State", short_name="SP")

        city_rn_with_schedule = baker.make("core.City", state=state_rn)
        parish_rn = baker.make("core.Parish", city=city_rn_with_schedule)
        baker.make("core.Schedule", parish=parish_rn)

        city_sp_with_schedule = baker.make("core.City", state=state_sp)
        parish_sp = baker.make("core.Parish", city=city_sp_with_schedule)
        baker.make("core.Schedule", parish=parish_sp)

        city_rn_without_schedule = baker.make("core.City", state=state_rn)
        baker.make("core.Parish", city=city_rn_without_schedule)

        result = City.objects.filter_with_schedule().filter(state=state_rn)

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
