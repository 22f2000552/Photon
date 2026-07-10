from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import FRONTEND_ORIGIN, GROQ_API_KEY
from .database import init_db
from .routers import requirements, rfqs, vendors
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_if_empty()
    yield


app = FastAPI(title="RFQ Copilot", description="AI procurement analyst for Indian contractors",
              version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requirements.router)
app.include_router(rfqs.router)
app.include_router(vendors.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/api/health")
def health():
    return {"status": "ok", "llm": "groq" if GROQ_API_KEY else "demo-mode (no key needed)"}