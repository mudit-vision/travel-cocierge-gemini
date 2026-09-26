"""Record a demo video of the Global Travel Concierge frontend using Playwright."""

import asyncio
import os
import glob
from google.cloud import storage
from playwright.async_api import async_playwright

GCP_PROJECT_ID = "qwiklabs-gcp-03-930b36426336"
GCS_BUCKET_NAME = "travel-concierge-media-930b36426336"
FRONTEND_URL = "https://travel-concierge-frontend-574604179225.us-east1.run.app"
VIDEO_DIR = "/config/.gemini/antigravity/scratch/travel-concierge/demo_videos"


async def main():
    os.makedirs(VIDEO_DIR, exist_ok=True)
    for old_file in glob.glob(os.path.join(VIDEO_DIR, "*.webm")):
        try:
            os.remove(old_file)
        except Exception:
            pass

    async with async_playwright() as p:
        print("Launching Chromium browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1280, "height": 800},
        )

        page = await context.new_page()
        print(f"Navigating to frontend URL: {FRONTEND_URL}...")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Prompt 1: Core feature (Allergies + Firestore Vegetarian Restaurant Search)
        prompt1 = "I have a severe peanut allergy. Find vegetarian restaurants in San Francisco and remember my allergy."
        print(f"Sending Prompt 1: '{prompt1}'...")
        await page.fill("#input", prompt1)
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Send')")

        # Wait for agent response (poll until new agent msg bubble appears with non-ellipsis text)
        print("Waiting for agent response to Prompt 1...")
        for _ in range(30):
            await page.wait_for_timeout(1000)
            bubbles = await page.locator(".msg.agent .bubble").all_inner_texts()
            if len(bubbles) >= 2 and "…" not in bubbles[-1]:
                print(f"Prompt 1 response received: {bubbles[-1][:100]}...")
                break

        await page.wait_for_timeout(3000)

        # Prompt 2: Richer feature (Tool call + AI Image Generation)
        prompt2 = "Generate a postcard image for a luxury hotel in Tokyo."
        print(f"Sending Prompt 2: '{prompt2}'...")
        await page.fill("#input", prompt2)
        await page.wait_for_timeout(1000)
        await page.click("button:has-text('Send')")

        # Wait for agent response to Prompt 2
        print("Waiting for agent response to Prompt 2...")
        for _ in range(45):
            await page.wait_for_timeout(1000)
            bubbles = await page.locator(".msg.agent .bubble").all_inner_texts()
            if len(bubbles) >= 3 and "…" not in bubbles[-1]:
                print(f"Prompt 2 response received: {bubbles[-1][:100]}...")
                break

        await page.wait_for_timeout(4000)

        # Close context to save video file
        print("Closing browser context to save video...")
        await context.close()
        await browser.close()

    # Find recorded video file
    video_files = glob.glob(os.path.join(VIDEO_DIR, "*.webm"))
    if not video_files:
        print("Error: No recorded video file found.")
        return

    recorded_path = video_files[0]
    filename = "demo_video.webm"
    print(f"Recorded video saved to: {recorded_path}")

    # Upload video to public GCS bucket
    print("Uploading demo video to GCS bucket...")
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    with open(recorded_path, "rb") as f:
        blob.upload_from_file(f, content_type="video/webm")

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
    print(f"DEMO VIDEO COMPLETE! Public GCS URL: {public_url}")


if __name__ == "__main__":
    asyncio.run(main())
