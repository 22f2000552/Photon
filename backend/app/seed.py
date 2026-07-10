"""Seed data: realistic vendor pool + two sample RFQs so the demo is alive
on first run. Canned messy replies power the 'Simulate replies' button.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .agents.graph import analyze_rfq, launch_rfq
from .database import SessionLocal
from .models import RFQ, Certificate, Requirement, Vendor, VendorContact
from .services import memory as memory_svc
from .services.requirement_parser import parse_requirement

TODAY = date.today()

VENDORS = [
    {
        "name": "Sangam Cement Traders", "city": "Prayagraj", "state": "Uttar Pradesh",
        "gst_number": "09AAACS1234F1Z5", "categories": ["cement"],
        "notes": "Authorized UltraTech & ACC dealer near Naini. Responsive on WhatsApp.",
        "contacts": [("whatsapp", "+91 94150 11111", True), ("phone", "+91 94150 11111", False)],
        "certs": [("BIS", "CM/L-7654321", TODAY + timedelta(days=400), "valid")],
        "demo_replies": {"cement": "372 per bag delivered, GST extra. Can supply 500 bags, delivery by 12 August. BIS certificate attached.", "channel": "whatsapp", "response_hours": 2},
        "history": [("replied_fast", "quoted within 2 hours"), ("on_time_delivery", "300 bags delivered on promised date"), ("cert_verified", "BIS licence verified")],
    },
    {
        "name": "Triveni Building Materials", "city": "Prayagraj", "state": "Uttar Pradesh",
        "gst_number": "09AABCT5678G1Z2", "categories": ["cement", "bricks"],
        "notes": "Old-school trader in Civil Lines, prefers email for written quotes.",
        "contacts": [("email", "trivenibuildmat@gmail.com", True), ("phone", "+91 98390 22222", False)],
        "certs": [("BIS", "CM/L-1122334", TODAY - timedelta(days=60), "expired")],
        "demo_replies": {"cement": "Rate Rs 355 per bag ex-godown, freight extra. Dispatch in 3-4 days. GST 28% extra.", "channel": "email", "response_hours": 9},
        "history": [("replied_fast", "quoted same day"), ("late_delivery", "delivered 2 days late in May 2026")],
    },
    {
        "name": "Kanha Cement Depot", "city": "Varanasi", "state": "Uttar Pradesh",
        "gst_number": "", "categories": ["cement"],
        "notes": "Cheap bulk supplier, WhatsApp only. Paperwork usually incomplete.",
        "contacts": [("whatsapp", "+91 90050 33333", True)],
        "certs": [("BIS", "", None, "missing_number")],
        "demo_replies": {"cement": "7300 per tonne ex godown. gst extra. delivery depends on truck availability, will try our best.", "channel": "whatsapp", "response_hours": 20},
        "history": [("replied_slow", "took a day to reply"), ("evasive_answer", "would not commit a delivery date"), ("cert_issue", "could not produce BIS number")],
    },
    {
        "name": "UP Cement Agencies", "city": "Kanpur", "state": "Uttar Pradesh",
        "gst_number": "09AAECU9012H1Z8", "categories": ["cement"],
        "notes": "Large distributor, formal quotes on email, a bit slow but dependable.",
        "contacts": [("email", "sales@upcementagencies.in", True), ("phone", "+91 93055 44444", False)],
        "certs": [("BIS", "CM/L-9988776", TODAY + timedelta(days=200), "valid")],
        "demo_replies": {"cement": "We can offer OPC 53 @ Rs 390 per bag delivered including GST. Delivery 7-10 days after order confirmation. BIS certificate attached.", "channel": "email", "response_hours": 26},
        "history": [("replied_slow", "quoted next day"), ("on_time_delivery", "full rake delivered on schedule"), ("cert_verified", "documents always in order")],
    },
    {
        "name": "Shree Balaji Enterprises", "city": "Prayagraj", "state": "Uttar Pradesh",
        "gst_number": "09XXXXX0000A0A0", "categories": ["cement", "sand"],
        "notes": "Phone-only trader near Jhunsi. Has gone silent on past enquiries.",
        "contacts": [("phone", "+91 88400 55555", True)],
        "certs": [],
        "demo_replies": {"cement": "__ghost__", "sand": "4300 per brass, will confirm delivery later"},
        "history": [("ghosted", "no reply to March 2026 RFQ"), ("ghosted", "no reply to follow-up call")],
    },
    {
        "name": "Ganga Buildmart", "city": "Prayagraj", "state": "Uttar Pradesh",
        "gst_number": "09AAFCG3456J1Z1", "categories": ["cement", "aggregate"],
        "notes": "Newer outfit, aggressive pricing, active on WhatsApp and email.",
        "contacts": [("whatsapp", "+91 79059 66666", True), ("email", "gangabuildmart@outlook.com", False)],
        "certs": [("BIS", "CM/L-5544332", TODAY + timedelta(days=320), "valid")],
        "demo_replies": {"cement": "368 per bag all inclusive delivered at site. delivery by monday. BIS cert attached.", "channel": "whatsapp", "response_hours": 4},
        "history": [("replied_fast", "instant WhatsApp quotes"), ("clear_commitment", "committed and met a tight deadline")],
    },
    {
        "name": "Prayag Steel & TMT", "city": "Prayagraj", "state": "Uttar Pradesh",
        "gst_number": "09AAHCP7890K1Z4", "categories": ["steel"],
        "notes": "TMT specialist — Kamdhenu and Rathi dealer. Quick on WhatsApp.",
        "contacts": [("whatsapp", "+91 96218 77777", True), ("phone", "+91 96218 77777", False)],
        "certs": [("ISI", "IS1786/CM/L-222111", TODAY + timedelta(days=500), "valid")],
        "demo_replies": {"steel": "Fe500D at 54500 per tonne delivered incl GST. MTC and test certificate attached. dispatch in 5 days.", "channel": "whatsapp", "response_hours": 3},
        "history": [("replied_fast", "quotes within the hour"), ("on_time_delivery", "12 MT delivered on time"), ("cert_verified", "MTC shared proactively")],
    },
    {
        "name": "Awadh Ispat", "city": "Lucknow", "state": "Uttar Pradesh",
        "gst_number": "09AAJCA2345L1Z7", "categories": ["steel"],
        "notes": "Regional stockist, better rates for full-truck loads.",
        "contacts": [("email", "awadhispat.sales@gmail.com", True), ("phone", "+91 90260 88888", False)],
        "certs": [("ISI", "IS1786/CM/L-333444", TODAY + timedelta(days=150), "valid")],
        "demo_replies": {"steel": "53800 per tonne ex-godown plus GST, transport extra. 7 days from advance.", "channel": "email", "response_hours": 14},
        "history": [("replied_slow", "replies within a day"), ("on_time_delivery", "consistent on committed dates")],
    },
    {
        "name": "Yamuna Sand Suppliers", "city": "Prayagraj", "state": "Uttar Pradesh",
        "gst_number": "", "categories": ["sand", "aggregate"],
        "notes": "River sand and gitti, phone bookings only, cash friendly.",
        "contacts": [("phone", "+91 83038 99999", True)],
        "certs": [],
        "demo_replies": {"sand": "4200 per brass delivered. no certificate for sand. 2 days.", "channel": "call_note", "response_hours": 6},
        "history": [("replied_fast", "answers calls promptly"), ("late_delivery", "one trip delayed by truck breakdown")],
    },
]

SAMPLE_RFQS = [
    # Fully analyzed sample so the dashboard shows a finished pipeline
    {"text": f"Need 20 tonnes Fe500D TMT steel in Prayagraj by {(TODAY + timedelta(days=12)).strftime('%d %B')}, "
             "budget ₹55,000 per tonne delivered, ISI test certificate mandatory",
     "simulate": True, "analyze": True},
    # In-flight sample stuck at outreach — shows the waiting state
    {"text": f"Need 30 brass river sand at Prayagraj site by {(TODAY + timedelta(days=8)).strftime('%d %B')}, budget ₹4,500 per brass",
     "simulate": False, "analyze": False},
]


def seed_if_empty() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Vendor).count() > 0:
            return

        for spec in VENDORS:
            vendor = Vendor(
                name=spec["name"], city=spec["city"], state=spec["state"],
                gst_number=spec["gst_number"], categories=spec["categories"],
                notes=spec["notes"], demo_replies=spec["demo_replies"],
            )
            db.add(vendor)
            db.flush()
            for channel, value, preferred in spec["contacts"]:
                db.add(VendorContact(vendor_id=vendor.id, channel=channel,
                                     value=value, is_preferred=preferred, verified=True))
            for cert_type, number, valid_till, status in spec["certs"]:
                db.add(Certificate(vendor_id=vendor.id, cert_type=cert_type, number=number,
                                   issued_by="BIS" if cert_type == "BIS" else "BIS/ISI",
                                   valid_till=valid_till, status=status))
            for event_type, detail in spec["history"]:
                memory_svc.record_event(db, vendor.id, event_type, detail)
        db.commit()

        # Sample RFQs run through the real pipeline (same code paths as the API)
        from .routers.rfqs import simulate_replies  # local import avoids a cycle

        for sample in SAMPLE_RFQS:
            fields, source, confidence = parse_requirement(sample["text"])
            requirement = Requirement(raw_text=sample["text"], parse_source=source,
                                      parse_confidence=confidence, **fields)
            db.add(requirement)
            db.flush()
            rfq = RFQ(requirement_id=requirement.id)
            db.add(rfq)
            db.commit()

            launch_rfq(rfq.id)
            if sample["simulate"]:
                simulate_replies(rfq.id, db)
            if sample["analyze"]:
                analyze_rfq(rfq.id)
        db.commit()
        print("Seeded vendor pool and sample RFQs.")
    finally:
        db.close()