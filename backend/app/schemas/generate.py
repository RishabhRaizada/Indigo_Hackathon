from pydantic import BaseModel
from typing import Optional


# ── Social ──────────────────────────────────────────────────────────────────

class SocialRequest(BaseModel):
    campaignType: str
    platforms: list[str]
    prompt: str
    tone: str = "Professional"
    audience: str = ""
    hashtagCount: int = 5
    ctaStyle: str = "Learn More"
    language: str = "English"
    projectId: str = ""
    projectName: str = ""


class SocialPlatformResult(BaseModel):
    platform: str
    content: str
    hashtags: list[str]


class SocialResponse(BaseModel):
    results: list[SocialPlatformResult]
    imageUrl: Optional[str] = None      # base64 data URL or None


# ── Copywriter ───────────────────────────────────────────────────────────────

class CopyRequest(BaseModel):
    channel: str
    brief: str
    tone: str = "Professional"
    wordLimit: int = 100
    seoKeywords: str = ""
    audience: str = ""
    language: str = "English"
    projectId: str = ""


class CopyVariant(BaseModel):
    label: str       # "Short", "Medium", "Long"
    content: str


class CopyResponse(BaseModel):
    variants: list[CopyVariant]


# ── Banner ───────────────────────────────────────────────────────────────────

class BannerRequest(BaseModel):
    description: str
    aspectRatio: str = "16:9"
    resolution: str = "hd"
    style: str = "Minimal"
    width: Optional[int] = None
    height: Optional[int] = None
    projectId: str = ""


class BannerResponse(BaseModel):
    imageUrl: Optional[str] = None      # base64 data URL or None
    enhancedPrompt: str


# ── Image Gen ────────────────────────────────────────────────────────────────

class ImageGenRequest(BaseModel):
    prompt: str
    style: str = "photoreal"
    size: str = "1024"
    projectId: str = ""


class ImageGenResponse(BaseModel):
    imageUrl: Optional[str] = None      # base64 data URL or None
    enhancedPrompt: str
