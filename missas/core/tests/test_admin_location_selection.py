from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from model_bakery import baker

from missas.core.admin import ScheduleAdmin
from missas.core.models import Location, Schedule

User = get_user_model()


@pytest.fixture
def admin_user():
    return baker.make(User, is_staff=True, is_superuser=True)


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def schedule_admin(admin_site):
    return ScheduleAdmin(Schedule, admin_site)


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
class TestGetScheduleAddressOptions:
    @patch("missas.core.facades.google_maps.settings.GOOGLE_MAPS_API_KEY", "test-key")
    def test_returns_single_option_when_one_result(self):
        from missas.core.facades.google_maps import get_schedule_address_options

        schedule = baker.make(
            "core.Schedule",
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Rua Teste, 123 - Natal, RN",
                    "name": "Igreja Matriz",
                    "place_id": "ChIJ1234567890",
                }
            ],
        }

        with patch("missas.core.facades.google_maps.googlemaps.Client") as mock_client:
            mock_client.return_value.places.return_value = mock_response

            result = get_schedule_address_options(schedule)

            assert result is not None
            assert len(result) == 1
            assert result[0]["name"] == "Igreja Matriz"
            assert result[0]["address"] == "Rua Teste, 123 - Natal, RN"
            assert result[0]["place_id"] == "ChIJ1234567890"

    @patch("missas.core.facades.google_maps.settings.GOOGLE_MAPS_API_KEY", "test-key")
    def test_returns_multiple_options_when_multiple_results(self):
        from missas.core.facades.google_maps import get_schedule_address_options

        schedule = baker.make(
            "core.Schedule",
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Rua Teste, 123 - Natal, RN",
                    "name": "Igreja Matriz Norte",
                    "place_id": "ChIJ1234567890",
                },
                {
                    "formatted_address": "Rua Teste, 456 - Natal, RN",
                    "name": "Igreja Matriz Sul",
                    "place_id": "ChIJ0987654321",
                },
            ],
        }

        with patch("missas.core.facades.google_maps.googlemaps.Client") as mock_client:
            mock_client.return_value.places.return_value = mock_response

            result = get_schedule_address_options(schedule)

            assert result is not None
            assert len(result) == 2
            assert result[0]["name"] == "Igreja Matriz Norte"
            assert result[1]["name"] == "Igreja Matriz Sul"

    @patch("missas.core.facades.google_maps.settings.GOOGLE_MAPS_API_KEY", "test-key")
    def test_returns_none_when_no_results(self):
        from missas.core.facades.google_maps import get_schedule_address_options

        schedule = baker.make(
            "core.Schedule",
            location_name="Igreja Inexistente",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_response = {"status": "ZERO_RESULTS", "results": []}

        with patch("missas.core.facades.google_maps.googlemaps.Client") as mock_client:
            mock_client.return_value.places.return_value = mock_response

            result = get_schedule_address_options(schedule)

            assert result is None


@pytest.mark.django_db
class TestGetScheduleAddressBackwardCompatibility:
    @patch("missas.core.facades.google_maps.settings.GOOGLE_MAPS_API_KEY", "test-key")
    def test_returns_single_result_with_full_response(self):
        from missas.core.facades.google_maps import get_schedule_address

        schedule = baker.make(
            "core.Schedule",
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Rua Teste, 123 - Natal, RN",
                    "name": "Igreja Matriz",
                    "place_id": "ChIJ1234567890",
                }
            ],
        }

        with patch("missas.core.facades.google_maps.googlemaps.Client") as mock_client:
            mock_client.return_value.places.return_value = mock_response

            result = get_schedule_address(schedule)

            assert result is not None
            assert result["name"] == "Igreja Matriz"
            assert result["address"] == "Rua Teste, 123 - Natal, RN"
            assert result["place_id"] == "ChIJ1234567890"
            assert "full_response" in result

    @patch("missas.core.facades.google_maps.settings.GOOGLE_MAPS_API_KEY", "test-key")
    def test_raises_value_error_when_multiple_results(self):
        from missas.core.facades.google_maps import get_schedule_address

        schedule = baker.make(
            "core.Schedule",
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_response = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Rua Teste, 123 - Natal, RN",
                    "name": "Igreja Matriz Norte",
                    "place_id": "ChIJ1234567890",
                },
                {
                    "formatted_address": "Rua Teste, 456 - Natal, RN",
                    "name": "Igreja Matriz Sul",
                    "place_id": "ChIJ0987654321",
                },
            ],
        }

        with patch("missas.core.facades.google_maps.googlemaps.Client") as mock_client:
            mock_client.return_value.places.return_value = mock_response

            with pytest.raises(ValueError):
                get_schedule_address(schedule)


