# RFQ Copilot

**An AI procurement analyst for Indian contractors.**

A contractor types one line — *"Need 500 bags of OPC 53 cement in Prayagraj by 15 August, budget ₹390 per bag delivered, BIS certificate mandatory"* — and RFQ Copilot parses it, scouts the existing vendor pool, contacts each vendor on the channel they actually use (WhatsApp, email, or a call note — this is India, email is not assumed), turns messy replies like *"7300 per tonne ex godown, gst extra, will try our best"* into structured quotes, levels every quote onto one comparable basis, and recommends the **top 3 vendors with evidence-backed reasoning**.

This is **not a marketplace**. It sits on top of the contractor's own vendor pool and helps them decide faster.

---

## Architecture

```
┌───────────────┐        ┌──────────────────────────────────────────┐
│  Next.js UI    │  REST  │  FastAPI                                  │
│  (dashboard,   │ ─────► │  ┌───────────── LangGraph ─────────────┐ │
│  RFQ pipeline, │        │  │ sourcing graph:  Scout → Outreach    │ │
│  shortlist,    │        │  │ analysis graph:  Collect → Analyst   │ │
│  vendor memory)│        │  └──────────────────────────────────────┘ │
└───────────────┘        │  Deterministic services (no LLM):         │
                         │   normalization · GST/freight leveling ·  │
                         │   unit conversion · scoring · validation  │
                         │  LLM layer (Groq behind an abstraction):  │
                         │   requirement parsing · reply parsing ·   │
                         │   RFQ drafting · explanation polish       │
                         │  PostgreSQL (or SQLite demo fallback)     │
                         └──────────────────────────────────────────┘
```

### The four brains

| Agent | Job |
|---|---|
| **Scout** | Searches the vendor pool by product + location, checks profile completeness, flags anomalies (expired BIS certificate, invalid GSTIN format, missing contact data, unclear product match) |
| **Outreach** | Picks the best channel per vendor (preferred contact → WhatsApp → email → call note), drafts the RFQ message, logs sent messages, ingests and parses replies, flags missing fields for follow-up |
| **Analyst** | Levels every quote to one basis (requirement unit, delivered, GST-inclusive), scores price / delivery confidence / documentation / reliability, ranks a top-3 shortlist with a plain-language explanation |
| **Vendor Memory** | Every RFQ writes behaviour back — response speed, ghosting, evasive answers, on-time delivery, certificate quality — and future rankings read it |

### LLM policy

Deterministic Python does everything that must be exact: unit conversion (1 tonne = 20 × 50 kg bags), GST leveling (product-specific rates), freight estimation, date math, scoring formulas. The LLM (Groq, behind a one-file provider abstraction in `backend/app/llm.py`) only extracts meaning from messy text and polishes explanations. **Every LLM call has a deterministic fallback, so the app runs fully with no API key (demo mode).**

---

## Folder structure

```
backend/
  app/
    main.py              FastAPI app, CORS, auto-seed on startup
    config.py            env + business rules (GST rates, freight estimates)
    database.py          engine (Postgres w/ pgvector, or SQLite fallback)
    models.py            vendors, vendor_contacts, requirements, rfqs,
                         rfq_messages, quotes, parsed_quote_items,
                         certificates, vendor_memory, reliability_events,
                         audit_logs
    schemas.py           typed request/response models
    llm.py               provider abstraction: Groq | Mock (demo mode)
    agents/
      graph.py           LangGraph sourcing + analysis graphs
      scout.py           vendor search, verification, anomaly flags
      outreach.py        channel outreach + reply ingestion
      analyst.py         scoring, top-3 shortlist, explanation
    services/
      requirement_parser.py   NL requirement → structured object
      reply_parser.py         messy reply → structured quote + evidence
      normalization.py        per bag/tonne, delivered/ex-godown, GST leveling
      scoring.py              price/delivery/docs/reliability formulas
      channels.py             channel selection + mock senders
      memory.py               vendor memory write-back
      audit.py                audit log helper
    routers/             requirements, rfqs, vendors endpoints
    seed.py              9 realistic vendors + 2 sample RFQs + history
  run.py                 uvicorn entrypoint
frontend/
  app/                   dashboard, /rfq/[id] pipeline page, /vendors
  components/            shortlist podium, quote table, outreach tracker,
                         scout results, vendor drawer w/ memory timeline
  lib/                   typed API client
```

