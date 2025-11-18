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
class TestScheduleAdmin:
    def test_reuse_action_exists(self, schedule_admin):
        assert "reuse_existing_locations" in schedule_admin.actions

    def test_create_locations_action_exists(self, schedule_admin):
        assert "create_locations_from_addresses" in schedule_admin.actions


@pytest.mark.django_db
class TestReuseExistingLocationsAction:
    def test_reuse_location_from_same_parish_and_location_name(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)
        location = baker.make(Location)

        existing_schedule = baker.make(
            Schedule,
            parish=parish,
            location=location,
            location_name="Capela São José",
        )
        new_schedule = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=new_schedule.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.reuse_existing_locations(request, queryset)

        new_schedule.refresh_from_db()
        assert new_schedule.location == location
        assert mock_message_user.call_count == 1

    def test_reuse_location_multiple_schedules(
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
        new_schedules = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
            _quantity=3,
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk__in=[s.pk for s in new_schedules])

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.reuse_existing_locations(request, queryset)

        for schedule in new_schedules:
            schedule.refresh_from_db()
            assert schedule.location == location
        assert mock_message_user.call_count == 1

    def test_skip_when_no_matching_location(
        self, schedule_admin, request_factory, admin_user, mocker
    ):
        parish = baker.make(Parish)

        schedule_without_match = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela Inexistente",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_without_match.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.reuse_existing_locations(request, queryset)

        schedule_without_match.refresh_from_db()
        assert schedule_without_match.location is None
        assert mock_message_user.call_count == 1

    def test_different_parish_same_location_name_no_reuse(
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
        schedule_different_parish = baker.make(
            Schedule,
            parish=parish2,
            location=None,
            location_name="Capela São José",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(pk=schedule_different_parish.pk)

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.reuse_existing_locations(request, queryset)

        schedule_different_parish.refresh_from_db()
        assert schedule_different_parish.location is None
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
        schedule_admin.reuse_existing_locations(request, queryset)

        assert mock_message_user.call_count == 1
        call_args = mock_message_user.call_args
        assert "Nenhum horário sem localização encontrado" in call_args[0][1]
        assert call_args[1]["level"] == "warning"

    def test_mixed_success_and_skip(
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
        schedule_with_match = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela São José",
        )
        schedule_without_match = baker.make(
            Schedule,
            parish=parish,
            location=None,
            location_name="Capela Inexistente",
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        queryset = Schedule.objects.filter(
            pk__in=[schedule_with_match.pk, schedule_without_match.pk]
        )

        mock_message_user = mocker.patch.object(schedule_admin, "message_user")
        schedule_admin.reuse_existing_locations(request, queryset)

        schedule_with_match.refresh_from_db()
        schedule_without_match.refresh_from_db()
        assert schedule_with_match.location == location
        assert schedule_without_match.location is None
        assert mock_message_user.call_count == 2
