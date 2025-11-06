import pytest
import requests
import responses
from model_bakery import baker

from missas.core.facades.google_maps import get_schedule_address


@pytest.fixture
def schedule_with_location():
    """Create a schedule with location name (not matriz)."""
    parish = baker.make("core.Parish", name="Paróquia São José")
    return baker.make(
        "core.Schedule",
        parish=parish,
        location_name="Capela Nossa Senhora",
    )


@pytest.fixture
def schedule_with_matriz():
    """Create a schedule with matriz location."""
    parish = baker.make("core.Parish", name="Paróquia São José")
    return baker.make(
        "core.Schedule",
        parish=parish,
        location_name="Matriz",
    )


@pytest.fixture
def schedule_without_location():
    """Create a schedule without location name."""
    parish = baker.make("core.Parish", name="Paróquia São José")
    return baker.make(
        "core.Schedule",
        parish=parish,
        location_name="",
    )


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_success(schedule_with_location, settings):
    """Test successful address retrieval from Google Places API."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "OK",
            "results": [
                {
                    "name": "Capela Nossa Senhora",
                    "formatted_address": "Rua Exemplo, 123 - Centro, Natal - RN, Brasil",
                    "geometry": {
                        "location": {
                            "lat": -5.7945,
                            "lng": -35.211,
                        }
                    },
                }
            ],
        },
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is not None
    assert result["address"] == "Rua Exemplo, 123 - Centro, Natal - RN, Brasil"
    assert result["lat"] == -5.7945
    assert result["lng"] == -35.211


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_with_matriz(schedule_with_matriz, settings):
    """Test address retrieval for matriz location includes parish name."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "OK",
            "results": [
                {
                    "name": "Paróquia São José",
                    "formatted_address": "Av. Principal, 456 - Centro, Natal - RN, Brasil",
                    "geometry": {
                        "location": {
                            "lat": -5.7945,
                            "lng": -35.211,
                        }
                    },
                }
            ],
        },
        status=200,
    )

    result = get_schedule_address(schedule_with_matriz)

    assert result is not None
    assert result["address"] == "Av. Principal, 456 - Centro, Natal - RN, Brasil"


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_without_location(schedule_without_location, settings):
    """Test address retrieval without location name uses parish name."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "OK",
            "results": [
                {
                    "name": "Paróquia São José",
                    "formatted_address": "Av. Principal, 456 - Centro, Natal - RN, Brasil",
                    "geometry": {
                        "location": {
                            "lat": -5.7945,
                            "lng": -35.211,
                        }
                    },
                }
            ],
        },
        status=200,
    )

    result = get_schedule_address(schedule_without_location)

    assert result is not None
    assert result["address"] == "Av. Principal, 456 - Centro, Natal - RN, Brasil"


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_no_results(schedule_with_location, settings):
    """Test when API returns no results."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "ZERO_RESULTS",
            "results": [],
        },
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is None


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_invalid_request(schedule_with_location, settings):
    """Test when API returns INVALID_REQUEST status."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "INVALID_REQUEST",
            "results": [],
        },
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is None


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_http_error(schedule_with_location, settings):
    """Test when API returns HTTP error."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={"error": "Internal Server Error"},
        status=500,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is None


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_network_error(schedule_with_location, settings):
    """Test when network error occurs."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        body=requests.exceptions.ConnectionError("Network error"),
    )

    result = get_schedule_address(schedule_with_location)

    assert result is None


@pytest.mark.django_db
def test_get_schedule_address_no_api_key(schedule_with_location, settings):
    """Test when API key is not configured."""
    settings.GOOGLE_MAPS_API_KEY = ""

    result = get_schedule_address(schedule_with_location)

    assert result is None


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_query_parameters(schedule_with_location, settings):
    """Test that correct query parameters are sent to API."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "OK",
            "results": [
                {
                    "name": "Test",
                    "formatted_address": "Test Address",
                    "geometry": {"location": {"lat": -5.7945, "lng": -35.211}},
                }
            ],
        },
        status=200,
    )

    get_schedule_address(schedule_with_location)

    assert len(responses.calls) == 1
    request = responses.calls[0].request
    assert "query" in request.url
    assert "key" in request.url
    assert "region=br" in request.url
    assert "type=church" in request.url


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_missing_coordinates(schedule_with_location, settings):
    """Test when API returns result without coordinates."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json={
            "status": "OK",
            "results": [
                {
                    "name": "Test",
                    "formatted_address": "Test Address",
                    "geometry": {},
                }
            ],
        },
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is not None
    assert result["address"] == "Test Address"
    assert result["lat"] is None
    assert result["lng"] is None
