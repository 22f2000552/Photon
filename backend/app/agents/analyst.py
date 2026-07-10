"""Analyst Agent — levels quotes, scores vendors, produces the top-3 shortlist.

All math is deterministic (services.scoring / services.normalization).
The LLM only polishes the explanation paragraph; a template version is
always generated first so demo mode reads well too.
"""
from sqlalchemy.orm import Session

from ..llm import get_provider
from ..models import RFQ, Vendor
from ..services import scoring
from ..services.audit import log


def _score_quotes(db: Session, rfq: RFQ) -> None:
    req = rfq.requirement
    priced = [q for q in rfq.quotes if q.normalized_price is not None]
    best = min((q.normalized_price for q in priced), default=0)
    certs_required = bool(req.certifications)

    for quote in rfq.quotes:
        vendor = db.get(Vendor, quote.vendor_id)
        p, p_ev = scoring.price_score(quote.normalized_price, best, req.budget_amount)
        d, d_ev = scoring.delivery_score(
            {"delivery_days": quote.delivery_days, "delivery_date": quote.delivery_date,
             "delivery_vague": quote.delivery_vague},
            req.deadline,
        )
        doc, doc_ev = scoring.doc_score(
            quote.cert_attached, [c.status for c in vendor.certificates], certs_required
        )
        r, r_ev = scoring.reliability_from_memory(vendor.memory)

        quote.price_score, quote.delivery_score = p, d
        quote.doc_score, quote.reliability_score = doc, r
        quote.overall_score = scoring.overall(p, d, doc, r)
        quote.score_evidence = {"price": p_ev, "delivery": d_ev, "docs": doc_ev, "reliability": r_ev}

    ranked = sorted(rfq.quotes, key=lambda q: q.overall_score or 0, reverse=True)
    for i, quote in enumerate(ranked, start=1):
        quote.rank = i


def _build_shortlist(db: Session, rfq: RFQ) -> list[dict]:
    top = sorted([q for q in rfq.quotes if q.rank], key=lambda q: q.rank)[:3]
    shortlist = []
    for quote in top:
        vendor = db.get(Vendor, quote.vendor_id)
        reasons = []
        ev = quote.score_evidence or {}
        if quote.price_score and quote.price_score >= 80:
            reasons.append(f"strong price ({ev.get('price', '')})")
        elif quote.price_score is not None:
            reasons.append(f"price: {ev.get('price', 'n/a')}")
        reasons.append(f"delivery: {ev.get('delivery', 'n/a')}")
        if quote.doc_score and quote.doc_score >= 70:
            reasons.append("documentation in order")
        elif ev.get("docs"):
            reasons.append(f"docs: {ev['docs']}")
        reasons.append(f"track record: {ev.get('reliability', 'n/a')}")
        risks = list(quote.flags or [])
        shortlist.append({
            "rank": quote.rank, "vendor_id": vendor.id, "vendor_name": vendor.name,
            "city": vendor.city, "quote_id": quote.id,
            "normalized_price": quote.normalized_price, "normalized_basis": quote.normalized_basis,
            "overall_score": quote.overall_score,
            "scores": {"price": quote.price_score, "delivery": quote.delivery_score,
                       "docs": quote.doc_score, "reliability": quote.reliability_score},
            "reasons": reasons, "risks": risks,
        })
    return shortlist


def _template_explanation(rfq: RFQ, shortlist: list[dict]) -> str:
    if not shortlist:
        return "No comparable quotes were received yet, so a shortlist cannot be formed."
    req = rfq.requirement
    top = shortlist[0]
    lines = [
        f"For {req.quantity:g} {req.unit} of {req.grade or req.product}"
        f"{' in ' + req.location if req.location else ''}, "
        f"{len(rfq.quotes)} quotes were compared on a leveled basis ({top['normalized_basis'] or 'delivered, incl. GST'})."
    ]
    for entry in shortlist:
        price = f"₹{entry['normalized_price']:g}" if entry["normalized_price"] else "price unclear"
        risk = f" Watch out: {entry['risks'][0]}." if entry["risks"] else ""
        lines.append(
            f"#{entry['rank']} {entry['vendor_name']} ({entry['city']}) — {price}, "
            f"overall {entry['overall_score']:g}/100. {entry['reasons'][1].capitalize()}.{risk}"
        )
    skipped = len(rfq.quotes) - len(shortlist)
    if skipped > 0:
        lines.append(f"{skipped} other quote(s) ranked lower on the same criteria.")
    return " ".join(lines)


def run_analyst(db: Session, rfq: RFQ) -> dict:
    _score_quotes(db, rfq)
    shortlist = _build_shortlist(db, rfq)
    explanation = _template_explanation(rfq, shortlist)

    polished = get_provider().complete(
        system=(
            "You are a procurement analyst for an Indian contractor. Rewrite this comparison "
            "summary as one clear, plain-language paragraph. Keep every number and vendor name "
            "exactly as given. Do not invent facts. Return only the paragraph."
        ),
        user=explanation,
    )

    rfq.shortlist = shortlist
    rfq.explanation = polished or explanation
    rfq.status = "analyzed"
    log(db, "rfq", rfq.id, "shortlist_generated", {"top": [s["vendor_name"] for s in shortlist]})
    return {"shortlist": shortlist, "explanation": rfq.explanation}