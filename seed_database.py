"""Seed script for Global Travel Concierge Firestore Database."""

import time
import subprocess
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


def seed_item(db, collection_name, item):
    for attempt in range(3):
        try:
            doc_ref = db.collection(collection_name).document()
            item_copy = dict(item)
            item_copy["created_at"] = firestore.SERVER_TIMESTAMP
            doc_ref.set(item_copy)
            print(f"  Added {collection_name[:-1]}: {item['name']}")
            return
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"  Failed to add {item['name']}: {e}")


def seed_data():
    db = get_firestore_client()
    print(f"Connected to Firestore in project: {FIRESTORE_PROJECT_ID}")

    # Sample Hotels
    hotels = [
        {
            "name": "The Green Haven Hotel",
            "city": "San Francisco",
            "price_tier": "$$$",
            "rating": 4.8,
            "amenities": ["WiFi", "Organic Breakfast", "EV Charging", "Spa"],
            "dietary_friendly": True,
            "description": "Boutique eco-hotel in downtown SF offering complimentary organic vegan breakfast.",
        },
        {
            "name": "Bayview Luxury Lodge",
            "city": "San Francisco",
            "price_tier": "$$$$",
            "rating": 4.9,
            "amenities": ["Infinity Pool", "Roof Garden", "24/7 Concierge", "Gourmet Dining"],
            "dietary_friendly": True,
            "description": "Luxury waterfront stay with panoramic Golden Gate views and plant-based room service.",
        },
        {
            "name": "Manhattan Plant & Stay",
            "city": "New York",
            "price_tier": "$$$",
            "rating": 4.7,
            "amenities": ["Fitness Center", "Vegan Minibar", "High-speed WiFi"],
            "dietary_friendly": True,
            "description": "Modern Midtown hotel dedicated to sustainable luxury and plant-based dining.",
        },
    ]

    # Sample Restaurants
    restaurants = [
        {
            "name": "Ananda Pure Vegetarian",
            "city": "San Francisco",
            "cuisine": "Indian & Fusion",
            "dietary_options": ["Vegetarian", "Vegan", "Jain"],
            "rating": 4.9,
            "price_range": "$$",
            "address": "450 Sutter St, San Francisco, CA",
        },
        {
            "name": "Shizen Vegan Sushi Bar",
            "city": "San Francisco",
            "cuisine": "Japanese Vegan",
            "dietary_options": ["Vegetarian", "Vegan"],
            "rating": 4.8,
            "price_range": "$$$",
            "address": "370 14th St, San Francisco, CA",
        },
        {
            "name": "Jain Delights & Sweets",
            "city": "New York",
            "cuisine": "North & South Indian",
            "dietary_options": ["Vegetarian", "Vegan", "Jain"],
            "rating": 4.7,
            "price_range": "$$",
            "address": "120 Lexington Ave, New York, NY",
        },
    ]

    # Sample Attractions
    attractions = [
        {
            "name": "Golden Gate Park",
            "city": "San Francisco",
            "category": "Nature & Parks",
            "description": "Expansive green park featuring Japanese Tea Garden, botanical gardens, and bison paddock.",
            "visit_duration_mins": 120,
            "entry_fee": "$0",
        },
        {
            "name": "Palace of Fine Arts",
            "city": "San Francisco",
            "category": "Landmarks & Architecture",
            "description": "Iconic Greco-Roman ruin structure set alongside a serene lagoon.",
            "visit_duration_mins": 60,
            "entry_fee": "$0",
        },
        {
            "name": "Central Park Botanical Loop",
            "city": "New York",
            "category": "Nature & Landmarks",
            "description": "Scenic walking loop through historic Conservatory Garden and Strawberry Fields.",
            "visit_duration_mins": 90,
            "entry_fee": "$0",
        },
    ]

    print("Seeding hotels...")
    for item in hotels:
        seed_item(db, "hotels", item)

    print("Seeding restaurants...")
    for item in restaurants:
        seed_item(db, "restaurants", item)

    print("Seeding attractions...")
    for item in attractions:
        seed_item(db, "attractions", item)

    print("🎉 Database seeding completed successfully!")


if __name__ == "__main__":
    seed_data()
