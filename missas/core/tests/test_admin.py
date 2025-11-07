import pytest
from django.contrib.admin import site
from model_bakery import baker

from missas.core.admin import LocationAdmin, ScheduleAdmin
from missas.core.models import Location, Schedule


@pytest.mark.django_db
class TestLocationAdmin:
    def test_schedule_filter_not_present(self):
        location_admin = LocationAdmin(Location, site)

        assert (
            not hasattr(location_admin, "list_filter")
            or location_admin.list_filter == ()
        )

    def test_other_fields_present(self):
        location_admin = LocationAdmin(Location, site)

        assert location_admin.list_display == ("name", "address", "maps_link")
        assert location_admin.ordering == ("name",)
        assert location_admin.search_fields == ("name", "address")


@pytest.mark.django_db
class TestScheduleAdmin:
    def test_location_filter_present(self):
        schedule_admin = ScheduleAdmin(Schedule, site)

        filter_fields = [
            f[0] if isinstance(f, tuple) else f for f in schedule_admin.list_filter
        ]
        assert "location" in filter_fields

    def test_location_filter_is_empty_field_filter(self):
        from django.contrib.admin import EmptyFieldListFilter

        schedule_admin = ScheduleAdmin(Schedule, site)

        location_filter = None
        for filter_item in schedule_admin.list_filter:
            if isinstance(filter_item, tuple) and filter_item[0] == "location":
                location_filter = filter_item
                break

        assert location_filter is not None
        assert location_filter[1] == EmptyFieldListFilter

    def test_location_field_in_list_display(self):
        schedule_admin = ScheduleAdmin(Schedule, site)

        assert "location_link" in schedule_admin.list_display

    def test_location_link_method_with_location(self):
        location = baker.make("core.Location", name="Test Location")
        schedule = baker.make("core.Schedule", location=location)

        schedule_admin = ScheduleAdmin(Schedule, site)
        link_html = schedule_admin.location_link(schedule)

        assert "Test Location" in link_html
        assert "admin/core/location" in link_html

    def test_location_link_method_without_location(self):
        schedule = baker.make("core.Schedule", location=None)

        schedule_admin = ScheduleAdmin(Schedule, site)
        link_html = schedule_admin.location_link(schedule)

        assert link_html == "-"
