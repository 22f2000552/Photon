from datetime import datetime, date

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now() -> datetime:
    return datetime.utcnow()


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), default="")
    state: Mapped[str] = mapped_column(String(100), default="")
    gst_number: Mapped[str] = mapped_column(String(30), default="")
    categories: Mapped[list] = mapped_column(JSON, default=list)  # ["cement", "steel"]
    notes: Mapped[str] = mapped_column(Text, default="")
    profile_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    # Canned messy replies per product family — powers demo simulation
    demo_replies: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    contacts: Mapped[list["VendorContact"]] = relationship(back_populates="vendor", cascade="all, delete-orphan")
    certificates: Mapped[list["Certificate"]] = relationship(back_populates="vendor", cascade="all, delete-orphan")
    memory: Mapped["VendorMemory"] = relationship(back_populates="vendor", uselist=False, cascade="all, delete-orphan")
    events: Mapped[list["ReliabilityEvent"]] = relationship(back_populates="vendor", cascade="all, delete-orphan")


class VendorContact(Base):
    __tablename__ = "vendor_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    channel: Mapped[str] = mapped_column(String(20))  # email | whatsapp | phone
    value: Mapped[str] = mapped_column(String(200))
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    vendor: Mapped[Vendor] = relationship(back_populates="contacts")


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    cert_type: Mapped[str] = mapped_column(String(50))  # BIS | ISI | Test Certificate
    number: Mapped[str] = mapped_column(String(100), default="")
    issued_by: Mapped[str] = mapped_column(String(200), default="")
    valid_till: Mapped[date | None] = mapped_column(Date, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), default="")
    # valid | expired | missing_number | invalid_format
    status: Mapped[str] = mapped_column(String(30), default="valid")

    vendor: Mapped[Vendor] = relationship(back_populates="certificates")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text)
    product: Mapped[str] = mapped_column(String(100), default="")
    grade: Mapped[str] = mapped_column(String(100), default="")
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), default="")
    location: Mapped[str] = mapped_column(String(100), default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_basis: Mapped[str] = mapped_column(String(50), default="")  # per bag delivered
    certifications: Mapped[list] = mapped_column(JSON, default=list)  # ["BIS"]
    delivery_terms: Mapped[str] = mapped_column(String(200), default="")
    parse_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    parse_source: Mapped[str] = mapped_column(String(20), default="rules")  # rules | llm
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class RFQ(Base):
    __tablename__ = "rfqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"))
    # draft -> scouting -> outreach -> collecting -> analyzed
    status: Mapped[str] = mapped_column(String(30), default="draft")
    scout_result: Mapped[list] = mapped_column(JSON, default=list)  # vendor candidates + flags
    shortlist: Mapped[list] = mapped_column(JSON, default=list)  # top-3 with reasoning
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    requirement: Mapped[Requirement] = relationship()
    messages: Mapped[list["RFQMessage"]] = relationship(back_populates="rfq", cascade="all, delete-orphan")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="rfq", cascade="all, delete-orphan")


class RFQMessage(Base):
    __tablename__ = "rfq_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    direction: Mapped[str] = mapped_column(String(10))  # outbound | inbound
    channel: Mapped[str] = mapped_column(String(20))  # email | whatsapp | call_note | upload | manual
    body: Mapped[str] = mapped_column(Text, default="")
    # sent | delivered | received | needs_clarification
    status: Mapped[str] = mapped_column(String(30), default="sent")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    rfq: Mapped[RFQ] = relationship(back_populates="messages")
    vendor: Mapped[Vendor] = relationship()


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    message_id: Mapped[int | None] = mapped_column(ForeignKey("rfq_messages.id"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")

    # Extracted fields (from messy reply)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_basis: Mapped[str] = mapped_column(String(30), default="")  # bag | tonne | kg
    delivery_included: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # delivered vs ex-godown
    gst_included: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    freight_included: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    delivery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivery_vague: Mapped[bool] = mapped_column(Boolean, default=False)
    cert_attached: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    flags: Mapped[list] = mapped_column(JSON, default=list)  # ambiguity / anomaly flags

    # Leveled comparison (deterministic Python, never LLM)
    normalized_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_basis: Mapped[str] = mapped_column(String(80), default="")
    normalization_notes: Mapped[list] = mapped_column(JSON, default=list)

    # Scores 0-100
    price_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    delivery_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    doc_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reliability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_evidence: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    rfq: Mapped[RFQ] = relationship(back_populates="quotes")
    vendor: Mapped[Vendor] = relationship()
    items: Mapped[list["ParsedQuoteItem"]] = relationship(back_populates="quote", cascade="all, delete-orphan")


class ParsedQuoteItem(Base):
    """Field-level extraction trace: what was extracted, from which phrase."""

    __tablename__ = "parsed_quote_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"))
    field: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence: Mapped[str] = mapped_column(String(300), default="")

    quote: Mapped[Quote] = relationship(back_populates="items")


class VendorMemory(Base):
    """Aggregated behavioural memory — the compounding layer."""

    __tablename__ = "vendor_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), unique=True)
    avg_response_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_rate: Mapped[float] = mapped_column(Float, default=0.0)  # replied / contacted
    on_time_rate: Mapped[float] = mapped_column(Float, default=0.0)  # honored promised dates
    ghost_count: Mapped[int] = mapped_column(Integer, default=0)
    doc_quality: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1
    reliability_score: Mapped[float] = mapped_column(Float, default=50.0)  # 0-100
    rfq_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    vendor: Mapped[Vendor] = relationship(back_populates="memory")


class ReliabilityEvent(Base):
    __tablename__ = "reliability_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    rfq_id: Mapped[int | None] = mapped_column(ForeignKey("rfqs.id"), nullable=True)
    # replied_fast | replied_slow | ghosted | on_time_delivery | late_delivery
    # | cert_verified | cert_issue | clear_commitment | evasive_answer
    event_type: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(String(300), default="")
    impact: Mapped[float] = mapped_column(Float, default=0.0)  # +/- on reliability score
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    vendor: Mapped[Vendor] = relationship(back_populates="events")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)