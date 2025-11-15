import pytest
from django.contrib.gis.geos import Point
from model_bakery import baker

from missas.core.models import Location


@pytest.mark.django_db
def test_location_with_point_field():
    google_response = {
        "status": "OK",
        "results": [
            {
                "geometry": {
                    "location": {
                        "lat": -5.959930399999999,
                        "lng": -36.6553998,
                    }
                },
                "place_id": "ChIJNd49U15KsAcR7mWxiSWl5mA",
            }
        ],
    }

    location = baker.make(
        Location,
        name="Test Church",
        address="Test Address, RN",
        google_maps_response=google_response,
        google_maps_place_id="ChIJNd49U15KsAcR7mWxiSWl5mA",
        point=Point(-36.6553998, -5.959930399999999, srid=4326),
    )

    assert location.point is not None
    assert location.point.x == -36.6553998
    assert location.point.y == -5.959930399999999
    assert location.point.srid == 4326


@pytest.mark.django_db
def test_location_without_point_field():
    google_response = {
        "status": "OK",
        "results": [
            {
                "geometry": {
                    "location": {
                        "lat": -5.959930399999999,
                        "lng": -36.6553998,
                    }
                },
                "place_id": "ChIJNd49U15KsAcR7mWxiSWl5mA",
            }
        ],
    }

    location = baker.make(
        Location,
        name="Test Church",
        address="Test Address, RN",
        google_maps_response=google_response,
        google_maps_place_id="ChIJNd49U15KsAcR7mWxiSWl5mA",
    )

    assert location.point is None


@pytest.mark.django_db
def test_location_point_from_google_maps_response():
    google_response = {
        "status": "OK",
        "results": [
            {
                "geometry": {
                    "location": {
                        "lat": -22.9068467,
                        "lng": -43.1728965,
                    }
                },
                "place_id": "ChIJW6AIkVl_mQARTSOcaxxt4Hk",
            }
        ],
    }

    location = baker.make(
        Location,
        name="Cristo Redentor",
        address="Rio de Janeiro, RJ",
        google_maps_response=google_response,
        google_maps_place_id="ChIJW6AIkVl_mQARTSOcaxxt4Hk",
    )

    lat = google_response["results"][0]["geometry"]["location"]["lat"]
    lng = google_response["results"][0]["geometry"]["location"]["lng"]

    location.point = Point(lng, lat, srid=4326)
    location.save()

    location.refresh_from_db()
    assert location.point.x == lng
    assert location.point.y == lat
