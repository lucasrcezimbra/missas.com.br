import logging

import googlemaps
from django.conf import settings

logger = logging.getLogger(__name__)


def get_schedule_address_options(schedule):
    """
    Get all possible address options for a schedule from Google Maps API.
    Returns a list of address options or None if no results found.
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
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

        data = gmaps.places(
            query=search_query,
            language="pt-BR",
            region="br",
            type="church",
        )

        logger.debug(f"Google Places API response for query '{search_query}': {data}")

        if data.get("status") == "OK" and data.get("results"):
            results = data["results"]

            address_options = []
            for result in results:
                formatted_address = result["formatted_address"]
                place_name = result.get("name", "")

                address_options.append(
                    {
                        "address": formatted_address,
                        "name": place_name,
                        "place_id": result.get("place_id"),
                    }
                )

            logger.debug(
                f"Found {len(address_options)} place(s) for query '{search_query}'"
            )
            return address_options

        logger.info(
            f"No address found for query: {search_query} (status: {data.get('status')})"
        )
        return None

    except Exception as e:
        logger.error(f"Error fetching address from Google Places API: {e}")
        return None


def get_schedule_address(schedule):
    """
    Get a single address for a schedule. Raises ValueError if multiple results found.
    For backward compatibility.
    """
    address_options = get_schedule_address_options(schedule)

    if address_options is None:
        return None

    if len(address_options) > 1:
        raise ValueError(
            f"Multiple results found. "
            f"Found {len(address_options)} results. Please refine the search query."
        )

    option = address_options[0]

    # Need to reconstruct the full response for backward compatibility
    return {
        "address": option["address"],
        "name": option["name"],
        "full_response": {
            "results": [
                {
                    "formatted_address": option["address"],
                    "name": option["name"],
                    "place_id": option["place_id"],
                }
            ]
        },
        "place_id": option["place_id"],
    }
