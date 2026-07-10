"""Level all quotes onto one comparable basis — pure deterministic Python.

Target basis: requirement's unit, delivered to site, GST inclusive.
Every adjustment is recorded in normalization_notes so the comparison
table can show its working.
"""
from ..config import (
    BAGS_PER_TONNE,
    DEFAULT_GST_RATE,
    FREIGHT_ESTIMATE_PER_BAG,
    FREIGHT_ESTIMATE_PER_TONNE,
    GST_RATES,
)


def normalize_quote(fields: dict, requirement_unit: str, product: str) -> tuple[float | None, str, list[str]]:
    """Returns (normalized_price, basis_label, notes)."""
    price = fields.get("price")
    if price is None:
        return None, "", ["cannot normalize: no price extracted"]

    notes: list[str] = []
    unit = fields.get("unit_basis") or requirement_unit or "unit"
    target = requirement_unit or unit

    # --- unit conversion (cement: 1 tonne = 20 x 50kg bags) ---
    if unit != target:
        if unit == "tonne" and target == "bag":
            price = price / BAGS_PER_TONNE
            notes.append(f"converted per tonne → per bag (÷{BAGS_PER_TONNE})")
        elif unit == "bag" and target == "tonne":
            price = price * BAGS_PER_TONNE
            notes.append(f"converted per bag → per tonne (×{BAGS_PER_TONNE})")
        elif unit == "kg" and target == "tonne":
            price = price * 1000
            notes.append("converted per kg → per tonne (×1000)")
        elif unit == "kg" and target == "bag":
            price = price * 50
            notes.append("converted per kg → per bag (×50)")
        else:
            notes.append(f"quoted per {unit}, compared as-is (no conversion rule to {target})")

    # --- freight: level everything to 'delivered' ---
    freight_in = fields.get("freight_included")
    delivered = fields.get("delivery_included")
    if freight_in is False or delivered is False:
        estimate = FREIGHT_ESTIMATE_PER_BAG if target == "bag" else FREIGHT_ESTIMATE_PER_TONNE
        price += estimate
        notes.append(f"added estimated freight ₹{estimate:g}/{target} (quote was ex-godown / freight extra)")
    elif freight_in is None and delivered is None:
        notes.append("freight treatment unknown — assumed delivered (flagged)")

    # --- GST: level everything to GST-inclusive ---
    gst_in = fields.get("gst_included")
    rate = GST_RATES.get(product, DEFAULT_GST_RATE)
    if gst_in is False:
        price *= 1 + rate
        notes.append(f"added GST {rate:.0%} (quote said GST extra)")
    elif gst_in is None:
        notes.append("GST treatment not stated — assumed inclusive (flagged)")

    return round(price, 2), f"per {target}, delivered, incl. GST", notes