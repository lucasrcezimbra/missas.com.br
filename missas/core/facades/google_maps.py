import logging
import re
from urllib.parse import parse_qs, urlparse

import googlemaps
import requests
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
            geometry = result["geometry"]["location"]

            logger.debug(f"Found place: {place_name} at address: {formatted_address}")

            return {
                "address": formatted_address,
                "name": place_name,
                "full_response": data,
                "place_id": result.get("place_id"),
                "latitude": geometry["lat"],
                "longitude": geometry["lng"],
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


def get_place_from_url(maps_url):
    """
    Extract place information from a Google Maps URL.
    Supports various Google Maps URL formats including shortened URLs.

    Args:
        maps_url: Google Maps URL (e.g., https://maps.app.goo.gl/xxx or full URLs)

    Returns:
        dict with keys: name, address, full_response, place_id, latitude, longitude
        or None if the place cannot be found

    Raises:
        ValueError: If the URL is invalid or place_id cannot be extracted
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY not configured")
        return None

    try:
        place_id = _extract_place_id_from_url(maps_url)

        if not place_id:
            raise ValueError("Could not extract place_id from URL")

        gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

        result = gmaps.place(
            place_id=place_id,
            language="pt-BR",
            region="br",
        )

        logger.debug(f"Google Place Details API response for place_id '{place_id}': {result}")

        if result.get("status") == "OK" and result.get("result"):
            place_data = result["result"]
            formatted_address = place_data.get("formatted_address", "")
            place_name = place_data.get("name", "")
            geometry = place_data["geometry"]["location"]

            logger.debug(f"Found place: {place_name} at address: {formatted_address}")

            return {
                "address": formatted_address,
                "name": place_name,
                "full_response": result,
                "place_id": place_id,
                "latitude": geometry["lat"],
                "longitude": geometry["lng"],
            }

        logger.info(f"No place found for place_id: {place_id} (status: {result.get('status')})")
        return None

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error fetching place details from Google Places API: {e}")
        raise ValueError(f"Error processing Google Maps URL: {str(e)}")


def _extract_place_id_from_url(maps_url):
    """
    Extract place_id from various Google Maps URL formats.
    Handles shortened URLs by following redirects.
    """
    try:
        if "goo.gl" in maps_url or "maps.app.goo.gl" in maps_url:
            response = requests.head(maps_url, allow_redirects=True, timeout=10)
            maps_url = response.url

        parsed = urlparse(maps_url)
        query_params = parse_qs(parsed.query)

        if "query_place_id" in query_params:
            return query_params["query_place_id"][0]

        if "/place/" in maps_url:
            match = re.search(r"/place/[^/]+/data=.*?!1s([^!]+)", maps_url)
            if match:
                return match.group(1)

        path_parts = parsed.path.split("/")
        for part in path_parts:
            if part.startswith("ChIJ") or part.startswith("0x"):
                return part

        match = re.search(r"!1s(ChIJ[a-zA-Z0-9_-]+)", maps_url)
        if match:
            return match.group(1)

        logger.warning(f"Could not extract place_id from URL: {maps_url}")
        return None

    except Exception as e:
        logger.error(f"Error extracting place_id from URL: {e}")
        return None
