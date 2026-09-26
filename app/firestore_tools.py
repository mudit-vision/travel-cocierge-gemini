"""Firestore backend tools for Global Travel Concierge."""

import subprocess
from typing import List, Optional
from google.cloud import firestore
from google.oauth2 import credentials

# HARDCODED PROJECT ID as required by Agent Platform specifications
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-930b36426336"


def get_firestore_client() -> firestore.Client:
    """Initialize Firestore client using the hardcoded project ID."""
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"], text=True
        ).strip()
        creds = credentials.Credentials(token)
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
    except Exception:
        return firestore.Client(project=FIRESTORE_PROJECT_ID)


db = get_firestore_client()


def search_hotels(city: str, max_price_tier: Optional[str] = None) -> List[dict]:
    """Search for hotels in a specific city with optional price tier filter.

    Args:
        city: City name to search hotels in (e.g. "San Francisco", "New York").
        max_price_tier: Optional max price tier ("$", "$$", "$$$", "$$$$").

    Returns:
        A list of matching hotel details.
    """
    try:
        query = db.collection("hotels").where("city", "==", city)
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if max_price_tier and data.get("price_tier") != max_price_tier:
                continue
            results.append(data)
        if not results:
            return [{"message": f"No hotels found in {city} matching criteria."}]
        return results
    except Exception as e:
        return [{"error": f"Failed to search hotels: {str(e)}"}]


def add_hotel(
    name: str,
    city: str,
    price_tier: str,
    rating: float,
    amenities: str,
    dietary_friendly: bool,
    description: str,
) -> str:
    """Add a new hotel listing to the travel database.

    Args:
        name: Name of the hotel.
        city: City location.
        price_tier: Price classification (e.g., "$", "$$", "$$$", "$$$$").
        rating: Customer rating (1.0 to 5.0).
        amenities: Comma-separated list of amenities (e.g. "WiFi, Pool, Spa, Vegan Breakfast").
        dietary_friendly: Whether the hotel caters to vegetarian/vegan guests.
        description: Short overview of the hotel.

    Returns:
        Status message confirming the addition.
    """
    try:
        doc_ref = db.collection("hotels").document()
        amenity_list = [a.strip() for a in amenities.split(",") if a.strip()]
        doc_ref.set({
            "name": name,
            "city": city,
            "price_tier": price_tier,
            "rating": rating,
            "amenities": amenity_list,
            "dietary_friendly": dietary_friendly,
            "description": description,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        return f"Successfully added hotel '{name}' (ID: {doc_ref.id}) to Firestore."
    except Exception as e:
        return f"Error adding hotel: {str(e)}"


def search_vegetarian_restaurants(
    city: str, dietary_option: Optional[str] = None
) -> List[dict]:
    """Search for vegetarian, vegan, or Jain restaurants in a target city.

    Args:
        city: The city name (e.g., "San Francisco", "New York").
        dietary_option: Specific requirement to filter by ("Vegetarian", "Vegan", or "Jain").

    Returns:
        A list of matching restaurant records.
    """
    try:
        query = db.collection("restaurants").where("city", "==", city)
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if dietary_option:
                options = [d.lower() for d in data.get("dietary_options", [])]
                if dietary_option.lower() not in options:
                    continue
            results.append(data)
        if not results:
            return [{"message": f"No restaurants found in {city} for dietary option '{dietary_option}'."}]
        return results
    except Exception as e:
        return [{"error": f"Failed to search restaurants: {str(e)}"}]


def add_vegetarian_restaurant(
    name: str,
    city: str,
    cuisine: str,
    dietary_options: str,
    rating: float,
    price_range: str,
    address: str,
) -> str:
    """Add a new vegetarian/vegan/Jain restaurant to the database.

    Args:
        name: Restaurant name.
        city: City name.
        cuisine: Cuisine style (e.g., "Indian", "Italian", "Organic Asian").
        dietary_options: Comma-separated list of suitable options (e.g., "Vegetarian, Vegan, Jain").
        rating: Rating out of 5.0.
        price_range: Price range indicator (e.g. "$$", "$$$").
        address: Street address.

    Returns:
        Status message.
    """
    try:
        doc_ref = db.collection("restaurants").document()
        dietary_list = [d.strip() for d in dietary_options.split(",") if d.strip()]
        doc_ref.set({
            "name": name,
            "city": city,
            "cuisine": cuisine,
            "dietary_options": dietary_list,
            "rating": rating,
            "price_range": price_range,
            "address": address,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        return f"Successfully added restaurant '{name}' (ID: {doc_ref.id}) to Firestore."
    except Exception as e:
        return f"Error adding restaurant: {str(e)}"


def get_top_attractions(city: str) -> List[dict]:
    """Search for top local attractions and landmarks in a city.

    Args:
        city: City name.

    Returns:
        List of attraction details.
    """
    try:
        query = db.collection("attractions").where("city", "==", city)
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        if not results:
            return [{"message": f"No attractions found in {city}."}]
        return results
    except Exception as e:
        return [{"error": f"Failed to get attractions: {str(e)}"}]