@pytest.mark.django_db
class TestAdminLocationSelection:
    def test_admin_action_redirects_to_selection_when_multiple_results(
        self, schedule_admin, admin_user, request_factory
    ):
        schedule = baker.make(
            "core.Schedule",
            location=None,
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_options = [
            {
                "address": "Rua Teste, 123 - Natal, RN",
                "name": "Igreja Matriz Norte",
                "place_id": "ChIJ1234567890",
            },
            {
                "address": "Rua Teste, 456 - Natal, RN",
                "name": "Igreja Matriz Sul",
                "place_id": "ChIJ0987654321",
            },
        ]

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        with patch(
            "missas.core.admin.get_schedule_address_options"
        ) as mock_get_address:
            mock_get_address.return_value = mock_options

            response = schedule_admin.create_locations_from_addresses(
                request, Schedule.objects.filter(id=schedule.id)
            )

            assert response.status_code == 200
            assert b"Selecionar Localiza" in response.content
            assert b"Igreja Matriz Norte" in response.content
            assert b"Igreja Matriz Sul" in response.content

    def test_admin_action_creates_location_with_single_result(
        self, schedule_admin, admin_user, request_factory
    ):
        schedule = baker.make(
            "core.Schedule",
            location=None,
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
            parish__city__name="Natal",
            parish__city__state__short_name="RN",
        )

        mock_options = [
            {
                "address": "Rua Teste, 123 - Natal, RN",
                "name": "Igreja Matriz",
                "place_id": "ChIJ1234567890",
            }
        ]

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        with patch(
            "missas.core.admin.get_schedule_address_options"
        ) as mock_get_address:
            mock_get_address.return_value = mock_options

            schedule_admin.create_locations_from_addresses(
                request, Schedule.objects.filter(id=schedule.id)
            )

            schedule.refresh_from_db()
            assert schedule.location is not None
            assert schedule.location.name == "Igreja Matriz"

    def test_selection_view_creates_location_from_selected_option(
        self, schedule_admin, admin_user, request_factory
    ):
        schedule = baker.make(
            "core.Schedule",
            location=None,
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
        )

        mock_options = [
            {
                "address": "Rua Teste, 123 - Natal, RN",
                "name": "Igreja Matriz Norte",
                "place_id": "ChIJ1234567890",
            },
            {
                "address": "Rua Teste, 456 - Natal, RN",
                "name": "Igreja Matriz Sul",
                "place_id": "ChIJ0987654321",
            },
        ]

        request = request_factory.post(
            "/admin/core/schedule/select-location/",
            {
                "selected_option": "1",
                "parish_id": str(schedule.parish.id),
                "location_name": "Igreja Matriz",
                "schedule_ids": str(schedule.id),
            },
        )
        request.user = admin_user
        request.session = {
            f"location_options_{schedule.parish.id}_Igreja Matriz": mock_options
        }
        setattr(request, "_messages", FallbackStorage(request))

        response = schedule_admin.select_location_view(request)

        assert response.status_code == 302
        schedule.refresh_from_db()
        assert schedule.location is not None
        assert schedule.location.name == "Igreja Matriz Sul"
        assert schedule.location.address == "Rua Teste, 456 - Natal, RN"

    def test_selection_view_handles_expired_session(
        self, schedule_admin, admin_user, request_factory
    ):
        schedule = baker.make("core.Schedule", location=None)

        request = request_factory.post(
            "/admin/core/schedule/select-location/",
            {
                "selected_option": "0",
                "parish_id": str(schedule.parish.id),
                "location_name": "Igreja Matriz",
                "schedule_ids": str(schedule.id),
            },
        )
        request.user = admin_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        response = schedule_admin.select_location_view(request)

        assert response.status_code == 302
        schedule.refresh_from_db()
        assert schedule.location is None

    def test_existing_location_reused(
        self, schedule_admin, admin_user, request_factory
    ):
        existing_location = baker.make(
            "core.Location",
            name="Igreja Matriz",
            address="Rua Teste, 123",
            google_maps_place_id="ChIJ1234567890",
        )

        schedule1 = baker.make(
            "core.Schedule",
            location=existing_location,
            location_name="Igreja Matriz",
            parish__name="Paróquia Teste",
        )

        schedule2 = baker.make(
            "core.Schedule",
            location=None,
            location_name="Igreja Matriz",
            parish=schedule1.parish,
        )

        request = request_factory.get("/admin/core/schedule/")
        request.user = admin_user
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))

        schedule_admin.create_locations_from_addresses(
            request, Schedule.objects.filter(id=schedule2.id)
        )

        schedule2.refresh_from_db()
        assert schedule2.location == existing_location

        assert Location.objects.count() == 1
