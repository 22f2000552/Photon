"""Channel selection + RFQ message drafting + mock senders.

India-first rule: email is NOT assumed. Preference order is the vendor's
preferred contact, then WhatsApp, then email, then a phone call note.
Real WhatsApp/email delivery is mocked for the hackathon; the send path is
one function per channel so real integrations slot in without refactoring.
"""
from ..llm import get_provider
from ..models import Requirement, Vendor

CHANNEL_PRIORITY = ["whatsapp", "email", "phone"]


def choose_channel(vendor: Vendor) -> tuple[str, str]:
    """Returns (channel, contact_value). Falls back to a call note."""
    contacts = {c.channel: c for c in vendor.contacts}
    preferred = next((c for c in vendor.contacts if c.is_preferred), None)
    if preferred:
        return preferred.channel, preferred.value
    for channel in CHANNEL_PRIORITY:
        if channel in contacts:
            return channel, contacts[channel].value
    return "call_note", ""


def draft_rfq_message(req: Requirement, vendor: Vendor, channel: str) -> str:
    qty = f"{req.quantity:g} {req.unit}" if req.quantity else "required quantity"
    spec = " ".join(x for x in [req.grade, req.product] if x) or "material"
    lines = [
        f"Namaste {vendor.name},",
        f"We need {qty} of {spec}" + (f" at {req.location}" if req.location else "") + ".",
    ]
    if req.deadline:
        lines.append(f"Delivery needed by {req.deadline.strftime('%d %b %Y')}.")
    if req.certifications:
        lines.append(f"Required documents: {', '.join(req.certifications)}.")
    lines.append("Please share: rate (mention per bag/tonne, GST and freight treatment), "
                 "delivery timeline, and certificate copy.")
    lines.append("— RFQ Copilot on behalf of the contractor")
    template = "\n".join(lines)

    polished = get_provider().complete(
        system=(
            f"Rewrite this RFQ for {channel} to an Indian building-material vendor. "
            "Keep it short, polite, businesslike, in simple English. Keep every data point. "
            "Return only the message text."
        ),
        user=template,
    )
    return polished or template


def send(channel: str, contact: str, body: str) -> dict:
    """Mock transport. Returns delivery metadata stored on the message."""
    if channel == "whatsapp":
        return {"transport": "mock-whatsapp", "to": contact, "delivered": True,
                "note": "Mocked — swap with WhatsApp Business API / Twilio in production"}
    if channel == "email":
        return {"transport": "mock-smtp", "to": contact, "delivered": True,
                "note": "Mocked — swap with SMTP/SES in production"}
    return {"transport": "call_note", "to": contact or "site engineer to call",
            "delivered": False, "note": "Logged as a call task for the team"}