from unittest.mock import Mock, patch

import pytest

from missas.core.facades.google_maps import (
    _extract_coordinates_from_url,
    _extract_place_id_from_url,
    _unshorten_url,
    get_location_from_google_maps_url,
)


class TestExtractPlaceIdFromUrl:
    def test_extract_place_id_from_query_param(self):
        url = "https://www.google.com/maps/search/?api=1&query=test&query_place_id=ChIJN1t_tDeuEmsRUsoyG83frY4"
        place_id = _extract_place_id_from_url(url)
        assert place_id == "ChIJN1t_tDeuEmsRUsoyG83frY4"

    def test_extract_place_id_from_data_param(self):
        url = "https://www.google.com/maps/place/Igreja+Matriz+de+Nossa+Senhora+da+Apresentação/@-5.7945046,-35.2108267,17z/data=!3m1!4b1!4m6!3m5!1sChIJ123ABC!8m2!3d-5.7945046!4d-35.2082518!16s%2Fg%2F11c5m7wz3q"
        place_id = _extract_place_id_from_url(url)
        assert place_id == "ChIJ123ABC"

    def test_extract_place_id_returns_none_for_invalid_url(self):
        url = "https://www.google.com/maps"
        place_id = _extract_place_id_from_url(url)
        assert place_id is None


class TestExtractCoordinatesFromUrl:
    def test_extract_coordinates_from_standard_url(self):
        url = "https://www.google.com/maps/@-5.7945046,-35.2108267,17z"
        lat, lng = _extract_coordinates_from_url(url)
        assert lat == -5.7945046
        assert lng == -35.2108267

    def test_extract_coordinates_from_place_url(self):
        url = "https://www.google.com/maps/place/Igreja/@-5.7945046,-35.2108267,17z"
        lat, lng = _extract_coordinates_from_url(url)
        assert lat == -5.7945046
        assert lng == -35.2108267

    def test_extract_coordinates_returns_none_for_invalid_url(self):
        url = "https://www.google.com/maps"
        lat, lng = _extract_coordinates_from_url(url)
        assert lat is None
        assert lng is None


class TestUnshortenUrl:
    @patch("missas.core.facades.google_maps.urlopen")
    def test_unshorten_url_success(self, mock_urlopen):
        mock_response = Mock()
        mock_response.url = "https://www.google.com/maps/place/test/@-5.79,-35.21,17z"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = _unshorten_url("https://maps.app.goo.gl/short")
        assert result == "https://www.google.com/maps/place/test/@-5.79,-35.21,17z"

    @patch("missas.core.facades.google_maps.urlopen")
    def test_unshorten_url_handles_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")

        result = _unshorten_url("https://maps.app.goo.gl/short")
        assert result == "https://maps.app.goo.gl/short"


class TestGetLocationFromGoogleMapsUrl:
    @pytest.mark.django_db
    @patch("missas.core.facades.google_maps.settings")
    @patch("missas.core.facades.google_maps.googlemaps.Client")
    @patch("missas.core.facades.google_maps._unshorten_url")
    def test_get_location_from_short_url(
        self, mock_unshorten, mock_gmaps_client, mock_settings
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test-key"
        mock_unshorten.return_value = "https://www.google.com/maps/place/Igreja/@-5.79,-35.21,17z/data=!3m1!4b1!4m6!3m5!1sChIJ123ABC!8m2!3d-5.79!4d-35.21!16s"

        mock_gmaps = Mock()
        mock_gmaps_client.return_value = mock_gmaps
        mock_gmaps.place.return_value = {
            "status": "OK",
            "result": {
                "name": "Igreja Matriz",
                "formatted_address": "Rua Principal, 123 - Centro, Natal - RN",
                "place_id": "ChIJ123ABC",
                "geometry": {"location": {"lat": -5.79, "lng": -35.21}},
            },
        }

        result = get_location_from_google_maps_url("https://maps.app.goo.gl/short")

        assert result is not None
        assert result["name"] == "Igreja Matriz"
        assert result["address"] == "Rua Principal, 123 - Centro, Natal - RN"
        assert result["place_id"] == "ChIJ123ABC"
        assert result["latitude"] == -5.79
        assert result["longitude"] == -35.21
        mock_unshorten.assert_called_once()

    @pytest.mark.django_db
    @patch("missas.core.facades.google_maps.settings")
    @patch("missas.core.facades.google_maps.googlemaps.Client")
    def test_get_location_from_url_with_place_id(
        self, mock_gmaps_client, mock_settings
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test-key"
        mock_gmaps = Mock()
        mock_gmaps_client.return_value = mock_gmaps
        mock_gmaps.place.return_value = {
            "status": "OK",
            "result": {
                "name": "Igreja Matriz",
                "formatted_address": "Rua Principal, 123 - Centro, Natal - RN",
                "place_id": "ChIJ123ABC",
                "geometry": {"location": {"lat": -5.79, "lng": -35.21}},
            },
        }

        url = "https://www.google.com/maps/search/?api=1&query=test&query_place_id=ChIJ123ABC"
        result = get_location_from_google_maps_url(url)

        assert result is not None
        assert result["name"] == "Igreja Matriz"
        assert result["place_id"] == "ChIJ123ABC"
        mock_gmaps.place.assert_called_once()

    @pytest.mark.django_db
    @patch("missas.core.facades.google_maps.settings")
    @patch("missas.core.facades.google_maps.googlemaps.Client")
    def test_get_location_from_url_with_coordinates(
        self, mock_gmaps_client, mock_settings
    ):
        mock_settings.GOOGLE_MAPS_API_KEY = "test-key"
        mock_gmaps = Mock()
        mock_gmaps_client.return_value = mock_gmaps
        mock_gmaps.reverse_geocode.return_value = [
            {
                "formatted_address": "Rua Principal, 123 - Centro, Natal - RN",
                "place_id": "ChIJ123ABC",
            }
        ]

        url = "https://www.google.com/maps/@-5.79,-35.21,17z"
        result = get_location_from_google_maps_url(url)

        assert result is not None
        assert result["address"] == "Rua Principal, 123 - Centro, Natal - RN"
        assert result["place_id"] == "ChIJ123ABC"
        assert result["latitude"] == -5.79
        assert result["longitude"] == -35.21
        mock_gmaps.reverse_geocode.assert_called_once_with(
            (-5.79, -35.21), language="pt-BR"
        )

    @pytest.mark.django_db
    @patch("missas.core.facades.google_maps.settings")
    def test_get_location_returns_none_when_api_key_not_configured(self, mock_settings):
        mock_settings.GOOGLE_MAPS_API_KEY = None

        result = get_location_from_google_maps_url("https://maps.app.goo.gl/short")
        assert result is None

    @pytest.mark.django_db
    @patch("missas.core.facades.google_maps.googlemaps.Client")
    def test_get_location_returns_none_for_invalid_url(self, mock_gmaps_client):
        url = "https://www.google.com/maps"
        result = get_location_from_google_maps_url(url)
        assert result is None
