"""Outreach Agent — contacts vendors on the best channel, ingests replies."""
from sqlalchemy.orm import Session

from ..models import RFQ, ParsedQuoteItem, Quote, RFQMessage, Vendor
from ..services import channels as channel_svc
from ..services import memory as memory_svc
from ..services.audit import log
from ..services.normalization import normalize_quote
from ..services.reply_parser import parse_reply


def run_outreach(db: Session, rfq: RFQ) -> list[RFQMessage]:
    """Send the RFQ to every qualified scouted vendor over its best channel."""
    req = rfq.requirement
    sent: list[RFQMessage] = []
    for candidate in rfq.scout_result or []:
        if not candidate.get("qualified", True):
            continue
        vendor = db.get(Vendor, candidate["vendor_id"])
        if vendor is None:
            continue
        channel, contact = channel_svc.choose_channel(vendor)
        body = channel_svc.draft_rfq_message(req, vendor, channel)
        meta = channel_svc.send(channel, contact, body)
        message = RFQMessage(
            rfq_id=rfq.id, vendor_id=vendor.id, direction="outbound",
            channel=channel, body=body, status="sent", meta=meta,
        )
        db.add(message)
        memory_svc.bump_rfq_count(db, vendor.id)
        sent.append(message)

    rfq.status = "outreach" if sent else rfq.status
    log(db, "rfq", rfq.id, "outreach_sent", {"count": len(sent)})
    db.flush()
    return sent


def ingest_reply(db: Session, rfq: RFQ, vendor_id: int, channel: str, text: str,
                 response_hours: float | None = None) -> Quote:
    """Store an inbound reply, parse it into a structured quote, update memory."""
    message = RFQMessage(
        rfq_id=rfq.id, vendor_id=vendor_id, direction="inbound",
        channel=channel, body=text, status="received",
    )
    db.add(message)
    db.flush()

    fields, evidence, confidence = parse_reply(text, rfq.requirement.product)
    normalized, basis, notes = normalize_quote(fields, rfq.requirement.unit, rfq.requirement.product)

    quote = Quote(
        rfq_id=rfq.id, vendor_id=vendor_id, message_id=message.id, raw_text=text,
        price=fields["price"], unit_basis=fields["unit_basis"] or "",
        delivery_included=fields["delivery_included"], gst_included=fields["gst_included"],
        freight_included=fields["freight_included"], delivery_days=fields["delivery_days"],
        delivery_date=fields.get("delivery_date"), delivery_vague=fields["delivery_vague"],
        cert_attached=fields["cert_attached"], confidence=confidence, flags=fields["flags"],
        normalized_price=normalized, normalized_basis=basis, normalization_notes=notes,
    )
    db.add(quote)
    db.flush()
    for item in evidence:
        db.add(ParsedQuoteItem(quote_id=quote.id, **item))

    # Clarification loop: if key fields are missing, mark and note what to ask
    missing = [f for f in fields["flags"] if "no price" in f or "GST treatment" in f or "no delivery" in f]
    if missing:
        message.status = "needs_clarification"
        message.meta = {"clarify": missing}

    # Vendor memory write-back
    if response_hours is not None:
        memory_svc.record_response(db, vendor_id, response_hours, rfq.id)
    if fields["delivery_vague"]:
        memory_svc.record_event(db, vendor_id, "evasive_answer", "hedged on delivery commitment", rfq.id)
    elif fields["delivery_days"] or fields.get("delivery_date"):
        memory_svc.record_event(db, vendor_id, "clear_commitment", "gave a concrete delivery timeline", rfq.id)
    if fields["cert_attached"]:
        memory_svc.record_event(db, vendor_id, "cert_verified", "shared certificate with quote", rfq.id)

    rfq.status = "collecting"
    log(db, "quote", quote.id, "reply_parsed",
        {"vendor_id": vendor_id, "confidence": confidence, "flags": fields["flags"]})
    return quote