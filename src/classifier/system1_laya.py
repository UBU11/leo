from typing import Tuple

# ponytail: token-based set intersection gives sub-millisecond screening without heavy ML models
TARGET_APPAREL_KEYWORDS = {
    "hoodie", "hoodies", "tee", "tees", "t-shirt", "sweatshirt", "sweatpants",
    "streetwear", "fleece", "terry", "french terry", "heavyweight", "gsm",
    "oversized", "cut and sew", "cut & sew", "blanks", "drop shoulder",
    "garment", "apparel", "clothing", "vintage wash", "loopback", "ribbed",
}

DISQUALIFYING_KEYWORDS = {
    "sneakers", "footwear", "shoes", "software", "saas", "digital download",
    "phone cases", "supplements", "skincare", "cosmetics", "furniture",
    "jewelry", "eyewear", "sunglasses", "marketplace", "electronics",
}


def screen_apparel_niche(raw_text: str) -> Tuple[bool, str]:
    if not raw_text:
        return False, "EMPTY_CONTENT"

    text = raw_text.lower()

    apparel_hits = sum(1 for kw in TARGET_APPAREL_KEYWORDS if kw in text)
    disqualify_hits = sum(1 for kw in DISQUALIFYING_KEYWORDS if kw in text)

    if disqualify_hits >= 3 and apparel_hits < 2:
        return False, "DISQUALIFIED_NON_APPAREL"

    if apparel_hits >= 2:
        if "streetwear" in text or "hoodie" in text or "heavyweight" in text:
            return True, "STREETWEAR_HEAVYWEIGHT"
        return True, "GENERAL_APPAREL"

    return False, "LOW_APPAREL_SIGNAL"
