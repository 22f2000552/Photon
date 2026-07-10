"""Typed request/response models for the API."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Requirements ----------

class RequirementCreate(BaseModel):
    text: str


class RequirementOut(ORM):
    id: int
    raw_text: str
    product: str
    grade: str
    quantity: float | None
    unit: str
    location: str
    deadline: date | None
    budget_amount: float | None
    budget_basis: str
    certifications: list
    delivery_terms: str
    parse_confidence: float
    parse_source: str


# ---------- Vendors ----------

class ContactOut(ORM):
    id: int
    channel: str
    value: str
    is_preferred: bool
    verified: bool


class CertificateOut(ORM):
    id: int
    cert_type: str
    number: str
    issued_by: str
    valid_till: date | None
    status: str


class MemoryOut(ORM):
    avg_response_hours: float | None
    response_rate: float
    on_time_rate: float
    ghost_count: int
    doc_quality: float
    reliability_score: float
    rfq_count: int


class EventOut(ORM):
    id: int
    event_type: str
    detail: str
    impact: float
    rfq_id: int | None
    created_at: datetime


class VendorOut(ORM):
    id: int
    name: str
    city: str
    state: str
    gst_number: str
    categories: list
    notes: str
    profile_completeness: float
    contacts: list[ContactOut] = []
    certificates: list[CertificateOut] = []
    memory: MemoryOut | None = None


class VendorProfileOut(VendorOut):
    events: list[EventOut] = []


# ---------- RFQ pipeline ----------

class MessageOut(ORM):
    id: int
    vendor_id: int
    direction: str
    channel: str
    body: str
    status: str
    meta: dict
    created_at: datetime


class ParsedItemOut(ORM):
    field: str
    value: str
    confidence: float
    evidence: str


class QuoteOut(ORM):
    id: int
    vendor_id: int
    raw_text: str
    price: float | None
    unit_basis: str
    delivery_included: bool | None
    gst_included: bool | None
    freight_included: bool | None
    delivery_days: int | None
    delivery_date: date | None
    delivery_vague: bool
    cert_attached: bool
    confidence: float
    flags: list
    normalized_price: float | None
    normalized_basis: str
    normalization_notes: list
    price_score: float | None
    delivery_score: float | None
    doc_score: float | None
    reliability_score: float | None
    overall_score: float | None
    rank: int | None
    score_evidence: dict
    items: list[ParsedItemOut] = []


class RFQSummary(ORM):
    id: int
    status: str
    created_at: datetime
    requirement: RequirementOut
    quote_count: int = 0
    contacted_count: int = 0


class RFQDetail(ORM):
    id: int
    status: str
    created_at: datetime
    requirement: RequirementOut
    scout_result: list
    shortlist: list
    explanation: str
    messages: list[MessageOut] = []
    quotes: list[QuoteOut] = []
    vendors: list[VendorOut] = []  # every vendor referenced by this RFQ


class ReplyIn(BaseModel):
    vendor_id: int
    channel: str = "manual"  # email | whatsapp | call_note | manual
    text: str