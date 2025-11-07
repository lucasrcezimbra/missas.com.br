from unittest.mock import Mock, patch

import pytest

from missas.core.facades.google_maps import get_schedule_address


@pytest.mark.django_db
class TestGetScheduleAddress:
    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps.settings")
    def test_raises_error_when_multiple_results(self, mock_settings, mock_gmaps_client):
        from model_bakery import baker

        mock_settings.GOOGLE_MAPS_API_KEY = "test-key"
        schedule = baker.make("core.Schedule", location_name="Igreja Matriz")

        mock_gmaps = Mock()
        mock_gmaps_client.return_value = mock_gmaps
        mock_gmaps.places.return_value = {
            "status": "OK",
            "results": [
                {
                    "name": "Igreja 1",
                    "formatted_address": "Address 1",
                    "place_id": "place1",
                },
                {
                    "name": "Igreja 2",
                    "formatted_address": "Address 2",
                    "place_id": "place2",
                },
            ],
        }

        with pytest.raises(ValueError) as excinfo:
            get_schedule_address(schedule)

        assert "Multiple results found" in str(excinfo.value)
        assert "2 results" in str(excinfo.value)

    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps.settings")
    def test_uses_search_url_format(self, mock_settings, mock_gmaps_client):
        from model_bakery import baker

        mock_settings.GOOGLE_MAPS_API_KEY = "test-key"
        schedule = baker.make("core.Schedule", location_name="Igreja Matriz")

        mock_gmaps = Mock()
        mock_gmaps_client.return_value = mock_gmaps
        mock_gmaps.places.return_value = {
            "status": "OK",
            "results": [
                {
                    "name": "Igreja Matriz",
                    "formatted_address": "Rua Principal, 123, Natal/RN",
                    "place_id": "place1",
                }
            ],
        }

        result = get_schedule_address(schedule)

        assert result is not None
        assert "google.com/maps/search/?api=1&query=" in result["url"]
        assert "place_id" not in result["url"]
        assert "Igreja+Matriz" in result["url"]

    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps.settings")
    def test_returns_none_when_no_results(self, mock_settings, mock_gmaps_client):
        from model_bakery import baker

        mock_settings.GOOGLE_MAPS_API_KEY = "test-key"
        schedule = baker.make("core.Schedule", location_name="Igreja Inexistente")

        mock_gmaps = Mock()
        mock_gmaps_client.return_value = mock_gmaps
        mock_gmaps.places.return_value = {"status": "ZERO_RESULTS", "results": []}

        result = get_schedule_address(schedule)

        assert result is None

    @patch("missas.core.facades.google_maps.settings")
    def test_returns_none_when_no_api_key(self, mock_settings):
        from model_bakery import baker

        mock_settings.GOOGLE_MAPS_API_KEY = None
        schedule = baker.make("core.Schedule", location_name="Igreja")

        result = get_schedule_address(schedule)

        assert result is None
