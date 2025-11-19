import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from model_bakery import baker

from missas.core.admin import ScheduleAdmin
from missas.core.models import Location, Parish, Schedule

User = get_user_model()


@pytest.fixture
def admin_user():
    return baker.make(User, is_staff=True, is_superuser=True)


@pytest.fixture
def schedule_admin():
    return ScheduleAdmin(Schedule, AdminSite())


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
class TestSetLocationsFromSameParish:
    def test_reuse_existing_location_from_same_parish(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        location = baker.make(Location)

        baker.make(
            Schedule,
            parish=parish,
            location=location,
            location_name="Capela São José",
        )
        schedule_without_location = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_without_location.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        schedule_without_location.refresh_from_db()
        assert schedule_without_location.location == location
        assert mock_message_user.call_count == 1

    def test_reuse_location_for_multiple_schedules(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        location = baker.make(Location)

        baker.make(
            Schedule,
            parish=parish,
            location=location,
            location_name="Capela São José",
        )
        schedules_without_location = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
            _quantity=3,
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(
            pk__in=[s.pk for s in schedules_without_location]
        )

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        for schedule in schedules_without_location:
            schedule.refresh_from_db()
            assert schedule.location == location
        assert mock_message_user.call_count == 1

    def test_skip_when_no_existing_location_found(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        schedule_without_location = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_without_location.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        schedule_without_location.refresh_from_db()
        assert schedule_without_location.location is None
        assert mock_message_user.call_count == 1

    def test_different_parishes_do_not_share_locations(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish1 = baker.make(Parish)
        parish2 = baker.make(Parish)
        location = baker.make(Location)

        baker.make(
            Schedule,
            parish=parish1,
            location=location,
            location_name="Capela São José",
        )
        schedule_parish2 = baker.make(
            Schedule,
            parish=parish2,
            location=None,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_parish2.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        schedule_parish2.refresh_from_db()
        assert schedule_parish2.location is None
        assert mock_message_user.call_count == 1

    def test_different_location_names_in_same_parish(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        location1 = baker.make(Location)
        location2 = baker.make(Location)

        baker.make(
            Schedule,
            parish=parish,
            location=location1,
            location_name="Capela São José",
        )
        baker.make(
            Schedule,
            parish=parish,
            location=location2,
            location_name="Capela Santa Maria",
        )
        schedule_without_location = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_without_location.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        schedule_without_location.refresh_from_db()
        assert schedule_without_location.location == location1
        assert mock_message_user.call_count == 1

    def test_warning_when_no_schedules_without_location(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        location = baker.make(Location)
        schedule_with_location = baker.make(
            Schedule,
            parish=parish,
            location=location,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_with_location.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        assert mock_message_user.call_count == 1
        call_args = mock_message_user.call_args
        assert "Nenhum horário sem localização encontrado" in call_args[0][1]
        assert call_args[1]["level"] == "warning"

    def test_mixed_results_with_some_updated_some_skipped(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        location = baker.make(Location)

        baker.make(
            Schedule,
            parish=parish,
            location=location,
            location_name="Capela São José",
        )
        schedule_to_update = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
        )
        schedule_to_skip = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela Santa Maria",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(
            pk__in=[schedule_to_update.pk, schedule_to_skip.pk]
        )

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.set_locations_from_same_parish(request, queryset)

        schedule_to_update.refresh_from_db()
        schedule_to_skip.refresh_from_db()
        assert schedule_to_update.location == location
        assert schedule_to_skip.location is None
        assert mock_message_user.call_count == 2
