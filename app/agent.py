# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import re
from zoneinfo import ZoneInfo
import requests

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.firestore_tools import (
    add_hotel,
    add_vegetarian_restaurant,
    get_top_attractions,
    search_hotels,
    search_vegetarian_restaurants,
)
from app.image_tools import generate_destination_image
from app.video_tools import generate_destination_video
from app.maps_tools import (
    geocode_address,
    search_nearby_places,
)


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def get_live_city_weather(city: str) -> dict:
    """Fetch real live weather conditions for any travel destination using the Open-Meteo public API.

    Args:
        city: The name of the target city (e.g., "San Francisco", "Tokyo", "New York").

    Returns:
        A dictionary containing live temperature, windspeed, weather code, and country location info.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = requests.get(geo_url, timeout=5).json()
        results = geo_res.get("results")
        if not results:
            return {"error": f"Could not find coordinates for city: {city}"}

        location = results[0]
        lat = location["latitude"]
        lon = location["longitude"]
        city_name = location["name"]
        country = location.get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url, timeout=5).json()
        current = weather_res.get("current_weather", {})

        temp_c = current.get("temperature")
        temp_f = round((temp_c * 9 / 5) + 32, 1) if temp_c is not None else None

        return {
            "city": city_name,
            "country": country,
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": temp_f,
            "windspeed_kmh": current.get("windspeed"),
            "weather_code": current.get("weathercode"),
            "timestamp": current.get("time"),
        }
    except Exception as e:
        return {"error": f"Failed to fetch live weather: {str(e)}"}


def calculate_travel_route_eta(
    waypoints: str,
    travel_mode: str = "walking",
    pace: str = "relaxed",
) -> dict:
    """Calculate estimated travel distance, transit duration, and optimal route schedule for waypoints.

    Args:
        waypoints: Comma-separated list of stop names/locations (e.g. "The Green Haven Hotel, Golden Gate Park, Ananda Pure Vegetarian").
        travel_mode: Mode of transportation ("walking" or "driving").
        pace: Traveler pace preference ("relaxed" or "fast-paced").

    Returns:
        A dictionary containing distance, total travel duration, and suggested schedule.
    """
    stops = [s.strip() for s in waypoints.split(",") if s.strip()]
    if len(stops) < 2:
        return {"error": "Please provide at least 2 waypoints to calculate a route."}

    num_legs = len(stops) - 1
    base_dist_per_leg = 2.5 if travel_mode.lower() == "walking" else 5.0
    total_distance = round(num_legs * base_dist_per_leg, 1)

    speed = 3.0 if travel_mode.lower() == "walking" else 25.0
    base_transit_mins = int((total_distance / speed) * 60)

    pace_multiplier = 1.3 if pace.lower() == "relaxed" else 1.0
    recommended_duration_mins = int(base_transit_mins * pace_multiplier)

    schedule = []
    current_offset = 0
    for i, stop_name in enumerate(stops):
        if i == 0:
            schedule.append(f"Start at {stop_name} (0 mins)")
        else:
            leg_mins = int(recommended_duration_mins / num_legs)
            current_offset += leg_mins
            schedule.append(f"Leg {i}: Arrive at {stop_name} (+{leg_mins} mins, total {current_offset} mins)")

    return {
        "waypoints": stops,
        "travel_mode": travel_mode,
        "pace": pace,
        "total_distance_miles": total_distance,
        "estimated_transit_mins": recommended_duration_mins,
        "suggested_schedule": schedule,
    }


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after agent turns to store conversation sessions in Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Warning: add_session_to_memory failed: {e}")
    return None


# Resolve Agent Engine resource name from deployment_metadata.json
agent_engine_resource_name = None
agent_engine_id = "3511600445581688832"
metadata_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
if os.path.exists(metadata_path):
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            runtime_id = metadata.get("remote_agent_runtime_id", "")
            if runtime_id:
                agent_engine_resource_name = runtime_id
                agent_engine_id = runtime_id.split("/")[-1]
    except Exception as e:
        print(f"Warning: Failed to load deployment_metadata.json: {e}")

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)

memory_service = VertexAiMemoryBankService(
    project="qwiklabs-gcp-03-930b36426336",
    location="us-east1",
    agent_engine_id=agent_engine_id,
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Global Travel Concierge, a helpful AI travel assistant. "
        "You remember the user's stated travel preferences, food allergies, and dietary restrictions "
        "(such as peanut allergies, gluten intolerance, dairy sensitivity, shellfish allergies, vegan/vegetarian/Jain needs) "
        "from previous conversations via Memory Bank and strictly apply them to personalize all recommendations and itineraries. "
        "Whenever a user mentions any allergy or dietary restriction, explicitly acknowledge it and save it to Memory Bank. "
        "Always cross-check recommended restaurants and dishes against the user's stored allergies to ensure safety. "
        "Use your Firestore tools to search for hotels, vegetarian/vegan/Jain restaurants, "
        "and top local attractions, as well as add new entries when requested. "
        "Use get_live_city_weather to fetch real-time weather forecasts for any city destination, "
        "use geocode_address to convert addresses to coordinates, "
        "use search_nearby_places to discover nearby restaurants or attractions using Google Places, "
        "use generate_destination_image to generate visual AI postcards/images for hotels, attractions, or places, "
        "use generate_destination_video to generate short video clips for destinations, hotels, or travel experiences using gemini-omni-flash-preview, "
        "use calculate_travel_route_eta to calculate travel time and route schedules for multi-stop itineraries, "
        "and use python code execution sandbox when calculation or dynamic data processing is required."
    ),
    workflow_description="Analyze the user request and return structured UI cards and visual displays when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        get_current_time,
        get_live_city_weather,
        search_hotels,
        add_hotel,
        search_vegetarian_restaurants,
        add_vegetarian_restaurant,
        get_top_attractions,
        calculate_travel_route_eta,
        geocode_address,
        search_nearby_places,
        generate_destination_image,
        generate_destination_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
