from unittest.mock import Mock, patch

import pytest

from missas.core.facades.google_maps import (
    _extract_place_id_from_url,
    get_place_from_url,
)


class TestExtractPlaceIdFromUrl:
    @patch("missas.core.facades.google_maps.requests.head")
    def test_extract_from_shortened_url(self, mock_head):
        mock_response = Mock()
        mock_response.url = "https://www.google.com/maps/place/data=!1sChIJtest123"
        mock_head.return_value = mock_response

        place_id = _extract_place_id_from_url("https://maps.app.goo.gl/test123")

        assert place_id == "ChIJtest123"
        mock_head.assert_called_once()

    def test_extract_from_query_place_id(self):
        url = "https://www.google.com/maps/search/?api=1&query=Test&query_place_id=ChIJtest123"
        place_id = _extract_place_id_from_url(url)
        assert place_id == "ChIJtest123"

    def test_extract_from_place_url_with_data(self):
        url = "https://www.google.com/maps/place/Test+Church/data=!1sChIJtest123!2s"
        place_id = _extract_place_id_from_url(url)
        assert place_id == "ChIJtest123"

    def test_extract_from_url_with_place_id_in_path(self):
        url = "https://www.google.com/maps/ChIJtest123"
        place_id = _extract_place_id_from_url(url)
        assert place_id == "ChIJtest123"

    def test_returns_none_for_invalid_url(self):
        url = "https://www.example.com/invalid"
        place_id = _extract_place_id_from_url(url)
        assert place_id is None


class TestGetPlaceFromUrl:
    @pytest.fixture
    def mock_place_response(self):
        return {
            "status": "OK",
            "result": {
                "name": "Igreja Matriz",
                "formatted_address": "Rua Principal, 123, Natal - RN, Brazil",
                "place_id": "ChIJtest123",
                "geometry": {
                    "location": {
                        "lat": -5.795000,
                        "lng": -35.211000,
                    }
                },
            },
        }

    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps._extract_place_id_from_url")
    @patch("missas.core.facades.google_maps.settings")
    def test_returns_place_data_for_valid_url(
        self, mock_settings, mock_extract, mock_gmaps_client, mock_place_response
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test_api_key"
        mock_extract.return_value = "ChIJtest123"

        mock_client_instance = Mock()
        mock_client_instance.place.return_value = mock_place_response
        mock_gmaps_client.return_value = mock_client_instance

        result = get_place_from_url("https://maps.app.goo.gl/test123")

        assert result is not None
        assert result["name"] == "Igreja Matriz"
        assert result["address"] == "Rua Principal, 123, Natal - RN, Brazil"
        assert result["place_id"] == "ChIJtest123"
        assert result["latitude"] == -5.795000
        assert result["longitude"] == -35.211000
        assert "full_response" in result

    @patch("missas.core.facades.google_maps._extract_place_id_from_url")
    @patch("missas.core.facades.google_maps.settings")
    def test_raises_value_error_when_place_id_not_found(
        self, mock_settings, mock_extract
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test_api_key"
        mock_extract.return_value = None

        with pytest.raises(ValueError, match="Could not extract place_id from URL"):
            get_place_from_url("https://invalid.url")

    @patch("missas.core.facades.google_maps.settings")
    def test_returns_none_when_api_key_not_configured(self, mock_settings):
        mock_settings.GOOGLE_MAPS_API_KEY = None

        result = get_place_from_url("https://maps.app.goo.gl/test123")

        assert result is None

    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps._extract_place_id_from_url")
    @patch("missas.core.facades.google_maps.settings")
    def test_returns_none_when_place_not_found(
        self, mock_settings, mock_extract, mock_gmaps_client
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test_api_key"
        mock_extract.return_value = "ChIJtest123"

        mock_client_instance = Mock()
        mock_client_instance.place.return_value = {
            "status": "NOT_FOUND",
            "result": None,
        }
        mock_gmaps_client.return_value = mock_client_instance

        result = get_place_from_url("https://maps.app.goo.gl/test123")

        assert result is None

    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps._extract_place_id_from_url")
    @patch("missas.core.facades.google_maps.settings")
    def test_raises_value_error_on_api_error(
        self, mock_settings, mock_extract, mock_gmaps_client
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test_api_key"
        mock_extract.return_value = "ChIJtest123"

        mock_client_instance = Mock()
        mock_client_instance.place.side_effect = Exception("API Error")
        mock_gmaps_client.return_value = mock_client_instance

        with pytest.raises(ValueError, match="Error processing Google Maps URL"):
            get_place_from_url("https://maps.app.goo.gl/test123")
