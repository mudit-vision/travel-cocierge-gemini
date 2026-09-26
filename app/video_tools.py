"""Video generation tools for Global Travel Concierge using Google's Omni model (gemini-omni-flash-preview)."""

import base64
import uuid
from typing import Optional
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# HARDCODED GCP PROJECT ID and GCS BUCKET NAME
GCP_PROJECT_ID = "qwiklabs-gcp-03-930b36426336"
GCS_BUCKET_NAME = "travel-concierge-media-930b36426336"


async def generate_destination_video(
    prompt: str,
    filename: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Generate a short video clip for a destination, hotel, or attraction using gemini-omni-flash-preview model.

    Saves the video as an artifact for the Playground UI and uploads it to Cloud Storage for public access.

    Args:
        prompt: Detailed description of the video to generate (e.g. "Short video clip of a cable car in San Francisco").
        filename: Optional base filename (e.g., "sf_cable_car.mp4").
        tool_context: Provided automatically by ADK to manage artifacts.

    Returns:
        A dictionary containing the prompt, public GCS video URL, and artifact status.
    """
    try:
        # Initialize Gemini Client for global region using Vertex AI
        client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location="global",
        )

        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        if not interaction.output_video or not interaction.output_video.data:
            return {"error": "Failed to extract video output from interaction response."}

        b64_str = interaction.output_video.data
        video_bytes = base64.b64decode(b64_str)
        mime_type = interaction.output_video.mime_type or "video/mp4"

        # Generate unique filename if not provided
        ext = "mp4"
        if not filename:
            clean_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:20]).strip("_")
            filename = f"{clean_prompt}_{uuid.uuid4().hex[:6]}.{ext}"
        elif not filename.endswith(f".{ext}"):
            filename = f"{filename}.{ext}"

        # 1. Save artifact to ADK tool_context (Playground Artifacts panel)
        artifact_saved = False
        if tool_context:
            try:
                await tool_context.save_artifact(
                    filename=filename,
                    artifact=types.Part.from_bytes(data=video_bytes, mime_type=mime_type),
                )
                artifact_saved = True
            except Exception as e:
                print(f"Warning: Failed to save artifact in tool_context: {e}")

        # 2. Upload video bytes directly to public GCS bucket (without saving to local disk)
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "prompt": prompt,
            "filename": filename,
            "public_video_url": public_url,
            "artifact_saved": artifact_saved,
            "status": "Video successfully generated, saved as artifact, and uploaded to GCS.",
        }

    except Exception as e:
        return {"error": f"Failed to generate destination video: {str(e)}"}
