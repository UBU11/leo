from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    queued = "queued"
    scraping = "scraping"
    classified = "classified"
    pending_approval = "pending_approval"
    approved = "approved"
    sent = "sent"
    rejected = "rejected"
    failed = "failed"


class Lead(BaseModel):
    domain: str
    status: LeadStatus = LeadStatus.queued
    brand_name: str | None = None
    contact_email: str | None = None
    hook: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GarmentAnalysis(BaseModel):
    is_apparel_brand: bool
    detected_categories: list[str] = Field(default_factory=list)
    aesthetic_notes: str | None = None


class OutreachMessage(BaseModel):
    recipient_email: str
    subject: str
    body_text: str