---

## Local setup

### Prerequisites
- Python 3.11+
- Node 18+
- (Optional) PostgreSQL 15+ with the pgvector extension — **not required**; without it the backend uses a local SQLite file

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows   (source .venv/bin/activate on mac/linux)
pip install -r requirements.txt
copy .env.example .env          # cp on mac/linux — works as-is with no edits
python run.py                   # → http://localhost:8000  (docs at /docs)
```

On first boot the database is created and **seeded automatically**: 9 vendors across cement/steel/sand with mixed channels (WhatsApp-only, email-only, phone-only), mixed certificate states (valid / expired / missing number), reliability history, one fully analyzed sample RFQ and one mid-flight RFQ.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                     # → http://localhost:3000
```

### Environment variables (`backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | *(empty → SQLite)* | Set to `postgresql+psycopg2://...` for Postgres + pgvector |
| `GROQ_API_KEY` | *(empty → demo mode)* | Enables LLM parsing/drafting; app is fully functional without it |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Swap models freely |
| `DEFAULT_GST_RATE` | `0.28` | Fallback GST rate for leveling |
| `FREIGHT_ESTIMATE_PER_BAG` / `_PER_TONNE` | `10` / `200` | Added when a quote is ex-godown / freight extra |

---

## Demo walkthrough (2 minutes)

1. Open **http://localhost:3000** — the dashboard already shows a completed steel RFQ and an in-flight sand RFQ.
2. Click **"Use example"** → **Start RFQ**. Within seconds: the requirement is parsed into a structured panel, Scout lists candidates with anomaly flags (expired certificate, missing GSTIN), and Outreach sends RFQs — note each vendor got its own channel (WhatsApp / email / call note).
3. Click **"Simulate vendor replies"** — messy replies flow in: per-bag vs per-tonne, GST extra vs inclusive, ex-godown vs delivered, one vendor answers *"will try our best"*, one vendor **ghosts entirely** (and takes a reliability hit).
4. Click **"Generate shortlist"** — the leveled comparison table shows every normalization step (₹7300/tonne ex-godown + GST becomes a comparable per-bag delivered price), and the **top-3 podium** appears with scores, reasons, and risk callouts. The "cheapest" quote often stops being cheapest once GST and freight are leveled — that's the product's money shot.
5. Click any vendor → the **profile drawer** shows contacts, certificates, and the reliability timeline that vendor memory built.
6. Log a real reply yourself via **"Log a reply"** (paste any messy text) — it parses live.

## API surface

`POST /api/requirements` · `GET /api/rfqs` · `GET /api/rfqs/{id}` · `POST /api/rfqs/{id}/scout` · `POST /api/rfqs/{id}/outreach` · `POST /api/rfqs/{id}/replies` · `POST /api/rfqs/{id}/replies/upload` (PDF/image quote) · `POST /api/rfqs/{id}/simulate-replies` · `POST /api/rfqs/{id}/shortlist` · `GET /api/vendors` · `GET /api/vendors/search` · `GET /api/vendors/{id}`

Interactive docs: **http://localhost:8000/docs**

## Production notes

- WhatsApp/email senders are mocked one function each in `services/channels.py` — swap in WhatsApp Business API / SMTP without touching anything else.
- pgvector is enabled automatically on Postgres for future semantic vendor search; keyword search is the default path.
- The LLM provider is one class — point it at any OpenAI-compatible endpoint.
=======
# Photon
