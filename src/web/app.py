from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.config import get_settings
from src.database.connection import get_db_connection

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Export Engine Review Dashboard")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class LeadApprovalPayload(BaseModel):
    generated_subject: Optional[str] = None
    generated_pitch: Optional[str] = None
    operator_notes: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def review_dashboard(request: Request):
    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        cursor = conn.execute(
            """
            SELECT id, domain, brand_name, country, contact_name, contact_email, 
                   instagram_handle, brand_tier, detected_gsm, fabric_construction, 
                   fit_style, generated_subject, generated_pitch, operator_notes, status
            FROM leads
            WHERE status = 'pending_approval'
            ORDER BY id ASC
            """
        )
        leads = [dict(row) for row in cursor.fetchall()]

    return templates.TemplateResponse(
        "review.html",
        {"request": request, "leads": leads},
    )


@app.post("/leads/{lead_id}/approve")
async def approve_lead(
    lead_id: int,
    generated_subject: str = Form(...),
    generated_pitch: str = Form(...),
    operator_notes: Optional[str] = Form(None),
):
    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        cursor = conn.execute(
            """
            UPDATE leads
            SET status = 'approved',
                generated_subject = ?,
                generated_pitch = ?,
                operator_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending_approval'
            """,
            (generated_subject, generated_pitch, operator_notes, lead_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found or not in pending_approval state")

    return RedirectResponse(url="/", status_code=303)


@app.post("/leads/{lead_id}/reject")
async def reject_lead(lead_id: int, operator_notes: Optional[str] = Form(None)):
    settings = get_settings()
    with get_db_connection(settings.database_path) as conn:
        cursor = conn.execute(
            """
            UPDATE leads
            SET status = 'rejected',
                operator_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending_approval'
            """,
            (operator_notes, lead_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found or not in pending_approval state")

    return RedirectResponse(url="/", status_code=303)
