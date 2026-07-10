import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..agents.graph import analyze_rfq
from ..agents.outreach import ingest_reply, run_outreach
from ..agents.scout import run_scout
from ..config import STORAGE_DIR
from ..database import get_db
from ..models import RFQ, Quote, RFQMessage, Vendor
from ..schemas import MessageOut, QuoteOut, ReplyIn, RFQDetail, RFQSummary, VendorOut
from ..services import memory as memory_svc
from ..services.audit import log

router = APIRouter(prefix="/api/rfqs", tags=["rfqs"])


def _get_rfq(db: Session, rfq_id: int) -> RFQ:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(404, "RFQ not found")
    return rfq


@router.get("", response_model=list[RFQSummary])
def list_rfqs(db: Session = Depends(get_db)):
    rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).all()
    out = []
    for rfq in rfqs:
        summary = RFQSummary.model_validate(rfq)
        summary.quote_count = len(rfq.quotes)
        summary.contacted_count = len({m.vendor_id for m in rfq.messages if m.direction == "outbound"})
        out.append(summary)
    return out


@router.get("/{rfq_id}", response_model=RFQDetail)
def get_rfq(rfq_id: int, db: Session = Depends(get_db)):
    rfq = _get_rfq(db, rfq_id)
    detail = RFQDetail.model_validate(rfq)
    detail.messages = [MessageOut.model_validate(m) for m in
                       sorted(rfq.messages, key=lambda m: m.created_at)]
    detail.quotes = [QuoteOut.model_validate(q) for q in rfq.quotes]
    vendor_ids = {m.vendor_id for m in rfq.messages} | {q.vendor_id for q in rfq.quotes} \
        | {c["vendor_id"] for c in (rfq.scout_result or [])}
    vendors = db.query(Vendor).filter(Vendor.id.in_(vendor_ids)).all() if vendor_ids else []
    detail.vendors = [VendorOut.model_validate(v) for v in vendors]
    return detail


@router.post("/{rfq_id}/scout")
def scout(rfq_id: int, db: Session = Depends(get_db)):
    rfq = _get_rfq(db, rfq_id)
    result = run_scout(db, rfq)
    db.commit()
    return {"candidates": result}


@router.post("/{rfq_id}/outreach")
def outreach(rfq_id: int, db: Session = Depends(get_db)):
    rfq = _get_rfq(db, rfq_id)
    sent = run_outreach(db, rfq)
    db.commit()
    return {"sent": len(sent)}


@router.post("/{rfq_id}/replies")
def add_reply(rfq_id: int, payload: ReplyIn, db: Session = Depends(get_db)):
    """Ingest a vendor reply from any channel (manual entry included)."""
    rfq = _get_rfq(db, rfq_id)
    quote = ingest_reply(db, rfq, payload.vendor_id, payload.channel, payload.text)
    db.commit()
    return {"quote_id": quote.id, "confidence": quote.confidence, "flags": quote.flags}


@router.post("/{rfq_id}/replies/upload")
def upload_reply(rfq_id: int, vendor_id: int = Form(...), note: str = Form(""),
                 file: UploadFile = File(...), db: Session = Depends(get_db)):
    """PDF / image quotation upload. Stored locally; marks documentation received."""
    rfq = _get_rfq(db, rfq_id)
    dest = STORAGE_DIR / f"{uuid.uuid4().hex[:8]}_{file.filename}"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    existing = db.query(Quote).filter_by(rfq_id=rfq_id, vendor_id=vendor_id).first()
    if existing and not note:
        # Attachment supporting an earlier reply — mark docs received
        existing.cert_attached = True
        db.add(RFQMessage(rfq_id=rfq_id, vendor_id=vendor_id, direction="inbound",
                          channel="upload", body=f"[file] {file.filename}",
                          status="received", meta={"file": str(dest.name)}))
        memory_svc.record_event(db, vendor_id, "cert_verified", f"uploaded {file.filename}", rfq_id)
        db.commit()
        return {"quote_id": existing.id, "attached_to": "existing quote"}

    quote = ingest_reply(db, rfq, vendor_id, "upload", note or f"[file] {file.filename}")
    quote.cert_attached = True
    db.commit()
    return {"quote_id": quote.id, "file": dest.name}


@router.post("/{rfq_id}/simulate-replies")
def simulate_replies(rfq_id: int, db: Session = Depends(get_db)):
    """Demo mode: replay each contacted vendor's canned messy reply."""
    rfq = _get_rfq(db, rfq_id)
    product = rfq.requirement.product or "cement"
    contacted = {m.vendor_id for m in rfq.messages if m.direction == "outbound"}
    replied = {q.vendor_id for q in rfq.quotes}
    ingested, ghosted = 0, 0

    for vendor_id in contacted - replied:
        vendor = db.get(Vendor, vendor_id)
        replies = vendor.demo_replies or {}
        text = replies.get(product) or replies.get("generic")
        if text == "__ghost__":
            memory_svc.record_event(db, vendor_id, "ghosted", "never replied to RFQ", rfq_id)
            ghosted += 1
            continue
        if not text:
            continue
        hours = float(replies.get("response_hours", (vendor_id * 7) % 24 + 2))
        ingest_reply(db, rfq, vendor_id, replies.get("channel", "whatsapp"), text, response_hours=hours)
        ingested += 1

    log(db, "rfq", rfq_id, "replies_simulated", {"ingested": ingested, "ghosted": ghosted})
    db.commit()
    return {"ingested": ingested, "ghosted": ghosted}


@router.post("/{rfq_id}/shortlist")
def shortlist(rfq_id: int, db: Session = Depends(get_db)):
    """Run the analysis graph: collect -> normalize -> score -> explain."""
    _get_rfq(db, rfq_id)
    state = analyze_rfq(rfq_id)
    if not state.get("shortlist"):
        return {"shortlist": [], "explanation": "No quotes to analyze yet — ingest or simulate replies first."}
    return {"shortlist": state["shortlist"], "explanation": state["explanation"]}