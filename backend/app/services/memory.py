"""Vendor memory: every RFQ writes behaviour back, future rankings read it."""
from sqlalchemy.orm import Session

from ..models import ReliabilityEvent, Vendor, VendorMemory

EVENT_IMPACT = {
    "replied_fast": +4, "replied_slow": -2, "ghosted": -10,
    "on_time_delivery": +8, "late_delivery": -8,
    "cert_verified": +3, "cert_issue": -5,
    "clear_commitment": +3, "evasive_answer": -4,
}


def get_or_create_memory(db: Session, vendor_id: int) -> VendorMemory:
    memory = db.query(VendorMemory).filter_by(vendor_id=vendor_id).first()
    if memory is None:
        memory = VendorMemory(vendor_id=vendor_id)
        db.add(memory)
        db.flush()
    return memory


def record_event(db: Session, vendor_id: int, event_type: str, detail: str = "",
                 rfq_id: int | None = None) -> ReliabilityEvent:
    impact = EVENT_IMPACT.get(event_type, 0)
    event = ReliabilityEvent(vendor_id=vendor_id, rfq_id=rfq_id,
                             event_type=event_type, detail=detail, impact=impact)
    db.add(event)
    memory = get_or_create_memory(db, vendor_id)
    memory.reliability_score = max(0.0, min(100.0, memory.reliability_score + impact))
    if event_type == "ghosted":
        memory.ghost_count += 1
    db.flush()
    return event


def record_response(db: Session, vendor_id: int, response_hours: float, rfq_id: int | None = None):
    memory = get_or_create_memory(db, vendor_id)
    if memory.avg_response_hours is None:
        memory.avg_response_hours = response_hours
    else:  # running average across RFQs
        memory.avg_response_hours = round((memory.avg_response_hours + response_hours) / 2, 1)
    event = "replied_fast" if response_hours <= 12 else "replied_slow"
    record_event(db, vendor_id, event, f"responded in {response_hours:g}h", rfq_id)


def bump_rfq_count(db: Session, vendor_id: int):
    memory = get_or_create_memory(db, vendor_id)
    memory.rfq_count += 1