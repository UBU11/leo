import json
from typing import Literal, Optional
import httpx
from pydantic import BaseModel, Field

from src.config import get_settings


class GarmentAnalysis(BaseModel):
    brand_tier: Literal["MICRO_CAPSULE", "MID_MARKET"] = Field(
        description="MICRO_CAPSULE if low SKU count, frequent drops, or indie label. MID_MARKET if established line with full collections."
    )
    detected_gsm: Optional[int] = Field(
        default=None,
        description="Detected fabric GSM (e.g. 300, 350, 400). Null if unstated.",
    )
    fabric_construction: str = Field(
        description="E.g., Loopback French Terry, Combed Cotton Fleece, Single Jersey."
    )
    fit_style: str = Field(
        description="E.g., Boxy oversized, drop shoulder, cropped athletic."
    )
    cold_email_hook: str = Field(
        description="2 sentences max. Acknowledge their specific style/fabric, then propose our 25-piece MOQ trial (for MICRO) or supply-line cost reduction (for MID_MARKET) with pre-stitched labels. No marketing fluff."
    )


SYSTEM_PROMPT = """You are an expert apparel production director and fabric sourcing specialist.
Analyze the provided brand website content and extract garment manufacturing parameters.
Return ONLY valid JSON matching this schema:
{
  "brand_tier": "MICRO_CAPSULE" or "MID_MARKET",
  "detected_gsm": integer or null,
  "fabric_construction": "string description",
  "fit_style": "string description",
  "cold_email_hook": "2 sentences max cold email hook"
}
"""


async def analyze_garment_content(
    raw_markdown: str,
    ollama_url: Optional[str] = None,
    model_name: Optional[str] = None,
) -> GarmentAnalysis:
    settings = get_settings()
    base_url = ollama_url or settings.ollama_url
    model = model_name or settings.ollama_model

    prompt = f"Website Content:\n\n{raw_markdown[:4000]}\n\nExtract garment analysis JSON:"

    # ponytail: direct httpx call to local ollama /api/chat; avoids heavy langchain/llama-index wrappers
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "format": "json",
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        raw_output = data.get("message", {}).get("content", "{}")
        parsed = json.loads(raw_output)
        return GarmentAnalysis.model_validate(parsed)
