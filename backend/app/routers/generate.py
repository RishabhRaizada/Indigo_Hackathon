from fastapi import APIRouter, HTTPException
from app.schemas.generate import (
    SocialRequest, SocialResponse, SocialPlatformResult,
    CopyRequest, CopyResponse, CopyVariant,
    BannerRequest, BannerResponse,
    ImageGenRequest, ImageGenResponse,
)
from app.services import openai_service, gemini_service

router = APIRouter(prefix="/api/v1/generate", tags=["generate"])


@router.get("/health")
async def health():
    return {"status": "ok"}


# ── Social ────────────────────────────────────────────────────────────────────

@router.post("/social", response_model=SocialResponse)
async def generate_social(req: SocialRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    if not req.platforms:
        raise HTTPException(status_code=400, detail="At least one platform is required")

    # Generate text for all platforms in parallel
    platform_results = await openai_service.generate_social_all_platforms(
        platforms=req.platforms,
        campaign_type=req.campaignType,
        prompt=req.prompt,
        tone=req.tone,
        audience=req.audience,
        hashtag_count=req.hashtagCount,
        cta_style=req.ctaStyle,
        language=req.language,
    )

    # Generate image from the prompt
    image_url = None
    try:
        enhanced = await openai_service.enhance_image_prompt(req.prompt, "photoreal")
        image_url = await gemini_service.generate_image(enhanced, "1:1")
    except Exception as e:
        print(f"[Social] Image generation skipped: {e}")

    results = [
        SocialPlatformResult(
            platform=r["platform"],
            content=r.get("content", ""),
            hashtags=r.get("hashtags", []),
        )
        for r in platform_results
    ]

    return SocialResponse(results=results, imageUrl=image_url)


# ── Copywriter ────────────────────────────────────────────────────────────────

@router.post("/copy", response_model=CopyResponse)
async def generate_copy(req: CopyRequest):
    if not req.brief.strip():
        raise HTTPException(status_code=400, detail="Brief is required")

    variants_raw = await openai_service.generate_copy_variants(
        channel=req.channel,
        brief=req.brief,
        tone=req.tone,
        word_limit=req.wordLimit,
        seo_keywords=req.seoKeywords,
        audience=req.audience,
        language=req.language,
    )

    return CopyResponse(
        variants=[CopyVariant(label=v["label"], content=v["content"]) for v in variants_raw]
    )


# ── Banner ────────────────────────────────────────────────────────────────────

@router.post("/banner", response_model=BannerResponse)
async def generate_banner(req: BannerRequest):
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")

    # Enhance prompt first, then generate image
    enhanced = await openai_service.enhance_image_prompt(req.description, req.style)

    # Map resolution to size hint for prompt
    res_hint = {"sd": "standard definition", "hd": "high resolution", "4k": "ultra-high resolution 4K"}.get(
        req.resolution, "high resolution"
    )
    full_prompt = f"{enhanced} {res_hint} marketing banner."

    image_url = await gemini_service.generate_image(full_prompt, req.aspectRatio)

    return BannerResponse(imageUrl=image_url, enhancedPrompt=enhanced)


# ── Image Gen ─────────────────────────────────────────────────────────────────

@router.post("/image", response_model=ImageGenResponse)
async def generate_image(req: ImageGenRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    enhanced = await openai_service.enhance_image_prompt(req.prompt, req.style)
    image_url = await gemini_service.generate_image(enhanced, "1:1")

    return ImageGenResponse(imageUrl=image_url, enhancedPrompt=enhanced)
