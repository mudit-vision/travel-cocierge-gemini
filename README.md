# Global Travel Concierge (`travel-cocierge-gemini`)

An intelligent, context-aware AI travel assistant built with Google Cloud's Agent Development Kit (ADK), Vertex AI Memory Bank, Firestore, Google Maps & Places APIs, and Agent-to-User Interface (A2UI) card rendering.

![Global Travel Concierge Demo](demo.gif)

---

## 🌟 Overview & Implemented Capabilities

`travel-cocierge-gemini` delivers personalized travel planning, accommodation recommendations, dietary-safe dining suggestions, live weather forecasts, and visual AI-generated media.

Based strictly on the codebase in `app/` and `agents-cli-manifest.yaml`, the agent implements:

- 🧠 **Personalized Allergy & Dietary Memory**: Uses **Vertex AI Memory Bank** (`VertexAiMemoryBankService`) to remember user preferences, severe food allergies (e.g., peanut, gluten, shellfish), and dietary restrictions (vegan, vegetarian, Jain) across chat sessions.
- 🥗 **Firestore Dining & Hotel Search**: Interacts directly with Google Cloud Firestore to query and add entries for hotels (`search_hotels`, `add_hotel`), vegetarian/vegan restaurants (`search_vegetarian_restaurants`, `add_vegetarian_restaurant`), and top local attractions (`get_top_attractions`).
- 📍 **Google Maps & Places Geolocation**: Converts addresses to geographic coordinates via `geocode_address` and searches nearby points of interest with `search_nearby_places`.
- 🌤️ **Live Weather Forecasts**: Retrieves real-time weather conditions for target travel destinations using `get_live_city_weather`.
- 🖼️ **Vertex AI Image Postcard Generation**: Generates visual AI postcards (`generate_destination_image`) using `gemini-3.1-flash-lite-image`, saving artifacts to ADK and uploading bytes to Google Cloud Storage.
- 🎥 **Google Omni Video Generation**: Produces short video clips (`generate_destination_video`) using `gemini-omni-flash-preview` in the `global` region.
- 🎨 **Dynamic A2UI Surface Rendering**: Outputs structured A2UI JSON cards (`A2uiSchemaManager`) rendered natively as flat cards, text rows, weather widgets, and image cards.
- 💬 **FastAPI A2A Web Proxy**: Includes a lightweight FastAPI server (`frontend/main.py`) that proxies requests to deployed A2A agent engines with custom Ocean Teal styling and clickable prompt shortcuts.

### 📋 Planned / Not Yet Implemented
- ✈️ **Live Flight Booking & Ticket Purchasing**: Planned future integration for real-time airline reservation APIs.

---

## 🏗️ Architecture

```
travel-cocierge-gemini/
├── app/
│   ├── agent.py            # Agent definition, system prompts, memory bank & callbacks
│   ├── firestore_tools.py  # Firestore hotel, restaurant & attraction tools
│   ├── image_tools.py      # Vertex AI image postcard generation tool
│   ├── video_tools.py      # Google Omni video generation tool
│   ├── maps_tools.py       # Google Maps Geocoding & Places tools
│   ├── weather_tools.py    # Live weather lookup tool
│   └── a2ui_utils.py       # A2UI response formatting callback
├── frontend/
│   ├── main.py             # FastAPI A2A proxy server
│   ├── requirements.txt    # Frontend dependencies
│   └── static/
│       └── index.html      # Styled chat interface with example prompt buttons
├── agents-cli-manifest.yaml# ADK agent manifest configuration
├── pyproject.toml          # Project dependencies and settings
├── demo.gif                # Recorded live interaction demo
└── README.md
```

---

## 🚀 Local Setup & Execution Instructions

### Prerequisites
- Python 3.11+
- `uv` package manager (`pip install uv`)
- Google Cloud Project with Vertex AI, Firestore, and Storage enabled

### 1. Environment Configuration
Create a `.env` file in the project root:

```bash
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="us-east1"
GOOGLE_MAPS_API_KEY="your-google-maps-api-key"
```

### 2. Install Dependencies
```bash
uv sync
```

### 3. Run Agent Locally (Playground Mode)
Start the agent in local ADK playground mode:

```bash
uv run agents-cli scaffold run
```

### 4. Run Frontend Locally
To launch the FastAPI proxy and chat interface locally:

```bash
cd frontend
pip install -r requirements.txt
export AGENT_DIRECTORY="app"
python main.py
```

Open a Web browser and navigate to the port output by the server (default `8080`).

---

## 🛠️ Deployment Instructions

### Deploy Agent to Agent Runtime (Reasoning Engine)
```bash
uv run agents-cli deploy \
  --project your-gcp-project-id \
  --region us-east1 \
  --update-env-vars GOOGLE_MAPS_API_KEY="your-google-maps-api-key"
```

### Deploy Frontend to Cloud Run
```bash
gcloud run deploy travel-concierge-frontend \
  --source ./frontend \
  --region us-east1 \
  --project your-gcp-project-id \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/us-east1/reasoningEngines/YOUR_ENGINE_ID",AGENT_DIRECTORY="app" \
  --allow-unauthenticated
```
