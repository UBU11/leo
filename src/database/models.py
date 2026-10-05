from typing import Literal

LeadStatus = Literal[
    "queued",
    "scraping",
    "classified",
    "pending_approval",
    "approved",
    "sent",
    "rejected",
    "failed",
]

LEAD_STATUSES: set[LeadStatus] = {
    "queued",
    "scraping",
    "classified",
    "pending_approval",
    "approved",
    "sent",
    "rejected",
    "failed",
}

# ponytail: state transitions modeled as a simple adjacency set; stdlib types only, no external FSM package needed
VALID_TRANSITIONS: dict[LeadStatus, set[LeadStatus]] = {
    "queued": {"scraping", "failed"},
    "scraping": {"classified", "rejected", "failed"},
    "classified": {"pending_approval", "rejected", "failed"},
    "pending_approval": {"approved", "rejected", "failed"},
    "approved": {"sent", "failed"},
    "sent": set(),
    "rejected": {"queued"},
    "failed": {"queued"},
}

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL UNIQUE,
    brand_name TEXT,
    country TEXT CHECK(country IN ('US', 'UK', 'AU', 'AE', 'OTHER')),
    contact_name TEXT,
    contact_email TEXT,
    instagram_handle TEXT,
    
    -- Scraped & Enriched Data
    raw_markdown TEXT,
    system1_passed INTEGER DEFAULT 0,
    system1_niche TEXT,
    
    -- Extracted Garment Parameters
    brand_tier TEXT CHECK(brand_tier IN ('MICRO_CAPSULE', 'MID_MARKET', 'UNKNOWN')),
    detected_gsm INTEGER,
    fabric_construction TEXT,
    fit_style TEXT,
    
    -- Copy & Review
    generated_subject TEXT,
    generated_pitch TEXT,
    operator_notes TEXT,
    
    -- State Machine
    status TEXT DEFAULT 'queued' CHECK(status IN (
        'queued', 'scraping', 'classified', 'pending_approval', 
        'approved', 'sent', 'rejected', 'failed'
    )),
    error_log TEXT,
    
    locked_until TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads (status);
CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads (domain);
"""


def is_valid_transition(current_status: LeadStatus, next_status: LeadStatus) -> bool:
    return next_status in VALID_TRANSITIONS.get(current_status, set())
