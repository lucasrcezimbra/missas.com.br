import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_schedule_address(schedule):
    """
    Fetch address and coordinates for a Schedule using Google Places API Text Search.

    Builds a search query from the schedule's location_name, parish name,
    city, and state, then queries Google Places API to find the specific place
    and get its formatted address and coordinates.

    Returns a dict with 'address', 'lat', and 'lng' keys, or None if not found.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY not configured")
        return None

    location_parts = []

    if schedule.location_name and "matriz" not in schedule.location_name.lower():
        location_parts.append(schedule.location_name)
        location_parts.append(schedule.parish.city.name)
        location_parts.append(schedule.parish.city.state.short_name)
    else:
        if schedule.location_name:
            location_parts.append(schedule.location_name)
        location_parts.append(schedule.parish.name)
        location_parts.append(schedule.parish.city.name)
        location_parts.append(schedule.parish.city.state.short_name)

    search_query = " ".join(location_parts)

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": search_query,
                "key": settings.GOOGLE_MAPS_API_KEY,
                "language": "pt-BR",
                "region": "br",
                "type": "church",
            },
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Google Places API response for query '{search_query}': {data}")

        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            formatted_address = result["formatted_address"]
            place_name = result.get("name", "")
            location = result["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]

            logger.debug(
                f"Found place: {place_name} at address: {formatted_address} ({lat}, {lng})"
            )

            return {
                "address": formatted_address,
                "lat": lat,
                "lng": lng,
                "name": place_name,
                "url": f"https://www.google.com/maps/place/?q=place_id:{result['place_id']}",
                "full_response": data,
            }

        logger.info(
            f"No address found for query: {search_query} (status: {data.get('status')})"
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching address from Google Places API: {e}")
        return None
