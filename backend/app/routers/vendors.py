from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ReliabilityEvent, Vendor
from ..schemas import EventOut, VendorOut, VendorProfileOut

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()


@router.get("/search", response_model=list[VendorOut])
def search_vendors(q: str = "", category: str = "", city: str = "", db: Session = Depends(get_db)):
    vendors = db.query(Vendor).all()
    q, category, city = q.lower(), category.lower(), city.lower()
    result = []
    for vendor in vendors:
        haystack = f"{vendor.name} {vendor.city} {vendor.notes} {' '.join(vendor.categories or [])}".lower()
        if q and q not in haystack:
            continue
        if category and category not in [c.lower() for c in (vendor.categories or [])]:
            continue
        if city and city != vendor.city.lower():
            continue
        result.append(vendor)
    return result


@router.get("/{vendor_id}", response_model=VendorProfileOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(404, "vendor not found")
    profile = VendorProfileOut.model_validate(vendor)
    events = (
        db.query(ReliabilityEvent)
        .filter_by(vendor_id=vendor_id)
        .order_by(ReliabilityEvent.created_at.desc())
        .limit(30)
        .all()
    )
    profile.events = [EventOut.model_validate(e) for e in events]
    return profile