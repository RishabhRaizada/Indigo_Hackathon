"""Gemini image generation service.

Available on this API key:
  - imagen-4.0-generate-001      (primary — Imagen 4, generate_images API)
  - gemini-2.5-flash-image       (fallback — generate_content with IMAGE modality)
"""
import base64
import asyncio
from functools import partial
from app.config import GEMINI_API_KEY

_ASPECT_MAP = {
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "4:5": "4:5",
    "21:9": "16:9",
}


def _generate_image_sync(prompt: str, aspect_ratio: str) -> str | None:
    """Synchronous image generation — runs in a thread executor."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    ar = _ASPECT_MAP.get(aspect_ratio, "1:1")

    # Primary: Imagen 4
    try:
        result = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=ar,
            ),
        )
        image_bytes = result.generated_images[0].image.image_bytes
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e1:
        print(f"[Gemini] Imagen 4 failed ({e1}), trying gemini-2.5-flash-image")

    # Fallback: Gemini 2.5 Flash Image
    try:
        result = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in result.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                return f"data:image/png;base64,{b64}"
    except Exception as e2:
        print(f"[Gemini] Fallback also failed ({e2})")

    return None


async def generate_image(prompt: str, aspect_ratio: str = "1:1") -> str | None:
    """Async wrapper — runs blocking Gemini call in thread pool."""
    loop = asyncio.get_event_loop()
    fn = partial(_generate_image_sync, prompt, aspect_ratio)
    return await loop.run_in_executor(None, fn)
