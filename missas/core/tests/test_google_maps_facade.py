import pytest
import requests
import responses
from model_bakery import baker

from missas.core.facades.google_maps import get_schedule_address


@pytest.fixture
def response_data():
    """Real Google Places API response example."""
    return {
        "html_attributions": [],
        "results": [
            {
                "business_status": "OPERATIONAL",
                "formatted_address": "R. Ver. Euclides Cavalcanti, 51, Ceará-Mirim - RN, 59570-000",
                "geometry": {
                    "location": {"lat": -5.6346745, "lng": -35.4250479},
                    "viewport": {
                        "northeast": {
                            "lat": -5.633344370107278,
                            "lng": -35.42362962010728,
                        },
                        "southwest": {
                            "lat": -5.636044029892722,
                            "lng": -35.42632927989272,
                        },
                    },
                },
                "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/worship_general-71.png",
                "icon_background_color": "#7B9EB0",
                "icon_mask_base_uri": "https://maps.gstatic.com/mapfiles/place_api/icons/v2/worship_christian_pinlet",
                "name": "Santuário Arquidiocesano de Nossa Senhora da Conceição",
                "opening_hours": {"open_now": True},
                "photos": [
                    {
                        "height": 1280,
                        "html_attributions": [
                            '<a href="https://maps.google.com/maps/contrib/113645645522892649036">Claudiuney Andrade</a>'
                        ],
                        "photo_reference": "AWn5SU5PhxvutH2fZAPaIoDt7R-3v14icR56f2BE7lC6V_2rEl4SthWHtHlMkNnCRu9AWwb1z08vIXdflS_qYIWZ9MdZbpWeqA0pcyQ4oGOMeXWz7bt6WT7dzKCHOYBcMWpOFC97WhkIQYrvo9kAgHPXJkBSKe5U7AHjVM1HESNphMV5mygXPpZrwtF3zblP9HuSLQ4khgYfQ8v4VmV4o2teHNI4gy0ijvqWPuDuebSMb7W0wUMkkySMSQJYEumH27gKj8omuj9AKmOnall-bEfUL7nn87j0qOG03xqNwChhoA1_ddCTf5I8MQGdsOnPOXmGIrEPkWgWia2hFNj6ff9_qm6d0w8a4iHfMfvSnL1XhaymHNCNrplYzybsqcUZdwNfaU29ADB27VPl5KFCquXbMI71cE6OsSTj5JTkJFeQzY6UwELmX6tXo_GfzLDRo6FlpUjWSTzTa_dLn6Yql156vEz-FrHVnkhJdLr6Q-hzya734an8aU25H_UpZXNasL2_8GNqp94iCX4mGEBaeEAoYgb-aouCmQkkulBJR22R_H-rQa2P3dJ3cEw66ovvrawwvPFzbwgR",
                        "width": 1024,
                    }
                ],
                "place_id": "ChIJ5_jZvo26swcRVVF77qTA_QU",
                "plus_code": {
                    "compound_code": "9H8F+4X Ceará-Mirim, State of Rio Grande do Norte",
                    "global_code": "69669H8F+4X",
                },
                "rating": 4.8,
                "reference": "ChIJ5_jZvo26swcRVVF77qTA_QU",
                "types": [
                    "church",
                    "place_of_worship",
                    "point_of_interest",
                    "establishment",
                ],
                "user_ratings_total": 526,
            }
        ],
        "status": "OK",
    }


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
def test_get_schedule_address_success(schedule_with_location, settings, response_data):
    """Test successful address retrieval from Google Places API."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is not None
    assert (
        result["address"]
        == "R. Ver. Euclides Cavalcanti, 51, Ceará-Mirim - RN, 59570-000"
    )
    assert result["lat"] == -5.6346745
    assert result["lng"] == -35.4250479


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_with_matriz(
    schedule_with_matriz, settings, response_data
):
    """Test address retrieval for matriz location includes parish name."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
        status=200,
    )

    result = get_schedule_address(schedule_with_matriz)

    assert result is not None
    assert (
        result["address"]
        == "R. Ver. Euclides Cavalcanti, 51, Ceará-Mirim - RN, 59570-000"
    )


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_without_location(
    schedule_without_location, settings, response_data
):
    """Test address retrieval without location name uses parish name."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
        status=200,
    )

    result = get_schedule_address(schedule_without_location)

    assert result is not None
    assert (
        result["address"]
        == "R. Ver. Euclides Cavalcanti, 51, Ceará-Mirim - RN, 59570-000"
    )


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_no_results(
    schedule_with_location, settings, response_data
):
    """Test when API returns no results."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    response_data["status"] = "ZERO_RESULTS"
    response_data["results"] = []

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is None


@pytest.mark.django_db
@responses.activate
def test_get_schedule_address_invalid_request(
    schedule_with_location, settings, response_data
):
    """Test when API returns INVALID_REQUEST status."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    response_data["status"] = "INVALID_REQUEST"
    response_data["results"] = []

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
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
def test_get_schedule_address_query_parameters(
    schedule_with_location, settings, response_data
):
    """Test that correct query parameters are sent to API."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
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
def test_get_schedule_address_missing_coordinates(
    schedule_with_location, settings, response_data
):
    """Test when API returns result without coordinates."""
    settings.GOOGLE_MAPS_API_KEY = "test-api-key"

    response_data["results"][0]["geometry"] = {}

    responses.add(
        responses.GET,
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        json=response_data,
        status=200,
    )

    result = get_schedule_address(schedule_with_location)

    assert result is not None
    assert (
        result["address"]
        == "R. Ver. Euclides Cavalcanti, 51, Ceará-Mirim - RN, 59570-000"
    )
    assert result["lat"] is None
    assert result["lng"] is None
