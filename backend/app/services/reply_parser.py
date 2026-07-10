"""Parse messy vendor replies into structured quote fields.

Handles real-world Indian vendor language:
  "372 per bag delivered"        "7300 per tonne ex-godown, GST extra"
  "delivery 7-10 days after order"   "will try our best"
  "BIS certificate attached"     "freight extra"

Every extracted field carries evidence (the phrase it came from) so the UI
can show why the system believes what it believes.
"""
import re
from datetime import date, datetime

from dateutil import parser as dateparser

from ..llm import get_provider

VAGUE_PHRASES = [
    "will try", "should be", "depends", "let us see", "most probably",
    "cannot commit", "not sure", "may be", "maybe", "hopefully", "we'll see",
]


def _extract(pattern: str, text: str, flags=re.IGNORECASE):
    return re.search(pattern, text, flags)


def parse_with_rules(text: str) -> tuple[dict, list[dict]]:
    """Returns (fields, evidence_items)."""
    lower = text.lower()
    fields: dict = {
        "price": None, "unit_basis": "", "delivery_included": None,
        "gst_included": None, "freight_included": None,
        "delivery_days": None, "delivery_date": None, "delivery_vague": False,
        "cert_attached": False, "flags": [],
    }
    items: list[dict] = []

    def note(field: str, value, evidence: str, confidence: float = 0.9):
        items.append({"field": field, "value": str(value), "evidence": evidence, "confidence": confidence})

    # --- price + unit basis ---
    m = _extract(r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(?:/|per\s*)\s*(bag|tonne|ton|mt|kg|cft|brass|piece|nos)", lower)
    if not m:
        # bare number followed by a basis word somewhere: "quoting 7300 ex godown per MT"
        m = _extract(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)", lower)
        if m:
            fields["price"] = float(m.group(1).replace(",", ""))
            note("price", fields["price"], m.group(0), 0.6)
            fields["flags"].append("price unit basis unclear")
    if m and fields["price"] is None:
        fields["price"] = float(m.group(1).replace(",", ""))
        unit = m.group(2)
        fields["unit_basis"] = {"ton": "tonne", "mt": "tonne", "piece": "nos"}.get(unit, unit)
        note("price", f'{fields["price"]} per {fields["unit_basis"]}', m.group(0))

    # --- delivered vs ex-godown ---
    if _extract(r"ex[-\s]?godown|ex[-\s]?works|ex[-\s]?factory|pickup|self lifting", lower):
        fields["delivery_included"] = False
        note("delivery_included", False, "ex-godown / pickup")
    elif _extract(r"\bdelivered\b|door delivery|at site|to site|including delivery", lower):
        fields["delivery_included"] = True
        note("delivery_included", True, "delivered / at site")

    # --- GST ---
    if _extract(r"gst\s*(?:@|at)?\s*\d{0,2}\s*%?\s*(?:extra|additional)|\+\s*gst|plus gst|excl\w* gst", lower):
        fields["gst_included"] = False
        note("gst_included", False, "GST extra")
    elif _extract(r"incl\w* gst|gst incl\w*|with gst|all inclusive|inclusive of gst", lower):
        fields["gst_included"] = True
        note("gst_included", True, "GST included")

    # --- freight ---
    if _extract(r"freight extra|transport extra|freight additional|transport charges extra", lower):
        fields["freight_included"] = False
        note("freight_included", False, "freight extra")
    elif _extract(r"freight incl\w*|including freight|transport incl\w*", lower) or fields["delivery_included"]:
        if _extract(r"freight|transport", lower) or fields["delivery_included"]:
            fields["freight_included"] = True
            note("freight_included", True, "delivered price / freight included", 0.8)

    # --- delivery timeline ---
    m = _extract(r"(\d+)\s*(?:-|to|–)\s*(\d+)\s*days?", lower)
    if m:
        fields["delivery_days"] = int(m.group(2))  # take the pessimistic end of the range
        note("delivery_days", f"{m.group(2)} (range {m.group(0)})", m.group(0))
    else:
        m = _extract(r"(?:in|within|delivery in|dispatch in)?\s*(\d+)\s*days?", lower)
        if m:
            fields["delivery_days"] = int(m.group(1))
            note("delivery_days", m.group(1), m.group(0))
    m = _extract(r"(?:by|delivery by|before)\s+(\d{1,2}(?:st|nd|rd|th)?\s+\w+|monday|tuesday|wednesday|thursday|friday|saturday|sunday)", lower)
    if m and fields["delivery_days"] is None:
        try:
            d = dateparser.parse(m.group(1), dayfirst=True, default=datetime.now()).date()
            if d < date.today():
                from datetime import timedelta
                d += timedelta(days=7)  # next weekday occurrence
            fields["delivery_date"] = d
            note("delivery_date", d.isoformat(), m.group(0))
        except (ValueError, OverflowError):
            pass

    # --- vagueness / evasive answers ---
    for phrase in VAGUE_PHRASES:
        if phrase in lower:
            fields["delivery_vague"] = True
            fields["flags"].append(f'evasive language: "{phrase}"')
            note("delivery_vague", True, phrase, 0.95)
            break

    # --- certificates ---
    if _extract(r"(bis|isi|test)\s*(cert\w*|licen\w*)?\s*(attached|enclosed|sent|available|sharing|shared)", lower) \
            or _extract(r"certificate (is )?(attached|available|enclosed)", lower):
        fields["cert_attached"] = True
        note("cert_attached", True, "certificate mentioned as attached/available")
    elif _extract(r"no (bis|certificate)|certificate not available|without certificate", lower):
        fields["cert_attached"] = False
        fields["flags"].append("vendor says certificate not available")
        note("cert_attached", False, "certificate not available", 0.95)

    # --- missing-field flags ---
    if fields["price"] is None:
        fields["flags"].append("no price found in reply")
    if fields["delivery_days"] is None and fields["delivery_date"] is None:
        fields["flags"].append("no delivery timeline")
    if fields["gst_included"] is None and fields["price"] is not None:
        fields["flags"].append("GST treatment not stated")

    return fields, items


def parse_reply(text: str, product: str = "") -> tuple[dict, list[dict], float]:
    """Returns (fields, evidence_items, confidence)."""
    fields, items = parse_with_rules(text)

    llm = get_provider().complete_json(
        system=(
            "You parse informal Indian vendor quote replies. Extract JSON with keys: "
            "price (number|null), unit_basis (bag/tonne/kg/nos/''), delivery_included (bool|null), "
            "gst_included (bool|null), freight_included (bool|null), delivery_days (int|null), "
            "delivery_vague (bool), cert_attached (bool), flags (list of strings for anything "
            f"ambiguous or evasive). Product context: {product or 'construction material'}."
        ),
        user=text,
    )
    if llm:
        for key in ("price", "unit_basis", "delivery_included", "gst_included",
                    "freight_included", "delivery_days", "delivery_vague", "cert_attached"):
            value = llm.get(key)
            if value is not None and value != "" and fields.get(key) in (None, "", False):
                fields[key] = value
        for flag in llm.get("flags") or []:
            if flag not in fields["flags"]:
                fields["flags"].append(str(flag))

    core = [fields["price"], fields["unit_basis"] or None,
            fields["delivery_days"] or fields["delivery_date"], fields["gst_included"]]
    confidence = round(sum(1 for v in core if v is not None) / len(core), 2)
    if fields["delivery_vague"]:
        confidence = max(0.1, confidence - 0.2)
    return fields, items, confidence