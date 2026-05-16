"""Azure OpenAI service — all text generation lives here.

NOTE: The Azure deployment (gpt-5-mini1) is a reasoning model.
Reasoning models:
  - Do not support 'temperature' parameter
  - Do not support 'max_tokens' (use 'max_completion_tokens')
  - Consume internal reasoning tokens before outputting — omit
    max_completion_tokens so the model can allocate enough budget.
"""
import json
import re
import asyncio
from openai import AsyncAzureOpenAI
from app.config import OPENAI_API_KEY, AZURE_ENDPOINT, AZURE_API_VERSION, AZURE_DEPLOYMENT

_client = AsyncAzureOpenAI(
    api_key=OPENAI_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_API_VERSION,
)

_PLATFORM_RULES = {
    "Instagram": "casual, emoji-rich, 150-220 chars for caption, visual-first writing, strong CTA",
    "Facebook": "conversational, 150-300 chars, community-oriented, question-based CTA",
    "Twitter": "punchy, max 250 chars, 1-2 hashtags only, no filler words",
    "WhatsApp": "personal, informal, no hashtags, feels like a direct message from a friend",
    "LinkedIn": "professional, 400-600 chars, narrative hook, industry-relevant, thought-leadership tone",
    "Email": "subject line on first line prefixed 'Subject:', then blank line, then body copy, clear CTA at end",
}

_STYLE_DIRECTIVES = {
    "photoreal": "photorealistic, DSLR photography style, natural lighting, sharp details",
    "illustration": "digital illustration, clean vector art style, vibrant colors",
    "3d": "3D render, cinema 4D style, soft shadows, depth of field, product visualization",
    "minimal": "minimalist, white space, single accent color, clean typography, no decoration",
    "corporate": "professional photography, blues and grays, structured composition",
    "futuristic": "dark background, neon accents, glowing elements, cyberpunk tech aesthetic",
    "luxury": "gold and black palette, elegant serif typography, high-end product photography",
}


def _parse_json_block(text: str) -> dict:
    """Extract JSON from a markdown code block or raw text."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    return json.loads(text.strip())


async def _chat(messages: list[dict]) -> str:
    """Single call to the reasoning model — no temperature, no token cap."""
    response = await _client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=messages,
    )
    return (response.choices[0].message.content or "").strip()


async def generate_social_content(
    platform: str,
    campaign_type: str,
    prompt: str,
    tone: str,
    audience: str,
    hashtag_count: int,
    cta_style: str,
    language: str,
) -> dict:
    """Return { content, hashtags } for a single platform."""
    rules = _PLATFORM_RULES.get(platform, "engaging, clear CTA")
    raw = await _chat([
        {
            "role": "user",
            "content": (
                f"You are an expert social media copywriter for {platform}.\n"
                f"Platform rules for {platform}: {rules}.\n\n"
                f"Campaign type: {campaign_type}\n"
                f"Product/Service: {prompt}\n"
                f"Tone: {tone}\n"
                f"Target audience: {audience}\n"
                f"CTA style: {cta_style}\n"
                f"Language: {language}\n"
                f"Number of hashtags: {hashtag_count}\n\n"
                f'Respond ONLY with valid JSON: {{"content": "...", "hashtags": ["#tag1"]}}\n'
                f"The content must follow {platform} rules. Include exactly {hashtag_count} hashtags."
            ),
        }
    ])
    try:
        return _parse_json_block(raw)
    except Exception:
        return {"content": raw, "hashtags": []}


async def generate_social_all_platforms(
    platforms: list[str],
    campaign_type: str,
    prompt: str,
    tone: str,
    audience: str,
    hashtag_count: int,
    cta_style: str,
    language: str,
) -> list[dict]:
    """Generate content for all platforms in parallel."""
    tasks = [
        generate_social_content(p, campaign_type, prompt, tone, audience, hashtag_count, cta_style, language)
        for p in platforms
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for platform, result in zip(platforms, results):
        if isinstance(result, Exception):
            out.append({"platform": platform, "content": f"Generation failed: {result}", "hashtags": []})
        else:
            out.append({"platform": platform, **result})
    return out


async def generate_copy_variants(
    channel: str,
    brief: str,
    tone: str,
    word_limit: int,
    seo_keywords: str,
    audience: str,
    language: str,
) -> list[dict]:
    """Return [{ label, content }] with Short / Medium / Long variants."""
    channel_note = {
        "email": "email body copy — include a subject line on the first line prefixed 'Subject:', blank line, then body",
        "landing": "landing page hero section — headline + subtext + CTA label",
        "ad": "paid ad — short headline + description",
        "push": "push notification — under 60 characters, urgency-driven",
    }.get(channel, channel)

    raw = await _chat([
        {
            "role": "user",
            "content": (
                f"You are a senior marketing copywriter.\n"
                f"Channel: {channel_note}\n"
                f"Brief: {brief}\n"
                f"Tone: {tone}\n"
                f"Audience: {audience}\n"
                f"SEO keywords (use naturally): {seo_keywords}\n"
                f"Language: {language}\n"
                f"Long variant word limit: {word_limit}\n\n"
                "Generate three ready-to-publish copy variants.\n"
                'Respond ONLY with valid JSON: {"short": "...", "medium": "...", "long": "..."}\n'
                f"short = ~20 words. medium = ~50 words. long = up to {word_limit} words."
            ),
        }
    ])
    try:
        parsed = _parse_json_block(raw)
        return [
            {"label": "Short", "content": parsed.get("short", "")},
            {"label": "Medium", "content": parsed.get("medium", "")},
            {"label": "Long", "content": parsed.get("long", "")},
        ]
    except Exception:
        return [{"label": "Variant 1", "content": raw}]


async def enhance_image_prompt(description: str, style: str) -> str:
    """Expand a brief description into a detailed visual prompt for image generation."""
    style_directive = _STYLE_DIRECTIVES.get(style.lower(), style)
    return await _chat([
        {
            "role": "user",
            "content": (
                f"You are an art director writing image generation prompts.\n"
                f"Brief: {description}\n"
                f"Visual style: {style_directive}\n\n"
                "Write a detailed visual prompt (2-3 sentences) describing composition, "
                "colors, lighting, and mood. Return only the prompt text, no preamble."
            ),
        }
    ])
