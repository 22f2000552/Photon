from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..agents.graph import launch_rfq
from ..database import get_db
from ..models import RFQ, Requirement
from ..schemas import RequirementCreate
from ..services.audit import log
from ..services.requirement_parser import parse_requirement

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.post("")
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db)):
    """Parse a natural-language requirement, create the RFQ, and immediately
    run the sourcing graph (Scout -> Outreach)."""
    fields, source, confidence = parse_requirement(payload.text)
    requirement = Requirement(
        raw_text=payload.text, parse_source=source, parse_confidence=confidence, **fields
    )
    db.add(requirement)
    db.flush()

    rfq = RFQ(requirement_id=requirement.id, status="draft")
    db.add(rfq)
    db.flush()
    log(db, "requirement", requirement.id, "created", {"source": source})
    db.commit()

    launch_rfq(rfq.id)  # LangGraph: scout -> outreach
    return {"rfq_id": rfq.id, "requirement_id": requirement.id}