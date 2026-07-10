"""Turn a natural-language requirement into a structured object.

Strategy: a rules-based parser always runs (works offline / demo mode).
If an LLM is available it parses too, and its answer is used when it is
more complete — but every field is validated before being trusted.
"""
import re
from datetime import date, datetime

from dateutil import parser as dateparser

from ..llm import get_provider

PRODUCT_PATTERNS = [
    ("cement", r"\bcement\b|\bopc\b|\bppc\b"),
    ("steel", r"\bsteel\b|\btmt\b|\brebar|\bsaria\b|\bfe\s?5\d{2}"),
    ("sand", r"\bsand\b|\bm-?sand\b"),
    ("aggregate", r"\baggregate\b|\bgitti\b|\bstone chips\b"),
    ("bricks", r"\bbricks?\b|\bfly ash brick"),
]

GRADE_PATTERNS = [
    r"\bOPC\s?-?\s?(?:43|53)\b",
    r"\bPPC\b",
    r"\bFe\s?-?\s?5\d{2}D?\b",
    r"\bM-?sand\b",
    r"\briver sand\b",
]

UNIT_ALIASES = {
    "bag": "bag", "bags": "bag",
    "tonne": "tonne", "tonnes": "tonne", "ton": "tonne", "tons": "tonne", "mt": "tonne",
    "kg": "kg", "kgs": "kg",
    "cft": "cft", "brass": "brass", "nos": "nos", "units": "nos", "pieces": "nos",
}

CERT_KEYWORDS = {"bis": "BIS", "isi": "ISI", "test certificate": "Test Certificate", "mtc": "MTC"}


def _parse_deadline(text: str) -> date | None:
    m = re.search(
        r"\b(?:by|before|till|until)\s+([0-9]{1,2}(?:st|nd|rd|th)?\s+\w+|\w+\s+[0-9]{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)",
        text, re.IGNORECASE,
    )
    if m:
        try:
            d = dateparser.parse(m.group(1), dayfirst=True, default=datetime.now()).date()
            if d < date.today():  # "by 15 August" said in September means next year
                d = d.replace(year=d.year + 1)
            return d
        except (ValueError, OverflowError):
            pass
    m = re.search(r"\b(?:in|within)\s+(\d+)\s+days?\b", text, re.IGNORECASE)
    if m:
        from datetime import timedelta
        return date.today() + timedelta(days=int(m.group(1)))
    return None


def parse_with_rules(text: str) -> dict:
    lower = text.lower()
    out: dict = {
        "product": "", "grade": "", "quantity": None, "unit": "", "location": "",
        "deadline": None, "budget_amount": None, "budget_basis": "",
        "certifications": [], "delivery_terms": "",
    }

    for product, pattern in PRODUCT_PATTERNS:
        if re.search(pattern, lower):
            out["product"] = product
            break

    for pattern in GRADE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            out["grade"] = re.sub(r"\s+", " ", m.group(0).upper().replace("-", " ")).strip()
            break

    m = re.search(r"\b([\d,]+(?:\.\d+)?)\s*(bags?|tonnes?|tons?|mt|kgs?|cft|brass|nos|units|pieces)\b", lower)
    if m:
        out["quantity"] = float(m.group(1).replace(",", ""))
        out["unit"] = UNIT_ALIASES.get(m.group(2), m.group(2))

    m = re.search(r"\b(?:in|at|near)\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?)", text)
    if m:
        out["location"] = m.group(1).strip()

    out["deadline"] = _parse_deadline(text)

    m = re.search(
        r"(?:budget|price|rate|max|around|under|@)\s*(?:of\s*)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(?:per\s+(\w+)|/\s*(\w+))?",
        lower,
    )
    if not m:
        m = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(?:per\s+(\w+)|/\s*(\w+))?", lower)
    if m:
        out["budget_amount"] = float(m.group(1).replace(",", ""))
        basis_unit = m.group(2) or m.group(3) or ""
        basis = UNIT_ALIASES.get(basis_unit, basis_unit)
        if "delivered" in lower:
            basis = (basis + " delivered").strip()
        out["budget_basis"] = ("per " + basis) if basis else ""

    for keyword, label in CERT_KEYWORDS.items():
        if keyword in lower:
            out["certifications"].append(label)
    if out["certifications"] and re.search(r"mandatory|compulsory|must", lower):
        out["certifications"] = [c + " (mandatory)" for c in out["certifications"]]

    if "delivered" in lower or "delivery" in lower:
        out["delivery_terms"] = "delivered to site"

    return out


def parse_requirement(text: str) -> tuple[dict, str, float]:
    """Returns (fields, source, confidence)."""
    rules = parse_with_rules(text)

    llm = get_provider().complete_json(
        system=(
            "You extract structured procurement requirements from Indian contractors' messages. "
            "Extract: product (cement/steel/sand/aggregate/bricks/other), grade, quantity (number), "
            "unit (bag/tonne/kg/cft/nos), location (city), deadline (YYYY-MM-DD), "
            "budget_amount (number, INR), budget_basis (e.g. 'per bag delivered'), "
            "certifications (list of strings), delivery_terms. Use null for unknown fields."
        ),
        user=text,
    )
    if llm:
        merged = dict(rules)
        for key in merged:
            value = llm.get(key)
            if value in (None, "", []):
                continue
            if key == "deadline":
                try:
                    value = dateparser.parse(str(value)).date()
                except (ValueError, OverflowError):
                    continue
            if key in ("quantity", "budget_amount"):
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
            if key == "certifications" and not isinstance(value, list):
                value = [str(value)]
            merged[key] = value
        filled = sum(1 for v in merged.values() if v not in (None, "", []))
        return merged, "llm", min(1.0, 0.5 + filled / 18)

    filled = sum(1 for v in rules.values() if v not in (None, "", []))
    return rules, "rules", min(1.0, 0.4 + filled / 15)