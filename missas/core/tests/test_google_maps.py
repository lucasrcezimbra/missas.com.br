import pytest

from missas.core.facades.google_maps import get_location_by_name


class TestGetLocationByName:
    def test_returns_none_when_api_key_not_configured(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = None

        result = get_location_by_name("Igreja Matriz")

        assert result is None

    def test_returns_none_when_location_name_is_empty(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        result = get_location_by_name("")

        assert result is None

    def test_returns_none_when_location_name_is_whitespace(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        result = get_location_by_name("   ")

        assert result is None

    def test_returns_location_data_when_found(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        mock_client = mocker.Mock()
        mock_client.places.return_value = {
            "status": "OK",
            "results": [
                {
                    "name": "Igreja Matriz",
                    "formatted_address": "Rua Principal, 123 - Natal, RN",
                    "place_id": "ChIJ123abc",
                }
            ],
        }

        mocker.patch(
            "missas.core.facades.google_maps.googlemaps.Client",
            return_value=mock_client,
        )

        result = get_location_by_name("Igreja Matriz")

        assert result is not None
        assert result["name"] == "Igreja Matriz"
        assert result["address"] == "Rua Principal, 123 - Natal, RN"
        assert result["place_id"] == "ChIJ123abc"
        assert result["full_response"]["status"] == "OK"

    def test_returns_none_when_no_results(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        mock_client = mocker.Mock()
        mock_client.places.return_value = {
            "status": "ZERO_RESULTS",
            "results": [],
        }

        mocker.patch(
            "missas.core.facades.google_maps.googlemaps.Client",
            return_value=mock_client,
        )

        result = get_location_by_name("NonExistent Church")

        assert result is None

    def test_raises_error_when_multiple_results(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        mock_client = mocker.Mock()
        mock_client.places.return_value = {
            "status": "OK",
            "results": [
                {
                    "name": "Igreja 1",
                    "formatted_address": "Address 1",
                    "place_id": "ChIJ123",
                },
                {
                    "name": "Igreja 2",
                    "formatted_address": "Address 2",
                    "place_id": "ChIJ456",
                },
            ],
        }

        mocker.patch(
            "missas.core.facades.google_maps.googlemaps.Client",
            return_value=mock_client,
        )

        with pytest.raises(ValueError) as exc_info:
            get_location_by_name("Igreja")

        assert "Multiple results found" in str(exc_info.value)

    def test_returns_none_when_api_error(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        mock_client = mocker.Mock()
        mock_client.places.side_effect = Exception("API Error")

        mocker.patch(
            "missas.core.facades.google_maps.googlemaps.Client",
            return_value=mock_client,
        )

        result = get_location_by_name("Igreja Matriz")

        assert result is None

    def test_calls_google_places_with_correct_parameters(self, mocker, settings):
        settings.GOOGLE_MAPS_API_KEY = "test-key"

        mock_client = mocker.Mock()
        mock_client.places.return_value = {
            "status": "OK",
            "results": [
                {
                    "name": "Igreja Matriz",
                    "formatted_address": "Rua Principal, 123",
                    "place_id": "ChIJ123",
                }
            ],
        }

        mocker.patch(
            "missas.core.facades.google_maps.googlemaps.Client",
            return_value=mock_client,
        )

        get_location_by_name("  Igreja Matriz  ")

        mock_client.places.assert_called_once_with(
            query="Igreja Matriz",
            language="pt-BR",
            region="br",
            type="church",
        )
