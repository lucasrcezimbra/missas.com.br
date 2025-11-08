import logging
from urllib.parse import quote_plus

import googlemaps
from django.conf import settings

logger = logging.getLogger(__name__)


def get_schedule_address(schedule):
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

            if len(results) > 1:
                raise ValueError(
                    f"Multiple results found for query '{search_query}'. "
                    f"Found {len(results)} results. Please refine the search query."
                )

            result = results[0]
            formatted_address = result["formatted_address"]
            place_name = result.get("name", "")

            logger.debug(f"Found place: {place_name} at address: {formatted_address}")

            return {
                "address": formatted_address,
                "name": place_name,
                "url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(place_name + ' ' + formatted_address)}",
                "full_response": data,
                "place_id": result.get("place_id"),
            }

        logger.info(
            f"No address found for query: {search_query} (status: {data.get('status')})"
        )
        return None

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error fetching address from Google Places API: {e}")
        return None
