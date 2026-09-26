"""Image generation tools for Global Travel Concierge."""

import uuid
from typing import Optional
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# HARDCODED GCP PROJECT ID and GCS BUCKET NAME as specified
GCP_PROJECT_ID = "qwiklabs-gcp-03-930b36426336"
GCS_BUCKET_NAME = "travel-concierge-media-930b36426336"


async def generate_destination_image(
    prompt: str,
    filename: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Generate an image for a destination, hotel, or attraction using gemini-3.1-flash-lite-image model.

    Saves the image as an artifact for the Playground UI and uploads it to Cloud Storage for public access.

    Args:
        prompt: Detailed description of the image to generate (e.g. "Golden Gate Park in San Francisco on a sunny day").
        filename: Optional base filename (e.g., "golden_gate_park.jpg").
        tool_context: Provided automatically by ADK to manage artifacts.

    Returns:
        A dictionary containing the prompt, public GCS image URL, and artifact status.
    """
    try:
        # Initialize Gemini Client for global region using Vertex AI
        client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location="global",
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        # Extract generated image bytes
        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": "Failed to extract image bytes from generation response."}

        # Generate unique filename if not provided
        ext = "png" if "png" in mime_type.lower() else "jpg"
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
                    artifact=types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                )
                artifact_saved = True
            except Exception as e:
                print(f"Warning: Failed to save artifact in tool_context: {e}")

        # 2. Upload image bytes directly to public GCS bucket
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "prompt": prompt,
            "filename": filename,
            "public_image_url": public_url,
            "artifact_saved": artifact_saved,
            "status": "Image successfully generated, saved as artifact, and uploaded to GCS.",
        }

    except Exception as e:
        return {"error": f"Failed to generate destination image: {str(e)}"}
