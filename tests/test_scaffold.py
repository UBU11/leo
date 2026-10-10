from datetime import datetime
from src.models import Lead, LeadStatus, GarmentAnalysis, OutreachMessage
from src.config import Settings


def test_domain_models():
    lead = Lead(domain="examplebrand.com", status=LeadStatus.queued)
    assert lead.domain == "examplebrand.com"
    assert lead.status == LeadStatus.queued
    assert isinstance(lead.created_at, datetime)

    analysis = GarmentAnalysis(is_apparel_brand=True, detected_categories=["hoodies"])
    assert analysis.is_apparel_brand is True

    msg = OutreachMessage(
        recipient_email="hello@examplebrand.com",
        subject="Direct Garment Export",
        body_text="Hi there",
    )
    assert msg.recipient_email == "hello@examplebrand.com"


def test_settings_load():
    settings = Settings()
    assert settings.app_env in ["development", "production", "test"]


def test_protocol_interfaces_exist():
    from typing import Protocol
    from src.database.repository import LeadRepository
    from src.ingest.loader import SeedLoader
    from src.scraper.crawler import StoreCrawler
    from src.classifier.analyzer import BrandAnalyzer
    from src.dispatcher.sender import OutboundSender
    from src.web.server import ReviewServer

    assert issubclass(LeadRepository, Protocol)
    assert issubclass(SeedLoader, Protocol)
    assert issubclass(StoreCrawler, Protocol)
    assert issubclass(BrandAnalyzer, Protocol)
    assert issubclass(OutboundSender, Protocol)
    assert issubclass(ReviewServer, Protocol)

