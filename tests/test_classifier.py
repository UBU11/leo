from src.classifier.system1_laya import screen_apparel_niche
from src.classifier.system2_ollama import GarmentAnalysis


def test_system1_detects_streetwear_apparel():
    content = "Heavyweight 350 GSM custom cut & sew streetwear hoodie with loopback french terry fleece."
    is_valid, category = screen_apparel_niche(content)
    assert is_valid is True
    assert category == "STREETWEAR_HEAVYWEIGHT"


def test_system1_rejects_non_apparel_domain():
    content = "SaaS software platform for managing enterprise phone cases and electronics marketplace."
    is_valid, category = screen_apparel_niche(content)
    assert is_valid is False
    assert category == "DISQUALIFIED_NON_APPAREL"


def test_garment_analysis_pydantic_schema():
    payload = {
        "brand_tier": "MICRO_CAPSULE",
        "detected_gsm": 380,
        "fabric_construction": "Loopback French Terry",
        "fit_style": "Boxy oversized drop shoulder",
        "cold_email_hook": "Loved your 380 GSM hoodies. We do 25-piece trial runs with custom care tags.",
    }
    model = GarmentAnalysis.model_validate(payload)
    assert model.brand_tier == "MICRO_CAPSULE"
    assert model.detected_gsm == 380
