import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from model_bakery import baker

from missas.core.admin import LocationAdmin
from missas.core.models import Location

User = get_user_model()


@pytest.fixture
def admin_user():
    return baker.make(User, is_staff=True, is_superuser=True)


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def location_admin(admin_site):
    return LocationAdmin(Location, admin_site)


@pytest.mark.django_db
class TestLocationAdminReadonlyFields:
    def test_get_readonly_fields_for_new_object(
        self, location_admin, request_factory, admin_user
    ):
        request = request_factory.get("/admin/core/location/add/")
        request.user = admin_user

        readonly_fields = location_admin.get_readonly_fields(request, obj=None)

        assert "address" not in readonly_fields
        assert "google_maps_place_id" in readonly_fields
        assert "maps_link" in readonly_fields
        assert "formatted_google_maps_response" in readonly_fields

    def test_get_readonly_fields_for_existing_object(
        self, location_admin, request_factory, admin_user
    ):
        request = request_factory.get("/admin/core/location/1/change/")
        request.user = admin_user
        location = baker.make(Location)

        readonly_fields = location_admin.get_readonly_fields(request, obj=location)

        assert "address" in readonly_fields
        assert "google_maps_place_id" in readonly_fields
        assert "maps_link" in readonly_fields
        assert "formatted_google_maps_response" in readonly_fields


@pytest.mark.django_db
class TestLocationAdminSaveModel:
    def test_save_model_creates_location_from_name(
        self, location_admin, request_factory, admin_user, mocker
    ):
        mock_get_location = mocker.patch(
            "missas.core.admin.get_location_by_name",
            return_value={
                "name": "Igreja Matriz",
                "address": "Rua Principal, 123 - Natal, RN",
                "full_response": {"status": "OK", "results": []},
                "place_id": "ChIJ123abc",
            },
        )

        request = request_factory.post("/admin/core/location/add/")
        request.user = admin_user
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        location = Location(name="Igreja Matriz")
        form = mocker.Mock()

        location_admin.save_model(request, location, form, change=False)

        mock_get_location.assert_called_once_with("Igreja Matriz")
        assert location.name == "Igreja Matriz"
        assert location.address == "Rua Principal, 123 - Natal, RN"
        assert location.google_maps_place_id == "ChIJ123abc"
        assert location.google_maps_response == {"status": "OK", "results": []}

    def test_save_model_shows_error_when_location_not_found(
        self, location_admin, request_factory, admin_user, mocker
    ):
        mock_get_location = mocker.patch(
            "missas.core.admin.get_location_by_name", return_value=None
        )

        request = request_factory.post("/admin/core/location/add/")
        request.user = admin_user
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        location = Location(name="NonExistent Church")
        form = mocker.Mock()

        location_admin.save_model(request, location, form, change=False)

        mock_get_location.assert_called_once_with("NonExistent Church")
        messages = list(request._messages)
        assert len(messages) == 1
        assert "Não foi possível encontrar localização" in str(messages[0])

    def test_save_model_shows_error_when_multiple_results(
        self, location_admin, request_factory, admin_user, mocker
    ):
        mock_get_location = mocker.patch(
            "missas.core.admin.get_location_by_name",
            side_effect=ValueError("Multiple results found"),
        )

        request = request_factory.post("/admin/core/location/add/")
        request.user = admin_user
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        location = Location(name="Igreja")
        form = mocker.Mock()

        location_admin.save_model(request, location, form, change=False)

        mock_get_location.assert_called_once_with("Igreja")
        messages = list(request._messages)
        assert len(messages) == 1
        assert "Multiple results found" in str(messages[0])

    def test_save_model_does_not_call_api_on_update(
        self, location_admin, request_factory, admin_user, mocker
    ):
        mock_get_location = mocker.patch("missas.core.admin.get_location_by_name")

        request = request_factory.post("/admin/core/location/1/change/")
        request.user = admin_user
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        location = baker.make(Location)
        form = mocker.Mock()

        location_admin.save_model(request, location, form, change=True)

        mock_get_location.assert_not_called()
