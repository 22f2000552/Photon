"""Scout Agent — searches the vendor pool, verifies profiles, flags anomalies."""
import re
from datetime import date

from sqlalchemy.orm import Session

from ..models import RFQ, Vendor
from ..services.audit import log

# GSTIN: 2-digit state code + 10-char PAN + entity code + 'Z' + checksum
GST_FORMAT = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$")


def profile_completeness(vendor: Vendor) -> float:
    checks = [
        bool(vendor.name), bool(vendor.city), bool(vendor.gst_number),
        bool(vendor.categories), len(vendor.contacts) > 0,
        any(c.channel == "whatsapp" for c in vendor.contacts),
        len(vendor.certificates) > 0,
    ]
    return round(sum(checks) / len(checks), 2)


def anomaly_flags(vendor: Vendor, product: str) -> list[str]:
    flags: list[str] = []
    if not vendor.contacts:
        flags.append("no contact details on file")
    if vendor.gst_number and not GST_FORMAT.match(vendor.gst_number):
        flags.append("GST number format looks invalid")
    if not vendor.gst_number:
        flags.append("GST number missing")
    for cert in vendor.certificates:
        if cert.status == "expired" or (cert.valid_till and cert.valid_till < date.today()):
            flags.append(f"{cert.cert_type} certificate expired")
        elif cert.status == "missing_number" or not cert.number:
            flags.append(f"{cert.cert_type} certificate has no number")
        elif cert.status == "invalid_format":
            flags.append(f"{cert.cert_type} certificate number format invalid")
    if product and product not in (vendor.categories or []):
        flags.append(f"product match unclear (deals in {', '.join(vendor.categories or ['?'])})")
    return flags


def run_scout(db: Session, rfq: RFQ) -> list[dict]:
    req = rfq.requirement
    candidates = db.query(Vendor).all()

    # Category match first, then location proximity
    matched = [v for v in candidates if not req.product or req.product in (v.categories or [])]
    if not matched:  # fall back to fuzzy note match so demo never dead-ends
        matched = [v for v in candidates if req.product and req.product in (v.notes or "").lower()] or candidates

    location = (req.location or "").lower()
    matched.sort(key=lambda v: (
        0 if location and v.city.lower() == location else (1 if location and v.state else 2),
        -(v.memory.reliability_score if v.memory else 50),
    ))

    result = []
    for vendor in matched[:8]:
        vendor.profile_completeness = profile_completeness(vendor)
        flags = anomaly_flags(vendor, req.product)
        result.append({
            "vendor_id": vendor.id,
            "name": vendor.name,
            "city": vendor.city,
            "channels": sorted({c.channel for c in vendor.contacts}),
            "certificates": [
                {"type": c.cert_type, "number": c.number or "—", "status": c.status}
                for c in vendor.certificates
            ],
            "profile_completeness": vendor.profile_completeness,
            "flags": flags,
            "reliability_score": vendor.memory.reliability_score if vendor.memory else 50.0,
            "past_rfqs": vendor.memory.rfq_count if vendor.memory else 0,
            "qualified": len([f for f in flags if "no contact" in f or "product match" in f]) == 0,
        })

    rfq.scout_result = result
    rfq.status = "scouting"
    log(db, "rfq", rfq.id, "scout_completed", {"candidates": len(result)})
    return result