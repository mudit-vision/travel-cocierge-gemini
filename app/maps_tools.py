"""Google Maps Geocoding and Places (New) function tools for Global Travel Concierge."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def geocode_address(address: str) -> dict:
    """Turn a street address or landmark name into geographic coordinates using Google Geocoding API.

    Args:
        address: Street address or landmark name (e.g. "450 Sutter St, San Francisco, CA" or "Golden Gate Park").

    Returns:
        A dictionary containing formatted address, location coordinates (latitude and longitude), and status.
    """
    if not MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": MAPS_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return {"error": f"Geocoding failed for '{address}': {data.get('status')}"}

        result = data["results"][0]
        location = result["geometry"]["location"]

        return {
            "address": address,
            "formatted_address": result.get("formatted_address"),
            "location": {
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
            },
            "place_id": result.get("place_id"),
        }
    except Exception as e:
        return {"error": f"Failed to geocode address: {str(e)}"}


def search_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1000.0,
) -> list:
    """Find nearby places of a given type around coordinates using Google Places API (New).

    Args:
        latitude: Latitude coordinate of the central location.
        longitude: Longitude coordinate of the central location.
        place_type: Type of place to search for (e.g. "restaurant", "hotel", "tourist_attraction", "park", "bakery").
        radius_meters: Search radius in meters (default is 1000m / 1km).

    Returns:
        A list of nearby place dictionaries containing name, address, location, and rating.
    """
    if not MAPS_API_KEY:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.types",
    }
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        data = response.json()

        places = data.get("places", [])
        if not places:
            return [{"message": f"No nearby '{place_type}' places found within {radius_meters}m."}]

        results = []
        for place in places:
            display_name = place.get("displayName", {}).get("text", "Unknown Place")
            formatted_address = place.get("formattedAddress", "")
            loc = place.get("location", {})
            rating = place.get("rating")

            results.append({
                "name": display_name,
                "address": formatted_address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                },
                "rating": rating,
            })
        return results
    except Exception as e:
        return [{"error": f"Failed to search nearby places: {str(e)}"}]
