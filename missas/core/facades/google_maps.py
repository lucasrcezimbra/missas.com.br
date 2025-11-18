import logging
import re
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

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


def _unshorten_url(short_url):
    # Only unshorten URLs from known Google Maps domains
    if not (
        short_url.startswith("https://maps.app.goo.gl/")
        or short_url.startswith("https://goo.gl/maps/")
    ):
        logger.warning(f"URL is not a Google Maps short URL: {short_url}")
        return short_url

    try:
        req = Request(short_url, headers={"User-Agent": "Mozilla/5.0"})  # noqa: S310
        with urlopen(req, timeout=10) as response:  # noqa: S310
            return response.url
    except Exception as e:
        logger.error(f"Error unshortening URL {short_url}: {e}")
        return short_url


def _extract_place_id_from_url(url):
    parsed_url = urlparse(url)

    if "query_place_id" in parsed_url.query:
        query_params = parse_qs(parsed_url.query)
        return query_params.get("query_place_id", [None])[0]

    if "place_id" in parsed_url.query:
        query_params = parse_qs(parsed_url.query)
        return query_params.get("place_id", [None])[0]

    place_id_match = re.search(r"!1s(ChIJ[^!&\s]+)", url)
    if place_id_match:
        return place_id_match.group(1)

    cid_match = re.search(r"[?&]cid=(\d+)", url)
    if cid_match:
        return None

    return None


def _extract_coordinates_from_url(url):
    coord_pattern = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    match = re.search(coord_pattern, url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def get_location_from_google_maps_url(maps_url):
    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY not configured")
        return None

    if "goo.gl" in maps_url or "maps.app.goo.gl" in maps_url:
        maps_url = _unshorten_url(maps_url)
        logger.debug(f"Unshortened URL: {maps_url}")

    place_id = _extract_place_id_from_url(maps_url)

    if place_id:
        try:
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            data = gmaps.place(place_id=place_id, language="pt-BR")

            logger.debug(
                f"Google Places API response for place_id '{place_id}': {data}"
            )

            if data.get("status") == "OK" and data.get("result"):
                result = data["result"]
                geometry = result["geometry"]["location"]

                return {
                    "address": result.get("formatted_address", ""),
                    "name": result.get("name", ""),
                    "full_response": data,
                    "place_id": place_id,
                    "latitude": geometry["lat"],
                    "longitude": geometry["lng"],
                }

            logger.warning(
                f"No place found for place_id: {place_id} (status: {data.get('status')})"
            )
            return None

        except Exception as e:
            logger.error(f"Error fetching place details from Google Places API: {e}")
            return None

    latitude, longitude = _extract_coordinates_from_url(maps_url)
    if latitude and longitude:
        try:
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            data = gmaps.reverse_geocode((latitude, longitude), language="pt-BR")

            logger.debug(
                f"Google Geocoding API response for coords ({latitude}, {longitude}): {data}"
            )

            if data:
                result = data[0]
                extracted_place_id = result.get("place_id")

                return {
                    "address": result.get("formatted_address", ""),
                    "name": result.get("name", result.get("formatted_address", "")),
                    "full_response": {"results": data},
                    "place_id": extracted_place_id,
                    "latitude": latitude,
                    "longitude": longitude,
                }

            logger.warning(
                f"No results from reverse geocoding for ({latitude}, {longitude})"
            )
            return None

        except Exception as e:
            logger.error(f"Error during reverse geocoding: {e}")
            return None

    logger.warning(f"Could not extract place_id or coordinates from URL: {maps_url}")
    return None
